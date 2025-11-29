"""
Fund-related Mock Services
Static data for 5 hardcoded funds
"""
from datetime import datetime, timedelta
from typing import Optional


# Hardcoded fund data
FUND_DATA = {
    "161005": {
        "code": "161005",
        "name": "Fuguo Tianhui Growth Mixed Fund",
        "short_name": "Fuguo Tianhui",
        "type": "Mixed",
        "nav": 3.2156,
        "acc_nav": 5.8765,
        "change_pct": 2.35,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-12-15", "amount": 0.5, "type": "Cash Dividend"},
            {"date": "2023-06-15", "amount": 0.3, "type": "Cash Dividend"},
        ]
    },
    "110003": {
        "code": "110003",
        "name": "E Fund SSE 50 Index A",
        "short_name": "E Fund Blue Chip",
        "type": "Index",
        "nav": 1.8542,
        "acc_nav": 3.2156,
        "change_pct": -0.85,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-12-01", "amount": 0.2, "type": "Cash Dividend"},
        ]
    },
    "002001": {
        "code": "002001",
        "name": "China AMC Return Mixed Fund A",
        "short_name": "China AMC Return",
        "type": "Mixed",
        "nav": 1.5680,
        "acc_nav": 4.1250,
        "change_pct": 1.25,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-11-20", "amount": 0.15, "type": "Cash Dividend"},
            {"date": "2023-08-20", "amount": 0.12, "type": "Cash Dividend"},
            {"date": "2023-05-20", "amount": 0.10, "type": "Cash Dividend"},
        ]
    },
    "202003": {
        "code": "202003",
        "name": "China Southern Excellence Growth Mixed A",
        "short_name": "Southern Excellence",
        "type": "Mixed",
        "nav": 2.3456,
        "acc_nav": 4.5678,
        "change_pct": 0.56,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-10-10", "amount": 0.25, "type": "Cash Dividend"},
        ]
    },
    "160505": {
        "code": "160505",
        "name": "Bosera Theme Industry Mixed Fund",
        "short_name": "Bosera Theme",
        "type": "Mixed",
        "nav": 2.8910,
        "acc_nav": 5.1234,
        "change_pct": -1.20,
        "update_date": "2024-01-15",
        "dividends": [
            {"date": "2023-09-05", "amount": 0.35, "type": "Cash Dividend"},
            {"date": "2023-03-05", "amount": 0.30, "type": "Cash Dividend"},
        ]
    },
}

# Fund name to code mapping
FUND_NAME_MAP = {
    "Fuguo Tianhui": "161005",
    "Fuguo Tianhui Growth": "161005",
    "E Fund Blue Chip": "110003",
    "E Fund SSE 50": "110003",
    "China AMC Return": "002001",
    "China AMC Return Mixed": "002001",
    "Southern Excellence": "202003",
    "Southern Excellence Growth": "202003",
    "Bosera Theme": "160505",
    "Bosera Theme Industry": "160505",
}


class FundServices:
    """Fund Service Class"""

    @staticmethod
    def get_fund_code(name_or_code: str) -> Optional[str]:
        """Get fund code by name or code"""
        if name_or_code in FUND_DATA:
            return name_or_code
        return FUND_NAME_MAP.get(name_or_code)

    @staticmethod
    async def get_fund_nav(fund_code: str) -> dict:
        """
        Get fund NAV

        Args:
            fund_code: Fund code

        Returns:
            Dictionary containing NAV information
        """
        fund = FUND_DATA.get(fund_code)
        if not fund:
            return {
                "success": False,
                "error": f"Fund code not found: {fund_code}",
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
        Get fund dividend information

        Args:
            fund_code: Fund code

        Returns:
            Dictionary containing dividend information
        """
        fund = FUND_DATA.get(fund_code)
        if not fund:
            return {
                "success": False,
                "error": f"Fund code not found: {fund_code}",
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
        """Get all fund list"""
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
    async def get_fund_performance(fund_code: str) -> dict:
        """
        Get fund performance metrics

        Args:
            fund_code: Fund code

        Returns:
            Dictionary containing performance information
        """
        fund = FUND_DATA.get(fund_code)
        if not fund:
            return {
                "success": False,
                "error": f"Fund code not found: {fund_code}",
                "available_funds": list(FUND_DATA.keys()),
            }

        # Generate mock performance data based on fund data
        nav = fund["nav"]
        change_pct = fund["change_pct"]

        return {
            "success": True,
            "data": {
                "code": fund["code"],
                "name": fund["name"],
                "type": fund["type"],
                "current_nav": nav,
                "ytd_return": round(change_pct * 3.5, 2),  # Mock YTD return
                "one_year_return": round(change_pct * 8.2, 2),  # Mock 1Y return
                "three_year_return": round(change_pct * 15.6, 2),  # Mock 3Y return
                "benchmark_comparison": {
                    "benchmark": "CSI 300 Index",
                    "benchmark_return": round(change_pct * 2.1, 2),
                    "excess_return": round(change_pct * 1.4, 2),
                },
                "risk_metrics": {
                    "volatility": round(abs(change_pct) * 5, 2),
                    "sharpe_ratio": round(1.2 if change_pct > 0 else 0.8, 2),
                    "max_drawdown": round(abs(change_pct) * 3, 2),
                },
                "update_date": fund["update_date"],
            }
        }

    @staticmethod
    async def process_dividend(fund_codes: list[str], method: str = "cash") -> dict:
        """
        Process fund dividend

        Args:
            fund_codes: List of fund codes
            method: Dividend method (cash: Cash Dividend, reinvest: Dividend Reinvestment)

        Returns:
            Processing result
        """
        results = []
        total_amount = 0

        for code in fund_codes:
            fund = FUND_DATA.get(code)
            if fund and fund["dividends"]:
                latest_dividend = fund["dividends"][0]
                amount = latest_dividend["amount"] * 10000  # Assuming 10,000 shares held
                total_amount += amount
                results.append({
                    "code": code,
                    "name": fund["name"],
                    "dividend_date": latest_dividend["date"],
                    "dividend_amount": latest_dividend["amount"],
                    "total_amount": amount,
                    "method": "Cash Dividend" if method == "cash" else "Dividend Reinvestment",
                    "status": "Processed",
                })

        return {
            "success": True,
            "data": {
                "processed_count": len(results),
                "total_amount": total_amount,
                "details": results,
            }
        }
