"""
Group Chat - Four-expert requirement analysis group (Flow 2)
Uses CrewAI framework with Mock LLM
Outputs requirements dict for SIPOC Generator
"""
import asyncio
from typing import Optional

# CrewAI disabled for Mock mode - no API key required
CREWAI_AVAILABLE = False


class RequirementGroupChat:
    """
    Requirement Analysis Group Chat - 4 Experts

    Expert composition:
    1. Planner: Analyze requirements, assign tasks to experts
    2. BA (Business Analyst): Analyze business process, identify SIPOC elements
    3. Tech: Design technical implementation
    4. Summarizer: Consolidate analysis results, output structured requirements

    Responsibilities:
    - Receive user requirements
    - Multi-expert collaborative analysis
    - Output requirements dict (for SIPOC Generator)
    """

    def __init__(self):
        # Mock mode - no CrewAI agents needed
        pass

    async def analyze(self, user_input: str, intent: str, on_expert_speak=None) -> dict:
        """
        Execute requirement analysis, return requirements dict

        Args:
            user_input: Original user input
            intent: Intent type
            on_expert_speak: Callback for expert speech display (name, emoji, speech)

        Returns:
            {
                "success": bool,
                "requirements": dict,           # Requirement document (for SIPOC Generator)
                "experts_involved": list,       # List of involved experts
                "analysis_summary": str,        # Analysis summary
            }
        """
        # Expert list: (name, emoji, short speech)
        experts = [
            ("Planner", "🎯", "Assigning tasks to experts..."),
            ("BA", "📊", "Identifying SIPOC elements..."),
            ("Tech", "💻", "Designing technical solution..."),
            ("Summarizer", "📝", "Generating requirements doc..."),
        ]

        # Display each expert with callback
        for name, emoji, speech in experts:
            if on_expert_speak:
                await on_expert_speak(name, emoji, speech)
            await asyncio.sleep(0.6)  # Simulate thinking

        # If CrewAI available, run Crew
        crew_output = None
        if CREWAI_AVAILABLE:
            crew_output = await self._run_crew(user_input, intent)

        # Build requirements (Mock preset + dynamic content)
        requirements = self._build_requirements(user_input, intent)

        return {
            "success": True,
            "requirements": requirements,
            "experts_involved": ["Planner", "BA", "Tech", "Summarizer"],
            "analysis_summary": crew_output or "Requirement analysis complete",
        }

    async def _run_crew(self, user_input: str, intent: str) -> Optional[str]:
        """Run CrewAI multi-expert collaboration"""
        try:
            tasks = [
                Task(
                    description=f"""Analyze user requirements and assign tasks:
User Input: {user_input}
Intent Type: {intent}

Please plan analysis tasks and assign to BA and Tech experts.""",
                    expected_output="Task assignment plan",
                    agent=self.planner,
                ),
                Task(
                    description=f"""Perform business process analysis:
User Requirement: {user_input}

Please identify SIPOC elements:
- Supplier (data sources)
- Input (parameters)
- Process (steps)
- Output (results)
- Customer (users)""",
                    expected_output="SIPOC business element analysis",
                    agent=self.ba,
                ),
                Task(
                    description=f"""Perform technical analysis:
User Requirement: {user_input}

Please design:
- Service interface specification
- Data sources and data flow
- Parameters and return format""",
                    expected_output="Technical implementation plan",
                    agent=self.tech,
                ),
                Task(
                    description="""Consolidate expert analysis results, generate structured requirement document.

Integrate BA's business analysis and Tech's technical solution, output structured requirements for SIPOC document generation.""",
                    expected_output="Structured requirement document",
                    agent=self.summarizer,
                ),
            ]

            crew = Crew(
                agents=[self.planner, self.ba, self.tech, self.summarizer],
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
            )

            result = crew.kickoff(inputs={"user_input": user_input, "intent": intent})
            return str(result)

        except Exception as e:
            print(f"CrewAI execution error: {e}")
            return None

    def _build_requirements(self, user_input: str, intent: str) -> dict:
        """
        Build requirements dict (Mock preset)

        This is the structured requirement passed to SIPOC Generator
        """
        # Dividend processing flow
        if "dividend" in intent or "dividend" in user_input.lower():
            return {
                "title": "Fund Dividend Processing Workflow",
                "description": user_input,
                "type": "dividend_processing",
                "supplier": ["Fund companies", "Custody bank database", "Investor account system"],
                "input": ["Dividend fund list", "Distribution method (cash/reinvest)", "Record date", "Ex-date"],
                "process_steps": [
                    "Retrieve pending dividend fund list",
                    "Validate dividend announcement info",
                    "Calculate distribution amount per investor",
                    "Execute dividend distribution/reinvestment",
                    "Update investor account balances",
                    "Generate dividend confirmation report",
                ],
                "output": ["Dividend processing results", "Account balance change records", "Dividend report"],
                "customer": ["Investors", "Fund managers", "Audit institutions"],
            }

        # NAV query flow
        if "nav" in intent or "nav" in user_input.lower():
            return {
                "title": "Fund NAV Query Workflow",
                "description": user_input,
                "type": "nav_query",
                "supplier": ["Fund valuation system", "Data service providers"],
                "input": ["Fund code", "Query date"],
                "process_steps": [
                    "Validate fund code",
                    "Query latest NAV data",
                    "Calculate price change",
                    "Format output result",
                ],
                "output": ["Unit NAV", "Accumulated NAV", "Price change", "Update date"],
                "customer": ["Investors", "Financial advisors"],
            }

        # Generic flow
        return {
            "title": "Automated Business Workflow",
            "description": user_input,
            "type": intent or "general",
            "supplier": ["Business systems"],
            "input": ["Business parameters"],
            "process_steps": ["Data retrieval", "Business processing", "Result validation"],
            "output": ["Processing results"],
            "customer": ["Users"],
        }
