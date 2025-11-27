"""
向量化服务
提供文本向量化功能
"""
from typing import Optional
import hashlib


class EmbeddingService:
    """向量化服务 - 使用Chroma内置的embedding功能"""

    def __init__(self, model_name: str = "default"):
        """
        初始化向量化服务

        Args:
            model_name: 模型名称 (Chroma使用默认的all-MiniLM-L6-v2)
        """
        self.model_name = model_name
        self._cache: dict[str, list[float]] = {}

    def embed_text(self, text: str) -> list[float]:
        """
        将文本转换为向量

        注意：Chroma会自动处理embedding，此方法主要用于缓存和预处理

        Args:
            text: 输入文本

        Returns:
            向量表示（如果使用Chroma，返回空列表由Chroma处理）
        """
        # 计算文本哈希作为缓存键
        text_hash = self._hash_text(text)

        if text_hash in self._cache:
            return self._cache[text_hash]

        # Chroma会自动使用sentence-transformers处理embedding
        # 这里返回空列表，实际embedding由Chroma完成
        return []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return [self.embed_text(text) for text in texts]

    def _hash_text(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class TextPreprocessor:
    """文本预处理器"""

    @staticmethod
    def preprocess(text: str) -> str:
        """
        预处理文本

        Args:
            text: 原始文本

        Returns:
            处理后的文本
        """
        # 去除多余空白
        text = " ".join(text.split())

        # 转换为小写（可选，根据需求）
        # text = text.lower()

        return text.strip()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[str]:
        """
        将长文本分割成块

        Args:
            text: 原始文本
            chunk_size: 块大小（字符数）
            overlap: 重叠字符数

        Returns:
            文本块列表
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # 尝试在句子边界分割
            if end < len(text):
                # 寻找最近的句号、感叹号或问号
                for punct in ["。", "！", "？", ".", "!", "?"]:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct > start:
                        end = last_punct + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # 下一块的起始位置，考虑重叠
            start = end - overlap if end < len(text) else len(text)

        return chunks

    @staticmethod
    def extract_keywords(text: str, top_k: int = 10) -> list[str]:
        """
        提取关键词（简单实现）

        Args:
            text: 输入文本
            top_k: 返回关键词数量

        Returns:
            关键词列表
        """
        # 中文停用词
        stopwords = {
            "的", "是", "在", "了", "和", "与", "或", "等", "这", "那",
            "有", "为", "以", "及", "对", "从", "到", "被", "让", "把",
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "and",
            "or", "but", "if", "then", "else", "when", "at", "by", "for",
            "with", "about", "against", "between", "into", "through",
            "during", "before", "after", "above", "below", "to", "from",
        }

        # 分词（简单按空格和标点分割）
        import re
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text.lower())

        # 统计词频
        word_counts = {}
        for word in words:
            if word not in stopwords and len(word) > 1:
                word_counts[word] = word_counts.get(word, 0) + 1

        # 按词频排序
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [word for word, _ in sorted_words[:top_k]]


# 全局实例
embedding_service = EmbeddingService()
text_preprocessor = TextPreprocessor()
