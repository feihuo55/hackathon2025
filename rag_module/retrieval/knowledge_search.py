"""
知识检索服务
基于RAG的知识库检索功能
"""
from typing import Optional
from dataclasses import dataclass
from ..chroma_client import chroma_client
from ..indexing.embeddings import text_preprocessor


@dataclass
class SearchResult:
    """检索结果"""
    content: str
    metadata: dict
    score: float
    doc_id: str


class KnowledgeSearch:
    """知识检索服务"""

    def __init__(self):
        self.chroma = chroma_client

    async def search(
        self,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """
        检索知识库

        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_type: 文档类型过滤
            min_score: 最小相关度分数

        Returns:
            检索结果列表
        """
        # 预处理查询
        processed_query = text_preprocessor.preprocess(query)

        # 构建过滤条件
        where = None
        if doc_type:
            where = {"doc_type": doc_type}

        try:
            results = self.chroma.query(
                query_text=processed_query,
                n_results=top_k,
                where=where,
            )

            search_results = []
            if results and results.get("ids") and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # 计算相关度分数
                    distance = results.get("distances", [[]])[0][i] if results.get("distances") else 0
                    score = 1 - distance  # 转换距离为相似度

                    if score >= min_score:
                        search_results.append(SearchResult(
                            content=results["documents"][0][i] if results.get("documents") else "",
                            metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                            score=score,
                            doc_id=doc_id,
                        ))

            return search_results

        except Exception as e:
            print(f"Warning: 知识检索失败: {e}")
            return []

    async def search_services(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """
        检索服务定义

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            服务检索结果
        """
        return await self.search(
            query=query,
            top_k=top_k,
            doc_type="service",
        )

    async def search_with_context(
        self,
        query: str,
        context: str = "",
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        带上下文的检索

        Args:
            query: 查询文本
            context: 上下文信息
            top_k: 返回数量

        Returns:
            检索结果
        """
        # 组合查询和上下文
        combined_query = f"{query} {context}".strip()
        return await self.search(combined_query, top_k)

    async def find_similar(
        self,
        doc_id: str,
        top_k: int = 5,
        exclude_self: bool = True,
    ) -> list[SearchResult]:
        """
        查找相似文档

        Args:
            doc_id: 文档ID
            top_k: 返回数量
            exclude_self: 是否排除自身

        Returns:
            相似文档列表
        """
        try:
            # 获取原文档内容
            all_docs = self.chroma.get_all_documents()
            doc_content = None

            if all_docs and all_docs.get("ids"):
                for i, id_ in enumerate(all_docs["ids"]):
                    if id_ == doc_id:
                        doc_content = all_docs["documents"][i]
                        break

            if not doc_content:
                return []

            # 使用文档内容作为查询
            results = await self.search(doc_content, top_k + (1 if exclude_self else 0))

            if exclude_self:
                results = [r for r in results if r.doc_id != doc_id]

            return results[:top_k]

        except Exception as e:
            print(f"Warning: 查找相似文档失败: {e}")
            return []

    async def hybrid_search(
        self,
        query: str,
        keywords: list[str] = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        混合检索（向量 + 关键词）

        Args:
            query: 查询文本
            keywords: 关键词列表
            top_k: 返回数量

        Returns:
            检索结果
        """
        # 向量检索
        vector_results = await self.search(query, top_k * 2)

        if not keywords:
            return vector_results[:top_k]

        # 关键词加权
        for result in vector_results:
            content_lower = result.content.lower()
            keyword_boost = 0

            for keyword in keywords:
                if keyword.lower() in content_lower:
                    keyword_boost += 0.1

            result.score = min(result.score + keyword_boost, 1.0)

        # 重新排序
        vector_results.sort(key=lambda x: x.score, reverse=True)

        return vector_results[:top_k]

    def get_statistics(self) -> dict:
        """获取检索服务统计"""
        return {
            "total_documents": self.chroma.count(),
            "index_initialized": self.chroma._ensure_initialized() if hasattr(self.chroma, '_ensure_initialized') else True,
        }


# 全局知识检索实例
knowledge_search = KnowledgeSearch()
