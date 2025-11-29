"""
Intent Recognition Agent
Analyzes user input, identifies intent types and key entities
"""
import json
import re
from typing import Optional
from .base_agent import BaseAgent
from service_module.mock_services.fund_services import FUND_NAME_MAP, FUND_DATA


INTENT_SYSTEM_PROMPT = """You are an intent recognition expert for custody bank business scenarios.

Identify the following intent types:
1. query - Query type: fund NAV, dividend records, fund list
2. creation - Creation type: batch dividend processing, new business process
3. unknown - Unrecognized intent

For query intents, extract:
- Query object: fund_nav, fund_dividend, fund_list
- Fund name or code (if any)

For creation intents, extract:
- Business type: dividend_processing, other
- Related parameters

Return analysis results in JSON format only."""


class IntentAgent(BaseAgent):
    """Intent Recognition Agent"""

    def __init__(self):
        super().__init__(
            name="IntentAgent",
            description="Analyze user input, identify intent types and key entities",
            system_prompt=INTENT_SYSTEM_PROMPT,
        )

    async def analyze(self, user_input: str) -> dict:
        """
        Analyze user input

        Args:
            user_input: User input text

        Returns:
            Intent analysis result
        """
        # Try rule-based matching first (fast path)
        rule_result = self._rule_based_analysis(user_input)
        if rule_result.get("confidence", 0) > 0.8:
            return rule_result

        # Use LLM for deep analysis
        try:
            llm_result = await self._llm_analysis(user_input)
            # Merge rule result and LLM result
            return self._merge_results(rule_result, llm_result)
        except Exception as e:
            # Return rule result if LLM fails
            print(f"LLM analysis failed: {e}")
            return rule_result

    def _rule_based_analysis(self, user_input: str) -> dict:
        """Rule-based quick analysis"""
        text = user_input.lower()

        result = {
            "type": "unknown",
            "confidence": 0.5,
            "entities": {},
            "original_input": user_input,
        }

        # NAV query intent
        nav_keywords = ["nav", "net value", "price", "value", "query fund", "check fund", "fund nav"]
        if any(kw in text for kw in nav_keywords):
            result["type"] = "query"
            result["query_type"] = "fund_nav"
            result["confidence"] = 0.9

            # Extract fund name or code
            fund_info = self._extract_fund_info(user_input)
            if fund_info:
                result["entities"]["fund_code"] = fund_info["code"]
                result["entities"]["fund_name"] = fund_info["name"]

        # Dividend query intent
        elif any(kw in text for kw in ["dividend history", "dividend record", "dividends",
                                        "query dividend", "check dividend"]):
            result["type"] = "query"
            result["query_type"] = "fund_dividend"
            result["confidence"] = 0.9

            fund_info = self._extract_fund_info(user_input)
            if fund_info:
                result["entities"]["fund_code"] = fund_info["code"]
                result["entities"]["fund_name"] = fund_info["name"]

        # Fund performance query intent
        elif any(kw in text for kw in ["performance", "return", "returns", "benchmark",
                                        "ytd", "year-to-date", "metrics", "fund performance",
                                        "performance metrics", "performance report"]):
            result["type"] = "query"
            result["query_type"] = "fund_performance"
            result["confidence"] = 0.9

            fund_info = self._extract_fund_info(user_input)
            if fund_info:
                result["entities"]["fund_code"] = fund_info["code"]
                result["entities"]["fund_name"] = fund_info["name"]

        # Fund list query
        elif any(kw in text for kw in ["fund list", "all funds", "show funds", "list funds",
                                        "available funds"]):
            result["type"] = "query"
            result["query_type"] = "fund_list"
            result["confidence"] = 0.9

        # Dividend processing intent
        elif any(kw in text for kw in ["process dividend", "dividend processing", "batch dividend",
                                        "dividend distribution", "distribute dividend"]):
            result["type"] = "creation"
            result["creation_type"] = "dividend_processing"
            result["confidence"] = 0.85

        # Compliance report processing intent
        elif any(kw in text for kw in ["compliance", "compliance report", "regulatory", "regulatory report",
                                        "monthly report", "report due", "compliance checklist"]):
            result["type"] = "creation"
            result["creation_type"] = "compliance_report"
            result["confidence"] = 0.85

            # Extract fund codes if present
            fund_codes = self._extract_multiple_fund_codes(user_input)
            if fund_codes:
                result["entities"]["fund_codes"] = fund_codes

        # Create process intent
        elif any(kw in text for kw in ["create process", "new service", "automation", "workflow",
                                        "new process", "create workflow"]):
            result["type"] = "creation"
            result["creation_type"] = "new_process"
            result["confidence"] = 0.7

        return result

    def _extract_multiple_fund_codes(self, text: str) -> list:
        """Extract multiple fund codes from text"""
        codes = re.findall(r'\b(\d{6})\b', text)
        return [code for code in codes if code in FUND_DATA]

    def _extract_fund_info(self, text: str) -> Optional[dict]:
        """Extract fund info from text"""
        # Try to match fund code
        code_match = re.search(r'\b(\d{6})\b', text)
        if code_match:
            code = code_match.group(1)
            if code in FUND_DATA:
                return {
                    "code": code,
                    "name": FUND_DATA[code]["name"],
                }

        # Try to match fund name
        for name, code in FUND_NAME_MAP.items():
            if name in text:
                return {
                    "code": code,
                    "name": FUND_DATA[code]["name"],
                }

        return None

    async def _llm_analysis(self, user_input: str) -> dict:
        """Use LLM for deep analysis"""
        prompt = f"""Analyze the following user input intent:

User input: "{user_input}"

Return JSON format analysis result containing:
- type: Intent type (query/creation/unknown)
- query_type or creation_type: Specific type
- entities: Extracted entities (fund name, code, etc.)
- confidence: Confidence score (0-1)

Return JSON only, no other content."""

        response = await self._call_llm(prompt, temperature=0.3)

        # Parse JSON response
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {"type": "unknown", "confidence": 0.3}

    def _merge_results(self, rule_result: dict, llm_result: dict) -> dict:
        """Merge rule result and LLM result"""
        # If rule result has higher confidence, use rule result
        if rule_result.get("confidence", 0) > llm_result.get("confidence", 0):
            return rule_result

        # Otherwise merge both
        merged = rule_result.copy()
        merged.update({
            k: v for k, v in llm_result.items()
            if v and k not in ["original_input"]
        })

        return merged

    async def execute(self, input_data: dict) -> dict:
        """Execute intent analysis"""
        user_input = input_data.get("user_input", "")
        return await self.analyze(user_input)
