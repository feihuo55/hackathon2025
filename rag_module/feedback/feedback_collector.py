"""
反馈收集器
提供用户界面层的反馈收集接口

功能：
- 提供简洁的反馈收集API
- 自动关联反馈到相关记忆层
- 触发学习和知识修正流程
- 支持异步和同步操作
"""
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio

from ..memory.feedback_memory import (
    FeedbackMemory,
    FeedbackType,
    FeedbackSource,
    Feedback,
)
from ..learning.relevance_learner import RelevanceLearner, get_relevance_learner
from ..learning.knowledge_refiner import KnowledgeRefiner, get_knowledge_refiner


@dataclass
class FeedbackContext:
    """反馈上下文，保存当前交互信息"""
    query: str
    response: str
    retrieved_doc_ids: List[str]
    intent: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class FeedbackCollector:
    """
    反馈收集器

    统一管理用户反馈的收集、处理和分发

    使用示例：
    ```python
    collector = FeedbackCollector()

    # 设置当前交互上下文
    collector.set_context(
        query="查询基金净值",
        response="基金161005的净值是1.234",
        retrieved_doc_ids=["doc_001", "doc_002"]
    )

    # 收集反馈
    await collector.thumbs_up()  # 正面反馈
    await collector.thumbs_down()  # 负面反馈
    await collector.submit_correction("正确的净值是1.235")  # 纠正
    ```
    """

    def __init__(
        self,
        feedback_memory: Optional[FeedbackMemory] = None,
        relevance_learner: Optional[RelevanceLearner] = None,
        knowledge_refiner: Optional[KnowledgeRefiner] = None,
        auto_trigger_learning: bool = True,
    ):
        """
        初始化反馈收集器

        Args:
            feedback_memory: 反馈记忆实例
            relevance_learner: 相关性学习器实例
            knowledge_refiner: 知识修正器实例
            auto_trigger_learning: 是否自动触发学习流程
        """
        self.feedback_memory = feedback_memory or FeedbackMemory()
        self.relevance_learner = relevance_learner or get_relevance_learner()
        self.knowledge_refiner = knowledge_refiner or get_knowledge_refiner()
        self.auto_trigger_learning = auto_trigger_learning

        self._current_context: Optional[FeedbackContext] = None
        self._feedback_callbacks: List[Callable[[Feedback], None]] = []

    def set_context(
        self,
        query: str,
        response: str,
        retrieved_doc_ids: Optional[List[str]] = None,
        intent: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        设置当前交互上下文

        每次用户交互后调用，为后续反馈收集准备上下文
        """
        self._current_context = FeedbackContext(
            query=query,
            response=response,
            retrieved_doc_ids=retrieved_doc_ids or [],
            intent=intent,
            session_id=session_id,
        )

    def clear_context(self):
        """清除当前上下文"""
        self._current_context = None

    def register_callback(self, callback: Callable[[Feedback], None]):
        """注册反馈回调（当收到反馈时触发）"""
        self._feedback_callbacks.append(callback)

    def _trigger_callbacks(self, feedback: Feedback):
        """触发所有回调"""
        for callback in self._feedback_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                print(f"Feedback callback error: {e}")

    async def _process_feedback(self, feedback: Feedback):
        """处理反馈：触发学习和修正流程"""
        if not self.auto_trigger_learning:
            return

        # 1. 更新相关性学习器
        if feedback.retrieved_doc_ids:
            if feedback.feedback_type in [FeedbackType.POSITIVE, FeedbackType.PERFECT]:
                self.relevance_learner.add_positive_feedback(
                    feedback.query,
                    feedback.retrieved_doc_ids,
                )
            elif feedback.feedback_type in [FeedbackType.NEGATIVE, FeedbackType.IRRELEVANT]:
                self.relevance_learner.add_negative_feedback(
                    feedback.query,
                    feedback.retrieved_doc_ids,
                )

        # 2. 处理纠正反馈
        if feedback.feedback_type == FeedbackType.CORRECTION and feedback.correction_text:
            self.knowledge_refiner.create_correction_action(
                query=feedback.query,
                original_response=feedback.response,
                correction_text=feedback.correction_text,
                target_doc_id=feedback.retrieved_doc_ids[0] if feedback.retrieved_doc_ids else None,
                feedback_ids=[feedback.feedback_id],
            )

        # 3. 触发回调
        self._trigger_callbacks(feedback)

    async def thumbs_up(self) -> Optional[Feedback]:
        """
        👍 正面反馈

        表示用户对回复满意
        """
        if not self._current_context:
            return None

        feedback = self.feedback_memory.add_positive_feedback(
            query=self._current_context.query,
            response=self._current_context.response,
            retrieved_doc_ids=self._current_context.retrieved_doc_ids,
            session_id=self._current_context.session_id,
            intent=self._current_context.intent,
        )

        await self._process_feedback(feedback)
        return feedback

    async def thumbs_down(self) -> Optional[Feedback]:
        """
        👎 负面反馈

        表示用户对回复不满意
        """
        if not self._current_context:
            return None

        feedback = self.feedback_memory.add_negative_feedback(
            query=self._current_context.query,
            response=self._current_context.response,
            retrieved_doc_ids=self._current_context.retrieved_doc_ids,
            session_id=self._current_context.session_id,
            intent=self._current_context.intent,
        )

        await self._process_feedback(feedback)
        return feedback

    async def submit_correction(
        self,
        correction_text: str,
    ) -> Optional[Feedback]:
        """
        ✏️ 提交纠正

        用户提供正确答案
        """
        if not self._current_context:
            return None

        feedback = self.feedback_memory.add_correction(
            query=self._current_context.query,
            response=self._current_context.response,
            correction_text=correction_text,
            retrieved_doc_ids=self._current_context.retrieved_doc_ids,
            session_id=self._current_context.session_id,
            intent=self._current_context.intent,
        )

        await self._process_feedback(feedback)
        return feedback

    async def mark_docs_relevant(
        self,
        doc_ids: List[str],
    ) -> Optional[Feedback]:
        """标记文档为相关"""
        if not self._current_context:
            return None

        feedback = self.feedback_memory.add_feedback(
            query=self._current_context.query,
            response=self._current_context.response,
            feedback_type=FeedbackType.POSITIVE,
            source=FeedbackSource.USER_EXPLICIT,
            retrieved_doc_ids=self._current_context.retrieved_doc_ids,
            relevant_doc_ids=doc_ids,
            session_id=self._current_context.session_id,
        )

        await self._process_feedback(feedback)
        return feedback

    async def mark_docs_irrelevant(
        self,
        doc_ids: List[str],
    ) -> Optional[Feedback]:
        """标记文档为不相关"""
        if not self._current_context:
            return None

        feedback = self.feedback_memory.add_feedback(
            query=self._current_context.query,
            response=self._current_context.response,
            feedback_type=FeedbackType.IRRELEVANT,
            source=FeedbackSource.USER_EXPLICIT,
            retrieved_doc_ids=self._current_context.retrieved_doc_ids,
            irrelevant_doc_ids=doc_ids,
            session_id=self._current_context.session_id,
        )

        await self._process_feedback(feedback)
        return feedback

    async def submit_rating(
        self,
        rating: int,
        comment: Optional[str] = None,
    ) -> Optional[Feedback]:
        """
        提交评分反馈 (1-5分)

        Args:
            rating: 1-5 分
            comment: 可选评论
        """
        if not self._current_context:
            return None

        # 映射评分到反馈类型和分数
        if rating >= 4:
            feedback_type = FeedbackType.POSITIVE
            score = 0.5 + (rating - 3) * 0.25  # 4->0.75, 5->1.0
        elif rating <= 2:
            feedback_type = FeedbackType.NEGATIVE
            score = -0.5 - (3 - rating) * 0.25  # 2->-0.75, 1->-1.0
        else:
            feedback_type = FeedbackType.PARTIAL
            score = 0.0

        metadata = {"rating": rating}
        if comment:
            metadata["comment"] = comment

        feedback = self.feedback_memory.add_feedback(
            query=self._current_context.query,
            response=self._current_context.response,
            feedback_type=feedback_type,
            source=FeedbackSource.USER_EXPLICIT,
            score=score,
            retrieved_doc_ids=self._current_context.retrieved_doc_ids,
            session_id=self._current_context.session_id,
            metadata=metadata,
        )

        await self._process_feedback(feedback)
        return feedback

    def should_prompt_feedback(self) -> bool:
        """
        判断是否应该提示用户提供反馈

        基于查询历史表现决定
        """
        if not self._current_context:
            return False
        return self.feedback_memory.should_request_feedback(
            self._current_context.query
        )

    def get_feedback_prompt_message(self) -> str:
        """获取反馈提示消息"""
        if self.should_prompt_feedback():
            return "这个回答对您有帮助吗？您的反馈可以帮助我们改进服务。"
        return ""

    def get_statistics(self) -> Dict:
        """获取反馈统计"""
        return {
            "feedback_memory": self.feedback_memory.get_statistics(),
            "relevance_learner": self.relevance_learner.get_statistics(),
            "knowledge_refiner": self.knowledge_refiner.get_statistics(),
        }

    def get_improvement_suggestions(self) -> List[Dict]:
        """获取改进建议"""
        return self.feedback_memory.get_improvement_suggestions()

    def get_pending_corrections(self) -> List[Dict]:
        """获取待处理的纠正"""
        return self.knowledge_refiner.export_pending_for_review()

    # ============ 同步方法（用于非异步环境） ============

    def thumbs_up_sync(self) -> Optional[Feedback]:
        """同步版本的正面反馈"""
        return asyncio.get_event_loop().run_until_complete(self.thumbs_up())

    def thumbs_down_sync(self) -> Optional[Feedback]:
        """同步版本的负面反馈"""
        return asyncio.get_event_loop().run_until_complete(self.thumbs_down())

    def submit_correction_sync(self, correction_text: str) -> Optional[Feedback]:
        """同步版本的纠正提交"""
        return asyncio.get_event_loop().run_until_complete(
            self.submit_correction(correction_text)
        )


# 全局反馈收集器实例
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """获取全局反馈收集器"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector


# ============ 便捷函数（用于UI层直接调用） ============

async def collect_thumbs_up(
    query: str,
    response: str,
    retrieved_doc_ids: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Optional[Feedback]:
    """便捷函数：收集正面反馈"""
    collector = get_feedback_collector()
    collector.set_context(
        query=query,
        response=response,
        retrieved_doc_ids=retrieved_doc_ids,
        session_id=session_id,
    )
    return await collector.thumbs_up()


async def collect_thumbs_down(
    query: str,
    response: str,
    retrieved_doc_ids: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Optional[Feedback]:
    """便捷函数：收集负面反馈"""
    collector = get_feedback_collector()
    collector.set_context(
        query=query,
        response=response,
        retrieved_doc_ids=retrieved_doc_ids,
        session_id=session_id,
    )
    return await collector.thumbs_down()


async def collect_correction(
    query: str,
    response: str,
    correction_text: str,
    retrieved_doc_ids: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Optional[Feedback]:
    """便捷函数：收集纠正反馈"""
    collector = get_feedback_collector()
    collector.set_context(
        query=query,
        response=response,
        retrieved_doc_ids=retrieved_doc_ids,
        session_id=session_id,
    )
    return await collector.submit_correction(correction_text)
