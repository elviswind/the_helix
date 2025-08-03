
### **Design: MCP (Master Control Program) Server**

#### **1. Role within the AR v3.0 Architecture**

The MCP Server is the central nervous system of the Agentic Retrieval framework. It is a backend service that:

1.  **Listens** for research requests via a REST API.
2.  **Orchestrates** the entire Dialectical Research workflow, from query decomposition to final synthesis.
3.  **Manages** the state of all research jobs, plans, and evidence dossiers.
4.  **Provides** a standardized `Tooling Layer` for the research agents to interact with all data sources (10-Ks, XBRL, databases, etc.).
5.  **Serves** the `Evidence Dossiers` to the `Dialectical Review Interface` for human adjudication.

This design shifts from a stateless script to a persistent, asynchronous server, using a modern web framework, a task queue, and a database.

#### **2. Core Technologies**

*   **Web Framework:** **FastAPI**. Ideal for its asynchronous capabilities (crucial for long-running agent tasks), automatic OpenAPI (Swagger) documentation, and Pydantic-based data validation.
*   **Task Queue:** **Celery** with **Redis** or **RabbitMQ**. Essential for managing the parallel, long-running `Research Agent` jobs in the background without blocking the API.
*   **Database:** **PostgreSQL** or **SQLite** (for simpler setups). Used for state management, storing `ResearchJob` status, `ResearchPlans`, and `EvidenceDossiers`.
*   **ORM:** **SQLAlchemy** or **SQLModel**. To map Python objects to database tables for state management.
*   **LLM Framework:** **LangChain** or **LlamaIndex**. To provide the agentic constructs, LLM integrations, and tool-use abstractions.

#### **3. MCP Server Architecture**

The server is composed of four main layers:

1.  **API Layer (FastAPI):** The external interface. Exposes REST endpoints for initiating research, checking status, retrieving dossiers, and submitting human approvals.
2.  **Orchestration Layer (Celery & Business Logic):** The "brain" of the server. This is where the `Orchestrator Agent` logic resides. It translates API calls into background tasks.
3.  **Agent & Tooling Layer:** Contains the definition for our `ResearchAgent` and the library of `Tools` they can use. This is where the refactored `XBRLFactTool` and `DocumentSectionTool` (from our previous design) will live.
4.  **State Management Layer (Database & ORM):** The persistent memory of the system. It tracks the progress and artifacts of every research job.



---

#### **4. Detailed Component Design**

**4.1. API Layer (FastAPI Endpoints)**

The API is the contract between the MCP Server and any client (e.g., the `Dialectical Review Interface`).

```python
# main.py (FastAPI App)
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from orchestrator import start_dialectical_research
from state_manager import get_job_status, get_dossiers, record_approval

app = FastAPI(title="AR v3.0 MCP Server")

class ResearchRequest(BaseModel):
    query: str
    user_id: str

@app.post("/research/start", status_code=202)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Initiates a new dialectical research job."""
    job_id = start_dialectical_research(request.query, request.user_id, background_tasks)
    return {"message": "Research job initiated.", "job_id": job_id}

@app.get("/research/{job_id}/status")
async def check_status(job_id: str):
    """Checks the status of a research job."""
    return get_job_status(job_id)

@app.get("/research/{job_id}/dossiers")
async def fetch_dossiers(job_id: str):
    """Fetches the Thesis and Antithesis dossiers for review."""
    return get_dossiers(job_id)

@app.post("/dossiers/{dossier_id}/approve")
async def approve_dossier(dossier_id: str, background_tasks: BackgroundTasks):
    """Records human approval for a dossier and may trigger synthesis."""
    result = record_approval(dossier_id, background_tasks)
    return result
```

**4.2. Orchestration Layer (Celery & Orchestrator Logic)**

This layer manages the workflow.

```python
# orchestrator.py
import uuid
from celery_worker import run_research_agent_task, run_synthesis_agent_task
from state_manager import create_new_job, update_job_on_approval

def start_dialectical_research(query: str, user_id: str, background_tasks):
    """
    The Orchestrator Agent's primary function.
    1. Creates the job record in the DB.
    2. Decomposes the query.
    3. Launches two parallel background tasks.
    """
    job_id = str(uuid.uuid4())
    
    # 1. Create job in database
    thesis_dossier_id, antithesis_dossier_id = create_new_job(job_id, query, user_id)

    # 2. Decompose query (could be a simple rule or an LLM call)
    thesis_mission = f"Build the strongest possible, evidence-based case FOR the following: {query}"
    antithesis_mission = f"Build the strongest possible, evidence-based case AGAINST the following: {query}"

    # 3. Launch background tasks using Celery
    background_tasks.add_task(run_research_agent_task.delay, job_id, thesis_dossier_id, thesis_mission)
    background_tasks.add_task(run_research_agent_task.delay, job_id, antithesis_dossier_id, antithesis_mission)
    
    return job_id

def trigger_synthesis_if_ready(job_id: str, background_tasks):
    """Called after a dossier is approved to check if both are ready."""
    job = get_job_status(job_id)
    if job.thesis_approved and job.antithesis_approved:
        background_tasks.add_task(run_synthesis_agent_task.delay, job_id)
```

**4.3. Agent & Tooling Layer (The Refactored Tools)**

The previous `sec_form_parser` and `xbrl_parser` are now formalized as `Tools` that any agent can use. This layer is highly extensible.

```python
# tools.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
# Import our refactored parsers
from parsers.xbrl_parser import get_financial_fact
from parsers.html_parser import get_section_text

# --- XBRL Fact Tool ---
class XBRLInput(BaseModel):
    symbol: str = Field(description="Company stock symbol")
    year: int = Field(description="Filing year")
    concept: str = Field(description="The financial metric, e.g., 'Revenue', 'NetIncome'")

class XBRLFactTool(BaseTool):
    name = "xbrl_financial_fact_retriever"
    description = "Retrieves a specific numerical financial fact (like Revenue, NetIncome) for a given company and year from its XBRL filing."
    args_schema: Type[BaseModel] = XBRLInput

    def _run(self, symbol: str, year: int, concept: str):
        return get_financial_fact(symbol, year, concept)

# --- Document Section Tool ---
class DocumentSectionInput(BaseModel):
    symbol: str = Field(description="Company stock symbol")
    year: int = Field(description="Filing year")
    section: str = Field(description="The 10-K section, e.g., '1A' for Risk Factors, '7' for MD&A")

class DocumentSectionTool(BaseTool):
    name = "document_section_retriever"
    description = "Retrieves the full text of a specific section (like 'Risk Factors') from a company's 10-K HTML filing."
    args_schema: Type[BaseModel] = DocumentSectionInput

    def _run(self, symbol: str, year: int, section: str):
        return get_section_text(symbol, year, section)

# The agent would be initialized with a list of these tools
available_tools = [XBRLFactTool(), DocumentSectionTool()]
```

**4.4. State Management Layer (Data Models)**

Using Pydantic/SQLModel, we define the structure of our database records, which directly aligns with the JSON in the AR v3.0 design document.

```python
# models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ProxyHypothesis(BaseModel):
    unobservable_claim: str
    deductive_chain: str
    observable_proxy: str

class ResearchStep(BaseModel):
    step_id: str
    description: str
    status: str # e.g., PENDING, RUNNING, COMPLETED, FAILED
    data_gap_identified: Optional[str] = None
    proxy_hypothesis: Optional[ProxyHypothesis] = None
    tool_used: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output_summary: Optional[str] = None
    evidence_ids: List[str] = []

class EvidenceItem(BaseModel):
    evidence_id: str
    finding: str
    source_document_id: str
    source_location: str
    tags: List[str] = []

class EvidenceDossier(BaseModel):
    dossier_id: str
    mission: str
    is_approved: bool = False
    plan: List[ResearchStep] = []
    evidence: List[EvidenceItem] = []
    summary: Optional[str] = None

class ResearchJob(BaseModel):
    job_id: str
    user_id: str
    initial_query: str
    status: str # e.g., PENDING, RUNNING, AWAITING_APPROVAL, SYNTHESIZING, COMPLETED
    thesis_dossier: EvidenceDossier
    antithesis_dossier: EvidenceDossier
    final_report: Optional[str] = None
```

#### **5. Core Workflow with MCP Server (Nike Example)**

1.  **Request:** A UI client sends a `POST` request to `/research/start` with the query "Evaluate the long-term investment case for Nike (NKE)."
2.  **Orchestration:**
    *   The `start_dialectical_research` function is called.
    *   It creates a `ResearchJob` record in the database with status `PENDING`.
    *   It defines the Thesis/Antithesis missions.
    *   It queues two background tasks: `run_research_agent_task.delay(job_id, 'thesis', ...)` and `run_research_agent_task.delay(job_id, 'antithesis', ...)`.
    *   The API immediately returns a `202 Accepted` with the `job_id`.
3.  **Execution (in background via Celery):**
    *   **Antithesis Agent** starts its `ResearchPlan`. It decides to check for an eroding moat.
    *   It forms a **Proxy Hypothesis**: "eroding moat -> rising inventory".
    *   It needs an observable proxy: "Total Inventory" from the last 3 years.
    *   It selects the `XBRLFactTool` and executes it with `(symbol='NKE', year=2023, concept='Inventory')`.
    *   The tool returns the numerical data. The agent records this as an `EvidenceItem` and updates its `ResearchPlan` and `EvidenceDossier` in the database.
    *   The **Thesis Agent** runs its own plan in parallel, likely using the same tool to look at `GrossProfit`.
4.  **Human Adjudication:**
    *   The `Dialectical Review Interface` polls `/research/{job_id}/status`. When the status becomes `AWAITING_APPROVAL`, it enables the review button.
    *   The UI calls `/research/{job_id}/dossiers` to fetch both dossiers and displays them side-by-side.
    *   The human verifier follows the **Structured Verification Protocol** and clicks "Approve" for the Thesis dossier. This sends a `POST` to `/dossiers/{thesis_dossier_id}/approve`.
    *   The `record_approval` function updates the dossier's `is_approved` flag to `True` and checks if both are now approved.
5.  **Synthesis:**
    *   Once the Antithesis dossier is also approved, the `trigger_synthesis_if_ready` function queues the final task: `run_synthesis_agent_task.delay(job_id)`.
    *   The Synthesis Agent runs, reads both approved dossiers from the database, generates the final report, and saves it to the `ResearchJob` record, updating the status to `COMPLETED`.
6.  **Output:** The user can now retrieve the final, balanced brief from the UI, which fetches it from the server.

This MCP Server design provides the robust, scalable, and auditable foundation required to bring the powerful vision of the AR v3.0 system to life. It correctly separates concerns, enabling parallel development of the agent's intelligence, the UI, and the underlying tooling.