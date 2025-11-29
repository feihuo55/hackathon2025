"""
SIPOC Template Definitions
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class SIPOCDocument:
    """SIPOC Document Data Structure"""
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
        """Convert to dictionary"""
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
        """Create from dictionary"""
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
    """SIPOC Template Collection"""

    @staticmethod
    def fund_dividend_processing() -> SIPOCDocument:
        """Fund Dividend Processing Template"""
        return SIPOCDocument(
            title="Fund Dividend Processing Workflow",
            description="Automated workflow for batch processing fund dividend distributions",
            supplier=[
                "Fund Company",
                "Custody Bank Database",
                "Investor Account System",
            ],
            input=[
                "Dividend Fund List",
                "Distribution Method (Cash/Reinvest)",
                "Record Date",
                "Ex-Dividend Date",
            ],
            process=[
                "1. Retrieve pending dividend fund list",
                "2. Validate fund dividend information",
                "3. Calculate dividend amount per account",
                "4. Execute dividend distribution",
                "5. Update account balances",
                "6. Generate dividend report",
            ],
            output=[
                "Dividend Processing Results",
                "Account Balance Change Records",
                "Dividend Report",
            ],
            customer=[
                "Investors",
                "Fund Managers",
                "Regulatory Authorities",
            ],
        )

    @staticmethod
    def fund_nav_query() -> SIPOCDocument:
        """Fund NAV Query Template"""
        return SIPOCDocument(
            title="Fund NAV Query Workflow",
            description="Query the latest NAV information for specified funds",
            supplier=[
                "Fund Valuation System",
                "Market Data Source",
            ],
            input=[
                "Fund Code/Name",
                "Query Date",
            ],
            process=[
                "1. Parse fund identifier",
                "2. Query NAV data",
                "3. Calculate price change percentage",
                "4. Format output",
            ],
            output=[
                "Unit NAV",
                "Cumulative NAV",
                "Price Change %",
                "Update Time",
            ],
            customer=[
                "Investors",
                "Account Managers",
            ],
        )

    @staticmethod
    def compliance_report_processing() -> SIPOCDocument:
        """Compliance Report Processing Template"""
        return SIPOCDocument(
            title="Compliance Report Processing Workflow",
            description="Process and submit monthly compliance reports to regulatory authorities",
            supplier=[
                "Fund Company",
                "Custody Bank Compliance System",
                "Document Management System",
            ],
            input=[
                "Fund Transaction Records",
                "Compliance Checklist",
                "Report Period (Month/Quarter)",
                "Regulatory Requirements",
            ],
            process=[
                "1. Collect fund transaction data",
                "2. Validate against compliance rules",
                "3. Generate compliance report",
                "4. Review and approve report",
                "5. Submit to regulatory authority",
                "6. Archive report documents",
            ],
            output=[
                "Compliance Report Document",
                "Submission Confirmation",
                "Audit Trail Records",
            ],
            customer=[
                "Regulatory Authorities",
                "Compliance Officers",
                "Fund Managers",
            ],
        )

    @staticmethod
    def fund_performance_query() -> SIPOCDocument:
        """Fund Performance Query Template"""
        return SIPOCDocument(
            title="Fund Performance Query Workflow",
            description="Query fund performance metrics including returns and benchmark comparison",
            supplier=[
                "Fund Performance System",
                "Benchmark Data Provider",
                "Market Data Source",
            ],
            input=[
                "Fund Code/Name",
                "Query Period",
                "Benchmark Index",
            ],
            process=[
                "1. Parse fund identifier",
                "2. Retrieve historical performance data",
                "3. Calculate returns (YTD, 1Y, 3Y, etc.)",
                "4. Compare with benchmark",
                "5. Format performance report",
            ],
            output=[
                "Performance Metrics",
                "Benchmark Comparison",
                "Performance Chart Data",
                "Risk Statistics",
            ],
            customer=[
                "Investors",
                "Fund Managers",
                "Financial Advisors",
            ],
        )

    @staticmethod
    def generic_email_processing(email_subject: str, email_summary: str) -> SIPOCDocument:
        """Generate SIPOC based on email content"""
        return SIPOCDocument(
            title=f"Email Processing: {email_subject[:50]}",
            description=f"Automated processing workflow for: {email_summary[:100]}",
            supplier=[
                "Email Sender",
                "Custody Bank Systems",
                "Data Sources",
            ],
            input=[
                "Email Content",
                "Attachments (if any)",
                "Request Details",
            ],
            process=[
                "1. Parse email content and extract requirements",
                "2. Validate request information",
                "3. Process request based on requirements",
                "4. Execute corresponding service",
                "5. Generate response/report",
            ],
            output=[
                "Processing Results",
                "Response Report",
                "Status Update",
            ],
            customer=[
                "Email Sender",
                "Related Stakeholders",
            ],
        )

    @staticmethod
    def empty_template(title: str, description: str) -> SIPOCDocument:
        """Empty Template"""
        return SIPOCDocument(
            title=title,
            description=description,
            supplier=[],
            input=[],
            process=[],
            output=[],
            customer=[],
        )
