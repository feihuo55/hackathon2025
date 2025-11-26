"""
SIPOC可视化组件
在Chainlit中展示SIPOC文档
"""
from typing import Union
from service_module.sipoc.templates import SIPOCDocument


def render_sipoc(sipoc_data: Union[dict, SIPOCDocument]) -> str:
    """
    渲染SIPOC文档为Markdown格式

    Args:
        sipoc_data: SIPOC数据（字典或SIPOCDocument对象）

    Returns:
        Markdown格式的SIPOC展示
    """
    if isinstance(sipoc_data, SIPOCDocument):
        sipoc = sipoc_data
    else:
        sipoc = SIPOCDocument.from_dict(sipoc_data)

    # 构建Markdown表格
    md = f"""## {sipoc.title}

> {sipoc.description}

### SIPOC 流程图

| Supplier (供应商) | Input (输入) | Process (流程) | Output (输出) | Customer (客户) |
|:-----------------|:-------------|:---------------|:--------------|:----------------|
"""

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

    md += f"\n---\n*状态: {sipoc.status} | 创建时间: {sipoc.created_at}*"

    return md


def render_sipoc_card(sipoc_data: Union[dict, SIPOCDocument]) -> str:
    """
    渲染SIPOC为卡片格式

    Args:
        sipoc_data: SIPOC数据

    Returns:
        卡片格式的展示
    """
    if isinstance(sipoc_data, SIPOCDocument):
        sipoc = sipoc_data
    else:
        sipoc = SIPOCDocument.from_dict(sipoc_data)

    cards = f"""## {sipoc.title}

{sipoc.description}

---

### S - 供应商 (Supplier)
"""
    for s in sipoc.supplier:
        cards += f"- {s}\n"

    cards += "\n### I - 输入 (Input)\n"
    for i in sipoc.input:
        cards += f"- {i}\n"

    cards += "\n### P - 流程 (Process)\n"
    for idx, p in enumerate(sipoc.process, 1):
        cards += f"{idx}. {p}\n"

    cards += "\n### O - 输出 (Output)\n"
    for o in sipoc.output:
        cards += f"- {o}\n"

    cards += "\n### C - 客户 (Customer)\n"
    for c in sipoc.customer:
        cards += f"- {c}\n"

    return cards


def render_process_flow(sipoc_data: Union[dict, SIPOCDocument]) -> str:
    """
    渲染流程步骤为可视化流程图（文本版）

    Args:
        sipoc_data: SIPOC数据

    Returns:
        文本流程图
    """
    if isinstance(sipoc_data, SIPOCDocument):
        sipoc = sipoc_data
    else:
        sipoc = SIPOCDocument.from_dict(sipoc_data)

    flow = f"## {sipoc.title} - 流程图\n\n"
    flow += "```\n"

    # 绘制简单的ASCII流程图
    for idx, step in enumerate(sipoc.process):
        if idx == 0:
            flow += f"  ┌─────────────────────────────────────┐\n"
            flow += f"  │  {step[:35]:35s} │\n"
            flow += f"  └───────────────────┬─────────────────┘\n"
        elif idx == len(sipoc.process) - 1:
            flow += f"                      │\n"
            flow += f"                      ▼\n"
            flow += f"  ┌─────────────────────────────────────┐\n"
            flow += f"  │  {step[:35]:35s} │\n"
            flow += f"  └─────────────────────────────────────┘\n"
        else:
            flow += f"                      │\n"
            flow += f"                      ▼\n"
            flow += f"  ┌─────────────────────────────────────┐\n"
            flow += f"  │  {step[:35]:35s} │\n"
            flow += f"  └───────────────────┬─────────────────┘\n"

    flow += "```\n"

    return flow


async def show_sipoc_with_confirmation(sipoc_data: dict) -> dict:
    """
    展示SIPOC并请求确认

    Args:
        sipoc_data: SIPOC数据

    Returns:
        包含渲染内容和确认提示的字典
    """
    rendered = render_sipoc(sipoc_data)

    return {
        "content": rendered,
        "confirmation_prompt": "请确认以上流程是否正确？（回复'确认'继续，或描述需要修改的内容）",
        "sipoc": sipoc_data,
    }
