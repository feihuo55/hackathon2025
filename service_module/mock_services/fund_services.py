"""
基金相关Mock服务
硬编码5只基金的静态数据
"""
from datetime import datetime, timedelta
from typing import Optional


# 硬编码的基金数据
FUND_DATA = {
    "161005": {
        "code": "161005",
        "name": "富国天惠成长混合",
        "short_name": "富国天惠",
        "type": "混合型",
        "nav": 3.2156,
        "acc_nav": 5.8765,
        "change_pct": 2.35,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-12-15", "amount": 0.5, "type": "现金分红"},
            {"date": "2023-06-15", "amount": 0.3, "type": "现金分红"},
        ]
    },
    "110003": {
        "code": "110003",
        "name": "易方达上证50指数A",
        "short_name": "易方达蓝筹",
        "type": "指数型",
        "nav": 1.8542,
        "acc_nav": 3.2156,
        "change_pct": -0.85,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-12-01", "amount": 0.2, "type": "现金分红"},
        ]
    },
    "002001": {
        "code": "002001",
        "name": "华夏回报混合A",
        "short_name": "华夏回报",
        "type": "混合型",
        "nav": 1.5680,
        "acc_nav": 4.1250,
        "change_pct": 1.25,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-11-20", "amount": 0.15, "type": "现金分红"},
            {"date": "2023-08-20", "amount": 0.12, "type": "现金分红"},
            {"date": "2023-05-20", "amount": 0.10, "type": "现金分红"},
        ]
    },
    "202003": {
        "code": "202003",
        "name": "南方绩优成长混合A",
        "short_name": "南方绩优",
        "type": "混合型",
        "nav": 2.3456,
        "acc_nav": 4.5678,
        "change_pct": 0.56,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-10-10", "amount": 0.25, "type": "现金分红"},
        ]
    },
    "160505": {
        "code": "160505",
        "name": "博时主题行业混合",
        "short_name": "博时主题",
        "type": "混合型",
        "nav": 2.8910,
        "acc_nav": 5.1234,
        "change_pct": -1.20,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-09-05", "amount": 0.35, "type": "现金分红"},
            {"date": "2023-03-05", "amount": 0.30, "type": "现金分红"},
        ]
    },
}

# 基金名称到代码的映射
FUND_NAME_MAP = {
    "富国天惠": "161005",
    "富国天惠成长混合": "161005",
    "易方达蓝筹": "110003",
    "易方达上证50": "110003",
    "华夏回报": "002001",
    "华夏回报混合": "002001",
    "南方绩优": "202003",
    "南方绩优成长": "202003",
    "博时主题": "160505",
    "博时主题行业": "160505",
}


class FundServices:
    """基金服务类"""

    @staticmethod
    def get_fund_code(name_or_code: str) -> Optional[str]:
        """根据名称或代码获取基金代码"""
        if name_or_code in FUND_DATA:
            return name_or_code
        return FUND_NAME_MAP.get(name_or_code)

    @staticmethod
    async def get_fund_nav(fund_code: str) -> dict:
        """
        获取基金净值

        Args:
            fund_code: 基金代码

        Returns:
            包含净值信息的字典
        """
        fund = FUND_DATA.get(fund_code)
        if not fund:
            return {
                "success": False,
                "error": f"未找到基金代码: {fund_code}",
                "available_funds": list(FUND_DATA.keys()),
            }

        return {
            "success": True,
            "data": {
                "code": fund["code"],
                "name": fund["name"],
                "nav": fund["nav"],
                "acc_nav": fund["acc_nav"],
                "change_pct": fund["change_pct"],
                "update_date": fund["update_date"],
            }
        }

    @staticmethod
    async def get_fund_dividend(fund_code: str) -> dict:
        """
        获取基金分红信息

        Args:
            fund_code: 基金代码

        Returns:
            包含分红信息的字典
        """
        fund = FUND_DATA.get(fund_code)
        if not fund:
            return {
                "success": False,
                "error": f"未找到基金代码: {fund_code}",
            }

        return {
            "success": True,
            "data": {
                "code": fund["code"],
                "name": fund["name"],
                "dividends": fund["dividends"],
                "total_dividend": sum(d["amount"] for d in fund["dividends"]),
            }
        }

    @staticmethod
    async def get_all_funds() -> dict:
        """获取所有基金列表"""
        funds = []
        for code, fund in FUND_DATA.items():
            funds.append({
                "code": code,
                "name": fund["name"],
                "short_name": fund["short_name"],
                "type": fund["type"],
            })
        return {
            "success": True,
            "data": funds,
        }

    @staticmethod
    async def process_dividend(fund_codes: list[str], method: str = "cash") -> dict:
        """
        处理基金分红

        Args:
            fund_codes: 基金代码列表
            method: 分红方式 (cash: 现金, reinvest: 再投资)

        Returns:
            处理结果
        """
        results = []
        total_amount = 0

        for code in fund_codes:
            fund = FUND_DATA.get(code)
            if fund and fund["dividends"]:
                latest_dividend = fund["dividends"][0]
                amount = latest_dividend["amount"] * 10000  # 假设持有1万份
                total_amount += amount
                results.append({
                    "code": code,
                    "name": fund["name"],
                    "dividend_date": latest_dividend["date"],
                    "dividend_amount": latest_dividend["amount"],
                    "total_amount": amount,
                    "method": "现金分红" if method == "cash" else "红利再投资",
                    "status": "已处理",
                })

        return {
            "success": True,
            "data": {
                "processed_count": len(results),
                "total_amount": total_amount,
                "details": results,
            }
        }
