"""
服务匹配器
基于RAG检索匹配最合适的服务，带有关键词回退
"""
from typing import Optional
from ..chroma_client import chroma_client


class ServiceMatcher:
    """服务匹配器"""

    def __init__(self):
        self.chroma = chroma_client
        self._services_indexed = False
        self._service_cache = []  # Fallback cache for keyword matching

    def index_services(self, services: list[dict]):
        """
        索引服务定义

        Args:
            services: 服务定义列表
        """
        if self._services_indexed:
            return

        # Always cache for keyword fallback
        self._service_cache = services

        documents = []
        metadatas = []
        ids = []

        for service in services:
            # 构建服务描述文档
            doc = f"""Service: {service['name']}
ID: {service['service_id']}
Description: {service['description']}
Keywords: {', '.join(service.get('keywords', []))}
Parameters: {', '.join(service.get('parameters', {}).keys())}"""

            documents.append(doc)
            metadatas.append({
                "service_id": service['service_id'],
                "name": service['name'],
                "type": "service",
            })
            ids.append(f"service_{service['service_id']}")

        if documents:
            # 先清空旧数据
            try:
                self.chroma.clear()
            except Exception:
                pass

            try:
                self.chroma.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
            except Exception as e:
                print(f"Warning: ChromaDB indexing failed: {e}")
                print("Using keyword-based fallback matching")

        self._services_indexed = True

    def _keyword_match(self, query: str, top_k: int = 3) -> list[dict]:
        """Keyword-based fallback matching"""
        query_lower = query.lower()
        scores = []

        for service in self._service_cache:
            score = 0
            name = service.get('name', '').lower()
            desc = service.get('description', '').lower()
            keywords = [k.lower() for k in service.get('keywords', [])]

            # Score based on keyword matching
            for word in query_lower.split():
                if word in name:
                    score += 3
                if word in desc:
                    score += 1
                if any(word in kw for kw in keywords):
                    score += 2

            if score > 0:
                scores.append({
                    "service_id": service['service_id'],
                    "name": service['name'],
                    "relevance_score": min(score / 10, 1.0),
                    "document": f"{service['name']}: {service['description']}",
                })

        # Sort by score and return top_k
        scores.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scores[:top_k]

    async def match_service(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        根据查询匹配服务

        Args:
            query: 用户查询
            top_k: 返回前K个结果

        Returns:
            匹配的服务列表
        """
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

                    matched_services.append({
                        "service_id": metadata.get("service_id", ""),
                        "name": metadata.get("name", ""),
                        "relevance_score": 1 - distance,  # 转换为相似度分数
                        "document": results["documents"][0][i] if results.get("documents") else "",
                    })

            if matched_services:
                return matched_services
        except Exception as e:
            print(f"ChromaDB query failed: {e}, using keyword fallback")

        # Fallback to keyword matching
        return self._keyword_match(query, top_k)

    async def find_best_match(
        self,
        query: str,
        threshold: float = 0.3,  # Lower threshold for keyword matching
    ) -> Optional[dict]:
        """
        找到最佳匹配的服务

        Args:
            query: 用户查询
            threshold: 相似度阈值

        Returns:
            最佳匹配的服务，如果没有匹配则返回None
        """
        matches = await self.match_service(query, top_k=1)

        if matches and matches[0].get("relevance_score", 0) >= threshold:
            return matches[0]

        return None

    def get_indexed_count(self) -> int:
        """获取已索引的服务数量"""
        try:
            return self.chroma.count()
        except Exception:
            return len(self._service_cache)
