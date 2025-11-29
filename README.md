# Custody Bank AI Automation Platform

## Theme

**Agentic AI for Custody Banking Operations Automation**

This project leverages Multi-Agent AI architecture combined with RAG (Retrieval-Augmented Generation) to intelligently automate custody banking operations, including email analysis, fund management queries, dividend processing, and dynamic business workflow generation.

---

## Problem Statement

Custody banks handle massive volumes of daily operational requests through emails, including:
- Fund NAV (Net Asset Value) queries
- Dividend distribution processing
- Compliance reporting
- Performance analysis requests

**Current Challenges:**
1. **Manual Processing:** Staff must read, classify, and route emails manually, leading to inefficiency
2. **Service Discovery:** Finding the right service/workflow for each request requires domain expertise
3. **No Existing Service:** When no matching service exists, creating new workflows is time-consuming
4. **Repetitive Work:** Similar requests require the same manual effort each time

**Our Solution:**
An AI-powered platform that:
- Automatically analyzes incoming emails and detects user intent
- Matches requests to existing services using semantic search (RAG)
- Executes matched services and returns formatted results
- When no service exists, generates new workflows using SIPOC methodology and creates executable services dynamically

---

## Key Features Implemented

### 1. Intelligent Email Analysis
- Automatic email content parsing and intent detection
- Support for both query-type and creation-type requests
- Multi-language support (English & Chinese)

### 2. Dual-Flow Processing Architecture

**Flow 1 - Query Execution (Existing Service Found)**
```
Email → Intent Analysis → Service Matching → Service Execution → Results
```
- Semantic service matching using ChromaDB vector search
- Keyword-based fallback matching for reliability
- Pre-built services: Fund NAV, Dividends, Performance, Compliance Reports

**Flow 2 - Service Creation (No Existing Service)**
```
Email → Intent Analysis → No Match → SIPOC Generation → Multi-Agent Collaboration →
Workflow Design → Service Code Generation → Service Registration → Execution
```
- Automatic SIPOC document generation
- Interactive multi-role collaboration (AI Agent, BA Agent, Tech Agent)
- Dynamic Python service code generation
- Automatic service registration for future reuse

### 3. Multi-Agent Collaboration System
- **Intent Agent:** Analyzes and classifies user requests
- **Executor Agent:** Executes matched services with proper parameters
- **Process Designer Agent:** Designs BPMN 2.0 workflows from requirements
- **Service Builder Agent:** Generates executable service code

### 4. RAG-Based Service Discovery
- ChromaDB vector database for semantic service matching
- Service embeddings using Sentence-Transformers
- Confidence scoring with threshold-based decisions
- Memory system for learning from interactions

### 5. Interactive BPMN 2.0 Workflow Visualization
- Visual workflow diagram generation
- Swimlane-based process representation
- Interactive "Generate Service" functionality

### 6. Real-time Processing Feedback
- Step-by-step analysis progress display
- Collapsible session management
- Editable analysis results before confirmation

### 7. User Feedback Loop
- Thumbs up/down feedback on AI responses
- Automatic component updates based on feedback (Service, Memory, RAG)
- Continuous learning capability

---

## Technical Design & Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              React Frontend (UI)                             │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ Sidebar  │ │EmailList │ │AnalysisPanel  │ │ChatWindow│ │ BPMWorkflow  │ │
│  └──────────┘ └──────────┘ └───────────────┘ └──────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend (api_server.py)                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────────┐   │
│  │ /analyze   │ │ /chat      │ │ /execute   │ │ /emails, /funds, etc.  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────────────┐
│    Agent Module      │ │    RAG Module    │ │      Service Module          │
│ ┌──────────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────────────────┐ │
│ │  Intent Agent    │ │ │ │ServiceMatcher│ │ │ │   Service Registry       │ │
│ │  Executor Agent  │ │ │ │  (ChromaDB)  │ │ │ │   - getFundNAV           │ │
│ │  Process Designer│ │ │ ├──────────────┤ │ │ │   - getFundDividend      │ │
│ │  Service Builder │ │ │ │Memory Manager│ │ │ │   - processDividend      │ │
│ └──────────────────┘ │ │ │  (Episodic)  │ │ │ │   - [Dynamic Services]   │ │
│ ┌──────────────────┐ │ │ └──────────────┘ │ │ ├──────────────────────────┤ │
│ │   Query Crew     │ │ └──────────────────┘ │ │   Workflow Executor      │ │
│ │   Creation Crew  │ │                      │ │   SIPOC Generator        │ │
│ └──────────────────┘ │                      │ │   Service Generator      │ │
└──────────────────────┘                      │ └──────────────────────────┘ │
          │                                   └──────────────────────────────┘
          ▼
┌──────────────────────┐
│   AWS Bedrock        │
│   Claude 3.5 Sonnet  │
└──────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18.2, TypeScript 5.3, Vite 5.0 |
| Backend | Python 3.10+, FastAPI |
| AI/LLM | AWS Bedrock (Claude 3.5 Sonnet) |
| Vector DB | ChromaDB with Sentence-Transformers |
| Agent Framework | CrewAI, LlamaIndex |
| Chat UI | Chainlit (Alternative interface) |

### Directory Structure

```
hackathon2025/
├── agent_module/              # Multi-Agent System
│   ├── agents/                # Individual AI agents
│   │   ├── intent_agent.py    # Intent recognition
│   │   ├── executor_agent.py  # Service execution
│   │   ├── process_designer.py# Workflow design
│   │   └── service_builder.py # Code generation
│   ├── crews/                 # Agent orchestration
│   │   ├── query_crew.py      # Query flow handling
│   │   └── creation_crew.py   # Creation flow handling
│   └── bedrock_client.py      # AWS Bedrock integration
│
├── rag_module/                # RAG System
│   ├── retrieval/
│   │   └── service_matcher.py # Semantic service matching
│   ├── memory/
│   │   ├── episodic_memory.py # Interaction history
│   │   └── memory_manager.py  # Memory orchestration
│   └── chroma_client.py       # Vector DB client
│
├── service_module/            # Business Services
│   ├── mock_services/
│   │   ├── fund_services.py   # Fund operations
│   │   ├── service_registry.py# Service management
│   │   └── workflow_executor.py
│   ├── sipoc/
│   │   ├── templates.py       # SIPOC templates
│   │   └── sipoc_generator.py
│   └── service_generator.py   # Dynamic service creation
│
├── ui/                        # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript definitions
│   │   └── App.tsx            # Main application
│   └── package.json
│
├── api_server.py              # FastAPI backend server
├── app.py                     # Chainlit entry point
├── config.py                  # Global configuration
└── requirements.txt           # Python dependencies
```

### Key Design Patterns

1. **Multi-Agent Architecture**
   - Specialized agents for different tasks
   - CrewAI-based orchestration for complex workflows
   - Asynchronous agent communication

2. **RAG with Fallback Strategy**
   - Primary: Vector similarity search (ChromaDB)
   - Fallback: Keyword-based matching
   - Confidence threshold for decision making

3. **SIPOC-Driven Workflow Design**
   - Suppliers → Inputs → Process → Outputs → Customers
   - Standardized business process documentation
   - Template-based generation with AI enhancement

4. **Service Registry Pattern**
   - Centralized service discovery and management
   - Dynamic service registration
   - Consistent invocation interface

5. **Event-Driven UI Updates**
   - Real-time processing step feedback
   - Session-based message management
   - Optimistic UI updates with confirmation

### Data Flow

**Flow 1: Query with Existing Service**
```
1. User selects email(s) and clicks "Analyze"
2. Backend analyzes email content, detects intent
3. ServiceMatcher finds matching service via RAG
4. ExecutorAgent executes service with extracted parameters
5. Results formatted and displayed in chat
```

**Flow 2: Create New Service**
```
1. User selects email(s) and clicks "Analyze"
2. Backend detects creation intent, no matching service
3. Multi-Agent Collaboration begins:
   - AI Agent: Understands requirements
   - BA Agent: Defines business process
   - Tech Agent: Specifies technical requirements
4. SIPOC document generated and displayed
5. User clicks "Generate Workflow" → BPMN diagram shown
6. User clicks "Generate Service" → Python code generated
7. Service registered and executed
8. Results returned to user
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/emails` | GET | Retrieve email list |
| `/api/analyze` | POST | Analyze selected emails |
| `/api/chat` | POST | Send chat message |
| `/api/execute` | POST | Execute workflow/service |
| `/api/funds` | GET | Get fund list |
| `/api/health` | GET | Health check |

### Running the Application

**Backend:**
```bash
cd hackathon2025
pip install -r requirements.txt
python api_server.py
```

**Frontend:**
```bash
cd hackathon2025/ui
npm install
npm run dev
```

**Access:**
- Frontend UI: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Demo Scenarios

### Scenario 1: Fund NAV Query (Flow 1)
1. Select email "Fund NAV Report"
2. Click "Analyze" → System detects query intent
3. Matches to `getFundNAV` service
4. Returns fund NAV data in formatted table

### Scenario 2: Dividend Processing (Flow 2)
1. Select email "Dividend Distribution Request"
2. Click "Analyze" → No existing service found
3. Multi-Agent collaboration generates SIPOC
4. Click "Generate Workflow" → BPMN diagram displayed
5. Click "Generate Service" → Service created and executed
6. Dividend processing results returned

---

## Future Enhancements

- Real database integration (replace mock data)
- Additional workflow templates
- Enhanced feedback learning system
- Multi-tenant support
- Audit logging and compliance tracking
