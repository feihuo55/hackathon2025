"""
反馈记忆系统
收集、存储和分析用户反馈，支持闭环学习优化

功能：
- 存储用户对回复的反馈（正面/负面/纠正）
- 记录检索结果的相关性反馈
- 支持反馈聚合和趋势分析
- 持久化存储
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib


class FeedbackType(Enum):
    """反馈类型枚举"""
    POSITIVE = "positive"           # 👍 回复有帮助
    NEGATIVE = "negative"           # 👎 回复无帮助
    CORRECTION = "correction"       # ✏️ 用户提供正确答案
    IRRELEVANT = "irrelevant"       # 检索结果不相关
    MISSING_INFO = "missing_info"   # 缺少关键信息
    PARTIAL = "partial"             # 部分正确
    PERFECT = "perfect"             # 完全正确


class FeedbackSource(Enum):
    """反馈来源"""
    USER_EXPLICIT = "user_explicit"     # 用户主动点击
    USER_CORRECTION = "user_correction" # 用户纠正
    IMPLICIT_CLICK = "implicit_click"   # 隐式点击行为
    IMPLICIT_DWELL = "implicit_dwell"   # 停留时间推断
    SYSTEM_AUTO = "system_auto"         # 系统自动判断


@dataclass
class Feedback:
    """反馈数据类"""
    feedback_id: str
    query: str                              # 原始查询
    response: str                           # 系统回复
    feedback_type: FeedbackType             # 反馈类型
    source: FeedbackSource                  # 反馈来源
    score: float = 0.0                      # 评分 (-1.0 到 1.0)
    correction_text: Optional[str] = None   # 用户纠正内容
    retrieved_doc_ids: List[str] = field(default_factory=list)  # 检索到的文档ID
    relevant_doc_ids: List[str] = field(default_factory=list)   # 用户标记相关的文档
    irrelevant_doc_ids: List[str] = field(default_factory=list) # 用户标记不相关的文档
    session_id: Optional[str] = None        # 会话ID
    intent: Optional[str] = None            # 识别的意图
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "feedback_id": self.feedback_id,
            "query": self.query,
            "response": self.response,
            "feedback_type": self.feedback_type.value,
            "source": self.source.value,
            "score": self.score,
            "correction_text": self.correction_text,
            "retrieved_doc_ids": self.retrieved_doc_ids,
            "relevant_doc_ids": self.relevant_doc_ids,
            "irrelevant_doc_ids": self.irrelevant_doc_ids,
            "session_id": self.session_id,
            "intent": self.intent,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Feedback":
        """从字典创建"""
        return cls(
            feedback_id=data["feedback_id"],
            query=data["query"],
            response=data.get("response", ""),
            feedback_type=FeedbackType(data["feedback_type"]),
            source=FeedbackSource(data.get("source", "user_explicit")),
            score=data.get("score", 0.0),
            correction_text=data.get("correction_text"),
            retrieved_doc_ids=data.get("retrieved_doc_ids", []),
            relevant_doc_ids=data.get("relevant_doc_ids", []),
            irrelevant_doc_ids=data.get("irrelevant_doc_ids", []),
            session_id=data.get("session_id"),
            intent=data.get("intent"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class QueryFeedbackStats:
    """查询反馈统计"""
    query_hash: str
    query_sample: str               # 查询样本
    total_feedbacks: int = 0
    positive_count: int = 0
    negative_count: int = 0
    correction_count: int = 0
    avg_score: float = 0.0
    last_feedback_at: Optional[str] = None

    @property
    def satisfaction_rate(self) -> float:
        """满意度"""
        total = self.positive_count + self.negative_count
        return self.positive_count / total if total > 0 else 0.5

    def to_dict(self) -> dict:
        return {
            "query_hash": self.query_hash,
            "query_sample": self.query_sample,
            "total_feedbacks": self.total_feedbacks,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "correction_count": self.correction_count,
            "avg_score": self.avg_score,
            "satisfaction_rate": self.satisfaction_rate,
            "last_feedback_at": self.last_feedback_at,
        }


class FeedbackMemory:
    """
    反馈记忆系统

    核心功能：
    1. 收集和存储用户反馈
    2. 计算查询级别的反馈统计
    3. 识别低质量回复模式
    4. 提供反馈数据用于知识优化
    """

    def __init__(
        self,
        max_feedbacks: int = 10000,
        enable_persistence: bool = True,
        storage_dir: str = "./data/memory",
    ):
        """
        初始化反馈记忆

        Args:
            max_feedbacks: 最大反馈记录数
            enable_persistence: 是否启用持久化
            storage_dir: 存储目录
        """
        self.max_feedbacks = max_feedbacks
        self._feedbacks: List[Feedback] = []
        self._query_stats: Dict[str, QueryFeedbackStats] = {}
        self._doc_relevance_scores: Dict[str, float] = {}  # doc_id -> 相关性分数
        self._enable_persistence = enable_persistence
        self._storage_dir = storage_dir
        self._persistence = None
        self._feedback_counter = 0

        # 加载已有数据
        if enable_persistence:
            self._load_from_disk()

    def _generate_feedback_id(self) -> str:
        """生成反馈ID"""
        self._feedback_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"fb_{timestamp}_{self._feedback_counter}"

    def _hash_query(self, query: str) -> str:
        """生成查询哈希（用于聚合相似查询）"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def add_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        source: FeedbackSource = FeedbackSource.USER_EXPLICIT,
        score: Optional[float] = None,
        correction_text: Optional[str] = None,
        retrieved_doc_ids: Optional[List[str]] = None,
        relevant_doc_ids: Optional[List[str]] = None,
        irrelevant_doc_ids: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        intent: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Feedback:
        """
        添加用户反馈

        Args:
            query: 用户查询
            response: 系统回复
            feedback_type: 反馈类型
            source: 反馈来源
            score: 评分 (-1.0 到 1.0)，如不提供则根据类型自动计算
            correction_text: 用户纠正文本
            retrieved_doc_ids: 检索到的文档ID列表
            relevant_doc_ids: 用户标记为相关的文档
            irrelevant_doc_ids: 用户标记为不相关的文档
            session_id: 会话ID
            intent: 意图
            metadata: 额外元数据

        Returns:
            创建的反馈对象
        """
        # 自动计算分数
        if score is None:
            score = self._calculate_score(feedback_type)

        feedback = Feedback(
            feedback_id=self._generate_feedback_id(),
            query=query,
            response=response,
            feedback_type=feedback_type,
            source=source,
            score=score,
            correction_text=correction_text,
            retrieved_doc_ids=retrieved_doc_ids or [],
            relevant_doc_ids=relevant_doc_ids or [],
            irrelevant_doc_ids=irrelevant_doc_ids or [],
            session_id=session_id,
            intent=intent,
            metadata=metadata or {},
        )

        self._feedbacks.append(feedback)

        # 更新查询统计
        self._update_query_stats(feedback)

        # 更新文档相关性分数
        self._update_doc_relevance(feedback)

        # 限制数量
        if len(self._feedbacks) > self.max_feedbacks:
            self._feedbacks = self._feedbacks[-self.max_feedbacks:]

        # 持久化
        self._save_to_disk()

        return feedback

    def _calculate_score(self, feedback_type: FeedbackType) -> float:
        """根据反馈类型计算分数"""
        score_map = {
            FeedbackType.PERFECT: 1.0,
            FeedbackType.POSITIVE: 0.8,
            FeedbackType.PARTIAL: 0.3,
            FeedbackType.NEGATIVE: -0.5,
            FeedbackType.IRRELEVANT: -0.8,
            FeedbackType.MISSING_INFO: -0.3,
            FeedbackType.CORRECTION: -0.2,  # 需要纠正说明有问题但用户愿意帮助
        }
        return score_map.get(feedback_type, 0.0)

    def _update_query_stats(self, feedback: Feedback):
        """更新查询统计"""
        query_hash = self._hash_query(feedback.query)

        if query_hash not in self._query_stats:
            self._query_stats[query_hash] = QueryFeedbackStats(
                query_hash=query_hash,
                query_sample=feedback.query[:100],
            )

        stats = self._query_stats[query_hash]
        stats.total_feedbacks += 1
        stats.last_feedback_at = feedback.created_at

        if feedback.feedback_type in [FeedbackType.POSITIVE, FeedbackType.PERFECT]:
            stats.positive_count += 1
        elif feedback.feedback_type in [FeedbackType.NEGATIVE, FeedbackType.IRRELEVANT]:
            stats.negative_count += 1
        elif feedback.feedback_type == FeedbackType.CORRECTION:
            stats.correction_count += 1

        # 更新平均分
        all_scores = [
            f.score for f in self._feedbacks
            if self._hash_query(f.query) == query_hash
        ]
        stats.avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

    def _update_doc_relevance(self, feedback: Feedback):
        """更新文档相关性分数"""
        # 正向反馈提升相关文档分数
        for doc_id in feedback.relevant_doc_ids:
            current = self._doc_relevance_scores.get(doc_id, 0.5)
            self._doc_relevance_scores[doc_id] = min(1.0, current + 0.1)

        # 负向反馈降低不相关文档分数
        for doc_id in feedback.irrelevant_doc_ids:
            current = self._doc_relevance_scores.get(doc_id, 0.5)
            self._doc_relevance_scores[doc_id] = max(0.0, current - 0.1)

        # 正面反馈也提升检索到的文档分数
        if feedback.feedback_type in [FeedbackType.POSITIVE, FeedbackType.PERFECT]:
            for doc_id in feedback.retrieved_doc_ids:
                if doc_id not in feedback.irrelevant_doc_ids:
                    current = self._doc_relevance_scores.get(doc_id, 0.5)
                    self._doc_relevance_scores[doc_id] = min(1.0, current + 0.05)

    def add_positive_feedback(
        self,
        query: str,
        response: str,
        retrieved_doc_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> Feedback:
        """快捷方法：添加正面反馈"""
        return self.add_feedback(
            query=query,
            response=response,
            feedback_type=FeedbackType.POSITIVE,
            retrieved_doc_ids=retrieved_doc_ids,
            **kwargs,
        )

    def add_negative_feedback(
        self,
        query: str,
        response: str,
        retrieved_doc_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> Feedback:
        """快捷方法：添加负面反馈"""
        return self.add_feedback(
            query=query,
            response=response,
            feedback_type=FeedbackType.NEGATIVE,
            retrieved_doc_ids=retrieved_doc_ids,
            **kwargs,
        )

    def add_correction(
        self,
        query: str,
        response: str,
        correction_text: str,
        **kwargs,
    ) -> Feedback:
        """快捷方法：添加纠正反馈"""
        return self.add_feedback(
            query=query,
            response=response,
            feedback_type=FeedbackType.CORRECTION,
            correction_text=correction_text,
            **kwargs,
        )

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """获取反馈"""
        for fb in self._feedbacks:
            if fb.feedback_id == feedback_id:
                return fb
        return None

    def get_recent_feedbacks(self, n: int = 20) -> List[Feedback]:
        """获取最近的反馈"""
        return self._feedbacks[-n:]

    def get_feedbacks_by_type(self, feedback_type: FeedbackType) -> List[Feedback]:
        """按类型获取反馈"""
        return [f for f in self._feedbacks if f.feedback_type == feedback_type]

    def get_feedbacks_for_query(self, query: str) -> List[Feedback]:
        """获取特定查询的所有反馈"""
        query_hash = self._hash_query(query)
        return [
            f for f in self._feedbacks
            if self._hash_query(f.query) == query_hash
        ]

    def get_negative_patterns(
        self,
        min_negative_count: int = 2,
        max_satisfaction_rate: float = 0.5,
    ) -> List[QueryFeedbackStats]:
        """
        获取低质量回复模式（需要改进的查询类型）

        Args:
            min_negative_count: 最小负面反馈数
            max_satisfaction_rate: 最大满意度阈值

        Returns:
            需要改进的查询统计列表
        """
        patterns = []
        for stats in self._query_stats.values():
            if (stats.negative_count >= min_negative_count and
                stats.satisfaction_rate <= max_satisfaction_rate):
                patterns.append(stats)

        # 按满意度升序排列（最差的在前）
        patterns.sort(key=lambda x: x.satisfaction_rate)
        return patterns

    def get_corrections(self, limit: int = 50) -> List[Feedback]:
        """获取用户纠正记录（用于知识学习）"""
        corrections = [
            f for f in self._feedbacks
            if f.feedback_type == FeedbackType.CORRECTION and f.correction_text
        ]
        return corrections[-limit:]

    def get_doc_relevance_boost(self, doc_id: str) -> float:
        """
        获取文档的相关性提升因子

        Returns:
            0.0-2.0 的提升因子，1.0 表示无变化
        """
        base_score = self._doc_relevance_scores.get(doc_id, 0.5)
        # 将 0-1 的分数映射到 0.5-1.5 的提升因子
        return 0.5 + base_score

    def get_query_quality_score(self, query: str) -> float:
        """
        获取查询的历史质���分数

        用于预判该类查询的回复质量，可用于触发额外检索或人工介入

        Returns:
            -1.0 到 1.0 的分数
        """
        query_hash = self._hash_query(query)
        stats = self._query_stats.get(query_hash)
        if stats:
            return stats.avg_score
        return 0.0  # 无历史数据，返回中性分数

    def should_request_feedback(self, query: str) -> bool:
        """
        判断是否应该主动请求用户反馈

        对于历史表现差的查询类型，建议主动请求反馈
        """
        score = self.get_query_quality_score(query)
        return score < -0.2

    def get_improvement_suggestions(self) -> List[Dict]:
        """
        获取改进建议

        基于反馈数据分析，返回系统改进建议
        """
        suggestions = []

        # 1. 低满意度查询
        negative_patterns = self.get_negative_patterns()
        if negative_patterns:
            suggestions.append({
                "type": "low_satisfaction_queries",
                "priority": "high",
                "description": "以下查询类型满意度较低，建议优化知识库或检索策略",
                "data": [p.to_dict() for p in negative_patterns[:5]],
            })

        # 2. 有纠正的查询
        corrections = self.get_corrections(limit=10)
        if corrections:
            suggestions.append({
                "type": "user_corrections",
                "priority": "high",
                "description": "用户提供了纠正信息，建议更新知识库",
                "data": [
                    {
                        "query": c.query,
                        "original_response": c.response[:100],
                        "correction": c.correction_text,
                    }
                    for c in corrections
                ],
            })

        # 3. 低相关性文档
        low_relevance_docs = [
            {"doc_id": doc_id, "score": score}
            for doc_id, score in self._doc_relevance_scores.items()
            if score < 0.3
        ]
        if low_relevance_docs:
            suggestions.append({
                "type": "low_relevance_documents",
                "priority": "medium",
                "description": "以下文档相关性评分较低，建议审查或更新",
                "data": sorted(low_relevance_docs, key=lambda x: x["score"])[:10],
            })

        return suggestions

    def get_statistics(self) -> Dict:
        """获取反馈统计"""
        if not self._feedbacks:
            return {
                "total_feedbacks": 0,
                "by_type": {},
                "avg_score": 0,
                "satisfaction_rate": 0,
            }

        type_counts = defaultdict(int)
        for f in self._feedbacks:
            type_counts[f.feedback_type.value] += 1

        positive_count = type_counts.get("positive", 0) + type_counts.get("perfect", 0)
        negative_count = type_counts.get("negative", 0) + type_counts.get("irrelevant", 0)
        total_rated = positive_count + negative_count

        return {
            "total_feedbacks": len(self._feedbacks),
            "by_type": dict(type_counts),
            "avg_score": sum(f.score for f in self._feedbacks) / len(self._feedbacks),
            "satisfaction_rate": positive_count / total_rated if total_rated > 0 else 0,
            "unique_queries": len(self._query_stats),
            "corrections_count": type_counts.get("correction", 0),
            "tracked_documents": len(self._doc_relevance_scores),
        }

    def clear(self):
        """清空反馈记忆"""
        self._feedbacks.clear()
        self._query_stats.clear()
        self._doc_relevance_scores.clear()
        self._save_to_disk()

    # ============ 持久化方法 ============

    def _get_persistence_helper(self):
        """获取持久化助手"""
        if not self._enable_persistence:
            return None

        if self._persistence is None:
            try:
                from .persistence import get_persistence
                self._persistence = get_persistence(self._storage_dir)
            except ImportError:
                pass

        return self._persistence

    def _load_from_disk(self):
        """从磁盘加载数据"""
        helper = self._get_persistence_helper()
        if helper:
            try:
                data = helper.load("feedback")
                if data:
                    self.from_dict(data)
            except Exception as e:
                print(f"Warning: 加载反馈记忆失败: {e}")

    def _save_to_disk(self):
        """保存数据到磁盘"""
        helper = self._get_persistence_helper()
        if helper:
            try:
                helper.save("feedback", self.to_dict())
            except Exception as e:
                print(f"Warning: 保存反馈记忆失败: {e}")

    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "feedbacks": [f.to_dict() for f in self._feedbacks],
            "query_stats": {k: v.to_dict() for k, v in self._query_stats.items()},
            "doc_relevance_scores": self._doc_relevance_scores,
            "feedback_counter": self._feedback_counter,
        }

    def from_dict(self, data: Dict):
        """从字典导入"""
        # 导入反馈
        self._feedbacks = [
            Feedback.from_dict(f) for f in data.get("feedbacks", [])
        ]

        # 导入查询统计
        for query_hash, stats_data in data.get("query_stats", {}).items():
            self._query_stats[query_hash] = QueryFeedbackStats(
                query_hash=stats_data["query_hash"],
                query_sample=stats_data["query_sample"],
                total_feedbacks=stats_data.get("total_feedbacks", 0),
                positive_count=stats_data.get("positive_count", 0),
                negative_count=stats_data.get("negative_count", 0),
                correction_count=stats_data.get("correction_count", 0),
                avg_score=stats_data.get("avg_score", 0.0),
                last_feedback_at=stats_data.get("last_feedback_at"),
            )

        # 导入文档相关性
        self._doc_relevance_scores = data.get("doc_relevance_scores", {})
        self._feedback_counter = data.get("feedback_counter", 0)

    def export(self) -> Dict:
        """导出数据（用于分析）"""
        return {
            "statistics": self.get_statistics(),
            "improvement_suggestions": self.get_improvement_suggestions(),
            "recent_feedbacks": [f.to_dict() for f in self.get_recent_feedbacks(50)],
            "negative_patterns": [p.to_dict() for p in self.get_negative_patterns()],
        }
