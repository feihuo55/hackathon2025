"""
SIPOC文档生成器
基于需求自动生成SIPOC流程文档
"""
import json
from typing import Optional
from .templates import SIPOCDocument, SIPOCTemplates


class SIPOCGenerator:
    """SIPOC文档生成器"""

    def __init__(self, bedrock_client=None):
        """
        初始化生成器

        Args:
            bedrock_client: Bedrock客户端，用于AI生成
        """
        self.bedrock_client = bedrock_client
        self.templates = SIPOCTemplates()

    async def generate_from_requirements(
        self,
        requirements: dict,
        use_template: bool = True,
    ) -> SIPOCDocument:
        """
        根据需求生成SIPOC文档

        Args:
            requirements: 需求信息字典
            use_template: 是否使用预定义模板

        Returns:
            SIPOC文档
        """
        title = requirements.get("title", "")
        description = requirements.get("description", "")
        process_type = requirements.get("type", "")

        # 尝试匹配预定义模板
        if use_template:
            if "分红" in title or "dividend" in process_type.lower():
                return self.templates.fund_dividend_processing()
            elif "净值" in title or "nav" in process_type.lower():
                return self.templates.fund_nav_query()

        # 如果有Bedrock客户端，使用AI生成
        if self.bedrock_client:
            return await self._generate_with_ai(requirements)

        # 返回空模板
        return self.templates.empty_template(title, description)

    async def _generate_with_ai(self, requirements: dict) -> SIPOCDocument:
        """使用AI生成SIPOC文档"""
        prompt = f"""基于以下需求，生成一个SIPOC流程文档。

需求信息：
{json.dumps(requirements, ensure_ascii=False, indent=2)}

请以JSON格式返回SIPOC文档，包含以下字段：
- title: 流程标题
- description: 流程描述
- supplier: 供应商/数据来源列表
- input: 输入参数列表
- process: 处理步骤列表（按顺序）
- output: 输出结果列表
- customer: 客户/使用者列表

只返回JSON，不要其他内容。"""

        system_prompt = "你是一个专业的业务流程分析师，擅长设计SIPOC流程文档。请用中文回答。"

        try:
            response = await self.bedrock_client.invoke(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            # 解析JSON响应
            # 尝试提取JSON部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return SIPOCDocument.from_dict(data)
        except Exception as e:
            print(f"AI生成SIPOC失败: {e}")

        # 失败时返回空模板
        return self.templates.empty_template(
            requirements.get("title", "未知流程"),
            requirements.get("description", ""),
        )

    def render_markdown(self, sipoc: SIPOCDocument) -> str:
        """
        渲染SIPOC为Markdown格式

        Args:
            sipoc: SIPOC文档

        Returns:
            Markdown格式字符串
        """
        md = f"# {sipoc.title}\n\n"
        md += f"**描述**: {sipoc.description}\n\n"
        md += f"**状态**: {sipoc.status}\n\n"
        md += "---\n\n"

        # SIPOC表格
        md += "## SIPOC 流程图\n\n"
        md += "| S (Supplier) | I (Input) | P (Process) | O (Output) | C (Customer) |\n"
        md += "|--------------|-----------|-------------|------------|-------------|\n"

        # 计算最大行数
        max_rows = max(
            len(sipoc.supplier),
            len(sipoc.input),
            len(sipoc.process),
            len(sipoc.output),
            len(sipoc.customer),
            1,
        )

        for i in range(max_rows):
            s = sipoc.supplier[i] if i < len(sipoc.supplier) else ""
            inp = sipoc.input[i] if i < len(sipoc.input) else ""
            p = sipoc.process[i] if i < len(sipoc.process) else ""
            o = sipoc.output[i] if i < len(sipoc.output) else ""
            c = sipoc.customer[i] if i < len(sipoc.customer) else ""
            md += f"| {s} | {inp} | {p} | {o} | {c} |\n"

        md += f"\n---\n\n*创建时间: {sipoc.created_at}*\n"

        return md

    def render_html(self, sipoc: SIPOCDocument) -> str:
        """
        渲染SIPOC为HTML格式

        Args:
            sipoc: SIPOC文档

        Returns:
            HTML格式字符串
        """
        html = f"""
<div class="sipoc-container" style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; border-radius: 8px;">
    <h2 style="color: #1e40af; margin-bottom: 10px;">{sipoc.title}</h2>
    <p style="color: #666; margin-bottom: 20px;">{sipoc.description}</p>

    <div style="display: flex; gap: 10px; overflow-x: auto;">
        <div style="flex: 1; min-width: 150px; background: #dbeafe; padding: 15px; border-radius: 8px;">
            <h4 style="color: #1e40af; margin: 0 0 10px 0;">S - 供应商</h4>
            <ul style="margin: 0; padding-left: 20px;">
                {"".join(f"<li>{s}</li>" for s in sipoc.supplier)}
            </ul>
        </div>

        <div style="flex: 1; min-width: 150px; background: #dcfce7; padding: 15px; border-radius: 8px;">
            <h4 style="color: #166534; margin: 0 0 10px 0;">I - 输入</h4>
            <ul style="margin: 0; padding-left: 20px;">
                {"".join(f"<li>{i}</li>" for i in sipoc.input)}
            </ul>
        </div>

        <div style="flex: 1; min-width: 150px; background: #fef3c7; padding: 15px; border-radius: 8px;">
            <h4 style="color: #92400e; margin: 0 0 10px 0;">P - 流程</h4>
            <ol style="margin: 0; padding-left: 20px;">
                {"".join(f"<li>{p}</li>" for p in sipoc.process)}
            </ol>
        </div>

        <div style="flex: 1; min-width: 150px; background: #fce7f3; padding: 15px; border-radius: 8px;">
            <h4 style="color: #9d174d; margin: 0 0 10px 0;">O - 输出</h4>
            <ul style="margin: 0; padding-left: 20px;">
                {"".join(f"<li>{o}</li>" for o in sipoc.output)}
            </ul>
        </div>

        <div style="flex: 1; min-width: 150px; background: #e0e7ff; padding: 15px; border-radius: 8px;">
            <h4 style="color: #3730a3; margin: 0 0 10px 0;">C - 客户</h4>
            <ul style="margin: 0; padding-left: 20px;">
                {"".join(f"<li>{c}</li>" for c in sipoc.customer)}
            </ul>
        </div>
    </div>

    <p style="color: #999; font-size: 12px; margin-top: 15px;">创建时间: {sipoc.created_at}</p>
</div>
"""
        return html
