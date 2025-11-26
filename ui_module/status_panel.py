"""
状态面板组件
显示执行状态、进度和系统信息
"""
from typing import Optional
from datetime import datetime


class StatusPanel:
    """状态面板"""

    def __init__(self):
        self._current_status = "idle"
        self._progress = 0
        self._message = ""
        self._start_time: Optional[datetime] = None

    def start_processing(self, message: str = "处理中..."):
        """开始处理"""
        self._current_status = "processing"
        self._progress = 0
        self._message = message
        self._start_time = datetime.now()

    def update_progress(self, progress: int, message: str = None):
        """更新进度"""
        self._progress = min(100, max(0, progress))
        if message:
            self._message = message

    def complete(self, message: str = "完成"):
        """完成处理"""
        self._current_status = "completed"
        self._progress = 100
        self._message = message

    def error(self, message: str = "发生错误"):
        """错误状态"""
        self._current_status = "error"
        self._message = message

    def reset(self):
        """重置状态"""
        self._current_status = "idle"
        self._progress = 0
        self._message = ""
        self._start_time = None

    def render(self) -> str:
        """
        渲染状态面板

        Returns:
            Markdown格式的状态显示
        """
        status_emoji = {
            "idle": "⚪",
            "processing": "🔄",
            "completed": "✅",
            "error": "❌",
        }

        emoji = status_emoji.get(self._current_status, "⚪")

        # 进度条
        filled = int(self._progress / 10)
        empty = 10 - filled
        progress_bar = "█" * filled + "░" * empty

        # 计算耗时
        elapsed = ""
        if self._start_time:
            delta = datetime.now() - self._start_time
            elapsed = f" | 耗时: {delta.seconds}秒"

        return f"""**状态**: {emoji} {self._current_status.upper()}
**进度**: [{progress_bar}] {self._progress}%{elapsed}
**信息**: {self._message}"""


def render_execution_status(
    stage: str,
    steps: list[dict],
    current_step: int = 0,
) -> str:
    """
    渲染执行状态

    Args:
        stage: 当前阶段
        steps: 步骤列表
        current_step: 当前步骤索引

    Returns:
        Markdown格式的状态
    """
    md = f"### 执行状态: {stage}\n\n"

    for i, step in enumerate(steps):
        if i < current_step:
            status = "✅"
        elif i == current_step:
            status = "🔄"
        else:
            status = "⏳"

        md += f"{status} **Step {i+1}**: {step.get('name', '未知步骤')}\n"
        if step.get('description'):
            md += f"   {step['description']}\n"

    return md


def render_result_card(
    title: str,
    success: bool,
    data: dict,
    message: str = "",
) -> str:
    """
    渲染结果卡片

    Args:
        title: 标题
        success: 是否成功
        data: 结果数据
        message: 消息

    Returns:
        Markdown格式的结果卡片
    """
    status = "✅ 成功" if success else "❌ 失败"

    md = f"""### {title}

**状态**: {status}
"""

    if message:
        md += f"\n{message}\n"

    if data:
        md += "\n**详细信息**:\n"
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                continue  # 跳过复杂类型
            md += f"- **{key}**: {value}\n"

    return md


def render_flow_status(flow_name: str, stages: list[str], current_stage: str) -> str:
    """
    渲染流程状态

    Args:
        flow_name: 流程名称
        stages: 阶段列表
        current_stage: 当前阶段

    Returns:
        Markdown格式的流程状态
    """
    md = f"### {flow_name}\n\n"

    for i, stage in enumerate(stages):
        if stage == current_stage:
            md += f"**→ {i+1}. {stage}** (当前)\n"
        elif stages.index(current_stage) > i if current_stage in stages else False:
            md += f"✓ {i+1}. {stage}\n"
        else:
            md += f"○ {i+1}. {stage}\n"

    return md
