"""
AWS Bedrock 客户端
使用 Bearer Token 认证调用 Claude 3.5 Sonnet
"""
import json
import aiohttp
from typing import Optional, AsyncGenerator
from config import AWS_CONFIG


class BedrockClient:
    """AWS Bedrock Claude 客户端"""

    def __init__(self):
        self.bearer_token = AWS_CONFIG["bearer_token"]
        self.region = AWS_CONFIG["region"]
        self.model_id = AWS_CONFIG["model_id"]
        self.max_tokens = AWS_CONFIG["max_tokens"]
        self.temperature = AWS_CONFIG["temperature"]
        self.endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        调用 Claude 模型

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            模型响应文本
        """
        url = f"{self.endpoint}/model/{self.model_id}/invoke"

        messages = [{"role": "user", "content": prompt}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Bedrock API error: {response.status} - {error_text}")

                result = await response.json()
                return result.get("content", [{}])[0].get("text", "")

    async def invoke_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式调用 Claude 模型

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            max_tokens: 最大token数
            temperature: 温度参数

        Yields:
            模型响应文本片段
        """
        url = f"{self.endpoint}/model/{self.model_id}/invoke-with-response-stream"

        messages = [{"role": "user", "content": prompt}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Bedrock API error: {response.status} - {error_text}")

                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "delta" in data and "text" in data["delta"]:
                                yield data["delta"]["text"]
                        except json.JSONDecodeError:
                            continue

    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        多轮对话

        Args:
            messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
            system_prompt: 系统提示词
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            模型响应文本
        """
        url = f"{self.endpoint}/model/{self.model_id}/invoke"

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Bedrock API error: {response.status} - {error_text}")

                result = await response.json()
                return result.get("content", [{}])[0].get("text", "")


# 全局客户端实例
bedrock_client = BedrockClient()
