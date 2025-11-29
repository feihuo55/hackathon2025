"""
Workflow Executor Service
Executes workflow steps based on SIPOC process definitions
Returns mock data for each step without affecting existing functionality
"""
from datetime import datetime
from typing import Optional
from .fund_services import FundServices, FUND_DATA


class WorkflowStepResult:
    """Result of a single workflow step execution"""
    def __init__(self, step_number: int, step_name: str, status: str,
                 data: dict = None, message: str = ""):
        self.step_number = step_number
        self.step_name = step_name
        self.status = status  # "completed", "in_progress", "pending", "error"
        self.data = data or {}
        self.message = message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "stepNumber": self.step_number,
            "stepName": self.step_name,
            "status": self.status,
            "data": self.data,
            "message": self.message,
            "timestamp": self.timestamp
        }


class WorkflowExecutor:
    """
    Executes SIPOC-based workflows with mock data
    Maps process steps to corresponding mock service calls
    """

    # Mock investor accounts for dividend processing
    MOCK_INVESTOR_ACCOUNTS = [
        {"account_id": "ACC001", "investor_name": "John Smith", "shares": 15000, "account_type": "Individual"},
        {"account_id": "ACC002", "investor_name": "China Pension Fund", "shares": 500000, "account_type": "Institutional"},
        {"account_id": "ACC003", "investor_name": "Jane Doe", "shares": 8000, "account_type": "Individual"},
        {"account_id": "ACC004", "investor_name": "Global Investment Ltd", "shares": 250000, "account_type": "Institutional"},
        {"account_id": "ACC005", "investor_name": "Robert Chen", "shares": 12000, "account_type": "Individual"},
    ]

    @classmethod
    async def execute_workflow(cls, sipoc: dict) -> dict:
        """
        Execute a complete workflow based on SIPOC definition

        Args:
            sipoc: SIPOC document dictionary with suppliers, inputs, process, outputs, customers

        Returns:
            Complete execution result with all step results
        """
        process_steps = sipoc.get("process", [])
        workflow_type = cls._detect_workflow_type(sipoc)

        step_results = []
        execution_data = {}  # Shared data across steps

        for i, step in enumerate(process_steps, 1):
            step_name = cls._extract_step_name(step)
            result = await cls._execute_step(
                step_number=i,
                step_name=step_name,
                step_description=step,
                workflow_type=workflow_type,
                execution_data=execution_data,
                sipoc=sipoc
            )
            step_results.append(result.to_dict())

            # Update shared execution data
            if result.data:
                execution_data.update(result.data)

        # Generate final summary
        summary = cls._generate_summary(workflow_type, step_results, execution_data)

        return {
            "success": True,
            "workflowType": workflow_type,
            "totalSteps": len(process_steps),
            "completedSteps": len([r for r in step_results if r["status"] == "completed"]),
            "stepResults": step_results,
            "summary": summary,
            "executionData": execution_data,
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def _detect_workflow_type(cls, sipoc: dict) -> str:
        """Detect workflow type from SIPOC content"""
        title = sipoc.get("title", "").lower()
        process_str = str(sipoc.get("process", [])).lower()

        if "dividend" in title or "dividend" in process_str:
            return "dividend_processing"
        elif "nav" in title or "nav" in process_str:
            return "nav_query"
        elif "compliance" in title or "compliance" in process_str:
            return "compliance_report"
        elif "performance" in title or "performance" in process_str:
            return "performance_query"
        else:
            return "generic_workflow"

    @classmethod
    def _extract_step_name(cls, step: str) -> str:
        """Extract clean step name from step description"""
        # Remove numbering like "1. " or "Step 1: "
        import re
        cleaned = re.sub(r'^[\d]+[\.\):\s]+', '', step)
        cleaned = re.sub(r'^Step\s+[\d]+[\.\):\s]+', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @classmethod
    async def _execute_step(cls, step_number: int, step_name: str, step_description: str,
                           workflow_type: str, execution_data: dict, sipoc: dict) -> WorkflowStepResult:
        """Execute a single workflow step with mock data"""

        step_lower = step_name.lower()

        # Route to appropriate handler based on workflow type and step content
        if workflow_type == "dividend_processing":
            return await cls._execute_dividend_step(step_number, step_name, step_lower, execution_data)
        elif workflow_type == "nav_query":
            return await cls._execute_nav_step(step_number, step_name, step_lower, execution_data)
        elif workflow_type == "compliance_report":
            return await cls._execute_compliance_step(step_number, step_name, step_lower, execution_data)
        elif workflow_type == "performance_query":
            return await cls._execute_performance_step(step_number, step_name, step_lower, execution_data)
        else:
            return await cls._execute_generic_step(step_number, step_name, step_lower, execution_data)

    @classmethod
    async def _execute_dividend_step(cls, step_number: int, step_name: str,
                                     step_lower: str, execution_data: dict) -> WorkflowStepResult:
        """Execute dividend processing workflow steps"""

        # Step 1: Retrieve pending dividend fund list
        if "retrieve" in step_lower or "pending" in step_lower or "fund list" in step_lower:
            funds_with_dividends = []
            for code, fund in FUND_DATA.items():
                if fund.get("dividends"):
                    funds_with_dividends.append({
                        "code": code,
                        "name": fund["name"],
                        "pending_dividend": fund["dividends"][0],
                        "nav": fund["nav"]
                    })
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"pending_funds": funds_with_dividends},
                message=f"Retrieved {len(funds_with_dividends)} funds with pending dividends"
            )

        # Step 2: Validate fund dividend information
        elif "validate" in step_lower or "validation" in step_lower:
            pending_funds = execution_data.get("pending_funds", [])
            validated_funds = []
            for fund in pending_funds:
                validated_funds.append({
                    **fund,
                    "validation_status": "Passed",
                    "validation_checks": [
                        {"check": "Fund Code Valid", "result": "Pass"},
                        {"check": "Dividend Amount Valid", "result": "Pass"},
                        {"check": "Record Date Valid", "result": "Pass"},
                        {"check": "Ex-Dividend Date Valid", "result": "Pass"}
                    ]
                })
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"validated_funds": validated_funds},
                message=f"Validated {len(validated_funds)} funds - All checks passed"
            )

        # Step 3: Calculate dividend amount per account
        elif "calculate" in step_lower or "amount" in step_lower:
            validated_funds = execution_data.get("validated_funds", execution_data.get("pending_funds", []))
            calculations = []
            total_distribution = 0

            for fund in validated_funds[:3]:  # Process first 3 funds
                dividend_rate = fund.get("pending_dividend", {}).get("amount", 0.1)
                fund_calculations = []
                fund_total = 0

                for account in cls.MOCK_INVESTOR_ACCOUNTS:
                    dividend_amount = account["shares"] * dividend_rate
                    fund_total += dividend_amount
                    fund_calculations.append({
                        "account_id": account["account_id"],
                        "investor_name": account["investor_name"],
                        "shares": account["shares"],
                        "dividend_rate": dividend_rate,
                        "dividend_amount": round(dividend_amount, 2)
                    })

                total_distribution += fund_total
                calculations.append({
                    "fund_code": fund["code"],
                    "fund_name": fund["name"],
                    "account_calculations": fund_calculations,
                    "fund_total": round(fund_total, 2)
                })

            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={
                    "calculations": calculations,
                    "total_distribution": round(total_distribution, 2),
                    "total_accounts": len(cls.MOCK_INVESTOR_ACCOUNTS)
                },
                message=f"Calculated dividends for {len(calculations)} funds, {len(cls.MOCK_INVESTOR_ACCOUNTS)} accounts. Total: ¥{total_distribution:,.2f}"
            )

        # Step 4: Execute dividend distribution
        elif "execute" in step_lower or "distribution" in step_lower:
            calculations = execution_data.get("calculations", [])
            distribution_results = []

            for calc in calculations:
                for acc_calc in calc.get("account_calculations", []):
                    distribution_results.append({
                        "transaction_id": f"DIV-{datetime.now().strftime('%Y%m%d')}-{acc_calc['account_id']}-{calc['fund_code']}",
                        "fund_code": calc["fund_code"],
                        "account_id": acc_calc["account_id"],
                        "amount": acc_calc["dividend_amount"],
                        "status": "Executed",
                        "execution_time": datetime.now().isoformat()
                    })

            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"distribution_results": distribution_results},
                message=f"Executed {len(distribution_results)} dividend transactions"
            )

        # Step 5: Update account balances
        elif "update" in step_lower or "balance" in step_lower:
            distribution_results = execution_data.get("distribution_results", [])
            balance_updates = []

            for account in cls.MOCK_INVESTOR_ACCOUNTS:
                account_dividends = [r for r in distribution_results if r.get("account_id") == account["account_id"]]
                total_received = sum(r.get("amount", 0) for r in account_dividends)

                balance_updates.append({
                    "account_id": account["account_id"],
                    "investor_name": account["investor_name"],
                    "previous_balance": round(account["shares"] * 2.5, 2),  # Mock previous balance
                    "dividend_received": round(total_received, 2),
                    "new_balance": round(account["shares"] * 2.5 + total_received, 2),
                    "update_status": "Completed"
                })

            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"balance_updates": balance_updates},
                message=f"Updated balances for {len(balance_updates)} accounts"
            )

        # Step 6: Generate dividend report
        elif "report" in step_lower or "generate" in step_lower:
            total_distribution = execution_data.get("total_distribution", 0)
            calculations = execution_data.get("calculations", [])

            report = {
                "report_id": f"RPT-DIV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "report_type": "Dividend Distribution Report",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_funds_processed": len(calculations),
                    "total_accounts_processed": len(cls.MOCK_INVESTOR_ACCOUNTS),
                    "total_amount_distributed": round(total_distribution, 2),
                    "distribution_method": "Cash Dividend",
                    "status": "Completed"
                },
                "fund_breakdown": [
                    {
                        "fund_code": calc["fund_code"],
                        "fund_name": calc["fund_name"],
                        "total_distributed": calc["fund_total"]
                    }
                    for calc in calculations
                ]
            }

            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"report": report},
                message=f"Generated dividend report: {report['report_id']}"
            )

        # Default handler for unrecognized steps
        return WorkflowStepResult(
            step_number=step_number,
            step_name=step_name,
            status="completed",
            data={},
            message=f"Step completed: {step_name}"
        )

    @classmethod
    async def _execute_nav_step(cls, step_number: int, step_name: str,
                                step_lower: str, execution_data: dict) -> WorkflowStepResult:
        """Execute NAV query workflow steps"""

        if "parse" in step_lower or "identifier" in step_lower:
            # Parse fund identifier
            fund_codes = list(FUND_DATA.keys())[:3]
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"fund_codes": fund_codes},
                message=f"Parsed {len(fund_codes)} fund identifiers"
            )

        elif "query" in step_lower or "nav" in step_lower:
            # Query NAV data
            fund_codes = execution_data.get("fund_codes", list(FUND_DATA.keys())[:3])
            nav_data = []
            for code in fund_codes:
                fund = FUND_DATA.get(code, {})
                nav_data.append({
                    "code": code,
                    "name": fund.get("name", ""),
                    "nav": fund.get("nav", 0),
                    "acc_nav": fund.get("acc_nav", 0),
                    "update_date": fund.get("update_date", "")
                })
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"nav_data": nav_data},
                message=f"Retrieved NAV data for {len(nav_data)} funds"
            )

        elif "calculate" in step_lower or "change" in step_lower:
            # Calculate price change
            nav_data = execution_data.get("nav_data", [])
            for item in nav_data:
                code = item.get("code")
                fund = FUND_DATA.get(code, {})
                item["change_pct"] = fund.get("change_pct", 0)
                item["change_amount"] = round(item["nav"] * item["change_pct"] / 100, 4)
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"nav_data": nav_data},
                message="Calculated price changes for all funds"
            )

        elif "format" in step_lower or "output" in step_lower:
            # Format output
            nav_data = execution_data.get("nav_data", [])
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"formatted_output": nav_data},
                message="Formatted NAV query results"
            )

        return WorkflowStepResult(
            step_number=step_number,
            step_name=step_name,
            status="completed",
            data={},
            message=f"Step completed: {step_name}"
        )

    @classmethod
    async def _execute_compliance_step(cls, step_number: int, step_name: str,
                                       step_lower: str, execution_data: dict) -> WorkflowStepResult:
        """Execute compliance report workflow steps"""

        if "collect" in step_lower or "transaction" in step_lower:
            transactions = [
                {"id": f"TXN-{i:04d}", "type": "Buy", "fund": "161005", "amount": 100000, "date": "2024-01-10"}
                for i in range(1, 11)
            ]
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"transactions": transactions},
                message=f"Collected {len(transactions)} transaction records"
            )

        elif "validate" in step_lower or "compliance" in step_lower:
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"validation_result": "All transactions comply with regulations"},
                message="All transactions validated against compliance rules"
            )

        elif "generate" in step_lower and "report" in step_lower:
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"report_id": f"COMP-{datetime.now().strftime('%Y%m%d')}"},
                message="Compliance report generated"
            )

        elif "review" in step_lower or "approve" in step_lower:
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"approval_status": "Approved", "approver": "Compliance Officer"},
                message="Report reviewed and approved"
            )

        elif "submit" in step_lower:
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"submission_id": f"SUB-{datetime.now().strftime('%Y%m%d%H%M')}"},
                message="Report submitted to regulatory authority"
            )

        elif "archive" in step_lower:
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"archive_location": "/documents/compliance/2024/"},
                message="Report archived successfully"
            )

        return WorkflowStepResult(
            step_number=step_number,
            step_name=step_name,
            status="completed",
            data={},
            message=f"Step completed: {step_name}"
        )

    @classmethod
    async def _execute_performance_step(cls, step_number: int, step_name: str,
                                        step_lower: str, execution_data: dict) -> WorkflowStepResult:
        """Execute fund performance query workflow steps"""

        if "parse" in step_lower or "identifier" in step_lower:
            fund_codes = list(FUND_DATA.keys())[:3]
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"fund_codes": fund_codes},
                message=f"Parsed {len(fund_codes)} fund identifiers"
            )

        elif "retrieve" in step_lower or "historical" in step_lower:
            fund_codes = execution_data.get("fund_codes", list(FUND_DATA.keys())[:3])
            performance_data = []
            for code in fund_codes:
                result = await FundServices.get_fund_performance(code)
                if result.get("success"):
                    performance_data.append(result["data"])
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"performance_data": performance_data},
                message=f"Retrieved historical data for {len(performance_data)} funds"
            )

        elif "calculate" in step_lower or "return" in step_lower:
            performance_data = execution_data.get("performance_data", [])
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"performance_data": performance_data},
                message="Calculated returns for all periods"
            )

        elif "compare" in step_lower or "benchmark" in step_lower:
            performance_data = execution_data.get("performance_data", [])
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"performance_data": performance_data},
                message="Benchmark comparison completed"
            )

        elif "format" in step_lower or "report" in step_lower:
            performance_data = execution_data.get("performance_data", [])
            return WorkflowStepResult(
                step_number=step_number,
                step_name=step_name,
                status="completed",
                data={"formatted_report": performance_data},
                message="Performance report formatted"
            )

        return WorkflowStepResult(
            step_number=step_number,
            step_name=step_name,
            status="completed",
            data={},
            message=f"Step completed: {step_name}"
        )

    @classmethod
    async def _execute_generic_step(cls, step_number: int, step_name: str,
                                    step_lower: str, execution_data: dict) -> WorkflowStepResult:
        """Execute generic workflow steps"""
        return WorkflowStepResult(
            step_number=step_number,
            step_name=step_name,
            status="completed",
            data={"step_output": f"Processed: {step_name}"},
            message=f"Step completed: {step_name}"
        )

    @classmethod
    def _generate_summary(cls, workflow_type: str, step_results: list, execution_data: dict) -> dict:
        """Generate workflow execution summary"""

        completed_steps = len([r for r in step_results if r["status"] == "completed"])
        total_steps = len(step_results)

        base_summary = {
            "workflow_type": workflow_type,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "success_rate": f"{(completed_steps/total_steps*100):.1f}%" if total_steps > 0 else "0%",
            "execution_status": "Completed" if completed_steps == total_steps else "Partial"
        }

        # Add workflow-specific summary data
        if workflow_type == "dividend_processing":
            base_summary.update({
                "total_distribution": execution_data.get("total_distribution", 0),
                "funds_processed": len(execution_data.get("calculations", [])),
                "accounts_processed": execution_data.get("total_accounts", 0),
                "report_id": execution_data.get("report", {}).get("report_id", "N/A")
            })
        elif workflow_type == "nav_query":
            nav_data = execution_data.get("nav_data", [])
            base_summary.update({
                "funds_queried": len(nav_data),
                "query_results": nav_data
            })
        elif workflow_type == "compliance_report":
            base_summary.update({
                "report_status": "Submitted",
                "submission_id": execution_data.get("submission_id", "N/A")
            })
        elif workflow_type == "performance_query":
            performance_data = execution_data.get("performance_data", [])
            base_summary.update({
                "funds_analyzed": len(performance_data),
                "analysis_results": performance_data
            })

        return base_summary
