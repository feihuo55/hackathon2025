# RAG 模块全面改进方案

## 改进概览

| 优先级 | 改进项 | 文件 | 状态 |
|--------|--------|------|------|
| P0 | 统一相似度计算 | knowledge_search.py, semantic_memory.py | 待实施 |
| P0 | 细化异常处理 | 多个文件 | 待实施 |
| P1 | 自定义中文 Embedding | embeddings.py (新增) | 待实施 |
| P1 | Hybrid Search (BM25) | bm25_search.py (新增) | 待实施 |
| P2 | 记忆 TTL 机制 | episodic_memory.py | 待实施 |
| P2 | 向量索引优化 | chroma_client.py | 待实施 |
| P3 | 检索质量监控 | metrics.py (新增) | 待实施 |

---

## P0-1: 统一相似度计算

### 问题
`knowledge_search.py` 使用 `1 - distance` 可能产生负数
`service_matcher.py` 使用 `1/(1+distance)` 始终在 0-1 之间

### 修改文件: `rag_module/retrieval/knowledge_search.py`

将第 63-65 行:
```python
# 计算相关度分数
distance = results.get("distances", [[]])[0][i] if results.get("distances") else 0
score = 1 - distance  # 转换距离为相似度
```

改为:
```python
# 计算相关度分数
# ChromaDB L2距离可能>1，使用 1/(1+distance) 确保在0-1之间
distance = results.get("distances", [[]])[0][i] if results.get("distances") else 0
score = 1.0 / (1.0 + distance) if distance >= 0 else 0.0
```

### 修改文件: `rag_module/memory/semantic_memory.py`

将第 145 行:
```python
"score": 1 - (results["distances"][0][i] if results.get("distances") else 0),
```

改为:
```python
"score": 1.0 / (1.0 + (results["distances"][0][i] if results.get("distances") else 0)),
```

---

## P0-2: 细化异常处理

### 新增文件: `rag_module/utils/exceptions.py`

```python
"""
RAG 模块自定义异常类
"""


class RAGBaseError(Exception):
    """RAG 模块基础异常"""
    pass


class ChromaDBError(RAGBaseError):
    """ChromaDB 相关错误"""
    pass


class ChromaDBConnectionError(ChromaDBError):
    """ChromaDB 连接错误"""
    pass


class ChromaDBQueryError(ChromaDBError):
    """ChromaDB 查询错误"""
    pass


class IndexingError(RAGBaseError):
    """索引相关错误"""
    pass


class DocumentLoadError(IndexingError):
    """文档加载错误"""
    pass


class EmbeddingError(RAGBaseError):
    """向量化错误"""
    pass


class RetrievalError(RAGBaseError):
    """检索相关错误"""
    pass


class ServiceMatchError(RetrievalError):
    """服务匹配错误"""
    pass


class MemoryError(RAGBaseError):
    """记忆相关错误"""
    pass


class PersistenceError(RAGBaseError):
    """持久化错误"""
    pass
```

### 修改示例: `knowledge_search.py`

```python
from ..utils.exceptions import ChromaDBQueryError, RetrievalError

async def search(self, ...):
    try:
        results = self.chroma.query(...)
    except chromadb.errors.InvalidCollectionException as e:
        raise ChromaDBQueryError(f"集合不存在: {e}")
    except chromadb.errors.ChromaError as e:
        raise ChromaDBQueryError(f"ChromaDB 查询失败: {e}")
    except Exception as e:
        logger.error(f"未知检索错误: {e}")
        raise RetrievalError(f"检索失败: {e}")
```

---

## P1-1: 自定义中文 Embedding 模型

### 新增文件: `rag_module/indexing/chinese_embeddings.py`

```python
"""
中文 Embedding 模型支持
支持多种中文向量模型：bge-zh, m3e, text2vec
"""
from typing import Optional, Union
from abc import ABC, abstractmethod
import numpy as np


class BaseEmbedding(ABC):
    """Embedding 基类"""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量"""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass


class SentenceTransformerEmbedding(BaseEmbedding):
    """基于 sentence-transformers 的 Embedding"""

    # 推荐的中文模型
    CHINESE_MODELS = {
        "bge-small-zh": "BAAI/bge-small-zh-v1.5",      # 512维, 快速
        "bge-base-zh": "BAAI/bge-base-zh-v1.5",        # 768维, 平衡
        "bge-large-zh": "BAAI/bge-large-zh-v1.5",      # 1024维, 最佳
        "m3e-base": "moka-ai/m3e-base",                 # 768维, 中文优化
        "text2vec": "shibing624/text2vec-base-chinese", # 768维
    }

    def __init__(
        self,
        model_name: str = "bge-small-zh",
        device: str = "cpu",
        normalize: bool = True,
    ):
        """
        初始化 Embedding 模型

        Args:
            model_name: 模型名称或路径
            device: 运行设备 (cpu/cuda)
            normalize: 是否归一化向量
        """
        self._model = None
        self._model_name = self.CHINESE_MODELS.get(model_name, model_name)
        self._device = device
        self._normalize = normalize
        self._dimension = None

    def _ensure_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self._model_name,
                    device=self._device
                )
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "请安装 sentence-transformers: pip install sentence-transformers"
                )
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量"""
        model = self._ensure_model()
        embedding = model.encode(
            text,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        model = self._ensure_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
            batch_size=32,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """向量维度"""
        if self._dimension is None:
            self._ensure_model()
        return self._dimension


class BedrockEmbedding(BaseEmbedding):
    """AWS Bedrock Embedding (Titan)"""

    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v1",
        region: str = "us-east-1",
    ):
        self._model_id = model_id
        self._region = region
        self._client = None

    def _ensure_client(self):
        """延迟初始化 Bedrock 客户端"""
        if self._client is None:
            import boto3
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self._region
            )
        return self._client

    def embed_text(self, text: str) -> list[float]:
        """调用 Bedrock Titan 获取向量"""
        import json
        client = self._ensure_client()

        response = client.invoke_model(
            modelId=self._model_id,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
        )

        result = json.loads(response["body"].read())
        return result["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量调用（Titan 不支持批量，逐个处理）"""
        return [self.embed_text(text) for text in texts]

    @property
    def dimension(self) -> int:
        """Titan embed v1 维度为 1536"""
        return 1536


class EmbeddingFactory:
    """Embedding 工厂类"""

    @staticmethod
    def create(
        provider: str = "sentence-transformer",
        model_name: str = "bge-small-zh",
        **kwargs
    ) -> BaseEmbedding:
        """
        创建 Embedding 实例

        Args:
            provider: 提供商 (sentence-transformer, bedrock, openai)
            model_name: 模型名称
            **kwargs: 额外参数
        """
        if provider == "sentence-transformer":
            return SentenceTransformerEmbedding(model_name, **kwargs)
        elif provider == "bedrock":
            return BedrockEmbedding(model_name, **kwargs)
        else:
            raise ValueError(f"不支持的 Embedding 提供商: {provider}")


# 默认实例（延迟初始化）
_default_embedding: Optional[BaseEmbedding] = None


def get_embedding(
    provider: str = None,
    model_name: str = None,
) -> BaseEmbedding:
    """获取 Embedding 实例"""
    global _default_embedding

    if provider or model_name:
        return EmbeddingFactory.create(
            provider=provider or "sentence-transformer",
            model_name=model_name or "bge-small-zh",
        )

    if _default_embedding is None:
        _default_embedding = SentenceTransformerEmbedding("bge-small-zh")

    return _default_embedding
```

### 修改 ChromaDB 使用自定义 Embedding

```python
# chroma_client.py 修改

from .indexing.chinese_embeddings import get_embedding

class ChromaClient:
    def __init__(self, embedding_function=None):
        self._embedding_fn = embedding_function

    def _ensure_initialized(self):
        if self._initialized:
            return True

        # 使用自定义 embedding function
        embedding = get_embedding()

        class CustomEmbeddingFunction:
            def __call__(self, input: list[str]) -> list[list[float]]:
                return embedding.embed_batch(input)

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=CustomEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )
```

---

## P1-2: 真正的 Hybrid Search (BM25)

### 新增文件: `rag_module/retrieval/bm25_search.py`

```python
"""
BM25 稀疏检索实现
支持中文分词和 RRF 融合
"""
import math
from typing import Optional
from collections import Counter
from dataclasses import dataclass


@dataclass
class BM25Result:
    """BM25 检索结果"""
    doc_id: str
    score: float
    content: str
    metadata: dict


class BM25Index:
    """BM25 索引"""

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """
        初始化 BM25 参数

        Args:
            k1: 词频饱和参数 (1.2-2.0)
            b: 文档长度归一化参数 (0-1)
            epsilon: IDF 平滑参数
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        self._documents: list[dict] = []
        self._doc_freqs: dict[str, int] = {}
        self._doc_lens: list[int] = []
        self._avgdl: float = 0
        self._tokenized_docs: list[list[str]] = []
        self._idf: dict[str, float] = {}

        # 延迟加载分词器
        self._tokenizer = None

    def _get_tokenizer(self):
        """获取分词器"""
        if self._tokenizer is None:
            try:
                from .tokenizer import ChineseTokenizer
                self._tokenizer = ChineseTokenizer()
            except ImportError:
                # 简单的空格分词
                class SimpleTokenizer:
                    def tokenize(self, text):
                        return text.lower().split()
                self._tokenizer = SimpleTokenizer()
        return self._tokenizer

    def _tokenize(self, text: str) -> list[str]:
        """分词"""
        tokenizer = self._get_tokenizer()
        return tokenizer.tokenize(text)

    def add_documents(self, documents: list[dict]):
        """
        添加文档到索引

        Args:
            documents: 文档列表，每个文档包含 id, content, metadata
        """
        for doc in documents:
            doc_id = doc.get("id", str(len(self._documents)))
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            tokens = self._tokenize(content)
            self._tokenized_docs.append(tokens)
            self._doc_lens.append(len(tokens))
            self._documents.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            })

            # 更新文档频率
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1

        # 重新计算平均文档长度和 IDF
        self._avgdl = sum(self._doc_lens) / len(self._doc_lens) if self._doc_lens else 0
        self._compute_idf()

    def _compute_idf(self):
        """计算 IDF"""
        n_docs = len(self._documents)
        for token, freq in self._doc_freqs.items():
            # IDF with smoothing
            idf = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1)
            self._idf[token] = max(idf, self.epsilon)

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[BM25Result]:
        """
        BM25 检索

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_tokens in enumerate(self._tokenized_docs):
            score = self._score_document(query_tokens, doc_tokens, i)
            scores.append((i, score))

        # 按分数排序
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
        """计算单个文档的 BM25 分数"""
        score = 0.0
        doc_len = self._doc_lens[doc_idx]
        doc_token_counts = Counter(doc_tokens)

        for token in query_tokens:
            if token not in self._idf:
                continue

            tf = doc_token_counts.get(token, 0)
            idf = self._idf[token]

            # BM25 公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avgdl)

            score += idf * numerator / denominator

        return score

    def clear(self):
        """清空索引"""
        self._documents.clear()
        self._doc_freqs.clear()
        self._doc_lens.clear()
        self._tokenized_docs.clear()
        self._idf.clear()
        self._avgdl = 0


class HybridSearcher:
    """混合检索器 - 融合向量检索和 BM25"""

    def __init__(
        self,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        """
        初始化混合检索器

        Args:
            vector_weight: 向量检索权重
            bm25_weight: BM25 权重
            rrf_k: RRF 常数 (通常 60)
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k
        self.bm25_index = BM25Index()

    def index_documents(self, documents: list[dict]):
        """索引文档到 BM25"""
        self.bm25_index.add_documents(documents)

    async def search(
        self,
        query: str,
        vector_search_fn,
        top_k: int = 10,
        use_rrf: bool = True,
    ) -> list[dict]:
        """
        混合检索

        Args:
            query: 查询文本
            vector_search_fn: 向量检索函数
            top_k: 返回数量
            use_rrf: 是否使用 RRF 融合

        Returns:
            融合后的结果
        """
        # 向量检索
        vector_results = await vector_search_fn(query, top_k * 2)

        # BM25 检索
        bm25_results = self.bm25_index.search(query, top_k * 2)

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
        RRF (Reciprocal Rank Fusion) 融合

        RRF Score = Σ 1/(k + rank)
        """
        scores = {}
        doc_map = {}

        # 向量结果排名
        for rank, result in enumerate(vector_results):
            doc_id = getattr(result, 'doc_id', result.get('doc_id', str(rank)))
            rrf_score = 1.0 / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + self.vector_weight * rrf_score
            doc_map[doc_id] = {
                "doc_id": doc_id,
                "content": getattr(result, 'content', result.get('content', '')),
                "metadata": getattr(result, 'metadata', result.get('metadata', {})),
            }

        # BM25 结果排名
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

        # 按融合分数排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            doc = doc_map[doc_id]
            doc["score"] = score
            results.append(doc)

        return results

    def _weighted_fusion(
        self,
        vector_results: list,
        bm25_results: list[BM25Result],
        top_k: int,
    ) -> list[dict]:
        """加权分数融合"""
        scores = {}
        doc_map = {}

        # 归一化向量分数
        if vector_results:
            max_v_score = max(
                getattr(r, 'score', r.get('score', 0))
                for r in vector_results
            ) or 1
            for result in vector_results:
                doc_id = getattr(result, 'doc_id', result.get('doc_id', ''))
                score = getattr(result, 'score', result.get('score', 0)) / max_v_score
                scores[doc_id] = self.vector_weight * score
                doc_map[doc_id] = {
                    "doc_id": doc_id,
                    "content": getattr(result, 'content', result.get('content', '')),
                    "metadata": getattr(result, 'metadata', result.get('metadata', {})),
                }

        # 归一化 BM25 分数
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

        # 排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            doc = doc_map[doc_id]
            doc["score"] = score
            results.append(doc)

        return results
```

---

## P2-1: 记忆 TTL 过期机制

### 修改文件: `rag_module/memory/episodic_memory.py`

```python
"""
事件记忆 - 支持 TTL 过期
"""
from datetime import datetime, timedelta
from typing import Optional
from collections import deque
from config import MEMORY_CONFIG


class EpisodicMemory:
    """事件记忆系统 - 支持 TTL"""

    def __init__(
        self,
        max_entries: int = None,
        ttl_hours: float = 24.0,  # 默认24小时过期
    ):
        """
        初始化事件记忆

        Args:
            max_entries: 最大记录数
            ttl_hours: 过期时间（小时），None 表示不过期
        """
        self.max_entries = max_entries or MEMORY_CONFIG.get("max_episodic_entries", 100)
        self.ttl_hours = ttl_hours
        self._memories: deque = deque(maxlen=self.max_entries)

    def add(
        self,
        event_type: str,
        content: dict,
        metadata: Optional[dict] = None,
    ):
        """添加事件记录"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "content": content,
            "metadata": metadata or {},
            "expires_at": (
                (datetime.now() + timedelta(hours=self.ttl_hours)).isoformat()
                if self.ttl_hours else None
            ),
        }
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
                expiry_time = datetime.fromisoformat(expires_at)
                if expiry_time > now:
                    valid_memories.append(memory)
            else:
                valid_memories.append(memory)

        self._memories = valid_memories

    def get_recent(self, n: int = 10, include_expired: bool = False) -> list[dict]:
        """获取最近的N条记录"""
        if not include_expired:
            self._cleanup_expired()

        memories = list(self._memories)
        return memories[-n:] if len(memories) >= n else memories

    def get_by_type(self, event_type: str) -> list[dict]:
        """按类型获取记录"""
        self._cleanup_expired()
        return [m for m in self._memories if m["event_type"] == event_type]

    def get_conversation_history(self) -> list[dict]:
        """获取对话历史"""
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
        """搜索记录"""
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

    def set_ttl(self, ttl_hours: float):
        """动态设置 TTL"""
        self.ttl_hours = ttl_hours
        self._cleanup_expired()
```

---

## P2-2: 向量索引优化配置

### 修改文件: `rag_module/chroma_client.py`

```python
def _ensure_initialized(self):
    """Ensure the client is initialized with optimized settings"""
    if self._initialized:
        return True

    try:
        self.persist_directory = CHROMA_CONFIG["persist_directory"]
        self.collection_name = CHROMA_CONFIG["collection_name"]

        # 初始化 Chroma 客户端
        self._client = chromadb.PersistentClient(path=self.persist_directory)

        # HNSW 索引优化配置
        hnsw_config = {
            "hnsw:space": "cosine",           # 使用余弦相似度
            "hnsw:construction_ef": 200,       # 构建时的搜索范围（越大越准确但更慢）
            "hnsw:search_ef": 100,             # 搜索时的范围
            "hnsw:M": 16,                      # 每个节点的连接数
            "hnsw:num_threads": 4,             # 并行线程数
        }

        # 获取或创建集合（带优化配置）
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "Service definitions for RAG retrieval",
                **hnsw_config,
            }
        )

        self._initialized = True
        return True
    except Exception as e:
        print(f"Warning: ChromaDB initialization failed: {e}")
        return False
```

### 新增预热方法

```python
def warmup(self, sample_queries: list[str] = None):
    """
    预热索引，提升首次查询性能

    Args:
        sample_queries: 示例查询列表
    """
    if not self._ensure_initialized():
        return

    # 默认预热查询
    if not sample_queries:
        sample_queries = [
            "基金净值查询",
            "分红处理",
            "持仓查询",
        ]

    for query in sample_queries:
        try:
            self._collection.query(
                query_texts=[query],
                n_results=1,
            )
        except Exception:
            pass
```

---

## P3: 检索质量监控

### 新增文件: `rag_module/utils/metrics.py`

```python
"""
检索质量指标监控
支持 MRR, NDCG, Precision@K, Recall@K
"""
import math
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class RetrievalMetrics:
    """检索指标"""
    mrr: float = 0.0                    # Mean Reciprocal Rank
    ndcg: float = 0.0                   # Normalized Discounted Cumulative Gain
    precision_at_k: dict = field(default_factory=dict)  # Precision@K
    recall_at_k: dict = field(default_factory=dict)     # Recall@K
    hit_rate: float = 0.0               # 命中率
    avg_latency_ms: float = 0.0         # 平均延迟


class RetrievalEvaluator:
    """检索质量评估器"""

    def __init__(self):
        self._query_logs: list[dict] = []
        self._feedback_logs: list[dict] = []

    def log_query(
        self,
        query: str,
        results: list[dict],
        latency_ms: float,
        metadata: Optional[dict] = None,
    ):
        """
        记录查询

        Args:
            query: 查询文本
            results: 检索结果
            latency_ms: 延迟（毫秒）
            metadata: 额外元数据
        """
        self._query_logs.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results": [
                {
                    "doc_id": r.get("doc_id", ""),
                    "score": r.get("score", 0),
                    "rank": i + 1,
                }
                for i, r in enumerate(results)
            ],
            "latency_ms": latency_ms,
            "metadata": metadata or {},
        })

    def log_feedback(
        self,
        query: str,
        relevant_doc_ids: list[str],
        feedback_type: str = "explicit",  # explicit, implicit
    ):
        """
        记录用户反馈（用于计算真实指标）

        Args:
            query: 查询文本
            relevant_doc_ids: 相关文档 ID 列表
            feedback_type: 反馈类型
        """
        self._feedback_logs.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "relevant_doc_ids": relevant_doc_ids,
            "feedback_type": feedback_type,
        })

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
        k_values: list[int] = [1, 3, 5, 10],
    ) -> RetrievalMetrics:
        """
        获取聚合指标

        Args:
            k_values: 计算 Precision@K 和 Recall@K 的 K 值列表
        """
        if not self._query_logs:
            return RetrievalMetrics()

        # 构建查询-相关文档映射
        query_relevance = {}
        for feedback in self._feedback_logs:
            query = feedback["query"]
            query_relevance[query] = set(feedback["relevant_doc_ids"])

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

            relevant_ids = query_relevance.get(query, set())
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
        )

    def get_statistics(self) -> dict:
        """获取统计信息"""
        return {
            "total_queries": len(self._query_logs),
            "total_feedbacks": len(self._feedback_logs),
            "metrics": self.get_aggregated_metrics().__dict__,
        }

    def clear(self):
        """清空日志"""
        self._query_logs.clear()
        self._feedback_logs.clear()


# 全局评估器实例
retrieval_evaluator = RetrievalEvaluator()
```

---

## 使用示例

### 1. 使用自定义 Embedding

```python
from rag_module.indexing.chinese_embeddings import get_embedding

# 使用 BGE 中文模型
embedding = get_embedding(provider="sentence-transformer", model_name="bge-base-zh")
vector = embedding.embed_text("基金净值查询")
```

### 2. 使用混合检索

```python
from rag_module.retrieval.bm25_search import HybridSearcher
from rag_module.retrieval.knowledge_search import knowledge_search

# 初始化混合检索器
hybrid = HybridSearcher(vector_weight=0.6, bm25_weight=0.4)

# 索引文档
hybrid.index_documents(documents)

# 混合检索
results = await hybrid.search(
    query="查询基金净值",
    vector_search_fn=knowledge_search.search,
    top_k=5,
    use_rrf=True,
)
```

### 3. 监控检索质量

```python
from rag_module.utils.metrics import retrieval_evaluator
import time

# 记录查询
start = time.time()
results = await search(query)
latency = (time.time() - start) * 1000

retrieval_evaluator.log_query(
    query=query,
    results=results,
    latency_ms=latency,
)

# 记录用户反馈（用户点击了第一个结果）
retrieval_evaluator.log_feedback(
    query=query,
    relevant_doc_ids=[results[0]["doc_id"]],
)

# 获取聚合指标
metrics = retrieval_evaluator.get_aggregated_metrics()
print(f"MRR: {metrics.mrr:.4f}")
print(f"Precision@3: {metrics.precision_at_k.get(3, 0):.4f}")
```

---

## 配置更新

### `config.py` 新增配置

```python
# Embedding 配置
EMBEDDING_CONFIG = {
    "provider": "sentence-transformer",  # sentence-transformer, bedrock
    "model_name": "bge-small-zh",
    "device": "cpu",  # cpu, cuda
    "normalize": True,
}

# BM25 配置
BM25_CONFIG = {
    "k1": 1.5,
    "b": 0.75,
    "epsilon": 0.25,
}

# 混合检索配置
HYBRID_SEARCH_CONFIG = {
    "vector_weight": 0.6,
    "bm25_weight": 0.4,
    "use_rrf": True,
    "rrf_k": 60,
}

# 记忆 TTL 配置
MEMORY_CONFIG = {
    "max_episodic_entries": 100,
    "episodic_ttl_hours": 24.0,  # 事件记忆 24 小时过期
    "max_summary_length": 500,
}

# ChromaDB 优化配置
CHROMA_CONFIG = {
    "persist_directory": "./data/chroma_db",
    "collection_name": "fund_services",
    "hnsw_space": "cosine",
    "hnsw_construction_ef": 200,
    "hnsw_search_ef": 100,
    "hnsw_m": 16,
}
```

---

## 依赖更新

### `requirements.txt` 新增

```
sentence-transformers>=2.2.0
rank-bm25>=0.2.2  # 可选，用于参考实现
```

---

## 实施顺序建议

1. **Week 1**: P0 改进（相似度计算、异常处理）
2. **Week 2**: P1 改进（Embedding、Hybrid Search）
3. **Week 3**: P2 改进（TTL、索引优化）
4. **Week 4**: P3 改进（监控）+ 测试

---

## 测试清单

- [ ] 相似度计算始终在 0-1 范围
- [ ] 异常被正确捕获和处理
- [ ] 中文 Embedding 正常工作
- [ ] BM25 检索返回合理结果
- [ ] 混合检索性能优于单一检索
- [ ] TTL 过期记录被正确清理
- [ ] 向量索引预热后查询更快
- [ ] 检索指标能正确计算和聚合
