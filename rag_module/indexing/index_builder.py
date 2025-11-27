"""
索引构建器
构建和管理RAG索引
"""
from typing import Optional
from .document_loader import Document, DocumentLoader
from ..chroma_client import chroma_client


class IndexBuilder:
    """索引构建器"""

    def __init__(self):
        self.chroma = chroma_client
        self.document_loader = DocumentLoader()
        self._indexed_ids: set = set()

    def build_from_documents(
        self,
        documents: list[Document],
        batch_size: int = 100,
    ) -> int:
        """
        从文档列表构建索引

        Args:
            documents: 文档列表
            batch_size: 批量处理大小

        Returns:
            成功索引的文档数量
        """
        if not documents:
            return 0

        indexed_count = 0

        # 分批处理
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                self._index_batch(batch)
                indexed_count += len(batch)
            except Exception as e:
                print(f"Warning: 索引批次失败: {e}")

        return indexed_count

    def _index_batch(self, documents: list[Document]):
        """索引一批文档"""
        doc_contents = []
        metadatas = []
        ids = []

        for doc in documents:
            # 跳过已索引的文档
            if doc.doc_id in self._indexed_ids:
                continue

            doc_contents.append(doc.content)
            metadatas.append({
                **doc.metadata,
                "doc_type": doc.doc_type,
            })
            ids.append(doc.doc_id)
            self._indexed_ids.add(doc.doc_id)

        if doc_contents:
            self.chroma.add_documents(
                documents=doc_contents,
                metadatas=metadatas,
                ids=ids,
            )

    def build_from_services(self, services: list[dict]) -> int:
        """
        从服务定义构建索引

        Args:
            services: 服务定义列表

        Returns:
            成功索引的数量
        """
        documents = self.document_loader.load_services(services)
        return self.build_from_documents(documents)

    def build_from_directory(
        self,
        dir_path: str,
        pattern: str = "*",
        recursive: bool = True,
    ) -> int:
        """
        从目录构建索引

        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归

        Returns:
            成功索引的数量
        """
        try:
            documents = self.document_loader.load_directory(
                dir_path, pattern, recursive
            )
            return self.build_from_documents(documents)
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            return 0

    def add_document(self, doc: Document) -> bool:
        """
        添加单个文档到索引

        Args:
            doc: 文档对象

        Returns:
            是否成功
        """
        try:
            if doc.doc_id in self._indexed_ids:
                # 更新已存在的文档
                self.chroma.update_document(
                    doc_id=doc.doc_id,
                    document=doc.content,
                    metadata={**doc.metadata, "doc_type": doc.doc_type},
                )
            else:
                self.chroma.add_documents(
                    documents=[doc.content],
                    metadatas=[{**doc.metadata, "doc_type": doc.doc_type}],
                    ids=[doc.doc_id],
                )
                self._indexed_ids.add(doc.doc_id)
            return True
        except Exception as e:
            print(f"Warning: 添加文档失败: {e}")
            return False

    def remove_document(self, doc_id: str) -> bool:
        """
        从索引移除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否成功
        """
        try:
            self.chroma.delete_document(doc_id)
            self._indexed_ids.discard(doc_id)
            return True
        except Exception as e:
            print(f"Warning: 移除文档失败: {e}")
            return False

    def clear_index(self):
        """清空索引"""
        try:
            self.chroma.clear()
            self._indexed_ids.clear()
        except Exception as e:
            print(f"Warning: 清空索引失败: {e}")

    def get_index_stats(self) -> dict:
        """获取索引统计信息"""
        return {
            "total_documents": self.chroma.count(),
            "indexed_ids": len(self._indexed_ids),
        }

    def rebuild_index(self, services: list[dict]) -> int:
        """
        重建索引

        Args:
            services: 服务定义列表

        Returns:
            成功索引的数量
        """
        self.clear_index()
        return self.build_from_services(services)


# 全局索引构建器实例
index_builder = IndexBuilder()
