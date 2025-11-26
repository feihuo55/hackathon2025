"""
服务构建智能体
根据SIPOC文档生成服务代码并注册
"""
import json
from typing import Optional
from .base_agent import BaseAgent
from service_module.sipoc.templates import SIPOCDocument


SERVICE_BUILDER_PROMPT = """你是一个服务构建专家，负责根据SIPOC流程文档生成可执行的服务代码。

你需要：
1. 分析SIPOC文档理解业务流程
2. 生成Python异步函数代码
3. 确保代码安全、可维护

生成的服务代码应该：
- 使用async/await语法
- 有清晰的文档字符串
- 包含适当的错误处理
- 返回标准格式的结果字典"""


class ServiceBuilder(BaseAgent):
    """服务构建智能体"""

    def __init__(self, service_registry=None):
        super().__init__(
            name="ServiceBuilder",
            description="根据SIPOC文档生成服务代码并注册",
            system_prompt=SERVICE_BUILDER_PROMPT,
        )
        self.registry = service_registry

    async def execute(self, input_data: dict) -> dict:
        """
        构建服务

        Args:
            input_data: 包含SIPOC文档和需求的字典

        Returns:
            构建结果
        """
        sipoc_data = input_data.get("sipoc", {})
        requirements = input_data.get("requirements", {})

        # 将字典转换为SIPOCDocument
        if isinstance(sipoc_data, dict):
            sipoc = SIPOCDocument.from_dict(sipoc_data)
        else:
            sipoc = sipoc_data

        # 生成服务定义
        service_def = await self._generate_service_definition(sipoc, requirements)

        # 生成服务代码（简化版，使用模板）
        service_code = await self._generate_service_code(sipoc, requirements)

        # 注册服务（如果有注册表）
        if self.registry and service_def:
            self._register_service(service_def, service_code)

        return {
            "success": True,
            "message": f"服务 '{service_def.get('name', '未知')}' 已成功创建",
            "service_definition": service_def,
            "service_code": service_code,
        }

    async def _generate_service_definition(
        self,
        sipoc: SIPOCDocument,
        requirements: dict,
    ) -> dict:
        """生成服务定义"""
        # 从SIPOC生成服务ID
        title = sipoc.title.replace(" ", "_").lower()
        service_id = f"auto_{title[:30]}"

        # 从输入生成参数定义
        parameters = {}
        for inp in sipoc.input:
            # 简单解析输入参数
            param_name = inp.replace(" ", "_").lower()[:20]
            parameters[param_name] = {
                "type": "string",
                "required": True,
                "description": inp,
            }

        # 从输出生成返回值定义
        returns = {}
        for out in sipoc.output:
            return_name = out.replace(" ", "_").lower()[:20]
            returns[return_name] = out

        return {
            "service_id": service_id,
            "name": sipoc.title,
            "description": sipoc.description,
            "parameters": parameters,
            "returns": returns,
            "keywords": [
                word for word in sipoc.title.split()
                if len(word) > 1
            ],
            "sipoc": sipoc.to_dict(),
        }

    async def _generate_service_code(
        self,
        sipoc: SIPOCDocument,
        requirements: dict,
    ) -> str:
        """生成服务代码"""
        # 对于基金分红处理，使用预定义模板
        creation_type = requirements.get("type", "")

        if creation_type == "dividend_processing":
            return self._generate_dividend_processing_code(sipoc)

        # 通用模板
        return self._generate_generic_service_code(sipoc)

    def _generate_dividend_processing_code(self, sipoc: SIPOCDocument) -> str:
        """生成分红处理服务代码"""
        code = '''
async def process_fund_dividend(fund_codes: list = None, method: str = "cash"):
    """
    基金分红处理服务

    Args:
        fund_codes: 基金代码列表，None表示全部
        method: 分红方式 (cash/reinvest)

    Returns:
        处理结果字典
    """
    from service_module.mock_services.fund_services import FundServices, FUND_DATA

    # 如果未指定基金，处理所有基金
    if fund_codes is None:
        fund_codes = list(FUND_DATA.keys())

    result = await FundServices.process_dividend(fund_codes, method)
    return result
'''
        return code

    def _generate_generic_service_code(self, sipoc: SIPOCDocument) -> str:
        """生成通用服务代码"""
        func_name = sipoc.title.replace(" ", "_").lower()[:30]

        # 生成参数列表
        params = []
        for inp in sipoc.input[:5]:  # 最多5个参数
            param_name = inp.replace(" ", "_").lower()[:15]
            params.append(f'{param_name}: str = ""')

        params_str = ", ".join(params) if params else ""

        # 生成处理步骤注释
        steps = "\n    ".join(
            f"# Step {i+1}: {step}"
            for i, step in enumerate(sipoc.process)
        )

        code = f'''
async def {func_name}({params_str}):
    """
    {sipoc.title}

    {sipoc.description}
    """
    {steps}

    # TODO: 实现具体业务逻辑
    return {{
        "success": True,
        "message": "服务执行完成",
        "data": {{}}
    }}
'''
        return code

    def _register_service(self, service_def: dict, service_code: str):
        """注册服务到注册表"""
        if not self.registry:
            return

        # 创建动态处理函数
        # 注意：这是简化实现，实际应使用更安全的方式
        async def dynamic_handler(**kwargs):
            return {
                "success": True,
                "message": f"动态服务 '{service_def['name']}' 执行完成",
                "data": kwargs,
            }

        self.registry.register(
            service_id=service_def["service_id"],
            name=service_def["name"],
            description=service_def["description"],
            handler=dynamic_handler,
            parameters=service_def["parameters"],
            returns=service_def["returns"],
            keywords=service_def.get("keywords", []),
        )

    async def build_and_execute(
        self,
        sipoc_data: dict,
        requirements: dict,
        execute_params: dict = None,
    ) -> dict:
        """
        构建并执行服务

        Args:
            sipoc_data: SIPOC文档数据
            requirements: 需求信息
            execute_params: 执行参数

        Returns:
            执行结果
        """
        # 先构建服务
        build_result = await self.execute({
            "sipoc": sipoc_data,
            "requirements": requirements,
        })

        if not build_result.get("success"):
            return build_result

        # 如果是分红处理，直接调用
        if requirements.get("type") == "dividend_processing":
            from service_module.mock_services.fund_services import FundServices, FUND_DATA

            fund_codes = execute_params.get("fund_codes") if execute_params else None
            if fund_codes is None:
                fund_codes = list(FUND_DATA.keys())

            method = execute_params.get("method", "cash") if execute_params else "cash"

            exec_result = await FundServices.process_dividend(fund_codes, method)

            return {
                "success": True,
                "message": "分红处理完成",
                "build_result": build_result,
                "execution_result": exec_result,
            }

        return {
            "success": True,
            "message": "服务已创建但未执行",
            "build_result": build_result,
        }
