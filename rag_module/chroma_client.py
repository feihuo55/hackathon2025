"""
Chroma向量数据库客户端
用于服务检索和知识存储
"""
import chromadb
from typing import Optional
from config import CHROMA_CONFIG


class ChromaClient:
    """Chroma数据库客户端 - 延迟初始化"""

    _instance: Optional["ChromaClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._client = None
            cls._instance._collection = None
        return cls._instance

    def __init__(self):
        # Delay initialization until first use
        pass

    def _ensure_initialized(self):
        """Ensure the client is initialized"""
        if self._initialized:
            return True

        try:
            self.persist_directory = CHROMA_CONFIG["persist_directory"]
            self.collection_name = CHROMA_CONFIG["collection_name"]

            # 初始化Chroma客户端 (new API)
            self._client = chromadb.PersistentClient(path=self.persist_directory)

            # 获取或创建集合
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Service definitions for RAG retrieval"}
            )

            self._initialized = True
            return True
        except Exception as e:
            print(f"Warning: ChromaDB initialization failed: {e}")
            print("Using fallback in-memory service matching")
            return False

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
    ):
        """
        添加文档到向量库

        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
        """
        if not self._ensure_initialized():
            return  # Skip if not initialized

        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def query(
        self,
        query_text: str,
        n_results: int = 3,
        where: Optional[dict] = None,
    ) -> dict:
        """
        查询相似文档

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            where: 过滤条件

        Returns:
            查询结果
        """
        if not self._ensure_initialized():
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}

        results = self._collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
        )
        return results

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
        self._collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"description": "Service definitions for RAG retrieval"}
        )


# 全局客户端实例 (will be lazy initialized)
chroma_client = ChromaClient()
