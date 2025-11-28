"""
Chroma向量数据库客户端 V2
优化版本 - 支持自定义 Embedding 和 HNSW 索引优化

使用方法：将此文件内容替换 chroma_client.py
"""
import chromadb
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 延迟导入配置
_config = None


def _get_config():
    """延迟加载配置"""
    global _config
    if _config is None:
        try:
            from config import CHROMA_CONFIG
            _config = CHROMA_CONFIG
        except ImportError:
            _config = {
                "persist_directory": "./data/chroma_db",
                "collection_name": "fund_services",
            }
    return _config


class ChromaClient:
    """Chroma数据库客户端 - 优化版本"""

    _instance: Optional["ChromaClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._client = None
            cls._instance._collection = None
            cls._instance._embedding_fn = None
        return cls._instance

    def __init__(self):
        # Delay initialization until first use
        pass

    def _ensure_initialized(self):
        """Ensure the client is initialized with optimized settings"""
        if self._initialized:
            return True

        try:
            config = _get_config()
            self.persist_directory = config.get("persist_directory", "./data/chroma_db")
            self.collection_name = config.get("collection_name", "fund_services")

            # 初始化 Chroma 客户端
            self._client = chromadb.PersistentClient(path=self.persist_directory)

            # HNSW 索引优化配置
            hnsw_metadata = {
                "description": "Service definitions for RAG retrieval",
                "hnsw:space": config.get("hnsw_space", "cosine"),  # 使用余弦相似度
                "hnsw:construction_ef": config.get("hnsw_construction_ef", 200),
                "hnsw:search_ef": config.get("hnsw_search_ef", 100),
                "hnsw:M": config.get("hnsw_m", 16),
            }

            # 尝试使用自定义 embedding function
            embedding_fn = self._get_embedding_function()

            # 获取或创建集合（带优化配置）
            if embedding_fn:
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_fn,
                    metadata=hnsw_metadata,
                )
            else:
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata=hnsw_metadata,
                )

            self._initialized = True
            logger.info(f"ChromaDB 初始化成功: {self.collection_name}")
            return True
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            print(f"Warning: ChromaDB initialization failed: {e}")
            print("Using fallback in-memory service matching")
            return False

    def _get_embedding_function(self):
        """获取自定义 embedding function"""
        try:
            # from .indexing.chinese_embeddings import get_chroma_embedding_function
            return None  # Disabled: get_chroma_embedding_function()
        except ImportError:
            logger.info("使用 ChromaDB 默认 embedding")
            return None

    @property
    def client(self):
        self._ensure_initialized()
        return self._client

    @property
    def collection(self):
        self._ensure_initialized()
        return self._collection

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
        embeddings: Optional[list[list[float]]] = None,
    ):
        """
        添加文档到向量库

        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
            embeddings: 预计算的向量（可选）
        """
        if not self._ensure_initialized():
            return

        try:
            if embeddings:
                self._collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings,
                )
            else:
                self._collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 3,
        where: Optional[dict] = None,
        query_embedding: Optional[list[float]] = None,
    ) -> dict:
        """
        查询相似文档

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
            query_embedding: 预计算的查询向量（可选）

        Returns:
            查询结果
        """
        if not self._ensure_initialized():
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        try:
            if query_embedding:
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where,
                )
            else:
                results = self._collection.query(
                    query_texts=[query_text],
                    n_results=n_results,
                    where=where,
                )
            return results
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def update_document(
        self,
        doc_id: str,
        document: str,
        metadata: dict,
    ):
        """更新文档"""
        if not self._ensure_initialized():
            return

        self._collection.update(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
        )

    def delete_document(self, doc_id: str):
        """删除文档"""
        if not self._ensure_initialized():
            return

        self._collection.delete(ids=[doc_id])

    def get_all_documents(self) -> dict:
        """获取所有文档"""
        if not self._ensure_initialized():
            return {"ids": [], "documents": [], "metadatas": []}

        return self._collection.get()

    def count(self) -> int:
        """获取文档数量"""
        if not self._ensure_initialized():
            return 0

        return self._collection.count()

    def clear(self):
        """清空集合"""
        if not self._ensure_initialized():
            return

        self._client.delete_collection(self.collection_name)

        # 重新创建带优化配置的集合
        config = _get_config()
        hnsw_metadata = {
            "description": "Service definitions for RAG retrieval",
            "hnsw:space": config.get("hnsw_space", "cosine"),
            "hnsw:construction_ef": config.get("hnsw_construction_ef", 200),
            "hnsw:search_ef": config.get("hnsw_search_ef", 100),
            "hnsw:M": config.get("hnsw_m", 16),
        }

        embedding_fn = self._get_embedding_function()
        if embedding_fn:
            self._collection = self._client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
                metadata=hnsw_metadata,
            )
        else:
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata=hnsw_metadata,
            )

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
                "基金列表",
                "风险评估",
            ]

        logger.info("开始预热索引...")
        for query in sample_queries:
            try:
                self._collection.query(
                    query_texts=[query],
                    n_results=1,
                )
            except Exception:
                pass
        logger.info("索引预热完成")

    def get_statistics(self) -> dict:
        """获取索引统计信息"""
        if not self._ensure_initialized():
            return {"initialized": False}

        return {
            "initialized": True,
            "collection_name": self.collection_name,
            "document_count": self.count(),
            "persist_directory": self.persist_directory,
        }


# 全局客户端实例 (will be lazy initialized)
chroma_client = ChromaClient()
