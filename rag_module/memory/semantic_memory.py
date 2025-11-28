"""
语义记忆
存储概念、事实和知识的长期记忆
"""
from datetime import datetime
from typing import Optional

# 延迟导入chromadb
chromadb = None

def _get_chromadb():
    global chromadb
    if chromadb is None:
        try:
            import chromadb as _chromadb
            chromadb = _chromadb
        except ImportError:
            pass
    return chromadb


class SemanticMemory:
    """语义记忆系统 - 存储知识和概念"""

    def __init__(self, collection_name: str = "semantic_memory"):
        """
        初始化语义记忆

        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self._client = None  # chromadb.PersistentClient
        self._collection = None
        self._initialized = False
        self._fallback_store: dict[str, dict] = {}  # 备用内存存储

    def _ensure_initialized(self) -> bool:
        """确保初始化"""
        if self._initialized:
            return True

        _chromadb = _get_chromadb()
        if _chromadb is None:
            return False

        try:
            from config import CHROMA_CONFIG
            persist_dir = CHROMA_CONFIG.get("persist_directory", "./data/chroma_db")
            self._client = _chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Semantic memory for knowledge storage"}
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"Warning: 语义记忆初始化失败: {e}")
            return False

    def store(
        self,
        knowledge_id: str,
        content: str,
        category: str = "general",
        metadata: Optional[dict] = None,
    ):
        """
        存储知识/概念

        Args:
            knowledge_id: 知识唯一标识
            content: 知识内容
            category: 知识类别 (service, concept, fact, rule)
            metadata: 额外元数据
        """
        entry_metadata = {
            "category": category,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **(metadata or {}),
        }

        if self._ensure_initialized():
            try:
                # 检查是否已存在
                existing = self._collection.get(ids=[knowledge_id])
                if existing and existing.get("ids"):
                    # 更新
                    self._collection.update(
                        ids=[knowledge_id],
                        documents=[content],
                        metadatas=[entry_metadata],
                    )
                else:
                    # 新增
                    self._collection.add(
                        ids=[knowledge_id],
                        documents=[content],
                        metadatas=[entry_metadata],
                    )
                return
            except Exception as e:
                print(f"Warning: 向量存储失败，使用备用存储: {e}")

        # 备用内存存储
        self._fallback_store[knowledge_id] = {
            "content": content,
            "metadata": entry_metadata,
        }

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        检索相关知识

        Args:
            query: 查询文本
            category: 类别过滤
            top_k: 返回数量

        Returns:
            相关知识列表
        """
        if self._ensure_initialized():
            try:
                where = {"category": category} if category else None
                results = self._collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=where,
                )

                knowledge_list = []
                if results and results.get("ids") and results["ids"][0]:
                    for i, kid in enumerate(results["ids"][0]):
                        knowledge_list.append({
                            "knowledge_id": kid,
                            "content": results["documents"][0][i] if results.get("documents") else "",
                            "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                            "score": 1.0 / (1.0 + (results["distances"][0][i] if results.get("distances") else 0)),
                        })
                return knowledge_list
            except Exception as e:
                print(f"Warning: 向量检索失败: {e}")

        # 使用备用存储的关键词匹配
        return self._fallback_search(query, category, top_k)

    def _fallback_search(
        self,
        query: str,
        category: Optional[str],
        top_k: int,
    ) -> list[dict]:
        """备用关键词搜索"""
        results = []
        query_lower = query.lower()

        for kid, data in self._fallback_store.items():
            if category and data["metadata"].get("category") != category:
                continue

            content = data["content"].lower()
            # 简单的关键词匹配计分
            score = sum(1 for word in query_lower.split() if word in content)

            if score > 0:
                results.append({
                    "knowledge_id": kid,
                    "content": data["content"],
                    "metadata": data["metadata"],
                    "score": min(score / len(query_lower.split()), 1.0),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_by_id(self, knowledge_id: str) -> Optional[dict]:
        """
        通过ID获取知识

        Args:
            knowledge_id: 知识ID

        Returns:
            知识内容
        """
        if self._ensure_initialized():
            try:
                result = self._collection.get(ids=[knowledge_id])
                if result and result.get("ids"):
                    return {
                        "knowledge_id": knowledge_id,
                        "content": result["documents"][0] if result.get("documents") else "",
                        "metadata": result["metadatas"][0] if result.get("metadatas") else {},
                    }
            except Exception:
                pass

        # 备用存储
        if knowledge_id in self._fallback_store:
            data = self._fallback_store[knowledge_id]
            return {
                "knowledge_id": knowledge_id,
                "content": data["content"],
                "metadata": data["metadata"],
            }

        return None

    def get_by_category(self, category: str) -> list[dict]:
        """
        按类别获取知识

        Args:
            category: 知识类别

        Returns:
            知识列表
        """
        if self._ensure_initialized():
            try:
                result = self._collection.get(
                    where={"category": category}
                )
                knowledge_list = []
                if result and result.get("ids"):
                    for i, kid in enumerate(result["ids"]):
                        knowledge_list.append({
                            "knowledge_id": kid,
                            "content": result["documents"][i] if result.get("documents") else "",
                            "metadata": result["metadatas"][i] if result.get("metadatas") else {},
                        })
                return knowledge_list
            except Exception:
                pass

        # 备用存储
        return [
            {
                "knowledge_id": kid,
                "content": data["content"],
                "metadata": data["metadata"],
            }
            for kid, data in self._fallback_store.items()
            if data["metadata"].get("category") == category
        ]

    def delete(self, knowledge_id: str):
        """删除知识"""
        if self._ensure_initialized():
            try:
                self._collection.delete(ids=[knowledge_id])
            except Exception:
                pass

        self._fallback_store.pop(knowledge_id, None)

    def update(
        self,
        knowledge_id: str,
        content: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """
        更新知识

        Args:
            knowledge_id: 知识ID
            content: 新内容
            metadata: 新元数据
        """
        existing = self.get_by_id(knowledge_id)
        if not existing:
            return

        new_content = content if content is not None else existing["content"]
        new_metadata = {**existing["metadata"], **(metadata or {})}
        new_metadata["updated_at"] = datetime.now().isoformat()

        self.store(
            knowledge_id=knowledge_id,
            content=new_content,
            category=new_metadata.get("category", "general"),
            metadata=new_metadata,
        )

    def count(self) -> int:
        """获取知识数量"""
        if self._ensure_initialized():
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._fallback_store)

    def clear(self):
        """清空语义记忆"""
        if self._ensure_initialized():
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Semantic memory for knowledge storage"}
                )
            except Exception:
                pass
        self._fallback_store.clear()
