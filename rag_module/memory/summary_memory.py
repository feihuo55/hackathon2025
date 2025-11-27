"""
摘要记忆
存储对话和事件的压缩摘要
支持JSON文件持久化
"""
from datetime import datetime
from typing import Optional
from collections import deque
from dataclasses import dataclass, field
from config import MEMORY_CONFIG

# 延迟导入持久化模块
_persistence_module = None


def _get_persistence():
    """延迟加载持久化模块"""
    global _persistence_module
    if _persistence_module is None:
        try:
            from .persistence import get_persistence, SummaryPersistence
            _persistence_module = (get_persistence, SummaryPersistence)
        except ImportError:
            pass
    return _persistence_module


@dataclass
class Summary:
    """摘要数据类"""
    summary_id: str
    content: str
    source_type: str  # conversation, session, task
    source_count: int  # 摘要来源的条目数
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "summary_id": self.summary_id,
            "content": self.content,
            "source_type": self.source_type,
            "source_count": self.source_count,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class SummaryMemory:
    """摘要记忆系统 - 存储压缩的对话和事件摘要"""

    def __init__(
        self,
        max_summaries: int = 50,
        max_summary_length: int = None,
        enable_persistence: bool = True,
        storage_dir: str = "./data/memory",
    ):
        """
        初始化摘要记忆

        Args:
            max_summaries: 最大摘要数量
            max_summary_length: 单个摘要最大长度
            enable_persistence: 是否启用持久化
            storage_dir: 存储目录
        """
        self.max_summaries = max_summaries
        self.max_summary_length = max_summary_length or MEMORY_CONFIG.get("max_summary_length", 500)
        self._summaries: deque[Summary] = deque(maxlen=max_summaries)
        self._summary_index: dict[str, Summary] = {}
        self._enable_persistence = enable_persistence
        self._persistence = None
        self._storage_dir = storage_dir

        # 尝试加载已有数据
        if enable_persistence:
            self._load_from_disk()

    def create_summary(
        self,
        content: str,
        source_type: str = "conversation",
        source_count: int = 1,
        summary_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Summary:
        """
        创建摘要

        Args:
            content: 摘要内容
            source_type: 来源类型
            source_count: 来源条目数
            summary_id: 摘要ID（可选）
            metadata: 额外元数据

        Returns:
            创建的摘要对象
        """
        # 截断过长的内容
        if len(content) > self.max_summary_length:
            content = content[:self.max_summary_length - 3] + "..."

        # 生成ID
        if not summary_id:
            summary_id = f"summary_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        summary = Summary(
            summary_id=summary_id,
            content=content,
            source_type=source_type,
            source_count=source_count,
            metadata=metadata or {},
        )

        self._summaries.append(summary)
        self._summary_index[summary_id] = summary

        # 清理旧的索引
        self._cleanup_index()

        # 自动保存
        self._save_to_disk()

        return summary

    def _cleanup_index(self):
        """清理不在队列中的索引"""
        current_ids = {s.summary_id for s in self._summaries}
        for sid in list(self._summary_index.keys()):
            if sid not in current_ids:
                del self._summary_index[sid]

    def summarize_conversation(
        self,
        messages: list[dict],
        max_messages: int = 10,
    ) -> Summary:
        """
        摘要对话历史

        Args:
            messages: 消息列表 [{"role": "user/assistant", "content": "..."}]
            max_messages: 最大处理消息数

        Returns:
            对话摘要
        """
        # 获取最近的消息
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

        # 构建摘要内容
        summary_parts = []
        topics = set()

        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                # 提取用户意图
                summary_parts.append(f"用户: {self._extract_intent(content)}")
                topics.update(self._extract_topics(content))
            elif role == "assistant":
                # 提取助手响应要点
                summary_parts.append(f"助手: {self._summarize_response(content)}")

        # 组合摘要
        content = "\n".join(summary_parts[-5:])  # 保留最近5条
        if topics:
            content = f"主题: {', '.join(list(topics)[:5])}\n{content}"

        return self.create_summary(
            content=content,
            source_type="conversation",
            source_count=len(recent_messages),
            metadata={"topics": list(topics)},
        )

    def _extract_intent(self, text: str) -> str:
        """提取用户意图（简化版）"""
        # 截取前100字符
        text = text[:100].strip()
        if len(text) > 50:
            # 尝试在句号处截断
            for punct in ["。", ".", "？", "?", "！", "!"]:
                idx = text.find(punct)
                if 0 < idx < 80:
                    return text[:idx + 1]
            return text[:50] + "..."
        return text

    def _summarize_response(self, text: str) -> str:
        """摘要助手响应（简化版）"""
        # 截取前80字符
        text = text[:150].strip()
        if len(text) > 80:
            return text[:80] + "..."
        return text

    def _extract_topics(self, text: str) -> set:
        """提取话题关键词"""
        # 金融领域关键词
        keywords = {
            "基金", "净值", "分红", "派息", "查询", "处理",
            "fund", "nav", "dividend", "query", "process"
        }

        topics = set()
        text_lower = text.lower()

        for kw in keywords:
            if kw.lower() in text_lower:
                topics.add(kw)

        return topics

    def get_summary(self, summary_id: str) -> Optional[Summary]:
        """获取摘要"""
        return self._summary_index.get(summary_id)

    def get_recent(self, n: int = 5) -> list[Summary]:
        """
        获取最近的摘要

        Args:
            n: 数量

        Returns:
            摘要列表
        """
        summaries = list(self._summaries)
        return summaries[-n:] if len(summaries) >= n else summaries

    def get_by_type(self, source_type: str) -> list[Summary]:
        """
        按类型获取摘要

        Args:
            source_type: 来源类型

        Returns:
            摘要列表
        """
        return [s for s in self._summaries if s.source_type == source_type]

    def get_context_summary(self, max_summaries: int = 3) -> str:
        """
        获取上下文摘要文本

        Args:
            max_summaries: 最大摘要数

        Returns:
            合并的摘要文本
        """
        recent = self.get_recent(max_summaries)
        if not recent:
            return ""

        parts = []
        for s in recent:
            parts.append(f"[{s.source_type}] {s.content}")

        return "\n---\n".join(parts)

    def merge_summaries(
        self,
        summaries: list[Summary],
        new_summary_id: Optional[str] = None,
    ) -> Summary:
        """
        合并多个摘要

        Args:
            summaries: 要合并的摘要列表
            new_summary_id: 新摘要ID

        Returns:
            合并后的摘要
        """
        if not summaries:
            return self.create_summary(
                content="",
                source_type="merged",
                source_count=0,
            )

        # 合并内容
        contents = [s.content for s in summaries]
        merged_content = " | ".join(contents)

        # 合并元数据中的topics
        all_topics = set()
        for s in summaries:
            topics = s.metadata.get("topics", [])
            all_topics.update(topics)

        total_source_count = sum(s.source_count for s in summaries)

        return self.create_summary(
            content=merged_content,
            source_type="merged",
            source_count=total_source_count,
            summary_id=new_summary_id,
            metadata={"topics": list(all_topics), "merged_from": len(summaries)},
        )

    def search(self, keyword: str) -> list[Summary]:
        """
        搜索摘要

        Args:
            keyword: 关键词

        Returns:
            匹配的摘要列表
        """
        keyword_lower = keyword.lower()
        results = []

        for summary in self._summaries:
            if keyword_lower in summary.content.lower():
                results.append(summary)
            elif any(keyword_lower in t.lower() for t in summary.metadata.get("topics", [])):
                results.append(summary)

        return results

    def count(self) -> int:
        """获取摘要数量"""
        return len(self._summaries)

    def clear(self):
        """清空摘要记忆"""
        self._summaries.clear()
        self._summary_index.clear()
        self._save_to_disk()

    def _get_persistence_helper(self):
        """获取持久化助手"""
        if not self._enable_persistence:
            return None

        if self._persistence is None:
            pm = _get_persistence()
            if pm:
                get_persistence, SummaryPersistence = pm
                persistence = get_persistence(self._storage_dir)
                self._persistence = SummaryPersistence(persistence)

        return self._persistence

    def _load_from_disk(self):
        """从磁盘加载数据"""
        helper = self._get_persistence_helper()
        if helper:
            try:
                data = helper.load_summaries()
                if data:
                    self.from_list(data)
            except Exception as e:
                print(f"Warning: 加载摘要记忆失败: {e}")

    def _save_to_disk(self):
        """保存数据到磁盘"""
        helper = self._get_persistence_helper()
        if helper:
            try:
                helper.save_summaries(self.to_list())
            except Exception as e:
                print(f"Warning: 保存摘要记忆失败: {e}")

    def save(self):
        """手动保存到磁盘"""
        self._save_to_disk()

    def from_list(self, data: list[dict]):
        """从列表导入数据"""
        for item in data:
            summary = Summary(
                summary_id=item["summary_id"],
                content=item["content"],
                source_type=item.get("source_type", "conversation"),
                source_count=item.get("source_count", 1),
                created_at=item.get("created_at", datetime.now().isoformat()),
                metadata=item.get("metadata", {}),
            )
            self._summaries.append(summary)
            self._summary_index[summary.summary_id] = summary

    def to_list(self) -> list[dict]:
        """导出为列表"""
        return [s.to_dict() for s in self._summaries]

    def get_statistics(self) -> dict:
        """获取统计信息"""
        type_counts = {}
        for s in self._summaries:
            type_counts[s.source_type] = type_counts.get(s.source_type, 0) + 1

        return {
            "total_summaries": len(self._summaries),
            "by_type": type_counts,
            "total_source_items": sum(s.source_count for s in self._summaries),
        }
