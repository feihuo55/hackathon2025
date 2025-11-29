# RAG Module - 检索增强生成模块
# 托管银行AI自动化平台的核心RAG能力
# V2: 增加用户反馈闭环学习系统

# 延迟导入以支持chromadb不可用的情况
def _lazy_import():
    """延迟导入依赖chromadb的模块"""
    global ChromaClient, chroma_client, index_builder, knowledge_search

    try:
        from .chroma_client import ChromaClient, chroma_client
        from .indexing.index_builder import index_builder
        from .retrieval.knowledge_search import knowledge_search
        return True
    except ImportError as e:
        print(f"Warning: ChromaDB not available: {e}")
        ChromaClient = None
        chroma_client = None
        index_builder = None
        knowledge_search = None
        return False


# 不依赖chromadb的导入
from .indexing.document_loader import Document, DocumentLoader, load_services_from_registry
from .indexing.embeddings import EmbeddingService, TextPreprocessor, embedding_service, text_preprocessor

from .retrieval.service_matcher import ServiceMatcher

# 记忆系统（含反馈记忆）
from .memory import (
    MemoryManager,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    Procedure,
    SummaryMemory,
    Summary,
    FeedbackMemory,
    Feedback,
    FeedbackType,
    FeedbackSource,
    MemoryPersistence,
    get_persistence,
)

# 反馈收集模块
from .feedback import (
    FeedbackCollector,
    get_feedback_collector,
    collect_thumbs_up,
    collect_thumbs_down,
    collect_correction,
)

# 学习模块
from .learning import (
    RelevanceLearner,
    get_relevance_learner,
    KnowledgeRefiner,
    get_knowledge_refiner,
)

# 反馈重排序
from .retrieval.feedback_reranker import (
    FeedbackReranker,
    get_feedback_reranker,
    rerank_with_feedback,
)

from .utils import (
    RetryConfig,
    with_retry,
    with_async_retry,
    CircuitBreaker,
    RAGError,
    IndexingError,
    RetrievalError,
    ServiceMatchError,
    safe_execute,
    safe_async_execute,
)

# 尝试导入依赖chromadb的模块
ChromaClient = None
chroma_client = None
index_builder = None
knowledge_search = None
_lazy_import()

# 动态导入IndexBuilder（不创建全局实例）
try:
    from .indexing.index_builder import IndexBuilder
except ImportError:
    IndexBuilder = None

try:
    from .retrieval.knowledge_search import KnowledgeSearch, SearchResult
except ImportError:
    KnowledgeSearch = None
    SearchResult = None

__all__ = [
    # Chroma客户端
    'ChromaClient',
    'chroma_client',

    # 索引
    'Document',
    'DocumentLoader',
    'IndexBuilder',
    'index_builder',
    'EmbeddingService',
    'TextPreprocessor',
    'embedding_service',
    'text_preprocessor',
    'load_services_from_registry',

    # 检索
    'ServiceMatcher',
    'KnowledgeSearch',
    'SearchResult',
    'knowledge_search',
    'FeedbackReranker',
    'get_feedback_reranker',
    'rerank_with_feedback',

    # 记忆
    'MemoryManager',
    'EpisodicMemory',
    'SemanticMemory',
    'ProceduralMemory',
    'Procedure',
    'SummaryMemory',
    'Summary',
    'FeedbackMemory',
    'Feedback',
    'FeedbackType',
    'FeedbackSource',
    'MemoryPersistence',
    'get_persistence',

    # 反馈收集
    'FeedbackCollector',
    'get_feedback_collector',
    'collect_thumbs_up',
    'collect_thumbs_down',
    'collect_correction',

    # 学习
    'RelevanceLearner',
    'get_relevance_learner',
    'KnowledgeRefiner',
    'get_knowledge_refiner',

    # 工具
    'RetryConfig',
    'with_retry',
    'with_async_retry',
    'CircuitBreaker',
    'RAGError',
    'IndexingError',
    'RetrievalError',
    'ServiceMatchError',
    'safe_execute',
    'safe_async_execute',
]
