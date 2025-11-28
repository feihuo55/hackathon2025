"""
Knowledge Search Service / 知识检索服务
RAG-based knowledge base retrieval with bilingual support
基于RAG的知识库检索功能，支持中英双语

Features / 功能:
- Vector-based semantic search / 向量语义检索
- Bilingual query support (Chinese/English) / 双语查询支持
- Hybrid search with keyword boosting / 关键词加权混合检索
- Context-aware search / 上下文感知检索
- Similar document discovery / 相似文档发现
"""
from typing import Optional
from dataclasses import dataclass
from ..chroma_client import chroma_client
from ..indexing.embeddings import text_preprocessor


@dataclass
class SearchResult:
    """
    Search Result / 检索结果

    Attributes:
        content: Document content / 文档内容
        metadata: Document metadata / 文档元数据
        score: Relevance score (0-1) / 相关度分数
        doc_id: Document identifier / 文档ID
    """
    content: str
    metadata: dict
    score: float
    doc_id: str


class KnowledgeSearch:
    """
    Knowledge Search Service with bilingual support
    知识检索服务 - 支持中英双语

    This class provides:
    - Vector-based semantic search using ChromaDB
    - Query preprocessing and optimization
    - Hybrid search combining vectors and keywords
    - Context-aware search capabilities

    本类提供：
    - 基于ChromaDB的向量语义检索
    - 查询预处理和优化
    - 向量与关键词结合的混合检索
    - 上下文感知检索能力
    """

    def __init__(self):
        """Initialize knowledge search service / 初始化知识检索服务"""
        self.chroma = chroma_client

    async def search(
        self,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """
        Search the knowledge base
        检索知识库

        Args:
            query: Query text (Chinese or English) / 查询文本（中文或英文）
            top_k: Number of results to return / 返回结果数量
            doc_type: Filter by document type / 文档类型过滤
            min_score: Minimum relevance score threshold / 最小相关度分数阈值

        Returns:
            List of SearchResult objects sorted by relevance
            按相关度排序的 SearchResult 列表
        """
        # Preprocess query / 预处理查询
        processed_query = text_preprocessor.preprocess(query)

        # Build filter condition / 构建过滤条件
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
                    # Calculate relevance score / 计算相关度分数
                    distance = results.get("distances", [[]])[0][i] if results.get("distances") else 0
                    # ChromaDB L2 distance may be >1, use 1/(1+distance) to ensure 0-1 range
                    # ChromaDB L2距离可能>1，使用 1/(1+distance) 确保在0-1之间
                    score = 1.0 / (1.0 + distance) if distance >= 0 else 0.0

                    if score >= min_score:
                        search_results.append(SearchResult(
                            content=results["documents"][0][i] if results.get("documents") else "",
                            metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                            score=score,
                            doc_id=doc_id,
                        ))

            return search_results

        except Exception as e:
            print(f"Warning: Knowledge search failed: {e}")
            return []

    async def search_services(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """
        Search service definitions
        检索服务定义

        Args:
            query: Query text / 查询文本
            top_k: Number of results / 返回数量

        Returns:
            List of service search results / 服务检索结果列表
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
        Search with context information
        带上下文的检索

        This combines the query with context information for better
        semantic matching. Useful for follow-up questions in conversations.

        结合查询和上下文信息以获得更好的语义匹配。
        适用于对话中的后续问题。

        Args:
            query: Query text / 查询文本
            context: Context information / 上下文信息
            top_k: Number of results / 返回数量

        Returns:
            List of search results / 检索结果
        """
        # Combine query and context / 组合查询和上下文
        combined_query = f"{query} {context}".strip()
        return await self.search(combined_query, top_k)

    async def find_similar(
        self,
        doc_id: str,
        top_k: int = 5,
        exclude_self: bool = True,
    ) -> list[SearchResult]:
        """
        Find similar documents
        查找相似文档

        Uses the content of an existing document to find semantically
        similar documents in the knowledge base.

        使用现有文档的内容在知识库中查找语义相似的文档。

        Args:
            doc_id: Document ID to find similar documents for / 文档ID
            top_k: Number of results / 返回数量
            exclude_self: Whether to exclude the source document / 是否排除源文档

        Returns:
            List of similar documents / 相似文档列表
        """
        try:
            # Get original document content / 获取原文档内容
            all_docs = self.chroma.get_all_documents()
            doc_content = None

            if all_docs and all_docs.get("ids"):
                for i, id_ in enumerate(all_docs["ids"]):
                    if id_ == doc_id:
                        doc_content = all_docs["documents"][i]
                        break

            if not doc_content:
                return []

            # Use document content as query / 使用文档内容作为查询
            results = await self.search(doc_content, top_k + (1 if exclude_self else 0))

            if exclude_self:
                results = [r for r in results if r.doc_id != doc_id]

            return results[:top_k]

        except Exception as e:
            print(f"Warning: Find similar documents failed: {e}")
            return []

    async def hybrid_search(
        self,
        query: str,
        keywords: list[str] = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Hybrid search combining vectors and keywords
        混合检索（向量 + 关键词）

        This method first performs vector search, then boosts scores
        for documents containing the specified keywords.

        此方法首先执行向量检索，然后为包含指定关键词的文档提升分数。

        Args:
            query: Query text (Chinese or English) / 查询文本（中文或英文）
            keywords: Optional keyword list for boosting / 用于提升的关键词列表
            top_k: Number of results / 返回数量

        Returns:
            Search results with keyword boosting / 带关键词提升的检索结果
        """
        # Vector search / 向量检索
        vector_results = await self.search(query, top_k * 2)

        if not keywords:
            return vector_results[:top_k]

        # Keyword boosting / 关键词加权
        for result in vector_results:
            content_lower = result.content.lower()
            keyword_boost = 0

            for keyword in keywords:
                if keyword.lower() in content_lower:
                    keyword_boost += 0.1

            result.score = min(result.score + keyword_boost, 1.0)

        # Re-sort by boosted scores / 按提升后的分数重新排序
        vector_results.sort(key=lambda x: x.score, reverse=True)

        return vector_results[:top_k]

    async def multilingual_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Multilingual-aware search
        多语言感知检索

        Detects query language and adjusts search strategy accordingly.
        检测查询语言并相应调整检索策略。

        Args:
            query: Query text in any language / 任意语言的查询文本
            top_k: Number of results / 返回数量

        Returns:
            Search results / 检索结果
        """
        # Detect language and expand with synonyms
        # 检测语言并使用同义词扩展
        try:
            from .tokenizer import BilingualTokenizer, expand_synonyms
            tokenizer = BilingualTokenizer()

            # Get query tokens with synonym expansion
            # 获取带同义词扩展的查询词
            expanded_tokens = tokenizer.tokenize_for_search(query)

            # Build expanded query / 构建扩展查询
            expanded_query = " ".join(set(expanded_tokens))

            return await self.search(expanded_query, top_k)
        except ImportError:
            # Fallback to basic search / 回退到基础检索
            return await self.search(query, top_k)

    def get_statistics(self) -> dict:
        """
        Get search service statistics
        获取检索服务统计信息

        Returns:
            Dictionary with index statistics
            包含索引统计信息的字典
        """
        return {
            "total_documents": self.chroma.count(),
            "index_initialized": self.chroma._ensure_initialized() if hasattr(self.chroma, '_ensure_initialized') else True,
        }


# Global knowledge search instance / 全局知识检索实例
knowledge_search = KnowledgeSearch()
