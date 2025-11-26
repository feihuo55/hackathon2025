"""
Executor Agent
Responsible for calling services and formatting results
"""
from typing import Optional
from .base_agent import BaseAgent
from service_module.mock_services import ServiceRegistry
from utils.language_detector import get_message, get_template


class ExecutorAgent(BaseAgent):
    """Executor Agent for service invocation"""

    def __init__(self, service_registry: ServiceRegistry = None):
        super().__init__(
            name="ExecutorAgent",
            description="Invoke matched services and format results",
        )
        self.registry = service_registry or ServiceRegistry()

    async def execute(self, input_data: dict) -> dict:
        """
        Execute service call

        Args:
            input_data: Dictionary containing service_id and parameters

        Returns:
            Execution result
        """
        service_id = input_data.get("service_id")
        parameters = input_data.get("parameters", {})
        lang = input_data.get("lang", "en")

        if not service_id:
            return {
                "success": False,
                "message": get_message('no_service_id', lang),
            }

        # Call service
        result = await self.registry.invoke(service_id, **parameters)

        # Format result
        formatted = await self._format_result(service_id, result, lang)

        return formatted

    async def _format_result(self, service_id: str, result: dict, lang: str = "en") -> dict:
        """Format service execution result"""
        if not result.get("success"):
            return {
                "success": False,
                "message": get_message('service_error', lang, error=result.get('error', 'Unknown error')),
                "raw_result": result,
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

    def _format_nav_result(self, data: dict, lang: str = "en") -> str:
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

    def _format_dividend_result(self, data: dict, lang: str = "en") -> str:
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
                amount_str = f"{d['amount']}" if lang == 'en' else f"{d['amount']} 元/份"
                lines.append(f"| {d['date']} | {amount_str} | {d['type']} |")

        return "\n".join(lines)

    def _format_fund_list(self, data: list, lang: str = "en") -> str:
        """Format fund list"""
        t = get_template('fund_list', lang)
        lines = [t['header'], ""]
        lines.append(f"| {t['code_col']} | {t['name_col']} | {t['type_col']} |")
        lines.append("|------|------|------|")

        for fund in data:
            lines.append(f"| {fund['code']} | {fund['name']} | {fund['type']} |")

        return "\n".join(lines)

    def _format_dividend_processing(self, data: dict, lang: str = "en") -> str:
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

    async def execute_with_confirmation(
        self,
        service_id: str,
        parameters: dict,
        require_confirmation: bool = False,
        lang: str = "en",
    ) -> dict:
        """
        Execute service (with optional confirmation)

        Args:
            service_id: Service ID
            parameters: Parameters
            require_confirmation: Whether human confirmation is required
            lang: Language code

        Returns:
            Execution result, or pending confirmation status if needed
        """
        if require_confirmation:
            return {
                "success": True,
                "status": "pending_confirmation",
                "message": get_message('confirm_operation', lang),
                "service_id": service_id,
                "parameters": parameters,
            }

        return await self.execute({
            "service_id": service_id,
            "parameters": parameters,
            "lang": lang,
        })
