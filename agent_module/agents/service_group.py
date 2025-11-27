"""
Service Build Group - Service build and execution group (Flow 2)
Uses CrewAI framework with Mock LLM
Builds and executes services based on SIPOC document
"""
import asyncio
from typing import Optional

# CrewAI disabled for Mock mode - no API key required
CREWAI_AVAILABLE = False
from service_module.mock_services.fund_services import FundServices, FUND_DATA


class ServiceBuildGroup:
    """
    Service Build Execution Group - 3 Experts

    Expert composition:
    1. CodeGenerator: Generate service code based on SIPOC
    2. Validator: Validate generated code correctness
    3. Executor: Execute service and return results

    Responsibilities:
    - Receive SIPOC document
    - Generate service code (Mock)
    - Validate code
    - Execute service
    """

    def __init__(self):
        # Mock mode - no CrewAI agents needed
        pass

    async def build_and_execute(self, sipoc: dict, intent: str, on_expert_speak=None) -> dict:
        """
        Build and execute service

        Args:
            sipoc: SIPOC document (dict format or SIPOCDocument object)
            intent: Intent type
            on_expert_speak: Callback for expert speech display (name, emoji, speech)

        Returns:
            {
                "success": bool,
                "execution_result": dict,      # Execution result
                "build_summary": str,          # Build summary
            }
        """
        # Handle SIPOC object
        if hasattr(sipoc, 'to_dict'):
            sipoc_dict = sipoc.to_dict()
        elif hasattr(sipoc, 'title'):
            sipoc_dict = {
                "title": sipoc.title,
                "description": sipoc.description,
            }
        else:
            sipoc_dict = sipoc

        # Code Generator expert
        if on_expert_speak:
            await on_expert_speak("CodeGenerator", "🔧", "Generating service code...")
        await asyncio.sleep(0.5)

        # Validator expert
        if on_expert_speak:
            await on_expert_speak("Validator", "✅", "Validation passed ✓")
        await asyncio.sleep(0.5)

        # If CrewAI available, run Crew
        crew_output = None
        if CREWAI_AVAILABLE:
            crew_output = await self._run_crew(sipoc_dict, intent)

        # Actually execute service (Mock)
        execution_result = await self._execute_service(intent)

        # Executor expert - display detailed results
        if on_expert_speak:
            data = execution_result.get("data", {})
            count = data.get("processed_count", 0)
            total_amount = data.get("total_amount", 0)
            if total_amount:
                await on_expert_speak("Result", "📊", f"Completed: {count} funds | Total dividend: ${total_amount:,.2f}")
            else:
                await on_expert_speak("Result", "📊", f"Completed: {count} items processed")

        return {
            "success": True,
            "execution_result": execution_result,
            "build_summary": crew_output or "Service built and executed successfully",
        }

    async def _run_crew(self, sipoc: dict, intent: str) -> Optional[str]:
        """Run CrewAI multi-expert collaboration"""
        try:
            title = sipoc.get("title", "Unknown Service")

            tasks = [
                Task(
                    description=f"""Generate service code based on SIPOC document:

SIPOC Document:
- Title: {title}
- Type: {sipoc.get('type', 'unknown')}
- Process: {sipoc.get('process_steps', sipoc.get('process', []))}

Please generate executable service code.""",
                    expected_output="Service code",
                    agent=self.code_generator,
                ),
                Task(
                    description="""Validate generated service code:

Validation items:
1. Syntax correctness
2. Parameter validation completeness
3. Error handling coverage
4. Security check

Output validation report.""",
                    expected_output="Code validation report",
                    agent=self.validator,
                ),
                Task(
                    description="""Execute validated service:

1. Prepare execution environment
2. Call service function
3. Collect execution results
4. Record execution logs

Return execution results.""",
                    expected_output="Execution results",
                    agent=self.executor,
                ),
            ]

            crew = Crew(
                agents=[self.code_generator, self.validator, self.executor],
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
            )

            result = crew.kickoff()
            return str(result)

        except Exception as e:
            print(f"CrewAI execution error: {e}")
            return None

    async def _execute_service(self, intent: str) -> dict:
        """
        Execute actual service (Mock)

        Call corresponding Mock service based on intent type
        """
        # Dividend processing - also handle create_workflow with dividend keywords
        if "dividend" in intent or "workflow" in intent or "create" in intent:
            # For Flow 2 (create workflow), simulate dividend processing
            fund_codes = list(FUND_DATA.keys())
            result = await FundServices.process_dividend(fund_codes, "cash")
            return result

        # NAV query (batch)
        if "nav" in intent:
            results = []
            for code in FUND_DATA.keys():
                nav_result = await FundServices.get_fund_nav(code)
                if nav_result.get("success"):
                    results.append(nav_result["data"])
            return {
                "success": True,
                "data": {
                    "processed_count": len(results),
                    "funds": results,
                },
            }

        # Generic success response - still process dividends for demo
        fund_codes = list(FUND_DATA.keys())
        result = await FundServices.process_dividend(fund_codes, "cash")
        return result
