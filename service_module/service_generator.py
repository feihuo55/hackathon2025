"""
动态服务生成器
根据SIPOC文档动态生成服务代码
"""
from typing import Optional, Callable, Any
from .sipoc.templates import SIPOCDocument


class ServiceGenerator:
    """动态服务生成器"""

    def __init__(self, service_registry=None):
        """
        初始化服务生成器

        Args:
            service_registry: 服务注册表
        """
        self.registry = service_registry
        self._generated_services: dict = {}

    def generate_service(
        self,
        sipoc: SIPOCDocument,
        service_id: Optional[str] = None,
    ) -> dict:
        """
        根据SIPOC生成服务定义

        Args:
            sipoc: SIPOC文档
            service_id: 服务ID（可选）

        Returns:
            服务定义字典
        """
        if not service_id:
            service_id = self._generate_service_id(sipoc.title)

        # 从SIPOC输入生成参数
        parameters = {}
        for inp in sipoc.input:
            param_name = self._sanitize_name(inp)
            parameters[param_name] = {
                "type": "string",
                "required": True,
                "description": inp,
            }

        # 从SIPOC输出生成返回值定义
        returns = {}
        for out in sipoc.output:
            return_name = self._sanitize_name(out)
            returns[return_name] = out

        service_def = {
            "service_id": service_id,
            "name": sipoc.title,
            "description": sipoc.description,
            "parameters": parameters,
            "returns": returns,
            "process_steps": sipoc.process,
            "sipoc": sipoc.to_dict(),
        }

        self._generated_services[service_id] = service_def
        return service_def

    def generate_handler(
        self,
        service_def: dict,
    ) -> Callable:
        """
        生成服务处理函数

        Args:
            service_def: 服务定义

        Returns:
            异步处理函数
        """
        async def handler(**kwargs) -> dict:
            """动态生成的服务处理函数"""
            # 这是一个占位实现
            # 实际应用中需要根据具体业务逻辑实现
            return {
                "success": True,
                "message": f"服务 '{service_def['name']}' 执行完成",
                "input": kwargs,
                "process_steps": service_def.get("process_steps", []),
            }

        return handler

    def register_service(
        self,
        sipoc: SIPOCDocument,
        service_id: Optional[str] = None,
    ) -> str:
        """
        生成并注册服务

        Args:
            sipoc: SIPOC文档
            service_id: 服务ID（可选）

        Returns:
            注册的服务ID
        """
        service_def = self.generate_service(sipoc, service_id)
        handler = self.generate_handler(service_def)

        if self.registry:
            self.registry.register(
                service_id=service_def["service_id"],
                name=service_def["name"],
                description=service_def["description"],
                handler=handler,
                parameters=service_def["parameters"],
                returns=service_def["returns"],
            )

        return service_def["service_id"]

    def _generate_service_id(self, title: str) -> str:
        """生成服务ID"""
        base_id = self._sanitize_name(title)
        return f"auto_{base_id}"

    def _sanitize_name(self, name: str) -> str:
        """清理名称为有效的标识符"""
        # 移除特殊字符，转换空格为下划线
        sanitized = name.replace(" ", "_").replace("-", "_")
        # 只保留字母数字和下划线
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        return sanitized[:30].lower()

    def get_generated_services(self) -> dict:
        """获取所有已生成的服务"""
        return self._generated_services.copy()
