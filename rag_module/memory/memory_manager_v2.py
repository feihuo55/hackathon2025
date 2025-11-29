"""
统一记忆管理器 V2
整合五层记忆系统：事件记忆、语义记忆、程序记忆、摘要记忆、反馈记忆
支持用户反馈收集和闭环学习优化
"""
from typing import Optional, List, Dict, Any
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .procedural_memory import ProceduralMemory, Procedure
from .summary_memory import SummaryMemory
from .feedback_memory import FeedbackMemory, FeedbackType, FeedbackSource, Feedback


class MemoryManagerV2:
    """
    统一记忆管理器 V2 - 整合五层记忆系统

    五层记忆：
    1. Episodic (事件记忆): 对话历史和交互事件
    2. Semantic (语义记忆): 知识和概念
    3. Procedural (程序记忆): 操作流程和技能
    4. Summary (摘要记忆): 压缩的历史摘要
    5. Feedback (反馈记忆): 用户反馈和学习信号
    """

    def __init__(self):
        """初始化记忆管理器"""
        # 五层记忆系统
        self.episodic = EpisodicMemory()      # 事件记忆：对话历史和交互事件
        self.semantic = SemanticMemory()       # 语义记忆：知识和概念
        self.procedural = ProceduralMemory()   # 程序记忆：操作流程和技能
        self.summary = SummaryMemory()         # 摘要记忆：压缩的历史摘要
        self.feedback = FeedbackMemory()       # 反馈记忆：用户反馈和学习信号

        self._session_data: dict = {}
        self._auto_summarize_threshold = 20    # 自动摘要阈值
        self._current_interaction: dict = {}   # 当前交互上下文（用于反馈关联）

    async def store_interaction(
        self,
        user_input: str,
        result: dict,
        retrieved_doc_ids: Optional[List[str]] = None,
    ):
        """
        存储用户交互

        Args:
            user_input: 用户输入
            result: 处理结果
            retrieved_doc_ids: 检索到的文档ID列表（用于后续反馈关联）
        """
        # 存储用户输入到事件记忆
        self.episodic.add(
            event_type="user_input",
            content={"text": user_input},
            metadata={"source": "user"},
        )

        # 存储系统响应到事件记忆
        response_text = result.get("message", "")
        self.episodic.add(
            event_type="agent_response",
            content={
                "text": response_text,
                "success": result.get("success", False),
                "data": result.get("data"),
            },
            metadata={"source": "system"},
        )

        # 保存当前交互上下文（用于后续反馈关联）
        self._current_interaction = {
            "query": user_input,
            "response": response_text,
            "retrieved_doc_ids": retrieved_doc_ids or [],
            "result": result,
        }

        # 检查是否需要自动摘要
        await self._check_auto_summarize()

    async def store_service_call(
        self,
        service_id: str,
        parameters: dict,
        result: dict,
    ):
        """
        存储服务调用记录

        Args:
            service_id: 服务ID
            parameters: 调用参数
            result: 调用结果
        """
        # 存储到事件记忆
        self.episodic.add(
            event_type="service_call",
            content={
                "service_id": service_id,
                "parameters": parameters,
                "result": result,
            },
            metadata={"source": "service"},
        )

        # 更新程序记忆中的执行记录
        success = result.get("success", False)
        self.procedural.record_execution(
            procedure_id=service_id,
            success=success,
            result=result,
        )

    # ============ 反馈收集方法 ============

    async def collect_feedback(
        self,
        feedback_type: FeedbackType,
        query: Optional[str] = None,
        response: Optional[str] = None,
        correction_text: Optional[str] = None,
        relevant_doc_ids: Optional[List[str]] = None,
        irrelevant_doc_ids: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Feedback:
        """
        收集用户反馈

        Args:
            feedback_type: 反馈类型
            query: 查询（如不提供则使用当前交互）
            response: 回复（如不提供则使用当前交互）
            correction_text: 纠正文本（用于纠正类反馈）
            relevant_doc_ids: 用户标记为相关的文档
            irrelevant_doc_ids: 用户标记为不相关的文档
            session_id: 会话ID
            metadata: 额外元数据

        Returns:
            创建的反馈对象
        """
        # 如果未提供query/response，使用当前交互
        actual_query = query or self._current_interaction.get("query", "")
        actual_response = response or self._current_interaction.get("response", "")
        retrieved_docs = self._current_interaction.get("retrieved_doc_ids", [])

        return self.feedback.add_feedback(
            query=actual_query,
            response=actual_response,
            feedback_type=feedback_type,
            source=FeedbackSource.USER_EXPLICIT,
            correction_text=correction_text,
            retrieved_doc_ids=retrieved_docs,
            relevant_doc_ids=relevant_doc_ids,
            irrelevant_doc_ids=irrelevant_doc_ids,
            session_id=session_id,
            metadata=metadata,
        )

    async def collect_positive_feedback(
        self,
        session_id: Optional[str] = None,
    ) -> Feedback:
        """快捷方法：收集正面反馈 👍"""
        return await self.collect_feedback(
            feedback_type=FeedbackType.POSITIVE,
            session_id=session_id,
        )

    async def collect_negative_feedback(
        self,
        session_id: Optional[str] = None,
    ) -> Feedback:
        """快捷方法：收集负面反馈 👎"""
        return await self.collect_feedback(
            feedback_type=FeedbackType.NEGATIVE,
            session_id=session_id,
        )

    async def collect_correction(
        self,
        correction_text: str,
        session_id: Optional[str] = None,
    ) -> Feedback:
        """快捷方法：收集纠正反馈 ✏️"""
        return await self.collect_feedback(
            feedback_type=FeedbackType.CORRECTION,
            correction_text=correction_text,
            session_id=session_id,
        )

    async def collect_doc_relevance_feedback(
        self,
        relevant_doc_ids: Optional[List[str]] = None,
        irrelevant_doc_ids: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Feedback:
        """收集文档相关性反馈"""
        # 根据反馈内容确定类型
        if irrelevant_doc_ids and not relevant_doc_ids:
            feedback_type = FeedbackType.IRRELEVANT
        elif relevant_doc_ids:
            feedback_type = FeedbackType.POSITIVE
        else:
            feedback_type = FeedbackType.PARTIAL

        return await self.collect_feedback(
            feedback_type=feedback_type,
            relevant_doc_ids=relevant_doc_ids,
            irrelevant_doc_ids=irrelevant_doc_ids,
            session_id=session_id,
        )

    def should_request_feedback(self) -> bool:
        """
        判断是否应该主动请求用户反馈

        基于当前查询的历史表现
        """
        query = self._current_interaction.get("query", "")
        if not query:
            return False
        return self.feedback.should_request_feedback(query)

    def get_query_quality_score(self, query: Optional[str] = None) -> float:
        """获取查询的历史质量分数"""
        actual_query = query or self._current_interaction.get("query", "")
        if not actual_query:
            return 0.0
        return self.feedback.get_query_quality_score(actual_query)

    # ============ 原有方法 ============

    async def store_knowledge(
        self,
        knowledge_id: str,
        content: str,
        category: str = "general",
        metadata: Optional[dict] = None,
    ):
        """存储知识到语义记忆"""
        self.semantic.store(
            knowledge_id=knowledge_id,
            content=content,
            category=category,
            metadata=metadata,
        )

    async def store_procedure(
        self,
        procedure_id: str,
        name: str,
        description: str,
        steps: list[dict],
        parameters: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Procedure:
        """存储操作流程到程序记忆"""
        return self.procedural.store_procedure(
            procedure_id=procedure_id,
            name=name,
            description=description,
            steps=steps,
            parameters=parameters,
            metadata=metadata,
        )

    async def save_session(self, history: list[dict]):
        """保存会话"""
        for item in history:
            role = item.get("role", "")
            content = item.get("content", "")

            if role == "user":
                self.episodic.add(
                    event_type="user_input",
                    content={"text": content},
                )
            elif role == "assistant":
                self.episodic.add(
                    event_type="agent_response",
                    content={"text": content},
                )

    async def _check_auto_summarize(self):
        """检查并执行自动摘要"""
        if self.episodic.count() >= self._auto_summarize_threshold:
            history = self.episodic.get_conversation_history()
            if history:
                self.summary.summarize_conversation(history)

    def get_context(self, max_turns: int = 5) -> str:
        """获取上下文摘要"""
        history = self.episodic.get_conversation_history()
        recent = history[-(max_turns * 2):]

        context_parts = []
        for item in recent:
            role = "用户" if item["role"] == "user" else "助手"
            context_parts.append(f"{role}: {item['content']}")

        return "\n".join(context_parts)

    def get_full_context(self, max_turns: int = 5) -> str:
        """获取完整上下文（包含摘要）"""
        parts = []

        summary_context = self.summary.get_context_summary(max_summaries=2)
        if summary_context:
            parts.append(f"历史摘要:\n{summary_context}")

        recent_context = self.get_context(max_turns)
        if recent_context:
            parts.append(f"最近对话:\n{recent_context}")

        return "\n\n".join(parts)

    async def retrieve_relevant_knowledge(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """检索相关知识"""
        return self.semantic.retrieve(query, top_k=top_k)

    async def find_relevant_procedure(
        self,
        query: str,
    ) -> Optional[Procedure]:
        """查找相关流程"""
        return self.procedural.get_best_procedure(query)

    def get_recent_services(self, n: int = 5) -> list[dict]:
        """获取最近调用的服务"""
        service_calls = self.episodic.get_by_type("service_call")
        return service_calls[-n:] if len(service_calls) >= n else service_calls

    def set_session_data(self, key: str, value):
        """设置会话数据"""
        self._session_data[key] = value

    def get_session_data(self, key: str, default=None):
        """获取会话数据"""
        return self._session_data.get(key, default)

    def clear_session(self):
        """清空会话数据"""
        self._session_data.clear()
        self.episodic.clear()
        self.summary.clear()
        self._current_interaction.clear()

    def clear_all(self):
        """清空所有记忆"""
        self._session_data.clear()
        self.episodic.clear()
        self.semantic.clear()
        self.procedural.clear()
        self.summary.clear()
        self.feedback.clear()
        self._current_interaction.clear()

    def get_statistics(self) -> dict:
        """获取记忆统计信息"""
        return {
            "episodic": {
                "total_memories": self.episodic.count(),
                "user_inputs": len(self.episodic.get_by_type("user_input")),
                "agent_responses": len(self.episodic.get_by_type("agent_response")),
                "service_calls": len(self.episodic.get_by_type("service_call")),
            },
            "semantic": {
                "total_knowledge": self.semantic.count(),
            },
            "procedural": self.procedural.get_statistics(),
            "summary": self.summary.get_statistics(),
            "feedback": self.feedback.get_statistics(),
        }

    def get_feedback_statistics(self) -> dict:
        """获取反馈统计"""
        return self.feedback.get_statistics()

    def get_improvement_suggestions(self) -> List[Dict]:
        """获取系统改进建议（基于反馈分析）"""
        return self.feedback.get_improvement_suggestions()

    def export_state(self) -> dict:
        """导出记忆状态（用于持久化）"""
        return {
            "episodic": self.episodic.to_list(),
            "procedural": self.procedural.to_dict(),
            "summary": self.summary.to_list(),
            "feedback": self.feedback.to_dict(),
            "session_data": self._session_data,
        }

    def import_state(self, state: dict):
        """导入记忆状态"""
        if "episodic" in state:
            for entry in state["episodic"]:
                self.episodic.add(
                    event_type=entry.get("event_type", "unknown"),
                    content=entry.get("content", {}),
                    metadata=entry.get("metadata", {}),
                )

        if "procedural" in state:
            self.procedural.from_dict(state["procedural"])

        if "feedback" in state:
            self.feedback.from_dict(state["feedback"])

        if "session_data" in state:
            self._session_data = state["session_data"]


# 为了向后兼容，创建别名
MemoryManager = MemoryManagerV2
