"""
统一记忆管理器
整合各类记忆系统
"""
from typing import Optional
from .episodic_memory import EpisodicMemory


class MemoryManager:
    """统一记忆管理器"""

    def __init__(self):
        """初始化记忆管理器"""
        self.episodic = EpisodicMemory()
        self._session_data: dict = {}

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
        # 存储用户输入
        self.episodic.add(
            event_type="user_input",
            content={"text": user_input},
            metadata={"source": "user"},
        )

        # 存储系统响应
        self.episodic.add(
            event_type="agent_response",
            content={
                "text": result.get("message", ""),
                "success": result.get("success", False),
                "data": result.get("data"),
            },
            metadata={"source": "system"},
        )

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
        self.episodic.add(
            event_type="service_call",
            content={
                "service_id": service_id,
                "parameters": parameters,
                "result": result,
            },
            metadata={"source": "service"},
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

    def get_statistics(self) -> dict:
        """获取记忆统计信息"""
        return {
            "total_memories": self.episodic.count(),
            "user_inputs": len(self.episodic.get_by_type("user_input")),
            "agent_responses": len(self.episodic.get_by_type("agent_response")),
            "service_calls": len(self.episodic.get_by_type("service_call")),
        }
