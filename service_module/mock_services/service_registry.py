"""
服务注册表
管理所有可用服务的注册和调用
"""
from typing import Callable, Optional, Any
from .fund_services import FundServices


class ServiceRegistry:
    """服务注册表"""

    def __init__(self):
        self._services: dict[str, dict] = {}
        self._register_default_services()

    def _register_default_services(self):
        """注册默认服务"""
        # 基金净值查询服务
        self.register(
            service_id="getFundNAV",
            name="基金净值查询",
            description="查询指定基金的单位净值、累计净值和涨跌幅",
            handler=FundServices.get_fund_nav,
            parameters={
                "fund_code": {
                    "type": "string",
                    "required": True,
                    "description": "基金代码，如161005"
                }
            },
            returns={
                "nav": "单位净值",
                "acc_nav": "累计净值",
                "change_pct": "涨跌幅百分比"
            },
            keywords=["净值", "基金", "查询", "NAV", "涨跌"]
        )

        # 基金分红查询服务
        self.register(
            service_id="getFundDividend",
            name="基金分红查询",
            description="查询指定基金的历史分红记录",
            handler=FundServices.get_fund_dividend,
            parameters={
                "fund_code": {
                    "type": "string",
                    "required": True,
                    "description": "基金代码"
                }
            },
            returns={
                "dividends": "分红记录列表",
                "total_dividend": "累计分红金额"
            },
            keywords=["分红", "派息", "红利", "分配"]
        )

        # 获取所有基金列表
        self.register(
            service_id="getAllFunds",
            name="获取基金列表",
            description="获取系统中所有可查询的基金列表",
            handler=FundServices.get_all_funds,
            parameters={},
            returns={
                "funds": "基金列表"
            },
            keywords=["列表", "所有基金", "基金列表"]
        )

        # 分红处理服务
        self.register(
            service_id="processDividend",
            name="基金分红处理",
            description="批量处理基金分红派息，支持现金分红和红利再投资",
            handler=FundServices.process_dividend,
            parameters={
                "fund_codes": {
                    "type": "list",
                    "required": True,
                    "description": "需要处理分红的基金代码列表"
                },
                "method": {
                    "type": "string",
                    "required": False,
                    "description": "分红方式: cash(现金) 或 reinvest(再投资)",
                    "default": "cash"
                }
            },
            returns={
                "processed_count": "处理数量",
                "total_amount": "分红总金额",
                "details": "处理详情"
            },
            keywords=["分红处理", "派息", "批量", "处理"]
        )

    def register(
        self,
        service_id: str,
        name: str,
        description: str,
        handler: Callable,
        parameters: dict,
        returns: dict,
        keywords: list[str] = None,
    ):
        """
        注册服务

        Args:
            service_id: 服务唯一标识
            name: 服务名称
            description: 服务描述
            handler: 服务处理函数
            parameters: 参数定义
            returns: 返回值定义
            keywords: 关键词列表，用于检索匹配
        """
        self._services[service_id] = {
            "service_id": service_id,
            "name": name,
            "description": description,
            "handler": handler,
            "parameters": parameters,
            "returns": returns,
            "keywords": keywords or [],
        }

    def get_service(self, service_id: str) -> Optional[dict]:
        """获取服务定义"""
        return self._services.get(service_id)

    def get_all_services(self) -> list[dict]:
        """获取所有服务定义（不含handler）"""
        services = []
        for service_id, service in self._services.items():
            services.append({
                "service_id": service["service_id"],
                "name": service["name"],
                "description": service["description"],
                "parameters": service["parameters"],
                "returns": service["returns"],
                "keywords": service["keywords"],
            })
        return services

    async def invoke(self, service_id: str, **kwargs) -> dict:
        """
        调用服务

        Args:
            service_id: 服务标识
            **kwargs: 服务参数

        Returns:
            服务执行结果
        """
        service = self._services.get(service_id)
        if not service:
            return {
                "success": False,
                "error": f"服务不存在: {service_id}",
                "available_services": list(self._services.keys()),
            }

        try:
            handler = service["handler"]
            result = await handler(**kwargs)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"服务执行失败: {str(e)}",
            }

    def get_service_descriptions(self) -> str:
        """获取所有服务的描述文本，用于RAG索引"""
        descriptions = []
        for service_id, service in self._services.items():
            desc = f"服务名称: {service['name']}\n"
            desc += f"服务ID: {service_id}\n"
            desc += f"描述: {service['description']}\n"
            desc += f"关键词: {', '.join(service['keywords'])}\n"
            descriptions.append(desc)
        return "\n---\n".join(descriptions)
