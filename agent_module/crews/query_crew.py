"""
Query Flow Orchestration (Flow 1)
Handles user query requests: Intent Recognition -> RAG Matching -> Service Execution -> Result Return
"""
from typing import Optional
from ..agents import IntentAgent, ExecutorAgent
from rag_module.retrieval import ServiceMatcher
from rag_module.memory import MemoryManager
from service_module.mock_services import ServiceRegistry
from service_module.mock_services.fund_services import FundServices
from utils.language_detector import detect_language, get_message


class QueryCrew:
    """Query Flow Orchestration"""

    def __init__(
        self,
        service_registry: ServiceRegistry,
        service_matcher: ServiceMatcher,
        memory_manager: MemoryManager,
    ):
        """
        Initialize query flow

        Args:
            service_registry: Service registry
            service_matcher: Service matcher
            memory_manager: Memory manager
        """
        self.registry = service_registry
        self.matcher = service_matcher
        self.memory = memory_manager

        # Initialize agents
        self.executor = ExecutorAgent(service_registry)

        # Index services to vector store
        self._index_services()

    def _index_services(self):
        """Index services to vector store"""
        services = self.registry.get_all_services()
        self.matcher.index_services(services)

    async def execute(
        self,
        user_input: str,
        intent_result: dict,
    ) -> dict:
        """
        Execute query flow

        Args:
            user_input: User input
            intent_result: Intent recognition result

        Returns:
            Query result
        """
        # Detect language for response
        lang = detect_language(user_input)

        query_type = intent_result.get("query_type", "")
        entities = intent_result.get("entities", {})

        # Step 1: Determine service based on intent type
        service_id, parameters = self._determine_service(query_type, entities, user_input)

        if not service_id:
            # Try RAG matching
            match = await self.matcher.find_best_match(user_input)
            if match:
                service_id = match.get("service_id")
                # Extract parameters from intent result
                parameters = self._extract_parameters(service_id, entities)

        if not service_id:
            return {
                "success": False,
                "message": get_message('no_service_match', lang),
            }

        # Step 2: Execute service
        result = await self.executor.execute({
            "service_id": service_id,
            "parameters": parameters,
            "lang": lang,
        })

        # Step 3: Store interaction record
        await self.memory.store_service_call(
            service_id=service_id,
            parameters=parameters,
            result=result,
        )

        return result

    def _determine_service(
        self,
        query_type: str,
        entities: dict,
        user_input: str,
    ) -> tuple[Optional[str], dict]:
        """
        Determine service and parameters based on query type

        Args:
            query_type: Query type
            entities: Extracted entities
            user_input: User input

        Returns:
            (service_id, parameters dict)
        """
        if query_type == "fund_nav":
            fund_code = entities.get("fund_code")
            if not fund_code:
                # Try to extract from input
                fund_code = self._extract_fund_code(user_input)

            if fund_code:
                return "getFundNAV", {"fund_code": fund_code}

        elif query_type == "fund_dividend":
            fund_code = entities.get("fund_code")
            if not fund_code:
                fund_code = self._extract_fund_code(user_input)

            if fund_code:
                return "getFundDividend", {"fund_code": fund_code}

        elif query_type == "fund_list":
            return "getAllFunds", {}

        elif query_type == "fund_performance":
            fund_code = entities.get("fund_code")
            if not fund_code:
                fund_code = self._extract_fund_code(user_input)

            if fund_code:
                return "getFundPerformance", {"fund_code": fund_code}

        return None, {}

    def _extract_fund_code(self, text: str) -> Optional[str]:
        """Extract fund code from text"""
        fund_info = FundServices.get_fund_code(text)
        if fund_info:
            return fund_info

        # Try to find from text
        import re
        code_match = re.search(r'\b(\d{6})\b', text)
        if code_match:
            return code_match.group(1)

        # Try to match fund name
        from service_module.mock_services.fund_services import FUND_NAME_MAP
        for name, code in FUND_NAME_MAP.items():
            if name in text:
                return code

        return None

    def _extract_parameters(
        self,
        service_id: str,
        entities: dict,
    ) -> dict:
        """Extract service parameters from entities"""
        service = self.registry.get_service(service_id)
        if not service:
            return {}

        parameters = {}
        param_defs = service.get("parameters", {})

        for param_name, param_def in param_defs.items():
            # Try to get parameter value from entities
            if param_name in entities:
                parameters[param_name] = entities[param_name]
            elif param_name == "fund_code" and "fund_code" in entities:
                parameters[param_name] = entities["fund_code"]

        return parameters
