"""
相关性学习器
基于用户反馈学习查询-文档相关性，优化检索排序

功能：
- 学习查询与文档的相关性权重
- 基于反馈的检索结果重排序
- 个性化相关性调整
- 支持在线学习和批量更新
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import math
import hashlib


@dataclass
class RelevanceSignal:
    """相关性信号"""
    query_hash: str
    doc_id: str
    signal_type: str        # positive, negative, click, correction
    strength: float         # 信号强度 (-1.0 到 1.0)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "query_hash": self.query_hash,
            "doc_id": self.doc_id,
            "signal_type": self.signal_type,
            "strength": self.strength,
            "timestamp": self.timestamp,
        }


@dataclass
class QueryDocRelevance:
    """查询-文档相关性记录"""
    query_hash: str
    doc_id: str
    relevance_score: float = 0.5      # 0-1，0.5为中性
    confidence: float = 0.0           # 置信度，基于信号数量
    signal_count: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "query_hash": self.query_hash,
            "doc_id": self.doc_id,
            "relevance_score": self.relevance_score,
            "confidence": self.confidence,
            "signal_count": self.signal_count,
            "last_updated": self.last_updated,
        }


class RelevanceLearner:
    """
    相关性学习器

    核心算法：
    1. 收集用户反馈信号（点击、评分、纠正等）
    2. 使用指数移动平均(EMA)更新相关性分数
    3. 基于置信度加权的重排序
    4. 支持冷启动和探索-利用平衡
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        decay_factor: float = 0.95,
        min_confidence_threshold: float = 0.3,
        exploration_bonus: float = 0.1,
        max_signals: int = 50000,
    ):
        """
        初始化相关性学习器

        Args:
            learning_rate: 学习率，控制新信号对分数的影响
            decay_factor: 时间衰减因子
            min_confidence_threshold: 最小置信度阈值
            exploration_bonus: 探索奖励（用于未知文档）
            max_signals: 最大信号记录数
        """
        self.learning_rate = learning_rate
        self.decay_factor = decay_factor
        self.min_confidence_threshold = min_confidence_threshold
        self.exploration_bonus = exploration_bonus
        self.max_signals = max_signals

        # 核心数据结构
        self._relevance_matrix: Dict[str, Dict[str, QueryDocRelevance]] = defaultdict(dict)
        self._signals: List[RelevanceSignal] = []
        self._global_doc_scores: Dict[str, float] = {}  # 文档全局质量分数
        self._query_patterns: Dict[str, List[str]] = {}  # 查询模式 -> 相关文档列表

    def _hash_query(self, query: str) -> str:
        """生成查询哈希"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def _normalize_query(self, query: str) -> str:
        """标准化查询"""
        return query.lower().strip()

    def add_signal(
        self,
        query: str,
        doc_id: str,
        signal_type: str,
        strength: float,
    ) -> RelevanceSignal:
        """
        添加相关性信号

        Args:
            query: 用户查询
            doc_id: 文档ID
            signal_type: 信号类型 (positive, negative, click, correction)
            strength: 信号强度 (-1.0 到 1.0)

        Returns:
            创建的信号对象
        """
        query_hash = self._hash_query(query)

        signal = RelevanceSignal(
            query_hash=query_hash,
            doc_id=doc_id,
            signal_type=signal_type,
            strength=strength,
        )

        self._signals.append(signal)

        # 限制信号数量
        if len(self._signals) > self.max_signals:
            self._signals = self._signals[-self.max_signals:]

        # 更新相关性矩阵
        self._update_relevance(query_hash, doc_id, signal)

        # 更新全局文档分数
        self._update_global_doc_score(doc_id, strength)

        return signal

    def _update_relevance(
        self,
        query_hash: str,
        doc_id: str,
        signal: RelevanceSignal,
    ):
        """更新查询-文档相关性"""
        if doc_id not in self._relevance_matrix[query_hash]:
            self._relevance_matrix[query_hash][doc_id] = QueryDocRelevance(
                query_hash=query_hash,
                doc_id=doc_id,
            )

        rel = self._relevance_matrix[query_hash][doc_id]

        # 使用指数移动平均更新分数
        # 将信号强度 (-1 到 1) 映射到 (0 到 1)
        target_score = (signal.strength + 1) / 2

        # EMA 更新
        rel.relevance_score = (
            (1 - self.learning_rate) * rel.relevance_score +
            self.learning_rate * target_score
        )

        # 更新信号计数和置信度
        rel.signal_count += 1
        # 置信度随信号数量增加而提升，但有上限
        rel.confidence = min(1.0, rel.signal_count / 10.0)
        rel.last_updated = datetime.now().isoformat()

    def _update_global_doc_score(self, doc_id: str, signal_strength: float):
        """更新文档全局质量分数"""
        current = self._global_doc_scores.get(doc_id, 0.5)
        # 缓慢更新全局分数
        target = (signal_strength + 1) / 2
        self._global_doc_scores[doc_id] = (
            0.95 * current + 0.05 * target
        )

    def add_positive_feedback(self, query: str, doc_ids: List[str]):
        """添加正面反馈（文档相关）"""
        for doc_id in doc_ids:
            self.add_signal(query, doc_id, "positive", 0.8)

    def add_negative_feedback(self, query: str, doc_ids: List[str]):
        """添加负面反馈（文档不相关）"""
        for doc_id in doc_ids:
            self.add_signal(query, doc_id, "negative", -0.8)

    def add_click_signal(self, query: str, doc_id: str, rank: int):
        """
        添加点击信号（隐式反馈）

        点击位置越靠后，信号越强（因为用户愿意翻页找到它）
        """
        # 基于排名的点击强度
        strength = min(0.9, 0.3 + 0.1 * rank)
        self.add_signal(query, doc_id, "click", strength)

    def add_correction_signal(
        self,
        query: str,
        incorrect_doc_ids: List[str],
        correct_info: str,
    ):
        """添加纠正信号"""
        for doc_id in incorrect_doc_ids:
            self.add_signal(query, doc_id, "correction", -0.5)

    def get_relevance_score(
        self,
        query: str,
        doc_id: str,
    ) -> Tuple[float, float]:
        """
        获取查询-文档相关性分数

        Returns:
            (relevance_score, confidence)
        """
        query_hash = self._hash_query(query)

        if doc_id in self._relevance_matrix.get(query_hash, {}):
            rel = self._relevance_matrix[query_hash][doc_id]
            return rel.relevance_score, rel.confidence

        # 无历史数据，返回基于全局分数的估计
        global_score = self._global_doc_scores.get(doc_id, 0.5)
        return global_score, 0.0

    def rerank_results(
        self,
        query: str,
        results: List[Dict],
        original_score_key: str = "score",
        doc_id_key: str = "doc_id",
        weight: float = 0.3,
    ) -> List[Dict]:
        """
        基于学习的相关性重排序检索结果

        Args:
            query: 用户查询
            results: 原始检索结果列表
            original_score_key: 原始分数字段名
            doc_id_key: 文档ID字段名
            weight: 学习分数的权重 (0-1)

        Returns:
            重排序后的结果
        """
        if not results:
            return results

        query_hash = self._hash_query(query)
        reranked = []

        for result in results:
            doc_id = result.get(doc_id_key, "")
            original_score = result.get(original_score_key, 0.5)

            # 获取学习的相关性分数
            learned_score, confidence = self.get_relevance_score(query, doc_id)

            # 基于置信度混合原始分数和学习分数
            effective_weight = weight * confidence

            # 加入探索奖励（对于低置信度的文档）
            exploration = self.exploration_bonus * (1 - confidence)

            # 最终分数计算
            final_score = (
                (1 - effective_weight) * original_score +
                effective_weight * learned_score +
                exploration
            )

            reranked.append({
                **result,
                "original_score": original_score,
                "learned_score": learned_score,
                "confidence": confidence,
                "final_score": final_score,
            })

        # 按最终分数排序
        reranked.sort(key=lambda x: x["final_score"], reverse=True)

        return reranked

    def get_recommended_docs(
        self,
        query: str,
        top_k: int = 5,
        min_confidence: float = 0.3,
    ) -> List[Tuple[str, float]]:
        """
        获取推荐文档（基于历史反馈）

        适用于补充检索结果

        Returns:
            [(doc_id, score), ...]
        """
        query_hash = self._hash_query(query)
        docs = self._relevance_matrix.get(query_hash, {})

        candidates = [
            (doc_id, rel.relevance_score, rel.confidence)
            for doc_id, rel in docs.items()
            if rel.confidence >= min_confidence and rel.relevance_score > 0.6
        ]

        # 按分数排序
        candidates.sort(key=lambda x: x[1] * x[2], reverse=True)

        return [(doc_id, score) for doc_id, score, _ in candidates[:top_k]]

    def get_docs_to_demote(
        self,
        query: str,
        threshold: float = 0.3,
    ) -> List[str]:
        """
        获取应降权的文档

        这些文档历史上对该类查询表现不佳
        """
        query_hash = self._hash_query(query)
        docs = self._relevance_matrix.get(query_hash, {})

        return [
            doc_id for doc_id, rel in docs.items()
            if rel.confidence >= self.min_confidence_threshold
            and rel.relevance_score < threshold
        ]

    def get_similar_queries(self, query: str) -> List[str]:
        """
        获取相似查询（基于共享高相关文档）

        用于查询扩展
        """
        query_hash = self._hash_query(query)
        current_docs = set(self._relevance_matrix.get(query_hash, {}).keys())

        if not current_docs:
            return []

        similar = []
        for other_hash, docs in self._relevance_matrix.items():
            if other_hash == query_hash:
                continue

            other_docs = set(docs.keys())
            overlap = len(current_docs & other_docs)

            if overlap > 0:
                # 计算 Jaccard 相似度
                jaccard = overlap / len(current_docs | other_docs)
                if jaccard > 0.3:
                    similar.append((other_hash, jaccard))

        similar.sort(key=lambda x: x[1], reverse=True)
        return [h for h, _ in similar[:5]]

    def decay_old_signals(self, days: int = 30):
        """
        衰减旧信号的影响

        定期调用以确保近期反馈更重要
        """
        cutoff = datetime.now()
        for query_hash, docs in self._relevance_matrix.items():
            for doc_id, rel in docs.items():
                try:
                    last_update = datetime.fromisoformat(rel.last_updated)
                    age_days = (cutoff - last_update).days
                    if age_days > days:
                        # 向中性值衰减
                        rel.relevance_score = (
                            self.decay_factor * rel.relevance_score +
                            (1 - self.decay_factor) * 0.5
                        )
                        rel.confidence *= self.decay_factor
                except (ValueError, TypeError):
                    pass

    def get_statistics(self) -> Dict:
        """获取学习器统计信息"""
        total_pairs = sum(len(docs) for docs in self._relevance_matrix.values())
        high_confidence_pairs = sum(
            1 for docs in self._relevance_matrix.values()
            for rel in docs.values()
            if rel.confidence >= self.min_confidence_threshold
        )

        return {
            "total_signals": len(self._signals),
            "unique_queries": len(self._relevance_matrix),
            "query_doc_pairs": total_pairs,
            "high_confidence_pairs": high_confidence_pairs,
            "tracked_documents": len(self._global_doc_scores),
            "avg_global_doc_score": (
                sum(self._global_doc_scores.values()) / len(self._global_doc_scores)
                if self._global_doc_scores else 0.5
            ),
        }

    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "relevance_matrix": {
                qh: {doc_id: rel.to_dict() for doc_id, rel in docs.items()}
                for qh, docs in self._relevance_matrix.items()
            },
            "signals": [s.to_dict() for s in self._signals[-1000:]],  # 只保存最近1000条
            "global_doc_scores": self._global_doc_scores,
        }

    def from_dict(self, data: Dict):
        """从字典导入"""
        # 导入相关性矩阵
        for query_hash, docs in data.get("relevance_matrix", {}).items():
            for doc_id, rel_data in docs.items():
                self._relevance_matrix[query_hash][doc_id] = QueryDocRelevance(
                    query_hash=rel_data["query_hash"],
                    doc_id=rel_data["doc_id"],
                    relevance_score=rel_data.get("relevance_score", 0.5),
                    confidence=rel_data.get("confidence", 0.0),
                    signal_count=rel_data.get("signal_count", 0),
                    last_updated=rel_data.get("last_updated", datetime.now().isoformat()),
                )

        # 导入信号（仅用于统计）
        for sig_data in data.get("signals", []):
            self._signals.append(RelevanceSignal(
                query_hash=sig_data["query_hash"],
                doc_id=sig_data["doc_id"],
                signal_type=sig_data["signal_type"],
                strength=sig_data["strength"],
                timestamp=sig_data.get("timestamp", ""),
            ))

        # 导入全局文档分数
        self._global_doc_scores = data.get("global_doc_scores", {})

    def clear(self):
        """清空学习数据"""
        self._relevance_matrix.clear()
        self._signals.clear()
        self._global_doc_scores.clear()


# 全局学习器实例
_relevance_learner: Optional[RelevanceLearner] = None


def get_relevance_learner() -> RelevanceLearner:
    """获取全局相关性学习器"""
    global _relevance_learner
    if _relevance_learner is None:
        _relevance_learner = RelevanceLearner()
    return _relevance_learner
