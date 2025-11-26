"""
智能体基类
所有智能体的公共接口和功能
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..bedrock_client import bedrock_client


class BaseAgent(ABC):
    """智能体基类"""

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: Optional[str] = None,
    ):
        """
        初始化智能体

        Args:
            name: 智能体名称
            description: 智能体描述
            system_prompt: 系统提示词
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.bedrock = bedrock_client

    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """
        执行智能体任务

        Args:
            input_data: 输入数据

        Returns:
            执行结果
        """
        pass

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        调用LLM

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数

        Returns:
            LLM响应
        """
        return await self.bedrock.invoke(
            prompt=prompt,
            system_prompt=system_prompt or self.system_prompt,
            temperature=temperature,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
