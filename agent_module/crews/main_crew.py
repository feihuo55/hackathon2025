"""
Main Crew - Main orchestrator, unified entry point
IntentAgent -> RAG -> Flow 1 or Flow 2

Core flow:
1. IntentAgent analyzes user intent
2. RAG retrieves matching services
3. Branch based on RAG results:
   - Service matched -> Flow 1 (ExecutorGroup executes)
   - Not matched -> Flow 2 (GroupChat analysis -> SIPOC -> ServiceGroup executes)
"""
import asyncio
from typing import Optional

from ..agents.intent_agent import IntentAgent
from ..agents.executor_group import ExecutorGroup
from ..agents.group_chat import RequirementGroupChat
from ..agents.service_group import ServiceBuildGroup
from service_module.mock_services import ServiceRegistry
from service_module.sipoc import SIPOCGenerator
from rag_module.retrieval.service_matcher import ServiceMatcher
from utils.language_detector import get_message, detect_language


# Intent to Service ID mapping (for quick matching)
INTENT_SERVICE_MAP = {
    "fund_nav": "getFundNAV",
    "fund_dividend_query": "getFundDividend",
    "fund_list": "getAllFunds",
    "dividend_process": "processDividend",
}


class MainCrew:
    """
    Main Orchestrator - Agent Module unified entry point

    Responsibilities:
    1. Coordinate IntentAgent and RAG
    2. Route to Flow 1 or Flow 2 based on RAG results
    3. Manage session state (Flow 2 multi-turn conversation)
    """

    def __init__(
        self,
        service_registry: ServiceRegistry = None,
        service_matcher: ServiceMatcher = None,
        memory_manager=None,
    ):
        # Service components
        self.registry = service_registry or ServiceRegistry()
        self.matcher = service_matcher or ServiceMatcher()

        # Initialize service index
        self._init_service_index()

        # Agents
        self.intent_agent = IntentAgent()

        # Flow 1: Execution group
        self.executor_group = ExecutorGroup(self.registry)

        # Flow 2: Requirement analysis group + Build execution group
        self.requirement_group = RequirementGroupChat()
        self.service_group = ServiceBuildGroup()
        self.sipoc_generator = SIPOCGenerator()

        # Session state (for Flow 2 multi-turn conversation)
        self._sessions = {}

    def _init_service_index(self):
        """Initialize service index"""
        services = self.registry.get_all_services()
        self.matcher.index_services(services)

    async def process(
        self,
        user_input: str,
        session_id: str = "default",
        lang: str = None,
        on_thinking=None,
        on_expert_speak=None,
    ) -> dict:
        """
        Process user input - unified entry point

        Args:
            user_input: User input text
            session_id: Session ID (for Flow 2 multi-turn)
            lang: Language code (None for auto-detect)
            on_thinking: Callback for thinking steps display
            on_expert_speak: Callback for expert speech display

        Returns:
            Processing result
        """
        # Auto-detect language
        if lang is None:
            lang = detect_language(user_input)

        # Check session state for Flow 2 multi-stage
        state = self._sessions.get(session_id, {})
        stage = state.get("stage")

        # Handle different Flow 2 stages
        if stage == "rag_not_found":
            return await self._handle_rag_not_found_response(user_input, session_id, lang, on_expert_speak)
        elif stage == "group_chat":
            return await self._handle_group_chat(user_input, session_id, lang, on_expert_speak)
        elif stage == "sipoc_confirming":
            return await self._handle_sipoc_confirmation(user_input, session_id, lang, on_expert_speak)

        # FAST PATH: If user input contains "create", go directly to Flow 2
        if "create" in user_input.lower() or "创建" in user_input:
            # Still do intent analysis for display
            intent_result = await self.intent_agent.analyze(user_input)
            if on_thinking and intent_result.get("thinking_steps"):
                await on_thinking(intent_result["thinking_steps"])
            if on_expert_speak:
                await on_expert_speak("RAG", "🔍", "Create request detected → Flow 2")
            # Force intent to create_workflow if unknown
            if intent_result["intent"] == "unknown":
                intent_result["intent"] = "create_workflow"
            return await self._start_flow2(user_input, intent_result, session_id, lang)

        # Step 1: Intent analysis
        intent_result = await self.intent_agent.analyze(user_input)

        # Display thinking steps via callback
        if on_thinking and intent_result.get("thinking_steps"):
            await on_thinking(intent_result["thinking_steps"])

        if intent_result["intent"] == "unknown":
            return {
                "success": False,
                "message": get_message('unknown_intent', lang),
            }

        # Step 2: RAG service retrieval
        rag_result = await self._match_service(
            intent=intent_result["intent"],
            entities=intent_result["entities"],
            user_input=user_input,
        )

        # Display RAG result
        if on_expert_speak:
            if rag_result.get("matched"):
                await on_expert_speak("RAG", "🔍", f"Found service: {rag_result['service_id']}")
            else:
                await on_expert_speak("RAG", "🔍", "No matching service found")

        # Step 3: Branch based on RAG result
        if rag_result.get("matched"):
            # Flow 1: Execute existing service
            return await self._execute_flow1(intent_result, rag_result, lang, on_expert_speak)
        else:
            # Flow 2: RAG not found - pause and wait for user input
            return await self._start_flow2(user_input, intent_result, session_id, lang)

    async def _match_service(
        self,
        intent: str,
        entities: dict,
        user_input: str,
    ) -> dict:
        """
        Service matching (combining intent mapping and RAG)

        Prioritize intent mapping for quick match, otherwise use RAG retrieval
        """
        # Fast path: Direct mapping based on intent
        if intent in INTENT_SERVICE_MAP:
            service_id = INTENT_SERVICE_MAP[intent]
            service = self.registry.get_service(service_id)
            if service:
                # Build parameters
                params = self._build_params(service_id, entities)
                return {
                    "matched": True,
                    "service_id": service_id,
                    "params": params,
                    "match_type": "intent_map",
                }

        # RAG retrieval
        best_match = await self.matcher.find_best_match(user_input, threshold=0.3)
        if best_match:
            service_id = best_match.get("service_id")
            params = self._build_params(service_id, entities)
            return {
                "matched": True,
                "service_id": service_id,
                "params": params,
                "relevance_score": best_match.get("relevance_score"),
                "match_type": "rag",
            }

        # Not matched
        return {"matched": False}

    def _build_params(self, service_id: str, entities: dict) -> dict:
        """Build parameters based on service ID and entities"""
        params = {}

        if service_id in ["getFundNAV", "getFundDividend"]:
            params["fund_code"] = entities.get("fund_code", "")

        elif service_id == "processDividend":
            # Batch processing: Get all fund codes
            from service_module.mock_services.fund_services import FUND_DATA
            if entities.get("scope") == "all":
                params["fund_codes"] = list(FUND_DATA.keys())
            elif entities.get("fund_code"):
                params["fund_codes"] = [entities["fund_code"]]
            else:
                params["fund_codes"] = list(FUND_DATA.keys())

            params["method"] = entities.get("method", "cash")

        return params

    async def _execute_flow1(
        self,
        intent_result: dict,
        rag_result: dict,
        lang: str,
        on_expert_speak=None,
    ) -> dict:
        """
        Flow 1: Execute existing service

        RAG matched service -> ExecutorGroup executes -> Format result
        """
        service_id = rag_result["service_id"]
        params = rag_result.get("params", {})

        # Display executor expert
        if on_expert_speak:
            await on_expert_speak("Executor", "📊", f"Calling {service_id}...")

        # Call ExecutorGroup
        result = await self.executor_group.execute(service_id, params, lang)

        # Display formatter expert
        if on_expert_speak:
            await on_expert_speak("Formatter", "📋", "Formatting output...")

        return result

    async def _start_flow2(
        self,
        user_input: str,
        intent_result: dict,
        session_id: str,
        lang: str,
    ) -> dict:
        """
        Flow 2 Step 1: RAG not found - pause and prompt user

        Save state and wait for user to provide more info or confirm
        """
        intent = intent_result.get("intent", "unknown")

        # Save state
        self._sessions[session_id] = {
            "stage": "rag_not_found",
            "original_input": user_input,
            "intent": intent,
            "entities": intent_result.get("entities", {}),
            "lang": lang,
            "collected_info": [user_input],  # Start collecting user inputs
        }

        return {
            "success": True,
            "status": "rag_not_found",
            "message": f"""**No existing service found for your request.**

I detected intent: **{intent}**

To create a new automated workflow, I need more information.

**Options:**
- Reply **confirm** to proceed with Group Chat analysis
- Provide additional details about your requirements
- Reply **cancel** to abort""",
        }

    async def _handle_rag_not_found_response(
        self,
        user_input: str,
        session_id: str,
        lang: str,
        on_expert_speak=None,
    ) -> dict:
        """Handle user response after RAG not found"""
        state = self._sessions[session_id]

        # Check if cancelled
        cancel_keywords = ["cancel", "no", "abort", "取消", "不", "算了"]
        if any(kw in user_input.lower() for kw in cancel_keywords):
            del self._sessions[session_id]
            return {"success": True, "status": "cancelled", "message": "Operation cancelled."}

        # Any other input (confirm OR additional info) triggers Group Chat
        # Collect the user input
        state["collected_info"].append(user_input)
        state["stage"] = "group_chat"
        state["chat_round"] = 0
        self._sessions[session_id] = state

        # Start Group Chat with all collected info
        return await self._handle_group_chat(user_input, session_id, lang, on_expert_speak)

    async def _handle_group_chat(
        self,
        user_input: str,
        session_id: str,
        lang: str,
        on_expert_speak=None,
    ) -> dict:
        """Handle Group Chat multi-round conversation"""
        state = self._sessions[session_id]
        chat_round = state.get("chat_round", 0)

        # Collect all info for analysis
        all_info = " | ".join(state.get("collected_info", []))

        # Run Group Chat analysis (with expert display)
        analysis = await self.requirement_group.analyze(all_info, state["intent"], on_expert_speak)
        requirements = analysis["requirements"]

        # Generate SIPOC
        sipoc = await self.sipoc_generator.generate_from_requirements(requirements)

        # Move to SIPOC confirmation stage
        state["stage"] = "sipoc_confirming"
        state["sipoc"] = sipoc
        state["requirements"] = requirements
        self._sessions[session_id] = state

        # Format confirmation message
        md = self.sipoc_generator.render_markdown(sipoc)

        return {
            "success": True,
            "status": "sipoc_confirming",
            "message": f"""**Group Chat Analysis Complete!**

Experts have analyzed your requirements and generated a SIPOC document:

{md}

**Please review and confirm:**
- Reply **confirm** or **yes** to build and execute the service
- Reply **cancel** to abort
- Or describe what needs to be modified""",
            "sipoc": sipoc.to_dict() if hasattr(sipoc, 'to_dict') else sipoc,
        }

    async def _handle_sipoc_confirmation(
        self,
        user_input: str,
        session_id: str,
        lang: str,
        on_expert_speak=None,
    ) -> dict:
        """Handle SIPOC confirmation - build and execute service"""
        state = self._sessions[session_id]

        # Check if confirmed
        confirm_keywords = ["confirm", "ok", "yes", "确认", "好", "执行", "是", "可以"]
        if any(kw in user_input.lower() for kw in confirm_keywords):
            # Execute ServiceGroup (with callback for expert display)
            sipoc = state["sipoc"]
            intent = state["intent"]

            build_result = await self.service_group.build_and_execute(sipoc, intent, on_expert_speak)

            # Clear session
            del self._sessions[session_id]

            # Format completion message
            completion_msg = self._format_completion_message(build_result, lang)

            return {
                "success": True,
                "status": "completed",
                "message": completion_msg,
                "sipoc": sipoc.to_dict() if hasattr(sipoc, 'to_dict') else sipoc,
                "result": build_result.get("execution_result", {}),
            }

        # User cancelled
        cancel_keywords = ["cancel", "no", "取消", "不", "算了"]
        if any(kw in user_input.lower() for kw in cancel_keywords):
            del self._sessions[session_id]
            return {"success": True, "status": "cancelled", "message": "Operation cancelled."}

        # User wants modification - collect new info and re-analyze
        state["collected_info"].append(user_input)
        state["stage"] = "group_chat"
        self._sessions[session_id] = state

        return await self._handle_group_chat(user_input, session_id, lang, on_expert_speak)

    def _format_confirmation_message(self, sipoc, analysis: dict, lang: str) -> str:
        """Format confirmation message"""
        # Render SIPOC as Markdown
        md = self.sipoc_generator.render_markdown(sipoc)

        experts = analysis.get("experts_involved", [])
        experts_str = ", ".join(experts)

        if lang == "zh":
            return f"""**Expert Analysis Complete!**

{experts_str} have completed requirement analysis. Generated process document:

{md}

Please confirm the process:
- Reply **confirm** or **yes** to proceed
- Reply **cancel** to abort
- Or describe what needs to be modified"""

        return f"""**Expert Analysis Complete!**

{experts_str} have completed requirement analysis. Generated process document:

{md}

Please confirm the process:
- Reply **confirm** or **yes** to proceed
- Reply **cancel** to abort
- Or describe what needs to be modified"""

    def _format_completion_message(self, result: dict, lang: str) -> str:
        """Format completion message with detailed results"""
        exec_result = result.get("execution_result", {})
        data = exec_result.get("data", {})

        processed_count = data.get("processed_count", 0)
        total_amount = data.get("total_amount", 0)

        msg = """**Service Created and Executed Successfully!**

**Results:**
"""
        msg += f"- Funds processed: {processed_count}\n"

        if total_amount:
            msg += f"- Total dividend amount: ${total_amount:,.2f}\n"

        # Add details if available
        details = data.get("details", [])
        if details:
            msg += "\n**Details:**\n"
            msg += "| Fund | Amount | Method | Status |\n"
            msg += "|------|--------|--------|--------|\n"
            for d in details[:5]:  # Show first 5
                msg += f"| {d.get('name', 'N/A')} | ${d.get('total_amount', 0):,.2f} | {d.get('method', 'cash')} | {d.get('status', 'done')} |\n"

        msg += "\nAll details have been recorded in the system."
        return msg

    def get_session_state(self, session_id: str) -> Optional[dict]:
        """Get session state (for debugging)"""
        return self._sessions.get(session_id)

    def clear_session(self, session_id: str):
        """Clear session state"""
        if session_id in self._sessions:
            del self._sessions[session_id]
