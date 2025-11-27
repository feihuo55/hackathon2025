"""
记忆持久化存储
支持JSON文件存储和加载
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
import threading


class MemoryPersistence:
    """记忆持久化管理器"""

    def __init__(
        self,
        storage_dir: str = "./data/memory",
        auto_save: bool = True,
        auto_save_interval: int = 60,
    ):
        """
        初始化持久化管理器

        Args:
            storage_dir: 存储目录
            auto_save: 是否自动保存
            auto_save_interval: 自动保存间隔（秒）
        """
        self.storage_dir = Path(storage_dir)
        self.auto_save = auto_save
        self.auto_save_interval = auto_save_interval
        self._last_save_time: dict[str, datetime] = {}
        self._dirty: dict[str, bool] = {}
        self._lock = threading.Lock()

        # 确保存储目录存在
        self._ensure_dir()

    def _ensure_dir(self):
        """确保存储目录存在"""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: 无法创建存储目录 {self.storage_dir}: {e}")

    def _get_file_path(self, memory_type: str) -> Path:
        """获取存储文件路径"""
        return self.storage_dir / f"{memory_type}.json"

    def save(self, memory_type: str, data: Any) -> bool:
        """
        保存数据到文件

        Args:
            memory_type: 记忆类型 (episodic, semantic, procedural, summary)
            data: 要保存的数据

        Returns:
            是否成功
        """
        with self._lock:
            try:
                file_path = self._get_file_path(memory_type)

                # 构建存储结构
                storage_data = {
                    "version": "1.0",
                    "memory_type": memory_type,
                    "saved_at": datetime.now().isoformat(),
                    "data": data,
                }

                # 先写入临时文件，再重命名（原子操作）
                temp_path = file_path.with_suffix(".tmp")
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(storage_data, f, ensure_ascii=False, indent=2)

                # 重命名为正式文件
                temp_path.replace(file_path)

                self._last_save_time[memory_type] = datetime.now()
                self._dirty[memory_type] = False

                return True
            except Exception as e:
                print(f"Warning: 保存 {memory_type} 失败: {e}")
                return False

    def load(self, memory_type: str) -> Optional[Any]:
        """
        从文件加载数据

        Args:
            memory_type: 记忆类型

        Returns:
            加载的数据，失败返回None
        """
        with self._lock:
            try:
                file_path = self._get_file_path(memory_type)

                if not file_path.exists():
                    return None

                with open(file_path, "r", encoding="utf-8") as f:
                    storage_data = json.load(f)

                return storage_data.get("data")
            except Exception as e:
                print(f"Warning: 加载 {memory_type} 失败: {e}")
                return None

    def exists(self, memory_type: str) -> bool:
        """检查存储文件是否存在"""
        return self._get_file_path(memory_type).exists()

    def delete(self, memory_type: str) -> bool:
        """
        删除存储文件

        Args:
            memory_type: 记忆类型

        Returns:
            是否成功
        """
        try:
            file_path = self._get_file_path(memory_type)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Warning: 删除 {memory_type} 失败: {e}")
            return False

    def mark_dirty(self, memory_type: str):
        """标记数据已更改，需要保存"""
        self._dirty[memory_type] = True

    def is_dirty(self, memory_type: str) -> bool:
        """检查数据是否需要保存"""
        return self._dirty.get(memory_type, False)

    def should_auto_save(self, memory_type: str) -> bool:
        """检查是否应该自动保存"""
        if not self.auto_save:
            return False
        if not self.is_dirty(memory_type):
            return False

        last_save = self._last_save_time.get(memory_type)
        if not last_save:
            return True

        elapsed = (datetime.now() - last_save).total_seconds()
        return elapsed >= self.auto_save_interval

    def get_storage_info(self) -> dict:
        """获取存储信息"""
        info = {
            "storage_dir": str(self.storage_dir),
            "files": [],
        }

        try:
            for file_path in self.storage_dir.glob("*.json"):
                stat = file_path.stat()
                info["files"].append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        except Exception:
            pass

        return info

    def export_all(self) -> dict:
        """导出所有记忆数据"""
        all_data = {}
        memory_types = ["episodic", "semantic", "procedural", "summary"]

        for memory_type in memory_types:
            data = self.load(memory_type)
            if data is not None:
                all_data[memory_type] = data

        return all_data

    def import_all(self, data: dict) -> dict[str, bool]:
        """
        导入所有记忆数据

        Args:
            data: 要导入的数据

        Returns:
            各类型的导入结果
        """
        results = {}
        for memory_type, memory_data in data.items():
            results[memory_type] = self.save(memory_type, memory_data)
        return results


class EpisodicPersistence:
    """事件记忆持久化助手"""

    def __init__(self, persistence: MemoryPersistence):
        self.persistence = persistence
        self.memory_type = "episodic"

    def save_entries(self, entries: list[dict]) -> bool:
        """保存事件记录"""
        return self.persistence.save(self.memory_type, {"entries": entries})

    def load_entries(self) -> list[dict]:
        """加载事件记录"""
        data = self.persistence.load(self.memory_type)
        if data:
            return data.get("entries", [])
        return []


class ProceduralPersistence:
    """程序记忆持久化助手"""

    def __init__(self, persistence: MemoryPersistence):
        self.persistence = persistence
        self.memory_type = "procedural"

    def save_procedures(self, procedures: dict) -> bool:
        """保存流程数据"""
        return self.persistence.save(self.memory_type, {"procedures": procedures})

    def load_procedures(self) -> dict:
        """加载流程数据"""
        data = self.persistence.load(self.memory_type)
        if data:
            return data.get("procedures", {})
        return {}


class SummaryPersistence:
    """摘要记忆持久化助手"""

    def __init__(self, persistence: MemoryPersistence):
        self.persistence = persistence
        self.memory_type = "summary"

    def save_summaries(self, summaries: list[dict]) -> bool:
        """保存摘要数据"""
        return self.persistence.save(self.memory_type, {"summaries": summaries})

    def load_summaries(self) -> list[dict]:
        """加载摘要数据"""
        data = self.persistence.load(self.memory_type)
        if data:
            return data.get("summaries", [])
        return []


# 全局持久化实例
_default_persistence: Optional[MemoryPersistence] = None


def get_persistence(storage_dir: str = "./data/memory") -> MemoryPersistence:
    """获取全局持久化实例"""
    global _default_persistence
    if _default_persistence is None:
        _default_persistence = MemoryPersistence(storage_dir=storage_dir)
    return _default_persistence
