"""
BM25 Sparse Retrieval Implementation / BM25 稀疏检索实现
Supports bilingual tokenization (Chinese/English) and RRF fusion
支持中英文分词和 RRF 融合

Features / 功能:
- BM25 algorithm for sparse text retrieval / BM25算法稀疏文本检索
- Bilingual tokenization support / 双语分词支持
- Hybrid search with vector + BM25 / 向量+BM25混合检索
- RRF (Reciprocal Rank Fusion) / RRF排名融合
- Weighted score fusion / 加权分数融合
"""
import math
from typing import Optional, Callable, Any
from collections import Counter
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BM25Result:
    """
    BM25 Search Result / BM25 检索结果

    Attributes:
        doc_id: Document identifier / 文档ID
        score: BM25 relevance score / BM25相关度分数
        content: Document content / 文档内容
        metadata: Additional metadata / 额外元数据
    """
    doc_id: str
    score: float
    content: str
    metadata: dict


class BM25Index:
    """
    BM25 Index for sparse text retrieval
    BM25 索引用于稀疏文本检索

    BM25 (Best Matching 25) is a ranking function used in information retrieval.
    This implementation supports:
    - Bilingual tokenization (Chinese/English)
    - Configurable parameters (k1, b, epsilon)
    - Document addition, removal, and search

    BM25是信息检索中使用的排名函数。此实现支持：
    - 双语分词（中文/英文）
    - 可配置参数（k1, b, epsilon）
    - 文档添加、删除和检索
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """
        Initialize BM25 parameters
        初始化 BM25 参数

        Args:
            k1: Term frequency saturation parameter (1.2-2.0)
                词频饱和参数，控制词频的影响程度
            b: Document length normalization parameter (0-1)
                文档长度归一化参数，控制长度对分数的影响
            epsilon: IDF smoothing parameter
                IDF 平滑参数，防止负值
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        # Internal data structures / 内部数据结构
        self._documents: list[dict] = []
        self._doc_freqs: dict[str, int] = {}  # Term -> document frequency
        self._doc_lens: list[int] = []  # Document lengths
        self._avgdl: float = 0  # Average document length
        self._tokenized_docs: list[list[str]] = []  # Tokenized documents
        self._idf: dict[str, float] = {}  # Inverse document frequency
        self._doc_id_to_idx: dict[str, int] = {}  # Doc ID to index mapping

        # Lazy load tokenizer / 延迟加载分词器
        self._tokenizer = None

    def _get_tokenizer(self):
        """
        Get tokenizer instance (lazy loading)
        获取分词器实例（延迟加载）
        """
        if self._tokenizer is None:
            try:
                from .tokenizer import BilingualTokenizer
                self._tokenizer = BilingualTokenizer()
                logger.info("Using BilingualTokenizer for BM25")
            except ImportError:
                # Fallback to simple tokenizer / 回退到简单分词
                logger.warning("Cannot load BilingualTokenizer, using simple tokenizer")

                class SimpleTokenizer:
                    """Simple fallback tokenizer / 简单回退分词器"""

                    def tokenize(self, text):
                        import re
                        # Split by Chinese chars, English words, and numbers
                        # 按中文字符、英文单词和数字分割
                        tokens = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+', text.lower())
                        return tokens

                    @staticmethod
                    def detect_language(text):
                        return "mixed"

                self._tokenizer = SimpleTokenizer()
        return self._tokenizer

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text using bilingual tokenizer
        使用双语分词器分词
        """
        tokenizer = self._get_tokenizer()
        return tokenizer.tokenize(text)

    def add_documents(self, documents: list[dict]):
        """
        Add documents to the index
        添加文档到索引

        Args:
            documents: List of documents, each with id, content, metadata
                      文档列表，每个文档包含 id, content, metadata
        """
        for doc in documents:
            doc_id = doc.get("id", doc.get("doc_id", str(len(self._documents))))
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Skip existing documents / 跳过已存在的文档
            if doc_id in self._doc_id_to_idx:
                continue

            tokens = self._tokenize(content)
            idx = len(self._documents)

            self._tokenized_docs.append(tokens)
            self._doc_lens.append(len(tokens))
            self._documents.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            })
            self._doc_id_to_idx[doc_id] = idx

            # Update document frequency / 更新文档频率
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1

        # Recalculate average document length and IDF
        # 重新计算平均文档长度和 IDF
        self._avgdl = sum(self._doc_lens) / len(self._doc_lens) if self._doc_lens else 0
        self._compute_idf()

    def _compute_idf(self):
        """
        Compute Inverse Document Frequency
        计算逆文档频率 (IDF)
        """
        n_docs = len(self._documents)
        for token, freq in self._doc_freqs.items():
            # IDF with smoothing (BM25 variant)
            # IDF 平滑处理（BM25 变体）
            idf = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1)
            self._idf[token] = max(idf, self.epsilon)

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[BM25Result]:
        """
        Perform BM25 search
        执行 BM25 检索

        Args:
            query: Query text (Chinese or English) / 查询文本（中文或英文）
            top_k: Number of results to return / 返回结果数量

        Returns:
            List of BM25Result objects sorted by relevance
            按相关度排序的 BM25Result 列表
        """
        if not self._documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = []

        for i, doc_tokens in enumerate(self._tokenized_docs):
            score = self._score_document(query_tokens, doc_tokens, i)
            scores.append((i, score))

        # Sort by score descending / 按分数降序排序
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            if score > 0:
                doc = self._documents[idx]
                results.append(BM25Result(
                    doc_id=doc["id"],
                    score=score,
                    content=doc["content"],
                    metadata=doc["metadata"],
                ))

        return results

    def _score_document(
        self,
        query_tokens: list[str],
        doc_tokens: list[str],
        doc_idx: int,
    ) -> float:
        """
        Calculate BM25 score for a single document
        计算单个文档的 BM25 分数

        BM25 formula:
        score = sum(IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl)))
        """
        score = 0.0
        doc_len = self._doc_lens[doc_idx]
        doc_token_counts = Counter(doc_tokens)

        for token in query_tokens:
            if token not in self._idf:
                continue

            tf = doc_token_counts.get(token, 0)
            if tf == 0:
                continue

            idf = self._idf[token]

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avgdl)

            score += idf * numerator / denominator

        return score

    def get_document(self, doc_id: str) -> Optional[dict]:
        """
        Get document by ID / 通过ID获取文档
        """
        idx = self._doc_id_to_idx.get(doc_id)
        if idx is not None:
            return self._documents[idx]
        return None

    def remove_document(self, doc_id: str):
        """
        Remove document by ID (rebuild index)
        通过ID删除文档（重建索引）

        Note: This rebuilds the entire index to maintain consistency
        注意：这会重建整个索引以保持一致性
        """
        if doc_id in self._doc_id_to_idx:
            docs_to_keep = [d for d in self._documents if d["id"] != doc_id]
            self.clear()
            self.add_documents(docs_to_keep)

    def clear(self):
        """Clear the index / 清空索引"""
        self._documents.clear()
        self._doc_freqs.clear()
        self._doc_lens.clear()
        self._tokenized_docs.clear()
        self._idf.clear()
        self._doc_id_to_idx.clear()
        self._avgdl = 0

    def count(self) -> int:
        """Get document count / 获取文档数量"""
        return len(self._documents)

    def get_statistics(self) -> dict:
        """
        Get index statistics / 获取索引统计信息
        """
        return {
            "total_documents": len(self._documents),
            "total_tokens": len(self._doc_freqs),
            "avg_doc_length": self._avgdl,
            "parameters": {
                "k1": self.k1,
                "b": self.b,
                "epsilon": self.epsilon,
            }
        }


class HybridSearcher:
    """
    Hybrid Searcher - Combines vector search and BM25
    混合检索器 - 融合向量检索和 BM25

    This class provides:
    - Combined vector + sparse retrieval
    - RRF (Reciprocal Rank Fusion) for rank combination
    - Weighted score fusion alternative
    - Configurable weights for each retrieval method

    本类提供：
    - 向量 + 稀疏检索组合
    - RRF（倒数排名融合）用于排名组合
    - 加权分数融合替代方案
    - 可配置的各检索方法权重
    """

    def __init__(
        self,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid searcher
        初始化混合检索器

        Args:
            vector_weight: Weight for vector search results (0-1)
                          向量检索权重
            bm25_weight: Weight for BM25 results (0-1)
                        BM25 权重
            rrf_k: RRF constant (typically 60)
                   RRF 常数，用于平滑排名分数
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k
        self.bm25_index = BM25Index()

    def index_documents(self, documents: list[dict]):
        """
        Index documents for BM25 search
        索引文档到 BM25

        Args:
            documents: List of documents with id, content, metadata
                      文档列表
        """
        self.bm25_index.add_documents(documents)

    async def search(
        self,
        query: str,
        vector_search_fn: Callable,
        top_k: int = 10,
        use_rrf: bool = True,
    ) -> list[dict]:
        """
        Perform hybrid search (async)
        执行混合检索（异步）

        Args:
            query: Query text / 查询文本
            vector_search_fn: Async vector search function / 异步向量检索函数
            top_k: Number of results / 返回数量
            use_rrf: Whether to use RRF fusion / 是否使用 RRF 融合

        Returns:
            Fused search results / 融合后的结果
        """
        # Vector search / 向量检索
        try:
            vector_results = await vector_search_fn(query, top_k * 2)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            vector_results = []

        # BM25 search / BM25 检索
        bm25_results = self.bm25_index.search(query, top_k * 2)

        if not vector_results and not bm25_results:
            return []

        if use_rrf:
            return self._rrf_fusion(vector_results, bm25_results, top_k)
        else:
            return self._weighted_fusion(vector_results, bm25_results, top_k)

    def search_sync(
        self,
        query: str,
        vector_results: list,
        top_k: int = 10,
        use_rrf: bool = True,
    ) -> list[dict]:
        """
        Perform hybrid search (sync, vector results provided)
        同步混合检索（向量结果已提供）

        Args:
            query: Query text / 查询文本
            vector_results: Pre-computed vector search results / 向量检索结果
            top_k: Number of results / 返回数量
            use_rrf: Whether to use RRF fusion / 是否使用 RRF 融合

        Returns:
            Fused search results / 融合后的结果
        """
        bm25_results = self.bm25_index.search(query, top_k * 2)

        if not vector_results and not bm25_results:
            return []

        if use_rrf:
            return self._rrf_fusion(vector_results, bm25_results, top_k)
        else:
            return self._weighted_fusion(vector_results, bm25_results, top_k)

    def _rrf_fusion(
        self,
        vector_results: list,
        bm25_results: list[BM25Result],
        top_k: int,
    ) -> list[dict]:
        """
        RRF (Reciprocal Rank Fusion)
        RRF（倒数排名融合）

        Formula: RRF Score = Σ weight * 1/(k + rank)
        公式：RRF 分数 = Σ 权重 * 1/(k + 排名)
        """
        scores = {}
        doc_map = {}

        # Vector results ranking / 向量结果排名
        for rank, result in enumerate(vector_results):
            doc_id = self._get_doc_id(result)
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + self.vector_weight * rrf_score
            if doc_id not in doc_map:
                doc_map[doc_id] = self._normalize_result(result)

        # BM25 results ranking / BM25 结果排名
        for rank, result in enumerate(bm25_results):
            doc_id = result.doc_id
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + self.bm25_weight * rrf_score
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "doc_id": doc_id,
                    "content": result.content,
                    "metadata": result.metadata,
                }

        # Sort by fused score / 按融合分数排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            doc = doc_map[doc_id]
            doc["score"] = score
            doc["fusion_method"] = "rrf"
            results.append(doc)

        return results

    def _weighted_fusion(
        self,
        vector_results: list,
        bm25_results: list[BM25Result],
        top_k: int,
    ) -> list[dict]:
        """
        Weighted score fusion (normalized)
        加权分数融合（归一化后）
        """
        scores = {}
        doc_map = {}

        # Normalize vector scores / 归一化向量分数
        if vector_results:
            max_v_score = max(
                self._get_score(r) for r in vector_results
            ) or 1
            for result in vector_results:
                doc_id = self._get_doc_id(result)
                score = self._get_score(result) / max_v_score
                scores[doc_id] = self.vector_weight * score
                if doc_id not in doc_map:
                    doc_map[doc_id] = self._normalize_result(result)

        # Normalize BM25 scores / 归一化 BM25 分数
        if bm25_results:
            max_b_score = max(r.score for r in bm25_results) or 1
            for result in bm25_results:
                doc_id = result.doc_id
                score = result.score / max_b_score
                scores[doc_id] = scores.get(doc_id, 0) + self.bm25_weight * score
                if doc_id not in doc_map:
                    doc_map[doc_id] = {
                        "doc_id": doc_id,
                        "content": result.content,
                        "metadata": result.metadata,
                    }

        # Sort / 排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            doc = doc_map[doc_id]
            doc["score"] = score
            doc["fusion_method"] = "weighted"
            results.append(doc)

        return results

    def _get_doc_id(self, result: Any) -> str:
        """Extract doc_id from result / 从结果中提取 doc_id"""
        if hasattr(result, 'doc_id'):
            return result.doc_id
        elif isinstance(result, dict):
            return result.get('doc_id', result.get('id', ''))
        return str(result)

    def _get_score(self, result: Any) -> float:
        """Extract score from result / 从结果中提取分数"""
        if hasattr(result, 'score'):
            return result.score
        elif isinstance(result, dict):
            return result.get('score', 0)
        return 0

    def _normalize_result(self, result: Any) -> dict:
        """Normalize result format / 标准化结果格式"""
        if isinstance(result, dict):
            return {
                "doc_id": result.get('doc_id', result.get('id', '')),
                "content": result.get('content', result.get('document', '')),
                "metadata": result.get('metadata', {}),
            }
        return {
            "doc_id": getattr(result, 'doc_id', ''),
            "content": getattr(result, 'content', ''),
            "metadata": getattr(result, 'metadata', {}),
        }

    def clear(self):
        """Clear BM25 index / 清空 BM25 索引"""
        self.bm25_index.clear()

    def get_statistics(self) -> dict:
        """Get statistics / 获取统计信息"""
        return {
            "bm25": self.bm25_index.get_statistics(),
            "weights": {
                "vector": self.vector_weight,
                "bm25": self.bm25_weight,
            },
            "rrf_k": self.rrf_k,
        }


# Global hybrid searcher instance / 全局混合检索器实例
_hybrid_searcher: Optional[HybridSearcher] = None


def get_hybrid_searcher(
    vector_weight: float = None,
    bm25_weight: float = None,
) -> HybridSearcher:
    """
    Get hybrid searcher instance (singleton pattern)
    获取混合检索器实例（单例模式）

    Args:
        vector_weight: Optional custom vector weight / 可选自定义向量权重
        bm25_weight: Optional custom BM25 weight / 可选自定义BM25权重

    Returns:
        HybridSearcher instance / HybridSearcher 实例
    """
    global _hybrid_searcher

    if vector_weight is not None or bm25_weight is not None:
        return HybridSearcher(
            vector_weight=vector_weight or 0.5,
            bm25_weight=bm25_weight or 0.5,
        )

    if _hybrid_searcher is None:
        # Try to load from config / 尝试从配置读取
        try:
            from config import HYBRID_SEARCH_CONFIG
            _hybrid_searcher = HybridSearcher(
                vector_weight=HYBRID_SEARCH_CONFIG.get("vector_weight", 0.5),
                bm25_weight=HYBRID_SEARCH_CONFIG.get("bm25_weight", 0.5),
                rrf_k=HYBRID_SEARCH_CONFIG.get("rrf_k", 60),
            )
        except (ImportError, KeyError):
            _hybrid_searcher = HybridSearcher()

    return _hybrid_searcher
