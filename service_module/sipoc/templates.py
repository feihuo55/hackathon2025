"""
SIPOC模板定义
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class SIPOCDocument:
    """SIPOC文档数据结构"""
    title: str
    description: str
    supplier: list[str] = field(default_factory=list)
    input: list[str] = field(default_factory=list)
    process: list[str] = field(default_factory=list)
    output: list[str] = field(default_factory=list)
    customer: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "draft"  # draft, pending_approval, approved, rejected

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "description": self.description,
            "supplier": self.supplier,
            "input": self.input,
            "process": self.process,
            "output": self.output,
            "customer": self.customer,
            "created_at": self.created_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SIPOCDocument":
        """从字典创建"""
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            supplier=data.get("supplier", []),
            input=data.get("input", []),
            process=data.get("process", []),
            output=data.get("output", []),
            customer=data.get("customer", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            status=data.get("status", "draft"),
        )


class SIPOCTemplates:
    """SIPOC模板集合"""

    @staticmethod
    def fund_dividend_processing() -> SIPOCDocument:
        """基金分红处理模板"""
        return SIPOCDocument(
            title="基金分红处理流程",
            description="批量处理基金分红派息的自动化流程",
            supplier=[
                "基金公司",
                "托管银行数据库",
                "投资者账户系统",
            ],
            input=[
                "分红基金列表",
                "分红方式(现金/再投资)",
                "权益登记日",
                "除息日",
            ],
            process=[
                "1. 获取待分红基金清单",
                "2. 验证基金分红信息",
                "3. 计算各账户分红金额",
                "4. 执行分红派发",
                "5. 更新账户余额",
                "6. 生成分红报告",
            ],
            output=[
                "分红处理结果",
                "账户余额变动记录",
                "分红报告",
            ],
            customer=[
                "投资者",
                "基金管理人",
                "监管机构",
            ],
        )

    @staticmethod
    def fund_nav_query() -> SIPOCDocument:
        """基金净值查询模板"""
        return SIPOCDocument(
            title="基金净值查询流程",
            description="查询指定基金的最新净值信息",
            supplier=[
                "基金估值系统",
                "行情数据源",
            ],
            input=[
                "基金代码/名称",
                "查询日期",
            ],
            process=[
                "1. 解析基金标识",
                "2. 查询净值数据",
                "3. 计算涨跌幅",
                "4. 格式化输出",
            ],
            output=[
                "单位净值",
                "累计净值",
                "涨跌幅",
                "更新时间",
            ],
            customer=[
                "投资者",
                "客户经理",
            ],
        )

    @staticmethod
    def empty_template(title: str, description: str) -> SIPOCDocument:
        """空白模板"""
        return SIPOCDocument(
            title=title,
            description=description,
            supplier=[],
            input=[],
            process=[],
            output=[],
            customer=[],
        )
