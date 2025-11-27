"""
文档加载器
支持加载各类文档用于RAG索引
"""
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Document:
    """文档数据类"""
    content: str
    metadata: dict
    doc_id: str
    doc_type: str = "text"


class DocumentLoader:
    """文档加载器"""

    def __init__(self):
        self._loaders = {
            ".json": self._load_json,
            ".txt": self._load_text,
            ".md": self._load_markdown,
        }

    def load_file(self, file_path: str | Path) -> list[Document]:
        """
        加载单个文件

        Args:
            file_path: 文件路径

        Returns:
            文档列表
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        loader = self._loaders.get(suffix)

        if loader is None:
            raise ValueError(f"不支持的文件类型: {suffix}")

        return loader(path)

    def load_directory(
        self,
        dir_path: str | Path,
        pattern: str = "*",
        recursive: bool = True,
    ) -> list[Document]:
        """
        加载目录下的所有文档

        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索

        Returns:
            文档列表
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")

        documents = []
        glob_func = path.rglob if recursive else path.glob

        for file_path in glob_func(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self._loaders:
                try:
                    docs = self.load_file(file_path)
                    documents.extend(docs)
                except Exception as e:
                    print(f"Warning: 加载文件失败 {file_path}: {e}")

        return documents

    def load_services(self, services: list[dict]) -> list[Document]:
        """
        从服务定义列表加载文档

        Args:
            services: 服务定义列表

        Returns:
            文档列表
        """
        documents = []

        for service in services:
            content = self._service_to_text(service)
            doc = Document(
                content=content,
                metadata={
                    "service_id": service.get("service_id", ""),
                    "name": service.get("name", ""),
                    "type": "service",
                    "keywords": service.get("keywords", []),
                },
                doc_id=f"service_{service.get('service_id', '')}",
                doc_type="service",
            )
            documents.append(doc)

        return documents

    def _service_to_text(self, service: dict) -> str:
        """将服务定义转换为文本"""
        parts = [
            f"服务名称: {service.get('name', '')}",
            f"服务ID: {service.get('service_id', '')}",
            f"描述: {service.get('description', '')}",
        ]

        keywords = service.get("keywords", [])
        if keywords:
            parts.append(f"关键词: {', '.join(keywords)}")

        parameters = service.get("parameters", {})
        if parameters:
            param_strs = []
            for name, info in parameters.items():
                param_desc = info.get("description", "") if isinstance(info, dict) else str(info)
                param_strs.append(f"  - {name}: {param_desc}")
            parts.append("参数:\n" + "\n".join(param_strs))

        returns = service.get("returns", {})
        if returns:
            return_strs = [f"  - {k}: {v}" for k, v in returns.items()]
            parts.append("返回值:\n" + "\n".join(return_strs))

        return "\n".join(parts)

    def _load_json(self, path: Path) -> list[Document]:
        """加载JSON文件"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []

        # 如果是服务定义列表
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    content = json.dumps(item, ensure_ascii=False, indent=2)
                    doc = Document(
                        content=content,
                        metadata={
                            "source": str(path),
                            "index": i,
                            **{k: v for k, v in item.items() if isinstance(v, (str, int, float, bool))},
                        },
                        doc_id=f"{path.stem}_{i}",
                        doc_type="json",
                    )
                    documents.append(doc)
        elif isinstance(data, dict):
            content = json.dumps(data, ensure_ascii=False, indent=2)
            doc = Document(
                content=content,
                metadata={"source": str(path)},
                doc_id=path.stem,
                doc_type="json",
            )
            documents.append(doc)

        return documents

    def _load_text(self, path: Path) -> list[Document]:
        """加载文本文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        doc = Document(
            content=content,
            metadata={"source": str(path)},
            doc_id=path.stem,
            doc_type="text",
        )
        return [doc]

    def _load_markdown(self, path: Path) -> list[Document]:
        """加载Markdown文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 按标题分割成多个文档
        documents = []
        sections = self._split_markdown_sections(content)

        for i, section in enumerate(sections):
            doc = Document(
                content=section["content"],
                metadata={
                    "source": str(path),
                    "title": section.get("title", ""),
                    "section_index": i,
                },
                doc_id=f"{path.stem}_section_{i}",
                doc_type="markdown",
            )
            documents.append(doc)

        return documents if documents else [Document(
            content=content,
            metadata={"source": str(path)},
            doc_id=path.stem,
            doc_type="markdown",
        )]

    def _split_markdown_sections(self, content: str) -> list[dict]:
        """分割Markdown为多个章节"""
        sections = []
        current_title = ""
        current_content = []

        for line in content.split("\n"):
            if line.startswith("# ") or line.startswith("## "):
                if current_content:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                    })
                current_title = line.lstrip("#").strip()
                current_content = [line]
            else:
                current_content.append(line)

        if current_content:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_content).strip(),
            })

        return sections


# 便捷函数
def load_services_from_registry(service_registry) -> list[Document]:
    """从服务注册表加载文档"""
    loader = DocumentLoader()
    services = service_registry.get_all_services()
    return loader.load_services(services)
