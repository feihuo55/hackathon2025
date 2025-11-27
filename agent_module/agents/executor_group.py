"""
Executor Group - Flow 1 service execution group
Uses CrewAI framework with Mock LLM
Responsible for executing RAG-matched services and formatting results
"""
import asyncio
from typing import Optional

# CrewAI disabled for Mock mode - no API key required
CREWAI_AVAILABLE = False
from service_module.mock_services import ServiceRegistry
from utils.language_detector import get_message, get_template


class ExecutorGroup:
    """
    Flow 1 Execution Group - 2 Experts

    Expert composition:
    1. Executor: Call services to retrieve data
    2. Formatter: Convert data to user-friendly display

    Responsibilities:
    - Receive RAG match results
    - Call corresponding services
    - Format output
    """

    def __init__(self, service_registry: ServiceRegistry = None):
        self.registry = service_registry or ServiceRegistry()
        # Mock mode - no CrewAI agents needed

    async def execute(
        self,
        service_id: str,
        params: dict,
        lang: str = "zh"
    ) -> dict:
        """
        Execute service and format results

        Args:
            service_id: Service ID (from RAG match)
            params: Service parameters
            lang: Language code

        Returns:
            {
                "success": bool,
                "message": str,      # Formatted message
                "data": dict,        # Raw data
            }
        """
        # Simulate thinking delay
        await asyncio.sleep(0.2)

        # If CrewAI available, run Crew (for demonstration)
        if CREWAI_AVAILABLE:
            await self._run_crew_demo(service_id)

        # Actually call service
        result = await self.registry.invoke(service_id, **params)

        # Format result
        formatted = self._format_result(service_id, result, lang)

        return formatted

    async def _run_crew_demo(self, service_id: str):
        """Run CrewAI demo (show multi-expert collaboration effect)"""
        try:
            tasks = [
                Task(
                    description=f"Execute service: {service_id}, retrieve data",
                    expected_output="Raw data from service",
                    agent=self.executor_agent,
                ),
                Task(
                    description="Format retrieved data into user-friendly display format",
                    expected_output="Formatted Markdown content",
                    agent=self.formatter_agent,
                ),
            ]

            crew = Crew(
                agents=[self.executor_agent, self.formatter_agent],
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
            )

            # Async execution (non-blocking)
            crew.kickoff()
        except Exception as e:
            # CrewAI demo failure doesn't affect main logic
            print(f"CrewAI demo skipped: {e}")

    def _format_result(self, service_id: str, result: dict, lang: str = "zh") -> dict:
        """Format service execution result"""
        if not result.get("success"):
            return {
                "success": False,
                "message": get_message('service_error', lang, error=result.get('error', 'Unknown error')),
                "data": {},
            }

        data = result.get("data", {})

        # Format output based on service type
        if service_id == "getFundNAV":
            message = self._format_nav_result(data, lang)
        elif service_id == "getFundDividend":
            message = self._format_dividend_result(data, lang)
        elif service_id == "getAllFunds":
            message = self._format_fund_list(data, lang)
        elif service_id == "processDividend":
            message = self._format_dividend_processing(data, lang)
        else:
            message = get_message('service_success', lang, data=str(data))

        return {
            "success": True,
            "message": message,
            "data": data,
        }

    def _format_nav_result(self, data: dict, lang: str = "zh") -> str:
        """Format NAV query result"""
        t = get_template('nav_result', lang)
        change_emoji = "📈" if data.get("change_pct", 0) >= 0 else "📉"
        change_sign = "+" if data.get("change_pct", 0) >= 0 else ""

        return f"""{t['header'].format(name=data.get('name', 'Unknown'), code=data.get('code', ''))}

| {t.get('nav_label', 'Metric')} | Value |
|------|------|
| {t['nav_label']} | {data.get('nav', 'N/A')} |
| {t['acc_nav_label']} | {data.get('acc_nav', 'N/A')} |
| {t['change_label']} | {change_emoji} {change_sign}{data.get('change_pct', 'N/A')}% |
| {t['date_label']} | {data.get('update_date', 'N/A')} |"""

    def _format_dividend_result(self, data: dict, lang: str = "zh") -> str:
        """Format dividend query result"""
        t = get_template('dividend_result', lang)
        lines = [t['header'].format(name=data.get('name', 'Unknown'))]
        lines.append("")
        lines.append(t['total'].format(amount=data.get('total_dividend', 0)))
        lines.append("")

        dividends = data.get("dividends", [])
        if dividends:
            lines.append(f"| {t['date_col']} | {t['amount_col']} | {t['type_col']} |")
            lines.append("|----------|----------|----------|")
            for d in dividends:
                amount_str = f"{d['amount']}" if lang == 'en' else f"{d['amount']} yuan/share"
                lines.append(f"| {d['date']} | {amount_str} | {d['type']} |")

        return "\n".join(lines)

    def _format_fund_list(self, data: list, lang: str = "zh") -> str:
        """Format fund list"""
        t = get_template('fund_list', lang)
        lines = [t['header'], ""]
        lines.append(f"| {t['code_col']} | {t['name_col']} | {t['type_col']} |")
        lines.append("|------|------|------|")

        for fund in data:
            lines.append(f"| {fund['code']} | {fund['name']} | {fund['type']} |")

        return "\n".join(lines)

    def _format_dividend_processing(self, data: dict, lang: str = "zh") -> str:
        """Format dividend processing result"""
        t = get_template('dividend_processing', lang)
        currency = "$" if lang == 'en' else "¥"

        lines = [t['header'], ""]
        lines.append(f"- {t['count']}: {data.get('processed_count', 0)}")
        lines.append(f"- {t['total']}: {currency}{data.get('total_amount', 0):,.2f}")
        lines.append("")

        details = data.get("details", [])
        if details:
            lines.append(f"| {t['fund_col']} | {t['amount_col']} | {t['method_col']} | {t['status_col']} |")
            lines.append("|------|----------|------|------|")
            for d in details:
                lines.append(
                    f"| {d['name']} | {currency}{d['total_amount']:,.2f} | {d['method']} | {d['status']} |"
                )

        return "\n".join(lines)
