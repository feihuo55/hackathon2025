"""
检索质量指标监控
支持 MRR, NDCG, Precision@K, Recall@K
"""
import math
import time
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """检索指标"""
    mrr: float = 0.0                    # Mean Reciprocal Rank
    ndcg: float = 0.0                   # Normalized Discounted Cumulative Gain
    precision_at_k: dict = field(default_factory=dict)  # Precision@K
    recall_at_k: dict = field(default_factory=dict)     # Recall@K
    hit_rate: float = 0.0               # 命中率
    avg_latency_ms: float = 0.0         # 平均延迟
    total_queries: int = 0              # 总查询数
    evaluated_queries: int = 0          # 有评估的查询数

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "mrr": self.mrr,
            "ndcg": self.ndcg,
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "hit_rate": self.hit_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "total_queries": self.total_queries,
            "evaluated_queries": self.evaluated_queries,
        }


class RetrievalEvaluator:
    """检索质量评估器"""

    def __init__(self, max_logs: int = 10000):
        """
        初始化评估器

        Args:
            max_logs: 最大日志数量
        """
        self._max_logs = max_logs
        self._query_logs: list[dict] = []
        self._feedback_logs: list[dict] = []
        self._query_id_counter = 0

    def log_query(
        self,
        query: str,
        results: list[Any],
        latency_ms: float,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        记录查询

        Args:
            query: 查询文本
            results: 检索结果
            latency_ms: 延迟（毫秒）
            metadata: 额外元数据

        Returns:
            查询 ID
        """
        self._query_id_counter += 1
        query_id = f"q_{self._query_id_counter}"

        log_entry = {
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results": [
                {
                    "doc_id": self._get_doc_id(r),
                    "score": self._get_score(r),
                    "rank": i + 1,
                }
                for i, r in enumerate(results)
            ],
            "result_count": len(results),
            "latency_ms": latency_ms,
            "metadata": metadata or {},
        }

        self._query_logs.append(log_entry)

        # 限制日志数量
        if len(self._query_logs) > self._max_logs:
            self._query_logs = self._query_logs[-self._max_logs:]

        return query_id

    def log_feedback(
        self,
        query: str,
        relevant_doc_ids: list[str],
        feedback_type: str = "explicit",
        query_id: Optional[str] = None,
    ):
        """
        记录用户反馈（用于计算真实指标）

        Args:
            query: 查询文本
            relevant_doc_ids: 相关文档 ID 列表
            feedback_type: 反馈类型 (explicit, implicit, click)
            query_id: 查询 ID（可选）
        """
        self._feedback_logs.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "query_id": query_id,
            "relevant_doc_ids": relevant_doc_ids,
            "feedback_type": feedback_type,
        })

        # 限制日志数量
        if len(self._feedback_logs) > self._max_logs:
            self._feedback_logs = self._feedback_logs[-self._max_logs:]

    def log_click(
        self,
        query: str,
        clicked_doc_id: str,
        rank: int,
        query_id: Optional[str] = None,
    ):
        """
        记录点击（隐式反馈）

        Args:
            query: 查询文本
            clicked_doc_id: 点击的文档 ID
            rank: 点击位置排名
            query_id: 查询 ID
        """
        self.log_feedback(
            query=query,
            relevant_doc_ids=[clicked_doc_id],
            feedback_type="click",
            query_id=query_id,
        )

    def calculate_mrr(self, results: list[dict], relevant_ids: set[str]) -> float:
        """
        计算 Mean Reciprocal Rank

        MRR = 1/rank of first relevant result
        """
        for i, result in enumerate(results):
            if result.get("doc_id") in relevant_ids:
                return 1.0 / (i + 1)
        return 0.0

    def calculate_ndcg(
        self,
        results: list[dict],
        relevance_scores: dict[str, float],
        k: int = 10,
    ) -> float:
        """
        计算 NDCG@K

        Args:
            results: 检索结果
            relevance_scores: 文档相关性分数 {doc_id: score}
            k: 截断位置
        """
        if not relevance_scores:
            return 0.0

        # DCG
        dcg = 0.0
        for i, result in enumerate(results[:k]):
            doc_id = result.get("doc_id", "")
            rel = relevance_scores.get(doc_id, 0)
            dcg += rel / math.log2(i + 2)  # log2(rank + 1)

        # IDCG (理想排序)
        ideal_rels = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_rels))

        return dcg / idcg if idcg > 0 else 0.0

    def calculate_precision_at_k(
        self,
        results: list[dict],
        relevant_ids: set[str],
        k: int,
    ) -> float:
        """计算 Precision@K"""
        if k <= 0:
            return 0.0

        hits = sum(
            1 for r in results[:k]
            if r.get("doc_id") in relevant_ids
        )
        return hits / k

    def calculate_recall_at_k(
        self,
        results: list[dict],
        relevant_ids: set[str],
        k: int,
    ) -> float:
        """计算 Recall@K"""
        if not relevant_ids:
            return 0.0

        hits = sum(
            1 for r in results[:k]
            if r.get("doc_id") in relevant_ids
        )
        return hits / len(relevant_ids)

    def get_aggregated_metrics(
        self,
        k_values: list[int] = None,
    ) -> RetrievalMetrics:
        """
        获取聚合指标

        Args:
            k_values: 计算 Precision@K 和 Recall@K 的 K 值列表
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]

        if not self._query_logs:
            return RetrievalMetrics()

        # 构建查询-相关文档映射
        query_relevance = {}
        for feedback in self._feedback_logs:
            query = feedback["query"]
            if query not in query_relevance:
                query_relevance[query] = set()
            query_relevance[query].update(feedback["relevant_doc_ids"])

        # 计算各项指标
        mrr_scores = []
        precision_scores = defaultdict(list)
        recall_scores = defaultdict(list)
        latencies = []
        hits = 0

        for log in self._query_logs:
            query = log["query"]
            results = log["results"]
            latencies.append(log["latency_ms"])

            relevant_ids = query_relevance.get(query)
            if not relevant_ids:
                continue

            # MRR
            mrr = self.calculate_mrr(results, relevant_ids)
            mrr_scores.append(mrr)

            if mrr > 0:
                hits += 1

            # Precision@K 和 Recall@K
            for k in k_values:
                p_at_k = self.calculate_precision_at_k(results, relevant_ids, k)
                r_at_k = self.calculate_recall_at_k(results, relevant_ids, k)
                precision_scores[k].append(p_at_k)
                recall_scores[k].append(r_at_k)

        # 聚合
        n_queries = len(self._query_logs)
        n_evaluated = len(mrr_scores)

        return RetrievalMetrics(
            mrr=sum(mrr_scores) / n_evaluated if n_evaluated else 0,
            hit_rate=hits / n_evaluated if n_evaluated else 0,
            precision_at_k={
                k: sum(scores) / len(scores) if scores else 0
                for k, scores in precision_scores.items()
            },
            recall_at_k={
                k: sum(scores) / len(scores) if scores else 0
                for k, scores in recall_scores.items()
            },
            avg_latency_ms=sum(latencies) / n_queries if n_queries else 0,
            total_queries=n_queries,
            evaluated_queries=n_evaluated,
        )

    def get_statistics(self) -> dict:
        """获取统计信息"""
        metrics = self.get_aggregated_metrics()
        return {
            "total_queries": len(self._query_logs),
            "total_feedbacks": len(self._feedback_logs),
            "metrics": metrics.to_dict(),
        }

    def get_recent_queries(self, n: int = 10) -> list[dict]:
        """获取最近的查询"""
        return self._query_logs[-n:]

    def get_slow_queries(self, threshold_ms: float = 1000, n: int = 10) -> list[dict]:
        """获取慢查询"""
        slow = [q for q in self._query_logs if q["latency_ms"] > threshold_ms]
        slow.sort(key=lambda x: x["latency_ms"], reverse=True)
        return slow[:n]

    def get_failed_queries(self, n: int = 10) -> list[dict]:
        """获取无结果的查询"""
        failed = [q for q in self._query_logs if q["result_count"] == 0]
        return failed[-n:]

    def clear(self):
        """清空日志"""
        self._query_logs.clear()
        self._feedback_logs.clear()
        self._query_id_counter = 0

    def export(self) -> dict:
        """导出数据"""
        return {
            "query_logs": self._query_logs,
            "feedback_logs": self._feedback_logs,
            "statistics": self.get_statistics(),
        }

    def _get_doc_id(self, result: Any) -> str:
        """从结果中提取 doc_id"""
        if hasattr(result, 'doc_id'):
            return result.doc_id
        elif isinstance(result, dict):
            return result.get('doc_id', result.get('id', ''))
        return str(result)

    def _get_score(self, result: Any) -> float:
        """从结果中提取分数"""
        if hasattr(result, 'score'):
            return result.score
        elif isinstance(result, dict):
            return result.get('score', 0)
        return 0


class QueryTimer:
    """查询计时器上下文管理器"""

    def __init__(self, evaluator: RetrievalEvaluator, query: str, metadata: dict = None):
        """
        初始化计时器

        Args:
            evaluator: 评估器实例
            query: 查询文本
            metadata: 额外元数据
        """
        self.evaluator = evaluator
        self.query = query
        self.metadata = metadata
        self.start_time = None
        self.results = None
        self.query_id = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.results is not None:
            latency_ms = (time.time() - self.start_time) * 1000
            self.query_id = self.evaluator.log_query(
                query=self.query,
                results=self.results,
                latency_ms=latency_ms,
                metadata=self.metadata,
            )
        return False

    def set_results(self, results: list):
        """设置查询结果"""
        self.results = results


# 全局评估器实例
_retrieval_evaluator: Optional[RetrievalEvaluator] = None


def get_retrieval_evaluator() -> RetrievalEvaluator:
    """获取全局评估器实例"""
    global _retrieval_evaluator
    if _retrieval_evaluator is None:
        _retrieval_evaluator = RetrievalEvaluator()
    return _retrieval_evaluator


# 便捷函数
def log_query(query: str, results: list, latency_ms: float, metadata: dict = None) -> str:
    """记录查询（便捷函数）"""
    return get_retrieval_evaluator().log_query(query, results, latency_ms, metadata)


def log_feedback(query: str, relevant_doc_ids: list[str], feedback_type: str = "explicit"):
    """记录反馈（便捷函数）"""
    get_retrieval_evaluator().log_feedback(query, relevant_doc_ids, feedback_type)


def get_metrics() -> RetrievalMetrics:
    """获取指标（便捷函数）"""
    return get_retrieval_evaluator().get_aggregated_metrics()
