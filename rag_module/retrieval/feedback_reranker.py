"""
基于反馈的检索结果重排序器
利用用户反馈信号优化检索排序

功能：
- 基于历史反馈调整检索分数
- 支持多种重排序策略
- 与现有检索服务无缝集成
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ..learning.relevance_learner import RelevanceLearner, get_relevance_learner
from ..memory.feedback_memory import FeedbackMemory


@dataclass
class RerankedResult:
    """重排序后的检索结果"""
    doc_id: str
    content: str
    original_score: float
    learned_score: float
    confidence: float
    final_score: float
    metadata: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "original_score": self.original_score,
            "learned_score": self.learned_score,
            "confidence": self.confidence,
            "final_score": self.final_score,
            "metadata": self.metadata,
        }


class FeedbackReranker:
    """
    基于反馈的重排序器

    将用户反馈信号融入检索排序，实现个性化和持续优化的检索结果
    """

    def __init__(
        self,
        relevance_learner: Optional[RelevanceLearner] = None,
        feedback_memory: Optional[FeedbackMemory] = None,
        feedback_weight: float = 0.3,
        exploration_factor: float = 0.1,
        demote_threshold: float = 0.3,
    ):
        """
        初始化重排序器

        Args:
            relevance_learner: 相关性学习器
            feedback_memory: 反馈记忆（用于文档级别的相关性提升）
            feedback_weight: 反馈分数权重 (0-1)
            exploration_factor: 探索因子（对未知文档的奖励）
            demote_threshold: 降权阈值（低于此分数的文档将被降权）
        """
        self.relevance_learner = relevance_learner or get_relevance_learner()
        self.feedback_memory = feedback_memory
        self.feedback_weight = feedback_weight
        self.exploration_factor = exploration_factor
        self.demote_threshold = demote_threshold

    def rerank(
        self,
        query: str,
        results: List[Dict],
        doc_id_key: str = "doc_id",
        content_key: str = "content",
        score_key: str = "score",
        metadata_key: str = "metadata",
    ) -> List[RerankedResult]:
        """
        重排序检索结果

        Args:
            query: 用户查询
            results: 原始检索结果
            doc_id_key: 文档ID字段名
            content_key: 内容字段名
            score_key: 分数字段名
            metadata_key: 元数据字段名

        Returns:
            重排序后的结果列表
        """
        if not results:
            return []

        reranked = []

        # 获取应降权的文档
        demote_docs = set(self.relevance_learner.get_docs_to_demote(
            query, self.demote_threshold
        ))

        for result in results:
            doc_id = self._extract_field(result, doc_id_key, "")
            content = self._extract_field(result, content_key, "")
            original_score = self._extract_field(result, score_key, 0.5)
            metadata = self._extract_field(result, metadata_key, {})

            # 获取学习的相关性分数
            learned_score, confidence = self.relevance_learner.get_relevance_score(
                query, doc_id
            )

            # 获取文档级别的反馈提升
            doc_boost = 1.0
            if self.feedback_memory:
                doc_boost = self.feedback_memory.get_doc_relevance_boost(doc_id)

            # 计算有效权重（基于置信度）
            effective_weight = self.feedback_weight * confidence

            # 探索奖励（对于低置信度的文档）
            exploration_bonus = self.exploration_factor * (1 - confidence)

            # 降权处理
            demote_penalty = 0.0
            if doc_id in demote_docs:
                demote_penalty = 0.2

            # 最终分数计算
            final_score = (
                (1 - effective_weight) * original_score +
                effective_weight * learned_score +
                exploration_bonus -
                demote_penalty
            ) * doc_boost

            # 确保分数在合理范围内
            final_score = max(0.0, min(1.0, final_score))

            reranked.append(RerankedResult(
                doc_id=doc_id,
                content=content,
                original_score=original_score,
                learned_score=learned_score,
                confidence=confidence,
                final_score=final_score,
                metadata=metadata,
            ))

        # 按最终分数排序
        reranked.sort(key=lambda x: x.final_score, reverse=True)

        return reranked

    def rerank_search_results(
        self,
        query: str,
        search_results: List[Any],
    ) -> List[RerankedResult]:
        """
        重排序 SearchResult 对象列表

        专门处理 KnowledgeSearch 返回的 SearchResult 对象
        """
        results = []
        for sr in search_results:
            results.append({
                "doc_id": getattr(sr, "doc_id", ""),
                "content": getattr(sr, "content", ""),
                "score": getattr(sr, "score", 0.5),
                "metadata": getattr(sr, "metadata", {}),
            })

        return self.rerank(query, results)

    def boost_results(
        self,
        query: str,
        results: List[Dict],
        boost_doc_ids: List[str],
        boost_factor: float = 1.5,
    ) -> List[Dict]:
        """
        提升特定文档的分数

        用于将用户之前标记为相关的文档提升到更高位置
        """
        boosted = []
        for result in results:
            doc_id = result.get("doc_id", "")
            score = result.get("score", 0.5)

            if doc_id in boost_doc_ids:
                score = min(1.0, score * boost_factor)

            boosted.append({**result, "score": score})

        boosted.sort(key=lambda x: x.get("score", 0), reverse=True)
        return boosted

    def filter_low_quality(
        self,
        query: str,
        results: List[Dict],
        min_confidence: float = 0.5,
        min_learned_score: float = 0.3,
    ) -> List[Dict]:
        """
        过滤低质量结果

        基于历史反馈，移除表现不佳的文档
        """
        filtered = []
        for result in results:
            doc_id = result.get("doc_id", "")
            learned_score, confidence = self.relevance_learner.get_relevance_score(
                query, doc_id
            )

            # 只有高置信度且分数低于阈值的才过滤
            if confidence >= min_confidence and learned_score < min_learned_score:
                continue

            filtered.append(result)

        return filtered

    def get_recommendations(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[tuple]:
        """
        获取基于反馈的推荐文档

        返回历史上表现好的文档，可用于补充检索结果
        """
        return self.relevance_learner.get_recommended_docs(query, top_k)

    def _extract_field(self, obj: Any, key: str, default: Any) -> Any:
        """从对象或字典中提取字段"""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def get_statistics(self) -> Dict:
        """获取重排序统计"""
        return {
            "relevance_learner": self.relevance_learner.get_statistics(),
            "feedback_weight": self.feedback_weight,
            "exploration_factor": self.exploration_factor,
        }


# 全局重排序器实例
_feedback_reranker: Optional[FeedbackReranker] = None


def get_feedback_reranker() -> FeedbackReranker:
    """获取全局反馈重排序器"""
    global _feedback_reranker
    if _feedback_reranker is None:
        _feedback_reranker = FeedbackReranker()
    return _feedback_reranker


# ============ 便捷函数 ============

def rerank_with_feedback(
    query: str,
    results: List[Dict],
    **kwargs,
) -> List[RerankedResult]:
    """便捷函数：使用反馈重排序"""
    return get_feedback_reranker().rerank(query, results, **kwargs)
