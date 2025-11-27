"""
程序记忆
存储操作流程、技能和执行步骤
支持JSON文件持久化
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from collections import OrderedDict

# 延迟导入持久化模块
_persistence_module = None


def _get_persistence():
    """延迟加载持久化模块"""
    global _persistence_module
    if _persistence_module is None:
        try:
            from .persistence import get_persistence, ProceduralPersistence
            _persistence_module = (get_persistence, ProceduralPersistence)
        except ImportError:
            pass
    return _persistence_module


@dataclass
class Procedure:
    """程序/流程定义"""
    procedure_id: str
    name: str
    description: str
    steps: list[dict]
    parameters: dict = field(default_factory=dict)
    success_count: int = 0
    failure_count: int = 0
    last_executed: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "procedure_id": self.procedure_id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "parameters": self.parameters,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "last_executed": self.last_executed,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class ProceduralMemory:
    """程序记忆系统 - 存储操作流程和技能"""

    def __init__(
        self,
        max_procedures: int = 100,
        enable_persistence: bool = True,
        storage_dir: str = "./data/memory",
    ):
        """
        初始化程序记忆

        Args:
            max_procedures: 最大存储流程数
            enable_persistence: 是否启用持久化
            storage_dir: 存储目录
        """
        self.max_procedures = max_procedures
        self._procedures: OrderedDict[str, Procedure] = OrderedDict()
        self._enable_persistence = enable_persistence
        self._persistence = None
        self._storage_dir = storage_dir

        # 尝试加载已有数据
        if enable_persistence:
            self._load_from_disk()

    def store_procedure(
        self,
        procedure_id: str,
        name: str,
        description: str,
        steps: list[dict],
        parameters: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Procedure:
        """
        存储流程

        Args:
            procedure_id: 流程唯一标识
            name: 流程名称
            description: 流程描述
            steps: 执行步骤列表
            parameters: 参数定义
            metadata: 额外元数据

        Returns:
            存储的流程对象
        """
        procedure = Procedure(
            procedure_id=procedure_id,
            name=name,
            description=description,
            steps=steps,
            parameters=parameters or {},
            metadata=metadata or {},
        )

        # 如果已存在则更新
        if procedure_id in self._procedures:
            existing = self._procedures[procedure_id]
            procedure.success_count = existing.success_count
            procedure.failure_count = existing.failure_count
            procedure.last_executed = existing.last_executed

        self._procedures[procedure_id] = procedure

        # 限制数量
        while len(self._procedures) > self.max_procedures:
            self._procedures.popitem(last=False)

        # 自动保存
        self._save_to_disk()

        return procedure

    def get_procedure(self, procedure_id: str) -> Optional[Procedure]:
        """获取流程"""
        return self._procedures.get(procedure_id)

    def find_procedure(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[Procedure]:
        """
        查找相关流程

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            匹配的流程列表
        """
        query_lower = query.lower()
        scored_procedures = []

        for procedure in self._procedures.values():
            score = 0

            # 名称匹配
            if query_lower in procedure.name.lower():
                score += 3

            # 描述匹配
            if query_lower in procedure.description.lower():
                score += 2

            # 关键词匹配
            for word in query_lower.split():
                if word in procedure.name.lower():
                    score += 1
                if word in procedure.description.lower():
                    score += 0.5

            # 成功率加权
            score *= (1 + procedure.success_rate * 0.5)

            if score > 0:
                scored_procedures.append((procedure, score))

        # 按分数排序
        scored_procedures.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in scored_procedures[:top_k]]

    def record_execution(
        self,
        procedure_id: str,
        success: bool,
        execution_time: Optional[float] = None,
        result: Optional[dict] = None,
    ):
        """
        记录执行结果

        Args:
            procedure_id: 流程ID
            success: 是否成功
            execution_time: 执行时间（秒）
            result: 执行结果
        """
        procedure = self._procedures.get(procedure_id)
        if not procedure:
            return

        if success:
            procedure.success_count += 1
        else:
            procedure.failure_count += 1

        procedure.last_executed = datetime.now().isoformat()

        # 记录执行历史到metadata
        if "execution_history" not in procedure.metadata:
            procedure.metadata["execution_history"] = []

        history_entry = {
            "timestamp": procedure.last_executed,
            "success": success,
            "execution_time": execution_time,
        }

        if result:
            history_entry["result_summary"] = str(result)[:200]

        procedure.metadata["execution_history"].append(history_entry)

        # 限制历史记录数量
        if len(procedure.metadata["execution_history"]) > 20:
            procedure.metadata["execution_history"] = procedure.metadata["execution_history"][-20:]

        # 自动保存
        self._save_to_disk()

    def get_best_procedure(self, query: str) -> Optional[Procedure]:
        """
        获取最佳匹配的流程

        Args:
            query: 查询文本

        Returns:
            最佳匹配的流程
        """
        procedures = self.find_procedure(query, top_k=1)
        return procedures[0] if procedures else None

    def get_recently_used(self, n: int = 5) -> list[Procedure]:
        """
        获取最近使用的流程

        Args:
            n: 数量

        Returns:
            流程列表
        """
        executed_procedures = [
            p for p in self._procedures.values()
            if p.last_executed is not None
        ]

        executed_procedures.sort(
            key=lambda x: x.last_executed or "",
            reverse=True
        )

        return executed_procedures[:n]

    def get_most_successful(self, n: int = 5) -> list[Procedure]:
        """
        获取成功率最高的流程

        Args:
            n: 数量

        Returns:
            流程列表
        """
        procedures = list(self._procedures.values())
        procedures.sort(key=lambda x: x.success_rate, reverse=True)
        return procedures[:n]

    def delete_procedure(self, procedure_id: str):
        """删除流程"""
        self._procedures.pop(procedure_id, None)

    def update_procedure(
        self,
        procedure_id: str,
        **updates,
    ) -> Optional[Procedure]:
        """
        更新流程

        Args:
            procedure_id: 流程ID
            **updates: 更新字段

        Returns:
            更新后的流程
        """
        procedure = self._procedures.get(procedure_id)
        if not procedure:
            return None

        for key, value in updates.items():
            if hasattr(procedure, key):
                setattr(procedure, key, value)

        return procedure

    def get_all_procedures(self) -> list[Procedure]:
        """获取所有流程"""
        return list(self._procedures.values())

    def count(self) -> int:
        """获取流程数量"""
        return len(self._procedures)

    def clear(self):
        """清空程序记忆"""
        self._procedures.clear()
        self._save_to_disk()

    def _get_persistence_helper(self):
        """获取持久化助手"""
        if not self._enable_persistence:
            return None

        if self._persistence is None:
            pm = _get_persistence()
            if pm:
                get_persistence, ProceduralPersistence = pm
                persistence = get_persistence(self._storage_dir)
                self._persistence = ProceduralPersistence(persistence)

        return self._persistence

    def _load_from_disk(self):
        """从磁盘加载数据"""
        helper = self._get_persistence_helper()
        if helper:
            try:
                data = helper.load_procedures()
                if data:
                    self.from_dict(data)
            except Exception as e:
                print(f"Warning: 加载程序记忆失败: {e}")

    def _save_to_disk(self):
        """保存数据到磁盘"""
        helper = self._get_persistence_helper()
        if helper:
            try:
                helper.save_procedures(self.to_dict())
            except Exception as e:
                print(f"Warning: 保存程序记忆失败: {e}")

    def save(self):
        """手动保存到磁盘"""
        self._save_to_disk()

    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            pid: p.to_dict()
            for pid, p in self._procedures.items()
        }

    def from_dict(self, data: dict):
        """从字典导入"""
        for pid, pdata in data.items():
            procedure = Procedure(
                procedure_id=pdata["procedure_id"],
                name=pdata["name"],
                description=pdata["description"],
                steps=pdata["steps"],
                parameters=pdata.get("parameters", {}),
                success_count=pdata.get("success_count", 0),
                failure_count=pdata.get("failure_count", 0),
                last_executed=pdata.get("last_executed"),
                created_at=pdata.get("created_at", datetime.now().isoformat()),
                metadata=pdata.get("metadata", {}),
            )
            self._procedures[pid] = procedure

    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = len(self._procedures)
        if total == 0:
            return {
                "total_procedures": 0,
                "avg_success_rate": 0,
                "most_used": None,
            }

        total_executions = sum(
            p.success_count + p.failure_count
            for p in self._procedures.values()
        )

        most_used = max(
            self._procedures.values(),
            key=lambda x: x.success_count + x.failure_count,
            default=None
        )

        return {
            "total_procedures": total,
            "total_executions": total_executions,
            "avg_success_rate": sum(p.success_rate for p in self._procedures.values()) / total,
            "most_used": most_used.name if most_used else None,
        }
