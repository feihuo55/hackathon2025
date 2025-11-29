"""
知识修正器
基于用户反馈自动优化和修正知识库内容

功能：
- 基于纠正反馈生成知识更新建议
- 自动识别需要更新的知识条目
- 支持知识版本管理
- 提供人工审核接口
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import difflib


class RefinementType(Enum):
    """修正类型"""
    UPDATE = "update"           # 更新现有知识
    ADD = "add"                 # 添加新知识
    DEPRECATE = "deprecate"     # 标记过时
    MERGE = "merge"             # 合并重复
    SPLIT = "split"             # 拆分过大条目
    ENHANCE = "enhance"         # 增强/补充信息
    CORRECT = "correct"         # 纠正错误


class RefinementStatus(Enum):
    """修正状态"""
    PENDING = "pending"         # 待审核
    APPROVED = "approved"       # 已批准
    REJECTED = "rejected"       # 已拒绝
    APPLIED = "applied"         # 已应用
    REVERTED = "reverted"       # 已回滚


@dataclass
class RefinementAction:
    """知识修正动作"""
    action_id: str
    refinement_type: RefinementType
    status: RefinementStatus = RefinementStatus.PENDING

    # 目标知识
    target_doc_id: Optional[str] = None
    target_content: Optional[str] = None

    # 修正内容
    new_content: Optional[str] = None
    change_description: str = ""

    # 来源信息
    source_query: Optional[str] = None
    source_feedback_ids: List[str] = field(default_factory=list)

    # 置信度和优先级
    confidence: float = 0.5         # 修正置信度
    priority: int = 0               # 优先级 (0-10)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    applied_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "refinement_type": self.refinement_type.value,
            "status": self.status.value,
            "target_doc_id": self.target_doc_id,
            "target_content": self.target_content,
            "new_content": self.new_content,
            "change_description": self.change_description,
            "source_query": self.source_query,
            "source_feedback_ids": self.source_feedback_ids,
            "confidence": self.confidence,
            "priority": self.priority,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "applied_at": self.applied_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RefinementAction":
        return cls(
            action_id=data["action_id"],
            refinement_type=RefinementType(data["refinement_type"]),
            status=RefinementStatus(data.get("status", "pending")),
            target_doc_id=data.get("target_doc_id"),
            target_content=data.get("target_content"),
            new_content=data.get("new_content"),
            change_description=data.get("change_description", ""),
            source_query=data.get("source_query"),
            source_feedback_ids=data.get("source_feedback_ids", []),
            confidence=data.get("confidence", 0.5),
            priority=data.get("priority", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            reviewed_at=data.get("reviewed_at"),
            reviewed_by=data.get("reviewed_by"),
            applied_at=data.get("applied_at"),
            metadata=data.get("metadata", {}),
        )


class KnowledgeRefiner:
    """
    知识修正器

    工作流程：
    1. 从反馈记忆收集用户纠正和负面反馈
    2. 分析反馈模式，识别需要修正的知识
    3. 生成修正建议（RefinementAction）
    4. 支持自动应用或人工审核
    5. 跟踪修正效果
    """

    def __init__(
        self,
        auto_apply_threshold: float = 0.9,
        min_feedback_count: int = 3,
        enable_auto_apply: bool = False,
    ):
        """
        初始化知识修正器

        Args:
            auto_apply_threshold: 自动应用的置信度阈值
            min_feedback_count: 触发修正的最小反馈数
            enable_auto_apply: 是否启用自动应用（默认需要人工审核）
        """
        self.auto_apply_threshold = auto_apply_threshold
        self.min_feedback_count = min_feedback_count
        self.enable_auto_apply = enable_auto_apply

        self._actions: List[RefinementAction] = []
        self._action_counter = 0
        self._knowledge_versions: Dict[str, List[Dict]] = {}  # doc_id -> [versions]
        self._apply_callbacks: List[Callable] = []

    def _generate_action_id(self) -> str:
        """生成动作ID"""
        self._action_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ref_{timestamp}_{self._action_counter}"

    def register_apply_callback(self, callback: Callable[[RefinementAction], bool]):
        """
        注册修正应用回调

        回调函数将在修正被应用时调用，用于实际更新知识库
        """
        self._apply_callbacks.append(callback)

    def create_correction_action(
        self,
        query: str,
        original_response: str,
        correction_text: str,
        target_doc_id: Optional[str] = None,
        feedback_ids: Optional[List[str]] = None,
    ) -> RefinementAction:
        """
        基于用户纠正创建修正动作

        Args:
            query: 原始查询
            original_response: 原始回复
            correction_text: 用户提供的正确信息
            target_doc_id: 相关文档ID
            feedback_ids: 相关反馈ID列表

        Returns:
            创建的修正动作
        """
        # 计算修正置信度
        confidence = self._calculate_correction_confidence(
            query, original_response, correction_text
        )

        action = RefinementAction(
            action_id=self._generate_action_id(),
            refinement_type=RefinementType.CORRECT,
            target_doc_id=target_doc_id,
            target_content=original_response,
            new_content=correction_text,
            change_description=f"用户纠正: 查询'{query[:50]}...'的回复需要更新",
            source_query=query,
            source_feedback_ids=feedback_ids or [],
            confidence=confidence,
            priority=self._calculate_priority(confidence, len(feedback_ids or [])),
        )

        self._actions.append(action)

        # 检查是否自动应用
        if self.enable_auto_apply and confidence >= self.auto_apply_threshold:
            self.apply_action(action.action_id)

        return action

    def create_knowledge_addition(
        self,
        query: str,
        new_knowledge: str,
        category: str = "general",
        feedback_ids: Optional[List[str]] = None,
    ) -> RefinementAction:
        """
        创建知识添加动作

        当用户反馈表明缺少某类信息时使用
        """
        action = RefinementAction(
            action_id=self._generate_action_id(),
            refinement_type=RefinementType.ADD,
            new_content=new_knowledge,
            change_description=f"添加新知识: 基于查询'{query[:50]}...'",
            source_query=query,
            source_feedback_ids=feedback_ids or [],
            confidence=0.6,  # 新增知识默认需要审核
            priority=5,
            metadata={"category": category},
        )

        self._actions.append(action)
        return action

    def create_enhancement_action(
        self,
        doc_id: str,
        current_content: str,
        enhancement: str,
        reason: str,
        feedback_ids: Optional[List[str]] = None,
    ) -> RefinementAction:
        """
        创建知识增强动作

        用于补充现有知识条目的信息
        """
        # 合并内容
        enhanced_content = f"{current_content}\n\n补充信息：{enhancement}"

        action = RefinementAction(
            action_id=self._generate_action_id(),
            refinement_type=RefinementType.ENHANCE,
            target_doc_id=doc_id,
            target_content=current_content,
            new_content=enhanced_content,
            change_description=f"增强知识: {reason}",
            source_feedback_ids=feedback_ids or [],
            confidence=0.7,
            priority=4,
        )

        self._actions.append(action)
        return action

    def create_deprecation_action(
        self,
        doc_id: str,
        content: str,
        reason: str,
        feedback_ids: Optional[List[str]] = None,
    ) -> RefinementAction:
        """
        创建知识废弃动作

        当知识过时或不再准确时使用
        """
        action = RefinementAction(
            action_id=self._generate_action_id(),
            refinement_type=RefinementType.DEPRECATE,
            target_doc_id=doc_id,
            target_content=content,
            change_description=f"标记废弃: {reason}",
            source_feedback_ids=feedback_ids or [],
            confidence=0.5,  # 废弃需要谨慎，默认需要审核
            priority=3,
        )

        self._actions.append(action)
        return action

    def _calculate_correction_confidence(
        self,
        query: str,
        original: str,
        correction: str,
    ) -> float:
        """
        计算纠正的置信度

        基于：
        1. 纠正内容的长度和质量
        2. 与原始内容的差异程度
        """
        # 基础分
        confidence = 0.5

        # 纠正内容长度合理性
        if 10 < len(correction) < 1000:
            confidence += 0.1

        # 检查纠正是否包含具体信息
        if any(char.isdigit() for char in correction):
            confidence += 0.1  # 包含数字，可能是具体数据

        # 计算与原始内容的差异
        similarity = difflib.SequenceMatcher(
            None, original.lower(), correction.lower()
        ).ratio()

        # 差异太小可能是无效纠正，差异太大可能是完全错误
        if 0.2 < similarity < 0.8:
            confidence += 0.2

        return min(1.0, confidence)

    def _calculate_priority(self, confidence: float, feedback_count: int) -> int:
        """计算优先级"""
        # 基于置信度和反馈数量
        base = int(confidence * 5)
        feedback_bonus = min(5, feedback_count)
        return min(10, base + feedback_bonus)

    def analyze_feedback_patterns(
        self,
        feedbacks: List[Dict],
        min_occurrences: int = 2,
    ) -> List[RefinementAction]:
        """
        分析反馈模式，自动生成修正建议

        Args:
            feedbacks: 反馈列表
            min_occurrences: 最小出现次数

        Returns:
            生成的修正动作列表
        """
        actions = []

        # 按查询分组
        query_feedbacks: Dict[str, List[Dict]] = {}
        for fb in feedbacks:
            query = fb.get("query", "")[:100]
            if query not in query_feedbacks:
                query_feedbacks[query] = []
            query_feedbacks[query].append(fb)

        for query, fbs in query_feedbacks.items():
            if len(fbs) < min_occurrences:
                continue

            # 统计反馈类型
            negative_count = sum(
                1 for f in fbs
                if f.get("feedback_type") in ["negative", "irrelevant"]
            )
            correction_count = sum(
                1 for f in fbs if f.get("feedback_type") == "correction"
            )

            # 如果负面反馈超过阈值，建议检查该查询的相关知识
            if negative_count >= min_occurrences:
                action = RefinementAction(
                    action_id=self._generate_action_id(),
                    refinement_type=RefinementType.UPDATE,
                    source_query=query,
                    change_description=f"查询'{query[:30]}...'收到{negative_count}次负面反馈，建议审查相关知识",
                    source_feedback_ids=[f.get("feedback_id", "") for f in fbs],
                    confidence=min(0.9, 0.5 + negative_count * 0.1),
                    priority=min(10, 3 + negative_count),
                    metadata={"negative_count": negative_count},
                )
                actions.append(action)
                self._actions.append(action)

            # 如果有纠正，创建纠正动作
            corrections = [f for f in fbs if f.get("correction_text")]
            if corrections:
                # 使用最新的纠正
                latest = corrections[-1]
                action = self.create_correction_action(
                    query=query,
                    original_response=latest.get("response", ""),
                    correction_text=latest.get("correction_text", ""),
                    feedback_ids=[f.get("feedback_id", "") for f in corrections],
                )
                actions.append(action)

        return actions

    def get_action(self, action_id: str) -> Optional[RefinementAction]:
        """获取修正动作"""
        for action in self._actions:
            if action.action_id == action_id:
                return action
        return None

    def get_pending_actions(
        self,
        min_priority: int = 0,
        limit: int = 20,
    ) -> List[RefinementAction]:
        """获取待审核的修正动作"""
        pending = [
            a for a in self._actions
            if a.status == RefinementStatus.PENDING and a.priority >= min_priority
        ]
        pending.sort(key=lambda x: (-x.priority, x.created_at))
        return pending[:limit]

    def approve_action(
        self,
        action_id: str,
        reviewer: str = "system",
    ) -> bool:
        """批准修正动作"""
        action = self.get_action(action_id)
        if not action or action.status != RefinementStatus.PENDING:
            return False

        action.status = RefinementStatus.APPROVED
        action.reviewed_at = datetime.now().isoformat()
        action.reviewed_by = reviewer

        return True

    def reject_action(
        self,
        action_id: str,
        reviewer: str = "system",
        reason: str = "",
    ) -> bool:
        """拒绝修正动作"""
        action = self.get_action(action_id)
        if not action or action.status != RefinementStatus.PENDING:
            return False

        action.status = RefinementStatus.REJECTED
        action.reviewed_at = datetime.now().isoformat()
        action.reviewed_by = reviewer
        action.metadata["rejection_reason"] = reason

        return True

    def apply_action(
        self,
        action_id: str,
    ) -> bool:
        """
        应用修正动作

        实际的知识库更新通过注册的回调函数执行
        """
        action = self.get_action(action_id)
        if not action:
            return False

        if action.status not in [RefinementStatus.PENDING, RefinementStatus.APPROVED]:
            return False

        # 保存版本历史
        if action.target_doc_id and action.target_content:
            self._save_version(action.target_doc_id, action.target_content)

        # 执行回调
        success = True
        for callback in self._apply_callbacks:
            try:
                if not callback(action):
                    success = False
                    break
            except Exception as e:
                action.metadata["apply_error"] = str(e)
                success = False
                break

        if success:
            action.status = RefinementStatus.APPLIED
            action.applied_at = datetime.now().isoformat()
        else:
            action.metadata["apply_failed"] = True

        return success

    def revert_action(self, action_id: str) -> bool:
        """回滚修正动作"""
        action = self.get_action(action_id)
        if not action or action.status != RefinementStatus.APPLIED:
            return False

        # 检查是否有版本历史可回滚
        if action.target_doc_id:
            versions = self._knowledge_versions.get(action.target_doc_id, [])
            if versions:
                # 这里只标记状态，实际回滚需要通过回调
                action.status = RefinementStatus.REVERTED
                action.metadata["reverted_at"] = datetime.now().isoformat()
                return True

        return False

    def _save_version(self, doc_id: str, content: str):
        """保存知识版本"""
        if doc_id not in self._knowledge_versions:
            self._knowledge_versions[doc_id] = []

        self._knowledge_versions[doc_id].append({
            "content": content,
            "saved_at": datetime.now().isoformat(),
        })

        # 限制版本数量
        if len(self._knowledge_versions[doc_id]) > 10:
            self._knowledge_versions[doc_id] = self._knowledge_versions[doc_id][-10:]

    def get_version_history(self, doc_id: str) -> List[Dict]:
        """获取知识版本历史"""
        return self._knowledge_versions.get(doc_id, [])

    def get_statistics(self) -> Dict:
        """获取修正器统计"""
        status_counts = {}
        type_counts = {}

        for action in self._actions:
            status = action.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            rtype = action.refinement_type.value
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        return {
            "total_actions": len(self._actions),
            "by_status": status_counts,
            "by_type": type_counts,
            "pending_count": status_counts.get("pending", 0),
            "applied_count": status_counts.get("applied", 0),
            "versioned_documents": len(self._knowledge_versions),
        }

    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "actions": [a.to_dict() for a in self._actions],
            "knowledge_versions": self._knowledge_versions,
            "action_counter": self._action_counter,
        }

    def from_dict(self, data: Dict):
        """从字典导入"""
        self._actions = [
            RefinementAction.from_dict(a) for a in data.get("actions", [])
        ]
        self._knowledge_versions = data.get("knowledge_versions", {})
        self._action_counter = data.get("action_counter", 0)

    def clear(self):
        """清空修正器数据"""
        self._actions.clear()
        self._knowledge_versions.clear()

    def export_pending_for_review(self) -> List[Dict]:
        """导出待审核项（用于人工审核界面）"""
        pending = self.get_pending_actions(limit=50)
        return [
            {
                "action_id": a.action_id,
                "type": a.refinement_type.value,
                "description": a.change_description,
                "confidence": a.confidence,
                "priority": a.priority,
                "target_doc_id": a.target_doc_id,
                "current_content": a.target_content[:200] if a.target_content else None,
                "suggested_content": a.new_content[:200] if a.new_content else None,
                "source_query": a.source_query,
                "created_at": a.created_at,
            }
            for a in pending
        ]


# 全局修正器实例
_knowledge_refiner: Optional[KnowledgeRefiner] = None


def get_knowledge_refiner() -> KnowledgeRefiner:
    """获取全局知识修正器"""
    global _knowledge_refiner
    if _knowledge_refiner is None:
        _knowledge_refiner = KnowledgeRefiner()
    return _knowledge_refiner
