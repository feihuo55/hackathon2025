"""
反馈模块
用户反馈收集、处理和闭环学习
"""
from .feedback_collector import (
    FeedbackCollector,
    FeedbackContext,
    get_feedback_collector,
    collect_thumbs_up,
    collect_thumbs_down,
    collect_correction,
)

__all__ = [
    "FeedbackCollector",
    "FeedbackContext",
    "get_feedback_collector",
    "collect_thumbs_up",
    "collect_thumbs_down",
    "collect_correction",
]
