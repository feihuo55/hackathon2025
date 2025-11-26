"""
消息处理器
处理Chainlit消息的格式化和路由
"""
from typing import Optional, Callable, Awaitable

try:
    import chainlit as cl
except ImportError:
    cl = None  # Chainlit not installed


class ChatHandler:
    """消息处理器"""

    def __init__(self):
        self._message_handlers: dict[str, Callable] = {}

    def register_handler(
        self,
        intent_type: str,
        handler: Callable[[str, dict], Awaitable[dict]],
    ):
        """
        注册消息处理器

        Args:
            intent_type: 意图类型
            handler: 处理函数
        """
        self._message_handlers[intent_type] = handler

    async def handle_message(
        self,
        message: str,
        intent_result: dict,
    ) -> dict:
        """
        处理消息

        Args:
            message: 用户消息
            intent_result: 意图识别结果

        Returns:
            处理结果
        """
        intent_type = intent_result.get("type", "unknown")
        handler = self._message_handlers.get(intent_type)

        if handler:
            return await handler(message, intent_result)

        return {
            "success": False,
            "message": "无法处理此类型的请求",
        }


async def send_thinking_message(content: str = "Processing..."):
    """
    发送思考中消息

    Args:
        content: 消息内容

    Returns:
        Chainlit消息对象
    """
    if cl is None:
        return None
    msg = cl.Message(content=content)
    await msg.send()
    return msg


async def update_message(msg, content: str):
    """
    更新消息内容

    Args:
        msg: 消息对象
        content: 新内容
    """
    if msg is None:
        return
    await msg.update(content=content)


async def send_result_message(
    result: dict,
    show_raw: bool = False,
):
    """
    发送结果消息

    Args:
        result: 处理结果
        show_raw: 是否显示原始数据

    Returns:
        Chainlit消息对象
    """
    message = result.get("message", "Done")

    if show_raw and result.get("data"):
        message += f"\n\n```json\n{result['data']}\n```"

    if cl is None:
        return None
    msg = cl.Message(content=message)
    await msg.send()
    return msg


async def send_error_message(error: str):
    """
    发送错误消息

    Args:
        error: 错误信息

    Returns:
        Chainlit消息对象
    """
    if cl is None:
        return None
    msg = cl.Message(content=f"**Error**: {error}")
    await msg.send()
    return msg


async def send_confirmation_request(
    content: str,
    options: list[str] = None,
):
    """
    发送确认请求

    Args:
        content: 确认内容
        options: 可选项

    Returns:
        Chainlit消息对象
    """
    message = content

    if options:
        message += "\n\nPlease select:"
        for i, opt in enumerate(options, 1):
            message += f"\n{i}. {opt}"

    if cl is None:
        return None
    msg = cl.Message(content=message)
    await msg.send()
    return msg


def format_fund_result(data: dict) -> str:
    """
    格式化基金查询结果

    Args:
        data: 基金数据

    Returns:
        格式化的字符串
    """
    change_emoji = "📈" if data.get("change_pct", 0) >= 0 else "📉"
    change_sign = "+" if data.get("change_pct", 0) >= 0 else ""

    return f"""### {data.get('name', '未知基金')} ({data.get('code', '')})

| 指标 | 数值 |
|------|------|
| 单位净值 | **{data.get('nav', 'N/A')}** |
| 累计净值 | {data.get('acc_nav', 'N/A')} |
| 涨跌幅 | {change_emoji} {change_sign}{data.get('change_pct', 'N/A')}% |
| 更新日期 | {data.get('update_date', 'N/A')} |"""


def format_dividend_result(data: dict) -> str:
    """
    格式化分红查询结果

    Args:
        data: 分红数据

    Returns:
        格式化的字符串
    """
    lines = [f"### {data.get('name', '未知基金')} - 分红记录\n"]
    lines.append(f"**累计分红**: {data.get('total_dividend', 0):.2f} 元/份\n")

    dividends = data.get("dividends", [])
    if dividends:
        lines.append("\n| 分红日期 | 分红金额 | 分红类型 |")
        lines.append("|----------|----------|----------|")
        for d in dividends:
            lines.append(f"| {d['date']} | {d['amount']} 元/份 | {d['type']} |")

    return "\n".join(lines)


def format_processing_result(data: dict) -> str:
    """
    格式化处理结果

    Args:
        data: 处理结果数据

    Returns:
        格式化的字符串
    """
    lines = ["### 处理完成\n"]
    lines.append(f"- **处理数量**: {data.get('processed_count', 0)}")
    lines.append(f"- **总金额**: ¥{data.get('total_amount', 0):,.2f}\n")

    details = data.get("details", [])
    if details:
        lines.append("\n| 基金 | 金额 | 方式 | 状态 |")
        lines.append("|------|------|------|------|")
        for d in details:
            lines.append(
                f"| {d.get('name', '')} | ¥{d.get('total_amount', 0):,.2f} | "
                f"{d.get('method', '')} | {d.get('status', '')} |"
            )

    return "\n".join(lines)
