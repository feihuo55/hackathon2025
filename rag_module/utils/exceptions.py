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
