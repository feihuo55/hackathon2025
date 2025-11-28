"""
中文 Embedding 模型支持
支持多种中文向量模型：bge-zh, m3e, text2vec
"""
from typing import Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseEmbedding(ABC):
    """Embedding 基类"""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量"""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass


class SentenceTransformerEmbedding(BaseEmbedding):
    """基于 sentence-transformers 的 Embedding"""

    # 推荐的中文模型
    CHINESE_MODELS = {
        "bge-small-zh": "BAAI/bge-small-zh-v1.5",      # 512维, 快速
        "bge-base-zh": "BAAI/bge-base-zh-v1.5",        # 768维, 平衡
        "bge-large-zh": "BAAI/bge-large-zh-v1.5",      # 1024维, 最佳
        "m3e-base": "moka-ai/m3e-base",                 # 768维, 中文优化
        "m3e-small": "moka-ai/m3e-small",               # 512维, 轻量
        "text2vec": "shibing624/text2vec-base-chinese", # 768维
        "paraphrase-multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # 384维, 多语言
    }

    def __init__(
        self,
        model_name: str = "bge-small-zh",
        device: str = "cpu",
        normalize: bool = True,
        cache_dir: Optional[str] = None,
    ):
        """
        初始化 Embedding 模型

        Args:
            model_name: 模型名称或路径
            device: 运行设备 (cpu/cuda)
            normalize: 是否归一化向量
            cache_dir: 模型缓存目录
        """
        self._model = None
        self._model_name = self.CHINESE_MODELS.get(model_name, model_name)
        self._device = device
        self._normalize = normalize
        self._cache_dir = cache_dir
        self._dimension = None

    def _ensure_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"加载 Embedding 模型: {self._model_name}")
                self._model = SentenceTransformer(
                    self._model_name,
                    device=self._device,
                    cache_folder=self._cache_dir,
                )
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"模型加载完成，向量维度: {self._dimension}")
            except ImportError:
                raise ImportError(
                    "请安装 sentence-transformers: pip install sentence-transformers"
                )
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量"""
        model = self._ensure_model()
        embedding = model.encode(
            text,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        if not texts:
            return []

        model = self._ensure_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
            batch_size=32,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """向量维度"""
        if self._dimension is None:
            self._ensure_model()
        return self._dimension


class BedrockEmbedding(BaseEmbedding):
    """AWS Bedrock Embedding (Titan)"""

    MODEL_DIMENSIONS = {
        "amazon.titan-embed-text-v1": 1536,
        "amazon.titan-embed-text-v2:0": 1024,
        "cohere.embed-english-v3": 1024,
        "cohere.embed-multilingual-v3": 1024,
    }

    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v1",
        region: str = "us-east-1",
    ):
        """
        初始化 Bedrock Embedding

        Args:
            model_id: Bedrock 模型 ID
            region: AWS 区域
        """
        self._model_id = model_id
        self._region = region
        self._client = None
        self._dimension = self.MODEL_DIMENSIONS.get(model_id, 1536)

    def _ensure_client(self):
        """延迟初始化 Bedrock 客户端"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self._region
                )
            except ImportError:
                raise ImportError("请安装 boto3: pip install boto3")
        return self._client

    def embed_text(self, text: str) -> list[float]:
        """调用 Bedrock Titan 获取向量"""
        import json
        client = self._ensure_client()

        try:
            response = client.invoke_model(
                modelId=self._model_id,
                body=json.dumps({"inputText": text}),
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return result["embedding"]
        except Exception as e:
            logger.error(f"Bedrock Embedding 调用失败: {e}")
            raise

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量调用（Titan 不支持原生批量，逐个处理）"""
        return [self.embed_text(text) for text in texts]

    @property
    def dimension(self) -> int:
        """向量维度"""
        return self._dimension


class ChromaEmbeddingAdapter:
    """ChromaDB Embedding Function 适配器"""

    def __init__(self, embedding: BaseEmbedding):
        """
        初始化适配器

        Args:
            embedding: BaseEmbedding 实例
        """
        self._embedding = embedding
        # ChromaDB 需要这些属性
        self.name = "custom_embedding"

    def __call__(self, input: list[str]) -> list[list[float]]:
        """ChromaDB 调用接口"""
        return self._embedding.embed_batch(input)


class EmbeddingFactory:
    """Embedding 工厂类"""

    @staticmethod
    def create(
        provider: str = "sentence-transformer",
        model_name: str = "bge-small-zh",
        **kwargs
    ) -> BaseEmbedding:
        """
        创建 Embedding 实例

        Args:
            provider: 提供商 (sentence-transformer, bedrock)
            model_name: 模型名称
            **kwargs: 额外参数

        Returns:
            BaseEmbedding 实例
        """
        if provider == "sentence-transformer":
            return SentenceTransformerEmbedding(model_name, **kwargs)
        elif provider == "bedrock":
            return BedrockEmbedding(model_name, **kwargs)
        else:
            raise ValueError(f"不支持的 Embedding 提供商: {provider}")


# 默认实例（延迟初始化）
_default_embedding: Optional[BaseEmbedding] = None


def get_embedding(
    provider: str = None,
    model_name: str = None,
    **kwargs
) -> BaseEmbedding:
    """
    获取 Embedding 实例

    Args:
        provider: 提供商
        model_name: 模型名称
        **kwargs: 额外参数

    Returns:
        BaseEmbedding 实例
    """
    global _default_embedding

    if provider or model_name:
        return EmbeddingFactory.create(
            provider=provider or "sentence-transformer",
            model_name=model_name or "bge-small-zh",
            **kwargs
        )

    if _default_embedding is None:
        # 尝试从配置读取
        try:
            from config import EMBEDDING_CONFIG
            _default_embedding = EmbeddingFactory.create(
                provider=EMBEDDING_CONFIG.get("provider", "sentence-transformer"),
                model_name=EMBEDDING_CONFIG.get("model_name", "bge-small-zh"),
                device=EMBEDDING_CONFIG.get("device", "cpu"),
                normalize=EMBEDDING_CONFIG.get("normalize", True),
            )
        except (ImportError, KeyError):
            # 使用默认配置
            _default_embedding = SentenceTransformerEmbedding("bge-small-zh")

    return _default_embedding


def get_chroma_embedding_function(
    provider: str = None,
    model_name: str = None,
    **kwargs
) -> ChromaEmbeddingAdapter:
    """
    获取 ChromaDB 兼容的 Embedding Function

    Args:
        provider: 提供商
        model_name: 模型名称

    Returns:
        ChromaEmbeddingAdapter 实例
    """
    embedding = get_embedding(provider, model_name, **kwargs)
    return ChromaEmbeddingAdapter(embedding)
