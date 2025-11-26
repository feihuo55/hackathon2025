"""
事件记忆
存储对话历史和交互事件
"""
from datetime import datetime
from typing import Optional
from collections import deque
from config import MEMORY_CONFIG


class EpisodicMemory:
    """事件记忆系统"""

    def __init__(self, max_entries: int = None):
        """
        初始化事件记忆

        Args:
            max_entries: 最大记录数
        """
        self.max_entries = max_entries or MEMORY_CONFIG["max_episodic_entries"]
        self._memories: deque = deque(maxlen=self.max_entries)

    def add(
        self,
        event_type: str,
        content: dict,
        metadata: Optional[dict] = None,
    ):
        """
        添加事件记录

        Args:
            event_type: 事件类型 (user_input, agent_response, service_call, etc.)
            content: 事件内容
            metadata: 元数据
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "content": content,
            "metadata": metadata or {},
        }
        self._memories.append(entry)

    def get_recent(self, n: int = 10) -> list[dict]:
        """
        获取最近的N条记录

        Args:
            n: 记录数量

        Returns:
            记录列表
        """
        memories = list(self._memories)
        return memories[-n:] if len(memories) >= n else memories

    def get_by_type(self, event_type: str) -> list[dict]:
        """
        按类型获取记录

        Args:
            event_type: 事件类型

        Returns:
            匹配的记录列表
        """
        return [m for m in self._memories if m["event_type"] == event_type]

    def get_conversation_history(self) -> list[dict]:
        """
        获取对话历史（用于上下文）

        Returns:
            对话历史列表
        """
        history = []
        for memory in self._memories:
            if memory["event_type"] == "user_input":
                history.append({
                    "role": "user",
                    "content": memory["content"].get("text", ""),
                })
            elif memory["event_type"] == "agent_response":
                history.append({
                    "role": "assistant",
                    "content": memory["content"].get("text", ""),
                })
        return history

    def search(self, keyword: str) -> list[dict]:
        """
        搜索记录

        Args:
            keyword: 关键词

        Returns:
            匹配的记录列表
        """
        results = []
        for memory in self._memories:
            content_str = str(memory.get("content", ""))
            if keyword.lower() in content_str.lower():
                results.append(memory)
        return results

    def clear(self):
        """清空记忆"""
        self._memories.clear()

    def count(self) -> int:
        """获取记录数量"""
        return len(self._memories)

    def to_list(self) -> list[dict]:
        """转换为列表"""
        return list(self._memories)
