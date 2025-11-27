# Indexing - 索引构建模块
from .document_loader import Document, DocumentLoader, load_services_from_registry
from .embeddings import EmbeddingService, TextPreprocessor, embedding_service, text_preprocessor

# 延迟导入依赖chromadb的模块
IndexBuilder = None
index_builder = None

def _lazy_import_index_builder():
    global IndexBuilder, index_builder
    try:
        from .index_builder import IndexBuilder as _IndexBuilder
        from .index_builder import index_builder as _index_builder
        IndexBuilder = _IndexBuilder
        index_builder = _index_builder
        return True
    except ImportError:
        return False

_lazy_import_index_builder()

__all__ = [
    'Document',
    'DocumentLoader',
    'load_services_from_registry',
    'IndexBuilder',
    'index_builder',
    'EmbeddingService',
    'TextPreprocessor',
    'embedding_service',
    'text_preprocessor',
]
