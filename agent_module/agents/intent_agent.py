"""
Intent Agent - Unified intent analysis
Does not distinguish Flow 1/2, only extracts user intent and entities
RAG decides the routing
Mock implementation that appears like real AI
"""
import asyncio
import re
from typing import Optional
from service_module.mock_services.fund_services import FUND_NAME_MAP, FUND_DATA


# Intent keyword mapping (does not distinguish Flow)
INTENT_KEYWORDS = {
    # Fund NAV query
    "fund_nav": {
        "zh": ["净值", "查询基金", "基金价格", "多少钱", "现在价格"],
        "en": ["nav", "net value", "price", "value", "query fund", "check fund"],
    },
    # Fund dividend history query
    "fund_dividend_query": {
        "zh": ["分红记录", "历史分红", "派息记录", "分红历史"],
        "en": ["dividend history", "dividend record", "dividends"],
    },
    # Fund list
    "fund_list": {
        "zh": ["所有基金", "基金列表", "有哪些基金", "显示基金", "查看基金"],
        "en": ["fund list", "all funds", "show funds", "list funds", "available funds"],
    },
    # Dividend processing (batch operation)
    "dividend_process": {
        "zh": ["处理分红", "分红派息", "批量分红", "分红处理", "执行分红"],
        "en": ["process dividend", "dividend processing", "batch dividend"],
    },
    # Create new workflow
    "create_workflow": {
        "zh": ["创建流程", "新增服务", "新建流程", "自动化", "新业务"],
        "en": ["create process", "new service", "automation", "workflow", "create workflow"],
    },
}


class IntentAgent:
    """
    Unified Intent Analysis Agent

    Responsibilities:
    1. Analyze user input, identify intent type
    2. Extract key entities (fund code, operation scope, etc.)
    3. Output structured intent for RAG retrieval

    Not responsible for:
    - Deciding Flow 1 or Flow 2 (RAG decides that)
    """

    def __init__(self):
        self.name = "IntentAgent"
        self.description = "Unified intent analysis, identify user requirements"

    async def analyze(self, user_input: str) -> dict:
        """
        Analyze user input, return intent and entities with thinking steps

        Args:
            user_input: User input text

        Returns:
            {
                "intent": str,          # Intent type
                "confidence": float,    # Confidence score
                "entities": dict,       # Extracted entities
                "original_input": str,  # Original input
                "thinking_steps": list, # Analysis steps for display
                "matched_keywords": list, # All matched keywords
            }
        """
        # Simulate AI thinking delay
        await asyncio.sleep(0.3)

        text = user_input.lower()
        thinking_steps = []  # Steps for frontend display

        # Collect ALL matched keywords across all intents
        all_matches = {}  # intent -> matched keywords
        for intent, keywords in INTENT_KEYWORDS.items():
            all_keywords = keywords.get("zh", []) + keywords.get("en", [])
            matched_kw = [kw for kw in all_keywords if kw in text]
            if matched_kw:
                all_matches[intent] = matched_kw

        # If we found matches, pick the best one (most keywords matched)
        if all_matches:
            # Sort by number of matches, pick the one with most
            best_intent = max(all_matches.keys(), key=lambda k: len(all_matches[k]))
            matched_keywords = all_matches[best_intent]

            # Build thinking steps showing all detected keywords
            all_detected = []
            for intent, kws in all_matches.items():
                all_detected.extend(kws)

            thinking_steps.append(f"Keywords detected: {', '.join(all_detected)}")
            thinking_steps.append(f"Primary intent: {best_intent}")
            if len(all_matches) > 1:
                thinking_steps.append(f"Related: {', '.join([k for k in all_matches.keys() if k != best_intent])}")
            thinking_steps.append("Confidence: 95%")

            return {
                "intent": best_intent,
                "confidence": 0.95,
                "entities": self._extract_entities(user_input),
                "original_input": user_input,
                "thinking_steps": thinking_steps,
                "matched_keywords": all_detected,
                "all_intents": list(all_matches.keys()),
            }

        # No clear intent matched
        thinking_steps.append("No matching keywords found")
        return {
            "intent": "unknown",
            "confidence": 0.3,
            "entities": self._extract_entities(user_input),
            "original_input": user_input,
            "thinking_steps": thinking_steps,
            "matched_keywords": [],
        }

    def _extract_entities(self, text: str) -> dict:
        """
        Extract entities from text

        Extracts:
        - fund_code: Fund code (6-digit number)
        - fund_name: Fund name
        - scope: Operation scope (all/single)
        - method: Dividend method (cash/reinvest)
        """
        entities = {}

        # Extract fund code (6-digit number)
        code_match = re.search(r'\b(\d{6})\b', text)
        if code_match:
            code = code_match.group(1)
            entities["fund_code"] = code
            # If code exists in database, also extract fund name
            if code in FUND_DATA:
                entities["fund_name"] = FUND_DATA[code]["name"]

        # Try to match by fund name
        if "fund_code" not in entities:
            fund_info = self._match_fund_by_name(text)
            if fund_info:
                entities["fund_code"] = fund_info["code"]
                entities["fund_name"] = fund_info["name"]

        # Extract operation scope
        if any(kw in text for kw in ["所有", "全部", "批量", "all", "batch"]):
            entities["scope"] = "all"
        elif entities.get("fund_code"):
            entities["scope"] = "single"

        # Extract dividend method
        if any(kw in text.lower() for kw in ["现金", "cash"]):
            entities["method"] = "cash"
        elif any(kw in text.lower() for kw in ["再投资", "reinvest"]):
            entities["method"] = "reinvest"

        return entities

    def _match_fund_by_name(self, text: str) -> Optional[dict]:
        """Match fund info by fund name"""
        for name, code in FUND_NAME_MAP.items():
            if name in text:
                return {
                    "code": code,
                    "name": FUND_DATA[code]["name"],
                }
        return None

    async def execute(self, input_data: dict) -> dict:
        """
        Execution entry point (compatible with old interface)

        Args:
            input_data: {"user_input": str}

        Returns:
            Intent analysis result
        """
        user_input = input_data.get("user_input", "")
        return await self.analyze(user_input)
