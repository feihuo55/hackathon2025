"""
Service Matcher / 服务匹配器
RAG-based service matching with Chinese tokenization and synonym expansion
基于RAG检索匹配最合适的服务，支持中英文分词和同义词扩展

Features / 功能:
- Bilingual query support (Chinese/English) / 双语查询支持
- Synonym expansion for financial terms / 金融术语同义词扩展
- Vector search with ChromaDB / 向量检索
- Keyword-based fallback matching / 关键词回退匹配
- Retry mechanism with exponential backoff / 指数退避重试机制
"""
from typing import Optional
from .tokenizer import BilingualTokenizer, expand_synonyms, calculate_text_similarity

# Lazy import retry module / 延迟导入重试模块
_retry_module = None


def _get_retry_utils():
    """Lazy load retry module / 延迟加载重试模块"""
    global _retry_module
    if _retry_module is None:
        try:
            from ..utils.retry import (
                with_async_retry,
                RetryConfig,
                safe_async_execute,
                ServiceMatchError,
            )
            _retry_module = {
                "with_async_retry": with_async_retry,
                "RetryConfig": RetryConfig,
                "safe_async_execute": safe_async_execute,
                "ServiceMatchError": ServiceMatchError,
            }
        except ImportError:
            pass
    return _retry_module


# Lazy import chroma_client / 延迟导入chroma_client
chroma_client = None


def _get_chroma_client():
    """Get ChromaDB client / 获取ChromaDB客户端"""
    global chroma_client
    if chroma_client is None:
        try:
            from ..chroma_client import chroma_client as _client
            chroma_client = _client
        except ImportError:
            pass
    return chroma_client


class ServiceMatcher:
    """
    Service Matcher with bilingual support
    服务匹配器 - 支持中英文分词和同义词扩展

    This class provides:
    - Vector-based semantic search using ChromaDB
    - Keyword-based fallback matching with synonym expansion
    - Bilingual query processing (Chinese/English)
    - Retry mechanism for fault tolerance

    本类提供：
    - 基于ChromaDB的向量语义检索
    - 支持同义词扩展的关键词回退匹配
    - 双语查询处理（中文/英文）
    - 容错重试机制
    """

    def __init__(self):
        """
        Initialize the service matcher
        初始化服务匹配器
        """
        self.chroma = _get_chroma_client()
        self._services_indexed = False
        self._service_cache = []  # Fallback cache for keyword matching
        self._tokenizer = BilingualTokenizer()

    def index_services(self, services: list[dict]):
        """
        Index service definitions for search
        索引服务定义用于检索

        Args:
            services: List of service definition dictionaries
                     Each service should have: service_id, name, description, keywords, parameters
                     服务定义列表，每个服务包含：service_id, name, description, keywords, parameters
        """
        if self._services_indexed:
            return

        # Always cache for keyword fallback / 始终缓存用于关键词回退
        self._service_cache = services

        # Preprocess services: expand keywords for each service
        # 预处理服务：为每个服务扩展关键词
        for service in self._service_cache:
            expanded_keywords = set(service.get('keywords', []))
            for kw in list(expanded_keywords):
                expanded_keywords.update(expand_synonyms(kw))
            service['_expanded_keywords'] = expanded_keywords

            # Pre-tokenize description and name / 预分词描述和名称
            service['_tokenized_desc'] = set(
                self._tokenizer.tokenize_for_search(service.get('description', ''))
            )
            service['_tokenized_name'] = set(
                self._tokenizer.tokenize_for_search(service.get('name', ''))
            )

        # Prepare documents for ChromaDB / 准备ChromaDB文档
        documents = []
        metadatas = []
        ids = []

        for service in services:
            # Build service description document with expanded keywords
            # 构建服务描述文档（包含扩展关键词）
            all_keywords = service.get('_expanded_keywords', service.get('keywords', []))
            doc = f"""Service: {service['name']}
ID: {service['service_id']}
Description: {service['description']}
Keywords: {', '.join(all_keywords)}
Parameters: {', '.join(service.get('parameters', {}).keys())}"""

            documents.append(doc)
            metadatas.append({
                "service_id": service['service_id'],
                "name": service['name'],
                "type": "service",
            })
            ids.append(f"service_{service['service_id']}")

        if documents:
            # Clear old data first / 先清空旧数据
            try:
                if self.chroma:
                    self.chroma.clear()
            except Exception:
                pass

            # Index to ChromaDB / 索引到ChromaDB
            try:
                if self.chroma:
                    self.chroma.add_documents(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids,
                    )
            except Exception as e:
                print(f"Warning: ChromaDB indexing failed: {e}")
                print("Using keyword-based fallback matching")

        self._services_indexed = True

    def _calculate_service_score(self, query_tokens: set, service: dict) -> float:
        """
        Calculate service matching score
        计算服务匹配分数

        Args:
            query_tokens: Set of tokenized query terms / 查询分词集合
            service: Service definition dictionary / 服务定义

        Returns:
            Matching score (0-1) / 匹配分数
        """
        score = 0.0

        # Get preprocessed service data / 获取预处理的服务数据
        name_tokens = service.get('_tokenized_name', set())
        desc_tokens = service.get('_tokenized_desc', set())
        keywords = service.get('_expanded_keywords', set(service.get('keywords', [])))
        keywords_lower = {k.lower() for k in keywords}

        # Calculate intersections / 计算交集
        name_matches = len(query_tokens & name_tokens)
        desc_matches = len(query_tokens & desc_tokens)

        # Keyword matching (consider synonyms) / 关键词匹配（考虑同义词）
        keyword_matches = 0
        direct_keyword_matches = 0  # Direct keyword match (not synonym)

        # Get original keywords (unexpanded) / 获取原始关键词（未扩展）
        original_keywords = set(k.lower() for k in service.get('keywords', []))

        for qt in query_tokens:
            qt_lower = qt.lower()
            # Direct keyword match (high weight) / 直接关键词匹配（高权重）
            if qt_lower in original_keywords:
                direct_keyword_matches += 1
            elif qt_lower in keywords_lower:
                keyword_matches += 1
            else:
                # Synonym match (lower weight) / 同义词匹配（较低权重）
                for syn in expand_synonyms(qt):
                    if syn.lower() in keywords_lower:
                        keyword_matches += 0.3
                        break

        # Weighted scoring / 加权计分
        # Name match has highest weight / 名称匹配权重最高
        score += name_matches * 5.0
        # Direct keyword match (high weight) / 直接关键词匹配（高权重）
        score += direct_keyword_matches * 4.0
        # Expanded keyword match / 扩展关键词匹配
        score += keyword_matches * 2.0
        # Description match / 描述匹配
        score += desc_matches * 1.0

        # Normalize based on query term coverage / 基于查询词覆盖率的归一化
        total_matches = name_matches + direct_keyword_matches + keyword_matches + desc_matches
        query_len = len(query_tokens) if query_tokens else 1
        coverage_factor = min(1.0, total_matches / max(query_len * 0.3, 1))

        # Normalize to 0-1 range / 归一化到0-1范围
        max_score = 15.0
        normalized_score = min(score / max_score, 1.0) * (0.4 + 0.6 * coverage_factor)

        return max(0.0, normalized_score)

    def _keyword_match(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Keyword-based matching with tokenization and synonyms
        基于关键词的匹配（支持分词和同义词）

        Args:
            query: Query text / 查询文本
            top_k: Number of results to return / 返回数量

        Returns:
            List of matching results / 匹配结果列表
        """
        # Tokenize query with synonym expansion / 使用分词器处理查询
        query_tokens = set(self._tokenizer.tokenize_for_search(query))

        scores = []

        for service in self._service_cache:
            score = self._calculate_service_score(query_tokens, service)

            if score > 0:
                scores.append({
                    "service_id": service['service_id'],
                    "name": service['name'],
                    "relevance_score": score,
                    "document": f"{service['name']}: {service['description']}",
                    "matched_keywords": list(query_tokens & service.get('_expanded_keywords', set())),
                })

        # Sort by score / 按分数排序
        scores.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scores[:top_k]

    async def match_service(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Match services based on query
        根据查询匹配服务

        Args:
            query: User query (Chinese or English) / 用户查询（中文或英文）
            top_k: Number of top results to return / 返回前K个结果

        Returns:
            List of matched services with relevance scores
            匹配的服务列表，包含相关度分数
        """
        return await self._match_service_with_retry(query, top_k)

    async def _match_service_with_retry(
        self,
        query: str,
        top_k: int,
    ) -> list[dict]:
        """
        Service matching with retry mechanism
        带重试的服务匹配
        """
        retry_utils = _get_retry_utils()

        # First try ChromaDB vector search / 首先尝试ChromaDB向量检索
        chroma_result = await self._try_chroma_match(query, top_k)
        if chroma_result:
            return chroma_result

        # Fallback to keyword matching / 回退到关键词匹配
        return self._keyword_match(query, top_k)

    async def _try_chroma_match(
        self,
        query: str,
        top_k: int,
        max_retries: int = 2,
    ) -> list[dict]:
        """
        Try ChromaDB matching with retry
        尝试使用ChromaDB匹配（带重试）
        """
        if not self.chroma:
            return []

        last_error = None
        for attempt in range(max_retries):
            try:
                results = self.chroma.query(
                    query_text=query,
                    n_results=top_k,
                    where={"type": "service"},
                )

                matched_services = []
                if results and results.get("ids") and results["ids"][0]:
                    for i, doc_id in enumerate(results["ids"][0]):
                        metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                        distance = results["distances"][0][i] if results.get("distances") else 0

                        # Convert distance to similarity score (0-1 range)
                        # 将距离转换为相似度分数 (0-1范围)
                        # ChromaDB L2 distance may be >1, use 1/(1+distance) to ensure 0-1 range
                        similarity = 1.0 / (1.0 + distance) if distance >= 0 else 0

                        matched_services.append({
                            "service_id": metadata.get("service_id", ""),
                            "name": metadata.get("name", ""),
                            "relevance_score": similarity,
                            "document": results["documents"][0][i] if results.get("documents") else "",
                        })

                if matched_services:
                    return matched_services
                return []

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

        if last_error:
            print(f"ChromaDB query failed after {max_retries} attempts: {last_error}, using keyword fallback")

        return []

    async def find_best_match(
        self,
        query: str,
        threshold: float = 0.15,
    ) -> Optional[dict]:
        """
        Find the best matching service
        找到最佳匹配的服务

        Args:
            query: User query / 用户查询
            threshold: Minimum similarity threshold / 相似度阈值

        Returns:
            Best matching service, or None if no match above threshold
            最佳匹配的服务，如果没有匹配则返回None
        """
        matches = await self.match_service(query, top_k=1)

        if matches and matches[0].get("relevance_score", 0) >= threshold:
            return matches[0]

        return None

    async def match_with_explanation(
        self,
        query: str,
        top_k: int = 3,
    ) -> dict:
        """
        Match services and return with explanation
        匹配服务并返回解释

        Args:
            query: User query / 用户查询
            top_k: Number of results / 返回数量

        Returns:
            Dictionary containing matches and explanation
            包含匹配结果和解释的字典
        """
        query_tokens = list(self._tokenizer.tokenize_for_search(query))
        matches = await self.match_service(query, top_k)

        return {
            "query": query,
            "query_tokens": query_tokens,
            "detected_language": self._tokenizer.detect_language(query),
            "matches": matches,
            "total_services": len(self._service_cache),
        }

    def get_indexed_count(self) -> int:
        """
        Get the count of indexed services
        获取已索引的服务数量
        """
        try:
            if self.chroma:
                return self.chroma.count()
        except Exception:
            pass
        return len(self._service_cache)

    def get_all_services(self) -> list[dict]:
        """
        Get all services (without internal fields)
        获取所有服务（不含内部字段）
        """
        return [
            {
                "service_id": s["service_id"],
                "name": s["name"],
                "description": s["description"],
                "keywords": s.get("keywords", []),
                "parameters": s.get("parameters", {}),
            }
            for s in self._service_cache
        ]


# Backward compatibility alias / 向后兼容别名
# Keep ChineseTokenizer import working
from .tokenizer import ChineseTokenizer
