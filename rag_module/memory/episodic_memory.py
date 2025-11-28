"""
事件记忆 V2
存储对话历史和交互事件
支持 TTL 过期机制

使用方法：将此文件内容替换 episodic_memory.py
"""
from datetime import datetime, timedelta
from typing import Optional
from collections import deque
from config import MEMORY_CONFIG


class EpisodicMemory:
    """事件记忆系统 - 支持 TTL 过期"""

    def __init__(
        self,
        max_entries: int = None,
        ttl_hours: Optional[float] = None,
    ):
        """
        初始化事件记忆

        Args:
            max_entries: 最大记录数
            ttl_hours: 过期时间（小时），None 表示不过期
        """
        self.max_entries = max_entries or MEMORY_CONFIG.get("max_episodic_entries", 100)
        self.ttl_hours = ttl_hours or MEMORY_CONFIG.get("episodic_ttl_hours", None)
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
        now = datetime.now()
        entry = {
            "timestamp": now.isoformat(),
            "event_type": event_type,
            "content": content,
            "metadata": metadata or {},
        }

        # 如果启用 TTL，添加过期时间
        if self.ttl_hours:
            entry["expires_at"] = (now + timedelta(hours=self.ttl_hours)).isoformat()

        self._memories.append(entry)

        # 清理过期记录
        self._cleanup_expired()

    def _cleanup_expired(self):
        """清理过期记录"""
        if not self.ttl_hours:
            return

        now = datetime.now()
        # 创建新的 deque，排除过期项
        valid_memories = deque(maxlen=self.max_entries)

        for memory in self._memories:
            expires_at = memory.get("expires_at")
            if expires_at:
                try:
                    expiry_time = datetime.fromisoformat(expires_at)
                    if expiry_time > now:
                        valid_memories.append(memory)
                except (ValueError, TypeError):
                    # 如果解析失败，保留记录
                    valid_memories.append(memory)
            else:
                # 没有过期时间的记录永久保留
                valid_memories.append(memory)

        self._memories = valid_memories

    def get_recent(self, n: int = 10, include_expired: bool = False) -> list[dict]:
        """
        获取最近的N条记录

        Args:
            n: 记录数量
            include_expired: 是否包含过期记录

        Returns:
            记录列表
        """
        if not include_expired:
            self._cleanup_expired()

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
        self._cleanup_expired()
        return [m for m in self._memories if m["event_type"] == event_type]

    def get_conversation_history(self) -> list[dict]:
        """
        获取对话历史（用于上下文）

        Returns:
            对话历史列表
        """
        self._cleanup_expired()
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
        self._cleanup_expired()
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
        """获取记录数量（不含过期）"""
        self._cleanup_expired()
        return len(self._memories)

    def to_list(self) -> list[dict]:
        """转换为列表"""
        self._cleanup_expired()
        return list(self._memories)

    def set_ttl(self, ttl_hours: Optional[float]):
        """
        动态设置 TTL

        Args:
            ttl_hours: 新的 TTL 值（小时），None 表示禁用
        """
        self.ttl_hours = ttl_hours
        if ttl_hours:
            self._cleanup_expired()

    def get_statistics(self) -> dict:
        """获取统计信息"""
        self._cleanup_expired()
        type_counts = {}
        for m in self._memories:
            t = m.get("event_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_entries": len(self._memories),
            "max_entries": self.max_entries,
            "ttl_hours": self.ttl_hours,
            "by_type": type_counts,
        }
