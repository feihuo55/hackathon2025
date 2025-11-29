# Retrieval - 检索服务模块（含反馈重排序）
from .service_matcher import ServiceMatcher
from .feedback_reranker import (
    FeedbackReranker,
    RerankedResult,
    get_feedback_reranker,
    rerank_with_feedback,
)

# 延迟导入依赖chromadb的模块
KnowledgeSearch = None
SearchResult = None
knowledge_search = None

def _lazy_import_knowledge_search():
    global KnowledgeSearch, SearchResult, knowledge_search
    try:
        from .knowledge_search import KnowledgeSearch as _KnowledgeSearch
        from .knowledge_search import SearchResult as _SearchResult
        from .knowledge_search import knowledge_search as _knowledge_search
        KnowledgeSearch = _KnowledgeSearch
        SearchResult = _SearchResult
        knowledge_search = _knowledge_search
        return True
    except ImportError:
        return False

_lazy_import_knowledge_search()

__all__ = [
    'ServiceMatcher',
    'KnowledgeSearch',
    'SearchResult',
    'knowledge_search',
    'FeedbackReranker',
    'RerankedResult',
    'get_feedback_reranker',
    'rerank_with_feedback',
]
