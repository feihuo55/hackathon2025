"""
FastAPI Backend Server for React UI
Exposes the existing services as REST APIs
Version: 2.0 - With Processing Steps Support
"""
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_module.crews import QueryCrew, CreationCrew
from agent_module.agents import IntentAgent
from rag_module.retrieval import ServiceMatcher
from rag_module.memory import MemoryManager
from service_module.mock_services import ServiceRegistry
from service_module.mock_services.fund_services import FUND_DATA
from service_module.sipoc.templates import SIPOCTemplates
from utils.language_detector import detect_language, get_message

app = FastAPI(title="Custody Bank AI API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global components
service_registry = ServiceRegistry()
service_matcher = ServiceMatcher()
memory_manager = MemoryManager()
intent_agent = IntentAgent()
query_crew = QueryCrew(service_registry, service_matcher, memory_manager)
creation_crew = CreationCrew(service_registry, memory_manager)

# Session storage for chat context
chat_sessions = {}


# ===== Request/Response Models =====

class EmailAttachment(BaseModel):
    id: str
    name: str
    size: str
    type: str
    emailId: str
    isSelected: bool = False


class Email(BaseModel):
    id: str
    from_addr: str
    subject: str
    summary: str
    date: str
    hasAttachment: bool
    attachments: list[EmailAttachment]
    isSelected: bool = False


class Folder(BaseModel):
    id: str
    name: str
    type: str
    children: Optional[list] = None


class AnalyzeRequest(BaseModel):
    emailIds: list[str]
    sessionId: str = "default"


class ChatRequest(BaseModel):
    message: str
    emailIds: list[str] = []
    sessionId: str = "default"


class ExecuteRequest(BaseModel):
    sipoc: dict
    sessionId: str = "default"


# ===== Mock Email Data =====

MOCK_EMAILS = [
    {
        "id": "1",
        "from_addr": "john.smith@fundcompany.com",
        "subject": "Fund NAV Report - Q4 2024",
        "summary": "Please find attached the quarterly NAV report. Fund 161005 (Fuguo Tianhui) performed excellently this quarter with NAV growth of 2.35%.",
        "date": "Nov 26",
        "hasAttachment": True,
        "attachments": [
            {"id": "a1", "name": "NAV_Report_Q4_2024.xlsx", "size": "245 KB", "type": "xlsx", "emailId": "1", "isSelected": False},
            {"id": "a2", "name": "Fund_Performance_Summary.pdf", "size": "1.2 MB", "type": "pdf", "emailId": "1", "isSelected": False},
        ],
        "isSelected": False,
    },
    {
        "id": "2",
        "from_addr": "sarah.chen@bank.com",
        "subject": "Dividend Distribution Request",
        "summary": "Requesting dividend distribution processing for Fund 161005. Please review and approve the authorization form attached. Distribution method: Cash dividend.",
        "date": "Nov 25",
        "hasAttachment": True,
        "attachments": [
            {"id": "a3", "name": "Dividend_Authorization.pdf", "size": "156 KB", "type": "pdf", "emailId": "2", "isSelected": False},
        ],
        "isSelected": False,
    },
    {
        "id": "3",
        "from_addr": "mike.johnson@investor.com",
        "subject": "Query: Fund 110003 Performance",
        "summary": "Please provide the latest performance metrics for Fund 110003 (E Fund SSE 50 Index A). Need year-to-date returns and benchmark comparison.",
        "date": "Nov 24",
        "hasAttachment": False,
        "attachments": [],
        "isSelected": False,
    },
    {
        "id": "4",
        "from_addr": "compliance@regulator.gov",
        "subject": "Monthly Compliance Report Due",
        "summary": "Reminder: Monthly compliance report is due this week. Please ensure all required documents are attached. Funds involved: 002001, 202003.",
        "date": "Nov 23",
        "hasAttachment": True,
        "attachments": [
            {"id": "a4", "name": "Compliance_Checklist.docx", "size": "89 KB", "type": "docx", "emailId": "4", "isSelected": False},
        ],
        "isSelected": False,
    },
]

MOCK_FOLDERS = [
    {
        "id": "f1",
        "name": "2024-11-26_john.smith_Fund_NAV_Report",
        "type": "folder",
        "children": [
            {"id": "f1a", "name": "NAV_Report_Q4_2024.xlsx", "type": "file"},
            {"id": "f1b", "name": "Fund_Performance_Summary.pdf", "type": "file"},
        ],
    },
    {
        "id": "f2",
        "name": "Dividend_Authorization.pdf",
        "type": "file",
    },
    {
        "id": "f3",
        "name": "Compliance_Checklist.docx",
        "type": "file",
    },
]


# ===== API Endpoints =====

@app.get("/api/emails")
async def get_emails():
    """Get list of emails"""
    return {"success": True, "data": MOCK_EMAILS}


@app.get("/api/folders")
async def get_folders():
    """Get list of folders/attachments"""
    return {"success": True, "data": MOCK_FOLDERS}


@app.get("/api/funds")
async def get_funds():
    """Get list of all funds"""
    funds = []
    for code, fund in FUND_DATA.items():
        funds.append({
            "code": code,
            "name": fund["name"],
            "short_name": fund["short_name"],
            "type": fund["type"],
            "nav": fund["nav"],
            "change_pct": fund["change_pct"],
        })
    return {"success": True, "data": funds}


@app.post("/api/analyze")
async def analyze_emails(request: AnalyzeRequest):
    """Analyze selected emails and return initial analysis"""
    processing_steps = []

    if not request.emailIds:
        raise HTTPException(status_code=400, detail="No emails selected")

    # Step 1: Get selected emails
    processing_steps.append({
        "step": 1,
        "title": "Reading Email Content",
        "thinking": f"Loading {len(request.emailIds)} selected email(s) and parsing content...",
        "details": [
            {"type": "module", "name": "Document Loader", "description": "Loading email content from source, parsing headers (From, Subject, Date) and extracting body text"},
        ]
    })

    selected_emails = [e for e in MOCK_EMAILS if e["id"] in request.emailIds]
    if not selected_emails:
        raise HTTPException(status_code=404, detail="Emails not found")

    # Step 2: Combine email content
    email = selected_emails[0]  # Use first email for analysis
    combined_content = f"Subject: {email['subject']}\nSummary: {email['summary']}"

    processing_steps.append({
        "step": 2,
        "title": "Extracting Key Information",
        "thinking": f"Found subject: '{email['subject']}'. Extracting entities like fund codes, dates, and action keywords...",
        "details": [
            {"type": "module", "name": "Embeddings", "description": "Converting text to vector representations using embedding model for semantic search"},
            {"type": "memory", "name": "Semantic Memory", "description": "Storing and retrieving conceptual knowledge about fund types, query patterns, and domain terms"},
        ]
    })

    # Step 3: Intent analysis
    processing_steps.append({
        "step": 3,
        "title": "Analyzing User Intent",
        "thinking": "Running intent recognition using rule-based matching and AI analysis...",
        "details": [
            {"type": "agent", "name": "Intent Agent", "description": "Analyzing email content to classify user intent (query/creation) and extract key parameters like fund codes and action types"},
            {"type": "memory", "name": "Episodic Memory", "description": "Recalling similar past requests and their successful resolutions to improve intent accuracy"},
        ]
    })

    # Use intent agent to analyze
    intent_result = await intent_agent.analyze(combined_content)

    # Debug logging
    print(f"[DEBUG /api/analyze] combined_content: {combined_content[:100]}...")
    print(f"[DEBUG /api/analyze] intent_result: {intent_result}")

    # Always use English for UI
    lang = "en"

    # Determine suggested action based on intent
    intent_type = intent_result.get("type", "unknown")
    query_type = intent_result.get("query_type", "")

    # Step 4: Determine action based on intent
    matched_service = None
    if intent_type == "query":
        if query_type == "fund_nav":
            suggested_action = "Query fund NAV"
            user_intent = "Query fund NAV information"
            matched_service = "FundNAVQuery"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}' with query type: '{query_type}'. Matching to FundNAVQuery service...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searching service registry using vector similarity to find services matching 'fund NAV query' intent"},
                    {"type": "service", "name": "FundNAVQuery", "description": "Service that retrieves real-time and historical NAV data for specified fund codes"},
                    {"type": "result", "description": "✓ Found matching service: FundNAVQuery (similarity: 0.95)"},
                ]
            })
        elif query_type == "fund_dividend":
            suggested_action = "Query dividend history"
            user_intent = "Query fund dividend history"
            matched_service = "DividendHistory"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}' with query type: '{query_type}'. Matching to DividendHistory service...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searching service registry using vector similarity to find services matching 'dividend query' intent"},
                    {"type": "service", "name": "DividendHistory", "description": "Service that retrieves dividend distribution records and payment history for funds"},
                    {"type": "result", "description": "✓ Found matching service: DividendHistory (similarity: 0.92)"},
                ]
            })
        elif query_type == "fund_performance":
            suggested_action = "Query fund performance"
            user_intent = "Query fund performance metrics"
            matched_service = "FundPerformance"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}' with query type: '{query_type}'. Matching to FundPerformance service...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searching service registry using vector similarity to find services matching 'performance query' intent"},
                    {"type": "service", "name": "FundPerformance", "description": "Service that calculates and returns fund performance metrics including YTD returns and benchmark comparison"},
                    {"type": "result", "description": "✓ Found matching service: FundPerformance (similarity: 0.91)"},
                ]
            })
        else:
            suggested_action = "Query fund information"
            user_intent = "Query fund related information"
            matched_service = "FundQuery"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}'. Matching to general FundQuery service...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searching service registry using vector similarity to find services matching general fund query intent"},
                    {"type": "service", "name": "FundQuery", "description": "General-purpose service for retrieving fund information and basic data"},
                    {"type": "result", "description": "✓ Found matching service: FundQuery (similarity: 0.88)"},
                ]
            })
    elif intent_type == "creation":
        creation_type = intent_result.get("creation_type", "")
        if creation_type == "compliance_report":
            suggested_action = "Create compliance report workflow"
            user_intent = "Process compliance report submission"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}' with creation type: '{creation_type}'. No direct service found. Will create new workflow...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searched 47 registered services for 'compliance report processing' - no exact match found"},
                    {"type": "result", "description": "✗ No matching service found in registry"},
                    {"type": "agent", "name": "Process Designer", "description": "Will design new workflow using SIPOC methodology to define suppliers, inputs, process, outputs, and customers"},
                ]
            })
        elif creation_type == "dividend_processing":
            suggested_action = "Create dividend processing workflow"
            user_intent = "Process fund dividend distribution"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}' with creation type: '{creation_type}'. No direct service found. Will create new workflow...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searched 47 registered services for 'dividend processing workflow' - no exact match found"},
                    {"type": "result", "description": "✗ No matching service found in registry"},
                    {"type": "agent", "name": "Process Designer", "description": "Will design new workflow using SIPOC methodology to define suppliers, inputs, process, outputs, and customers"},
                ]
            })
        else:
            suggested_action = "Create new workflow"
            user_intent = "Create new business process"
            processing_steps.append({
                "step": 4,
                "title": "Matching Service",
                "thinking": f"Detected intent: '{intent_type}' with creation type: '{creation_type}'. No direct service found. Will generate SIPOC to define workflow...",
                "details": [
                    {"type": "rag", "name": "Service Matcher", "description": "Searched service registry for matching workflows - no suitable match found"},
                    {"type": "result", "description": "✗ No matching service found in registry"},
                    {"type": "agent", "name": "Process Designer", "description": "Will design new workflow using SIPOC methodology to define suppliers, inputs, process, outputs, and customers"},
                ]
            })
    else:
        suggested_action = "Analyze email content"
        user_intent = "Understand user requirements"
        processing_steps.append({
            "step": 4,
            "title": "Matching Service",
            "thinking": "Intent unclear. Will generate SIPOC to define the service requirements...",
            "details": [
                {"type": "rag", "name": "Service Matcher", "description": "Searched service registry but could not determine clear intent match"},
                {"type": "result", "description": "✗ No matching service found - intent unclear"},
            ]
        })

    # Step 5: Generate recommendation
    recommendation_details = []
    if matched_service:
        recommendation_details = [
            {"type": "crew", "name": "Query Crew", "description": "Orchestrating agents to execute the matched service and format response data"},
            {"type": "result", "description": f"Ready to execute {matched_service} service on user confirmation"},
        ]
    else:
        recommendation_details = [
            {"type": "crew", "name": "Creation Crew", "description": "Coordinating BA Agent and Tech Agent to collaboratively generate SIPOC document"},
            {"type": "module", "name": "SIPOC Generator", "description": "Creating structured workflow definition with suppliers, inputs, process steps, outputs, and customers"},
            {"type": "result", "description": "Will generate SIPOC document for workflow creation"},
        ]

    processing_steps.append({
        "step": 5,
        "title": "Generating Recommendation",
        "thinking": f"Preparing action: '{suggested_action}'. Awaiting user confirmation to proceed...",
        "details": recommendation_details
    })

    # Store the analysis result in session for later confirmation
    session_id = request.sessionId
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "history": [],
            "intent_result": None,
            "stage": "initial",
        }
    chat_sessions[session_id]["intent_result"] = intent_result
    chat_sessions[session_id]["stage"] = "awaiting_confirmation"
    chat_sessions[session_id]["email_content"] = combined_content

    return {
        "success": True,
        "data": {
            "emailSubject": email["subject"],
            "summary": email["summary"],
            "attachments": [a["name"] for a in email.get("attachments", [])],
            "userIntent": user_intent,
            "suggestedAction": suggested_action,
            "intentResult": intent_result,
            "language": lang,
            "processingSteps": processing_steps,
            "matchedService": matched_service,  # Service name if found, None otherwise
        }
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Handle chat messages and return AI response"""
    message = request.message
    session_id = request.sessionId
    processing_steps = []

    # Get or create session
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "history": [],
            "intent_result": None,
            "stage": "initial",
        }

    session = chat_sessions[session_id]
    lang = "en"  # Always use English for UI

    # Check if this is a confirmation
    is_confirmation = any(word in message.lower() for word in ["yes", "proceed", "correct", "confirm", "ok", "sure"])
    is_rejection = any(word in message.lower() for word in ["no", "wrong", "incorrect", "cancel", "reject"])

    # Check if this is a reanalysis request (from user clicking No and selecting feedback)
    is_reanalyze_intent = "[REANALYZE_INTENT]" in message
    is_reanalyze_action = "[REANALYZE_ACTION]" in message
    is_user_feedback_missing = "[USER_FEEDBACK_MISSING_INFO]" in message
    is_user_feedback_other = "[USER_FEEDBACK_OTHER]" in message

    # Debug logging
    print(f"[DEBUG /api/chat] session_id: {session_id}")
    print(f"[DEBUG /api/chat] is_confirmation: {is_confirmation}")
    print(f"[DEBUG /api/chat] is_reanalyze_intent: {is_reanalyze_intent}")
    print(f"[DEBUG /api/chat] is_reanalyze_action: {is_reanalyze_action}")
    print(f"[DEBUG /api/chat] session stage: {session.get('stage')}")
    print(f"[DEBUG /api/chat] session intent_result: {session.get('intent_result')}")

    try:
        # Handle confirmation of initial analysis - execute immediately
        if is_confirmation and session.get("stage") == "awaiting_confirmation":
            stored_intent = session.get("intent_result", {})
            stored_intent_type = stored_intent.get("type", "unknown")
            stored_query_type = stored_intent.get("query_type", "")
            email_content = session.get("email_content", "")

            # Execute based on stored intent
            if stored_intent_type == "query":
                # Build processing steps for query execution with detailed module/agent info
                processing_steps.append({
                    "step": 1,
                    "title": "Processing Confirmation",
                    "thinking": "User confirmed the suggested action. Preparing to execute query...",
                    "details": [
                        {"type": "module", "name": "Request Validator", "description": "Validating user confirmation and extracting query parameters from session"},
                        {"type": "memory", "name": "Episodic Memory", "description": "Retrieving stored intent analysis and matched service information"},
                    ]
                })
                processing_steps.append({
                    "step": 2,
                    "title": "Retrieving Service",
                    "thinking": f"Loading {stored_query_type or 'fund'} query service from registry...",
                    "details": [
                        {"type": "rag", "name": "Service Registry", "description": f"Locating '{stored_query_type or 'fund'}' service implementation from registered services"},
                        {"type": "service", "name": f"{'FundNAVQuery' if stored_query_type == 'fund_nav' else 'FundPerformance' if stored_query_type == 'fund_performance' else 'DividendHistory' if stored_query_type == 'fund_dividend' else 'FundQuery'}", "description": "Service module loaded and initialized with required parameters"},
                        {"type": "result", "description": "✓ Service ready for execution"},
                    ]
                })
                processing_steps.append({
                    "step": 3,
                    "title": "Executing Query",
                    "thinking": "Connecting to data sources and executing the query...",
                    "details": [
                        {"type": "crew", "name": "Query Crew", "description": "Orchestrating query execution with data validation and error handling"},
                        {"type": "agent", "name": "Data Agent", "description": "Connecting to fund database and retrieving requested information"},
                        {"type": "memory", "name": "Semantic Memory", "description": "Applying domain knowledge for data interpretation and formatting"},
                    ]
                })

                # Execute query directly
                result = await query_crew.execute(email_content, stored_intent)

                processing_steps.append({
                    "step": 4,
                    "title": "Formatting Results",
                    "thinking": "Query completed successfully. Formatting response data...",
                    "details": [
                        {"type": "module", "name": "Response Formatter", "description": "Converting query results to user-friendly format with proper units and labels"},
                        {"type": "result", "description": "✓ Query executed successfully, results formatted for display"},
                    ]
                })

                session["stage"] = "completed"

                return {
                    "success": True,
                    "data": {
                        "response": result.get("message", "Query completed"),
                        "hasServiceMatch": True,
                        "queryResult": result,
                        "processingSteps": processing_steps,
                    }
                }
            elif stored_intent_type == "creation":
                print(f"[DEBUG /api/chat] Processing CREATION intent, creation_type: {stored_intent.get('creation_type')}")
                # Build processing steps for SIPOC generation with detailed module/agent info
                processing_steps.append({
                    "step": 1,
                    "title": "Processing Confirmation",
                    "thinking": "User confirmed the creation request. Initializing SIPOC generation workflow...",
                    "details": [
                        {"type": "module", "name": "Request Validator", "description": "Validating user confirmation and extracting context from session state"},
                        {"type": "memory", "name": "Episodic Memory", "description": "Retrieving conversation history and previous analysis results from session"},
                    ]
                })

                # Generate SIPOC for creation
                creation_type = stored_intent.get("creation_type", "")
                if creation_type == "dividend_processing":
                    processing_steps.append({
                        "step": 2,
                        "title": "Selecting Template",
                        "thinking": "Identified creation type: 'dividend_processing'. Loading dividend processing template...",
                        "details": [
                            {"type": "rag", "name": "Template Matcher", "description": "Searching SIPOC template registry using semantic similarity for 'dividend processing' workflows"},
                            {"type": "module", "name": "SIPOC Templates", "description": "Loading fund_dividend_processing template with predefined suppliers, inputs, process steps, outputs, customers"},
                            {"type": "result", "description": "✓ Found matching template: fund_dividend_processing (confidence: 0.96)"},
                        ]
                    })
                    sipoc = SIPOCTemplates.fund_dividend_processing()
                elif creation_type == "compliance_report":
                    processing_steps.append({
                        "step": 2,
                        "title": "Selecting Template",
                        "thinking": "Identified creation type: 'compliance_report'. Loading compliance report processing template...",
                        "details": [
                            {"type": "rag", "name": "Template Matcher", "description": "Searching SIPOC template registry using semantic similarity for 'compliance report' workflows"},
                            {"type": "module", "name": "SIPOC Templates", "description": "Loading compliance_report_processing template with regulatory requirements"},
                            {"type": "result", "description": "✓ Found matching template: compliance_report_processing (confidence: 0.94)"},
                        ]
                    })
                    sipoc = SIPOCTemplates.compliance_report_processing()
                else:
                    processing_steps.append({
                        "step": 2,
                        "title": "Selecting Template",
                        "thinking": f"Identified creation type: '{creation_type or 'general'}'. Loading appropriate template...",
                        "details": [
                            {"type": "rag", "name": "Template Matcher", "description": "Searching SIPOC template registry for matching workflow patterns"},
                            {"type": "module", "name": "SIPOC Templates", "description": "Loading generic workflow template based on content analysis"},
                            {"type": "result", "description": "✓ Using general fund service template"},
                        ]
                    })
                    sipoc = SIPOCTemplates.fund_nav_query()

                sipoc_dict = sipoc.to_dict()

                # Create collaboration data for SIPOC generation step
                collaboration_data = {
                    "isActive": True,
                    "roles": [
                        {
                            "id": "ai",
                            "name": "Claude AI",
                            "role": "AI",
                            "avatar": "bot",
                            "contribution": "Orchestrates the SIPOC generation process and synthesizes inputs from domain experts"
                        },
                        {
                            "id": "ba",
                            "name": "BA Agent",
                            "role": "BA",
                            "avatar": "briefcase",
                            "contribution": "Validates business process flows, stakeholder relationships, and compliance requirements"
                        },
                        {
                            "id": "tech",
                            "name": "Tech Agent",
                            "role": "Tech",
                            "avatar": "code",
                            "contribution": "Ensures technical feasibility and integration with existing fund management systems"
                        }
                    ],
                    "messages": [
                        {
                            "roleId": "ai",
                            "content": "I've analyzed the dividend processing request. Let me coordinate with BA Agent and Tech Agent to build a comprehensive SIPOC."
                        },
                        {
                            "roleId": "ba",
                            "content": "Based on our fund operations, the key suppliers should include the Fund Company, Custody Bank Database, and Investor Account System. The process must comply with regulatory requirements."
                        },
                        {
                            "roleId": "tech",
                            "content": "From a technical standpoint, we need to ensure the process integrates with our account management API and generates proper audit trails. I recommend including validation steps."
                        },
                        {
                            "roleId": "ai",
                            "content": f"Thank you both. I've synthesized your inputs into a SIPOC with {len(sipoc.supplier)} suppliers, {len(sipoc.input)} inputs, {len(sipoc.process)} process steps, {len(sipoc.output)} outputs, and {len(sipoc.customer)} customers."
                        }
                    ],
                    "generatedSipoc": {
                        "suppliers": sipoc_dict["supplier"],
                        "inputs": sipoc_dict["input"],
                        "process": sipoc_dict["process"],
                        "outputs": sipoc_dict["output"],
                        "customers": sipoc_dict["customer"]
                    }
                }

                processing_steps.append({
                    "step": 3,
                    "title": "Generating SIPOC Document",
                    "thinking": f"Orchestrating multi-agent collaboration to build SIPOC with {len(sipoc.supplier)} suppliers, {len(sipoc.process)} process steps...",
                    "details": [
                        {"type": "crew", "name": "Creation Crew", "description": "Coordinating BA Agent and Tech Agent to collaboratively generate SIPOC document"},
                        {"type": "agent", "name": "BA Agent", "description": "Analyzing business process requirements, stakeholder relationships, and compliance needs"},
                        {"type": "agent", "name": "Tech Agent", "description": "Validating technical feasibility, API integrations, and system dependencies"},
                        {"type": "memory", "name": "Semantic Memory", "description": "Retrieving domain knowledge about fund operations, regulatory requirements, and best practices"},
                    ],
                    "showCollaboration": True,
                    "collaboration": collaboration_data
                })

                session["stage"] = "sipoc_generated"
                session["sipoc"] = sipoc_dict

                processing_steps.append({
                    "step": 4,
                    "title": "Preparing Review",
                    "thinking": "SIPOC document ready. Presenting for user review and approval...",
                    "details": [
                        {"type": "module", "name": "SIPOC Formatter", "description": "Formatting SIPOC document for visual presentation with structured sections"},
                        {"type": "module", "name": "Workflow Generator", "description": "Preparing BPMN 2.0 workflow generation capability based on process steps"},
                        {"type": "result", "description": f"✓ SIPOC document ready: {len(sipoc.supplier)} suppliers, {len(sipoc.input)} inputs, {len(sipoc.process)} process steps, {len(sipoc.output)} outputs, {len(sipoc.customer)} customers"},
                    ]
                })

                response_text = "I've generated the SIPOC document based on the multi-role collaboration. Please review the document above and click 'Generate Workflow' to create the BPMN 2.0 workflow diagram."

                # Debug: Log the processingSteps before returning
                print(f"[DEBUG /api/chat] Returning {len(processing_steps)} processing steps")
                for i, step in enumerate(processing_steps):
                    print(f"[DEBUG /api/chat] Step {i+1}: showCollaboration={step.get('showCollaboration')}")

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "hasServiceMatch": True,
                        "sipoc": {
                            "suppliers": sipoc_dict["supplier"],
                            "inputs": sipoc_dict["input"],
                            "process": sipoc_dict["process"],
                            "outputs": sipoc_dict["output"],
                            "customers": sipoc_dict["customer"],
                        },
                        "processingSteps": processing_steps,
                        "actions": [
                            {"id": "generate", "label": "Generate Workflow", "type": "generateWorkflow"}
                        ],
                    }
                }
            else:
                # Unknown intent - generate SIPOC based on email content
                processing_steps.append({
                    "step": 1,
                    "title": "Processing Confirmation",
                    "thinking": "User confirmed. Analyzing email content to determine service type..."
                })

                email_content = session.get("email_content", "")

                processing_steps.append({
                    "step": 2,
                    "title": "Content Analysis",
                    "thinking": "Scanning for keywords: compliance, performance, dividend, NAV..."
                })

                # Try to match email content to appropriate SIPOC template
                email_lower = email_content.lower()
                template_name = "generic"

                if "compliance" in email_lower or "regulatory" in email_lower:
                    sipoc = SIPOCTemplates.compliance_report_processing()
                    template_name = "compliance_report_processing"
                elif "performance" in email_lower or "return" in email_lower or "benchmark" in email_lower:
                    sipoc = SIPOCTemplates.fund_performance_query()
                    template_name = "fund_performance_query"
                elif "dividend" in email_lower or "distribution" in email_lower:
                    sipoc = SIPOCTemplates.fund_dividend_processing()
                    template_name = "fund_dividend_processing"
                elif "nav" in email_lower or "净值" in email_lower:
                    sipoc = SIPOCTemplates.fund_nav_query()
                    template_name = "fund_nav_query"
                else:
                    # Use generic template based on email content
                    lines = email_content.split("\n")
                    subject = ""
                    summary = ""
                    for line in lines:
                        if line.startswith("Subject:"):
                            subject = line.replace("Subject:", "").strip()
                        elif line.startswith("Summary:"):
                            summary = line.replace("Summary:", "").strip()
                    sipoc = SIPOCTemplates.generic_email_processing(subject or "Email Request", summary or email_content[:100])

                processing_steps.append({
                    "step": 3,
                    "title": "Generating SIPOC Document",
                    "thinking": f"Selected template: '{template_name}'. Building SIPOC document..."
                })

                sipoc_dict = sipoc.to_dict()
                session["stage"] = "sipoc_generated"
                session["sipoc"] = sipoc_dict

                processing_steps.append({
                    "step": 4,
                    "title": "Preparing Review",
                    "thinking": "SIPOC document generated. Presenting for user review..."
                })

                response_text = "I've analyzed your request and generated a SIPOC document. Please review and click 'Generate Workflow' to proceed."

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "hasServiceMatch": True,
                        "sipoc": {
                            "suppliers": sipoc_dict["supplier"],
                            "inputs": sipoc_dict["input"],
                            "process": sipoc_dict["process"],
                            "outputs": sipoc_dict["output"],
                            "customers": sipoc_dict["customer"],
                        },
                        "processingSteps": processing_steps,
                        "actions": [
                            {"id": "generate", "label": "Generate Workflow", "type": "generateWorkflow"}
                        ],
                    }
                }

        # Handle reanalysis requests (user feedback from clicking No)
        if is_reanalyze_intent or is_reanalyze_action or is_user_feedback_missing or is_user_feedback_other:
            email_content = session.get("email_content", "")
            stored_intent = session.get("intent_result", {})

            print(f"[DEBUG /api/chat] Handling reanalysis request")
            print(f"[DEBUG /api/chat] Original email_content: {email_content[:100] if email_content else 'None'}...")
            print(f"[DEBUG /api/chat] Original intent: {stored_intent}")

            if is_reanalyze_intent:
                # User says the detected intent is wrong - provide alternative interpretation
                # For Email 1 (Fund NAV Report), suggest it might be a creation request instead of query
                if stored_intent.get("type") == "query":
                    # Try suggesting creation flow instead - provide clickable options
                    response_text = f"""I apologize for the misunderstanding. Let me reconsider your request.

**Re-analyzing the email content:**
Looking at the email again, I see it mentions "{email_content[:50]}..."

**Alternative Interpretation:**
Please select what you'd like me to do:"""

                    session["stage"] = "awaiting_option_selection"

                    return {
                        "success": True,
                        "data": {
                            "response": response_text,
                            "hasServiceMatch": False,
                            "actions": [
                                {"id": "process_nav", "label": "Process the NAV report data", "type": "option", "value": "process_nav_report"},
                                {"id": "generate_summary", "label": "Generate a summary/workflow", "type": "option", "value": "generate_workflow"},
                                {"id": "create_service", "label": "Create a new service", "type": "option", "value": "create_new_service"},
                                {"id": "no", "label": "None of the above", "type": "reject"},
                            ],
                        }
                    }
                else:
                    # Original was creation, suggest query instead - provide clickable options
                    response_text = f"""I apologize for the misunderstanding. Let me reconsider your request.

**Re-analyzing the email content:**
Looking at the email again, I see it mentions "{email_content[:50]}..."

**Alternative Interpretation:**
Please select what you'd like me to do:"""

                    session["stage"] = "awaiting_option_selection"

                    return {
                        "success": True,
                        "data": {
                            "response": response_text,
                            "hasServiceMatch": False,
                            "actions": [
                                {"id": "query_nav", "label": "Query fund NAV information", "type": "option", "value": "query_fund_nav"},
                                {"id": "query_performance", "label": "Query fund performance", "type": "option", "value": "query_fund_performance"},
                                {"id": "query_dividend", "label": "Query dividend history", "type": "option", "value": "query_dividend_history"},
                                {"id": "no", "label": "None of the above", "type": "reject"},
                            ],
                        }
                    }

            elif is_reanalyze_action:
                # User says the suggested action is wrong - suggest different action
                stored_type = stored_intent.get("type", "unknown")
                stored_query_type = stored_intent.get("query_type", "")

                if stored_type == "query":
                    # Suggest different query types
                    if stored_query_type == "fund_nav":
                        new_query_type = "fund_performance"
                        response_text = """I apologize for suggesting the wrong action. Let me offer alternatives.

**Based on the email content, perhaps you need:**
- Query **fund performance** metrics instead of NAV
- Check **dividend history** for the mentioned fund
- Review **compliance status** of the fund

**Revised Suggested Action:** Query fund performance metrics

Would you like me to proceed with performance query instead?"""
                        matched_service = "FundPerformance"
                    else:
                        new_query_type = "fund_nav"
                        response_text = """I apologize for suggesting the wrong action. Let me reconsider.

**Alternative actions available:**
- Query **fund NAV** information
- Check **account balances**
- Review **transaction history**

**Revised Suggested Action:** Query fund NAV

Would you like me to proceed with this action?"""
                        matched_service = "FundNAVQuery"

                    session["intent_result"] = {
                        "type": "query",
                        "query_type": new_query_type,
                    }
                else:
                    # For creation type, suggest different creation
                    response_text = """I apologize for suggesting the wrong workflow. Let me offer alternatives.

**Alternative workflow options:**
- **Dividend Processing** - Process fund dividend distributions
- **Compliance Report** - Generate compliance documentation
- **Performance Report** - Create fund performance summary

Please select the workflow type you need, or describe what you're trying to accomplish."""
                    matched_service = None

                session["stage"] = "awaiting_confirmation"

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "hasServiceMatch": matched_service is not None,
                        "matchedService": matched_service,
                        "actions": [
                            {"id": "yes", "label": "Yes, proceed", "type": "confirm"},
                            {"id": "no", "label": "No, that's not right", "type": "reject"},
                        ],
                    }
                }

            elif is_user_feedback_missing or is_user_feedback_other:
                # User provided additional context - re-analyze with this info
                # Extract the user's explanation from the message
                if is_user_feedback_missing:
                    user_explanation = message.replace("[USER_FEEDBACK_MISSING_INFO]", "").strip()
                else:
                    user_explanation = message.replace("[USER_FEEDBACK_OTHER]", "").strip()

                response_text = f"""Thank you for the clarification. Let me re-analyze based on your feedback.

**Your feedback:** {user_explanation[:200]}

**Updated Analysis:**
I understand now. Based on your input, I will adjust my approach accordingly.

**Revised Suggested Action:** Process your request with the corrected understanding

Would you like me to proceed?"""

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "hasServiceMatch": False,
                        "actions": [
                            {"id": "yes", "label": "Yes, proceed", "type": "confirm"},
                            {"id": "no", "label": "No, that's not right", "type": "reject"},
                        ],
                    }
                }

        # Handle option selection from reanalyze flow
        if session.get("stage") == "awaiting_option_selection":
            email_content = session.get("email_content", "")

            # Check what option was selected based on message content
            if message in ["process_nav_report", "generate_workflow", "create_new_service"]:
                # User selected a creation option - update intent and confirm
                if message == "process_nav_report":
                    creation_type = "nav_report_processing"
                elif message == "generate_workflow":
                    creation_type = "workflow_generation"
                else:
                    creation_type = "new_service_creation"

                session["intent_result"] = {"type": "creation", "creation_type": creation_type}
                session["stage"] = "awaiting_confirmation"

                response_text = f"""Great choice! I'll proceed with **{message.replace('_', ' ')}**.

Would you like me to create a SIPOC workflow for this?"""

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "hasServiceMatch": False,
                        "actions": [
                            {"id": "yes", "label": "Yes, proceed", "type": "confirm"},
                            {"id": "no", "label": "No, that's not right", "type": "reject"},
                        ],
                    }
                }

            elif message in ["query_fund_nav", "query_fund_performance", "query_dividend_history"]:
                # User selected a query option
                if message == "query_fund_nav":
                    query_type = "fund_nav"
                    matched_service = "FundNAVQuery"
                elif message == "query_fund_performance":
                    query_type = "fund_performance"
                    matched_service = "FundPerformance"
                else:
                    query_type = "fund_dividend"
                    matched_service = "DividendHistory"

                session["intent_result"] = {"type": "query", "query_type": query_type}
                session["stage"] = "awaiting_confirmation"

                response_text = f"""Great choice! I found a matching service.

**✓ Found Matching Service:** `{matched_service}`

Would you like me to execute this query?"""

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "hasServiceMatch": True,
                        "matchedService": matched_service,
                        "actions": [
                            {"id": "yes", "label": "Yes, proceed", "type": "confirm"},
                            {"id": "no", "label": "No, that's not right", "type": "reject"},
                        ],
                    }
                }

        # Analyze intent for new messages
        intent_result = await intent_agent.analyze(message)
        intent_type = intent_result.get("type", "unknown")

        if intent_type == "query":
            # Execute query
            result = await query_crew.execute(message, intent_result)

            session["history"].append({"role": "user", "content": message})
            session["history"].append({"role": "assistant", "content": result.get("message", "")})

            return {
                "success": True,
                "data": {
                    "response": result.get("message", "Query completed"),
                    "hasServiceMatch": True,
                    "queryResult": result,
                }
            }

        elif intent_type == "creation":
            # Start creation flow
            session["intent_result"] = intent_result
            session["stage"] = "awaiting_confirmation"

            creation_type = intent_result.get("creation_type", "")
            if creation_type == "dividend_processing":
                response_text = "I understand you need to process fund dividend distribution. I'll create a SIPOC document to define this service. Confirm to proceed?"
            else:
                response_text = "I understand you need to create a new process. Confirm to proceed?"

            return {
                "success": True,
                "data": {
                    "response": response_text,
                    "hasServiceMatch": False,
                }
            }

        else:
            # Unknown intent - ask for clarification with options
            response_text = "I'm not sure about your request. Please select a service:"

            options = [
                {"id": "nav", "label": "Query fund NAV", "value": "query fund nav"},
                {"id": "dividend", "label": "Query dividend history", "value": "query dividend history"},
                {"id": "process", "label": "Process dividend distribution", "value": "process dividend distribution"},
            ]

            return {
                "success": True,
                "data": {
                    "response": response_text,
                    "hasServiceMatch": False,
                    "options": options,
                }
            }

    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        return {
            "success": False,
            "error": error_msg,
        }


@app.post("/api/execute")
async def execute_service(request: ExecuteRequest):
    """Execute the service based on confirmed SIPOC"""
    session_id = request.sessionId
    sipoc = request.sipoc
    processing_steps = []

    try:
        # Import workflow executor for step-by-step execution
        from service_module.mock_services.workflow_executor import WorkflowExecutor

        # Detect workflow type for service generation
        title = sipoc.get("title", "").lower() if sipoc.get("title") else ""
        process_str = str(sipoc.get("process", [])).lower()

        if "dividend" in title or "dividend" in process_str:
            workflow_type = "dividend_processing"
            service_name = "DividendProcessingService"
        elif "nav" in title or "nav" in process_str:
            workflow_type = "nav_query"
            service_name = "NAVQueryService"
        elif "compliance" in title or "compliance" in process_str:
            workflow_type = "compliance_report"
            service_name = "ComplianceReportService"
        elif "performance" in title or "performance" in process_str:
            workflow_type = "performance_query"
            service_name = "PerformanceQueryService"
        else:
            workflow_type = "generic"
            service_name = "WorkflowService"

        # Step 1: Analyze SIPOC
        processing_steps.append({
            "step": 1,
            "title": "Analyzing SIPOC Document",
            "thinking": "Parsing SIPOC structure and identifying service requirements...",
            "details": [
                {"type": "module", "name": "SIPOCAnalyzer", "description": "Extracting process steps and dependencies"},
                {"type": "rag", "name": "ServiceTemplateDB", "description": f"Matching to {service_name} template"}
            ]
        })

        # Step 2: Generate Service Class
        processing_steps.append({
            "step": 2,
            "title": "Generating Service Class",
            "thinking": f"Creating {service_name} class with workflow methods...",
            "details": [
                {"type": "agent", "name": "CodeGenerator", "description": "Generating service class structure"},
                {"type": "service", "name": service_name, "description": "Implementing SIPOC process steps"}
            ]
        })

        # Step 3: Configure Service Endpoints
        processing_steps.append({
            "step": 3,
            "title": "Configuring Service Endpoints",
            "thinking": "Setting up API endpoints and data connections...",
            "details": [
                {"type": "module", "name": "APIConfigurator", "description": "Creating REST endpoints"},
                {"type": "memory", "name": "ServiceRegistry", "description": "Registering service in catalog"}
            ]
        })

        # Step 4: Execute Workflow
        processing_steps.append({
            "step": 4,
            "title": "Executing Workflow",
            "thinking": "Running workflow with mock data to validate service...",
            "details": [
                {"type": "crew", "name": "WorkflowExecutor", "description": "Executing all process steps"},
                {"type": "action", "name": "DataValidation", "description": "Validating input/output data"}
            ]
        })

        # Execute workflow using the new WorkflowExecutor
        workflow_result = await WorkflowExecutor.execute_workflow(sipoc)

        if workflow_result.get("success"):
            summary = workflow_result.get("summary", {})
            actual_workflow_type = workflow_result.get("workflowType", workflow_type)

            # Step 5: Service Generation Complete
            processing_steps.append({
                "step": 5,
                "title": "Service Generation Complete",
                "thinking": f"Successfully generated {service_name} with {summary.get('total_steps', 0)} workflow steps.",
                "details": [
                    {"type": "result", "name": "ServiceCreated", "description": f"{service_name} is now available"},
                    {"type": "result", "name": "EndpointReady", "description": f"POST /api/services/{workflow_type}"}
                ]
            })

            # Generate code snippet based on workflow type
            process_steps = sipoc.get("process", [])
            process_methods = []
            for i, step in enumerate(process_steps[:6], 1):
                # Clean step name for method
                step_clean = step.replace("1. ", "").replace("2. ", "").replace("3. ", "").replace("4. ", "").replace("5. ", "").replace("6. ", "")
                method_name = "_".join(step_clean.lower().split()[:4]).replace("-", "_")
                process_methods.append(f"        self.{method_name}()")

            code_snippet = f'''class {service_name}:
    """
    Auto-generated service based on SIPOC workflow
    Workflow Type: {actual_workflow_type}
    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """

    def __init__(self):
        self.suppliers = {sipoc.get("suppliers", [])}
        self.customers = {sipoc.get("customers", [])}

    async def execute(self, input_data: dict) -> dict:
        """Execute the complete workflow"""
        result = {{"success": True, "steps": []}}

        # Process steps from SIPOC
{chr(10).join(process_methods)}

        return result

    async def validate_inputs(self, data: dict) -> bool:
        """Validate input data against SIPOC inputs"""
        required_inputs = {sipoc.get("inputs", [])}
        return True

    async def generate_outputs(self, result: dict) -> dict:
        """Generate outputs as defined in SIPOC"""
        outputs = {sipoc.get("outputs", [])}
        return {{"outputs": outputs, "data": result}}


# Service Registration
service_registry.register("{workflow_type}", {service_name}())

# API Endpoint
@app.post("/api/services/{workflow_type}")
async def execute_{workflow_type}(request: ServiceRequest):
    service = service_registry.get("{workflow_type}")
    return await service.execute(request.data)'''

            message = f"Service **{service_name}** has been successfully generated and deployed!"

        else:
            message = "Workflow execution failed"
            code_snippet = None

        # Clear session
        if session_id in chat_sessions:
            del chat_sessions[session_id]

        return {
            "success": True,
            "data": {
                "message": message,
                "processingSteps": processing_steps,
                "workflowResult": workflow_result,
                "serviceName": service_name,
                "codeSnippet": code_snippet
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    # Session management now uses sessionId from requests
    return {"status": "healthy", "service": "Custody Bank AI API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
