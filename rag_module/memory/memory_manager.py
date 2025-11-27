"""
统一记忆管理器
整合四层记忆系统：事件记忆、语义记忆、程序记忆、摘要记忆
"""
from typing import Optional
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .procedural_memory import ProceduralMemory, Procedure
from .summary_memory import SummaryMemory


class MemoryManager:
    """统一记忆管理器 - 整合四层记忆系统"""

    def __init__(self):
        """初始化记忆管理器"""
        # 四层记忆系统
        self.episodic = EpisodicMemory()      # 事件记忆：对话历史和交互事件
        self.semantic = SemanticMemory()       # 语义记忆：知识和概念
        self.procedural = ProceduralMemory()   # 程序记忆：操作流程和技能
        self.summary = SummaryMemory()         # 摘要记忆：压缩的历史摘要

        self._session_data: dict = {}
        self._auto_summarize_threshold = 20    # 自动摘要阈值

    async def store_interaction(
        self,
        user_input: str,
        result: dict,
    ):
        """
        存储用户交互

        Args:
            user_input: 用户输入
            result: 处理结果
        """
        # 存储用户输入到事件记忆
        self.episodic.add(
            event_type="user_input",
            content={"text": user_input},
            metadata={"source": "user"},
        )

        # 存储系统响应到事件记忆
        self.episodic.add(
            event_type="agent_response",
            content={
                "text": result.get("message", ""),
                "success": result.get("success", False),
                "data": result.get("data"),
            },
            metadata={"source": "system"},
        )

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

    async def store_knowledge(
        self,
        knowledge_id: str,
        content: str,
        category: str = "general",
        metadata: Optional[dict] = None,
    ):
        """
        存储知识到语义记忆

        Args:
            knowledge_id: 知识ID
            content: 知识内容
            category: 类别
            metadata: 元数据
        """
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
        """
        存储操作流程到程序记忆

        Args:
            procedure_id: 流程ID
            name: 流程名称
            description: 描述
            steps: 步骤列表
            parameters: 参数定义
            metadata: 元数据

        Returns:
            存储的流程对象
        """
        return self.procedural.store_procedure(
            procedure_id=procedure_id,
            name=name,
            description=description,
            steps=steps,
            parameters=parameters,
            metadata=metadata,
        )

    async def save_session(self, history: list[dict]):
        """
        保存会话

        Args:
            history: 对话历史
        """
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
            # 获取对话历史并创建摘要
            history = self.episodic.get_conversation_history()
            if history:
                self.summary.summarize_conversation(history)

    def get_context(self, max_turns: int = 5) -> str:
        """
        获取上下文摘要

        Args:
            max_turns: 最大对话轮数

        Returns:
            上下文字符串
        """
        history = self.episodic.get_conversation_history()
        recent = history[-(max_turns * 2):]  # 每轮包含user和assistant

        context_parts = []
        for item in recent:
            role = "用户" if item["role"] == "user" else "助手"
            context_parts.append(f"{role}: {item['content']}")

        return "\n".join(context_parts)

    def get_full_context(self, max_turns: int = 5) -> str:
        """
        获取完整上下文（包含摘要）

        Args:
            max_turns: 最大对话轮数

        Returns:
            完整上下文字符串
        """
        parts = []

        # 添加历史摘要
        summary_context = self.summary.get_context_summary(max_summaries=2)
        if summary_context:
            parts.append(f"历史摘要:\n{summary_context}")

        # 添加最近对话
        recent_context = self.get_context(max_turns)
        if recent_context:
            parts.append(f"最近对话:\n{recent_context}")

        return "\n\n".join(parts)

    async def retrieve_relevant_knowledge(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        检索相关知识

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            相关知识列表
        """
        return self.semantic.retrieve(query, top_k=top_k)

    async def find_relevant_procedure(
        self,
        query: str,
    ) -> Optional[Procedure]:
        """
        查找相关流程

        Args:
            query: 查询文本

        Returns:
            最佳匹配的流程
        """
        return self.procedural.get_best_procedure(query)

    def get_recent_services(self, n: int = 5) -> list[dict]:
        """
        获取最近调用的服务

        Args:
            n: 数量

        Returns:
            服务调用记录列表
        """
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

    def clear_all(self):
        """清空所有记忆"""
        self._session_data.clear()
        self.episodic.clear()
        self.semantic.clear()
        self.procedural.clear()
        self.summary.clear()

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
        }

    def export_state(self) -> dict:
        """导出记忆状态（用于持久化）"""
        return {
            "episodic": self.episodic.to_list(),
            "procedural": self.procedural.to_dict(),
            "summary": self.summary.to_list(),
            "session_data": self._session_data,
        }

    def import_state(self, state: dict):
        """导入记忆状态"""
        # 导入事件记忆
        if "episodic" in state:
            for entry in state["episodic"]:
                self.episodic.add(
                    event_type=entry.get("event_type", "unknown"),
                    content=entry.get("content", {}),
                    metadata=entry.get("metadata", {}),
                )

        # 导入程序记忆
        if "procedural" in state:
            self.procedural.from_dict(state["procedural"])

        # 导入会话数据
        if "session_data" in state:
            self._session_data = state["session_data"]
