from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import time
import uuid
from typing import Dict, Any

app = FastAPI(title="Agentic Retrieval System v2.0", version="2.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mock data storage (in production, this would be a database)
mock_jobs: Dict[str, Dict[str, Any]] = {}
mock_dossiers: Dict[str, Dict[str, Any]] = {}

class ResearchQuery(BaseModel):
    query: str

class JobResponse(BaseModel):
    job_id: str

class JobStatus(BaseModel):
    status: str
    thesis_dossier_id: str = None
    antithesis_dossier_id: str = None

class EvidenceItem(BaseModel):
    id: str
    title: str
    content: str
    source: str
    confidence: float

class ResearchPlan(BaseModel):
    plan_id: str
    steps: list

class Dossier(BaseModel):
    dossier_id: str
    mission: str
    status: str
    research_plan: ResearchPlan
    evidence_items: list[EvidenceItem]
    summary_of_findings: str

@app.post("/v2/research", response_model=JobResponse)
async def create_research_job(query: ResearchQuery):
    """CP1-T102: Mock endpoint that accepts a query and returns a job ID"""
    job_id = f"mock-job-v2-{uuid.uuid4().hex[:8]}"
    
    # Create mock job record
    mock_jobs[job_id] = {
        "job_id": job_id,
        "query": query.query,
        "status": "RESEARCHING",
        "created_at": time.time()
    }
    
    # Simulate processing delay
    time.sleep(2)
    
    # Update status to indicate completion
    mock_jobs[job_id]["status"] = "AWAITING_VERIFICATION"
    
    # Create mock dossier IDs
    thesis_dossier_id = f"mock-thesis-{uuid.uuid4().hex[:8]}"
    antithesis_dossier_id = f"mock-antithesis-{uuid.uuid4().hex[:8]}"
    
    mock_jobs[job_id]["thesis_dossier_id"] = thesis_dossier_id
    mock_jobs[job_id]["antithesis_dossier_id"] = antithesis_dossier_id
    
    return JobResponse(job_id=job_id)

@app.get("/")
async def read_root():
    """Serve the main research initiation page"""
    return FileResponse("static/index.html")

@app.get("/research/{job_id}")
async def read_research_results(job_id: str):
    """Serve the research results page"""
    return FileResponse("static/research.html")

@app.get("/v2/research/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a research job"""
    if job_id not in mock_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = mock_jobs[job_id]
    
    # Simulate initial researching state
    if job["status"] == "RESEARCHING":
        return JobStatus(status="RESEARCHING")
    
    # Return completed state with dossier IDs
    return JobStatus(
        status=job["status"],
        thesis_dossier_id=job.get("thesis_dossier_id"),
        antithesis_dossier_id=job.get("antithesis_dossier_id")
    )

@app.get("/v2/dossiers/{dossier_id}", response_model=Dossier)
async def get_dossier(dossier_id: str):
    """CP1-T103: Get a mock dossier with hardcoded data"""
    
    # Create mock dossier data based on the ID
    if dossier_id.startswith("mock-thesis"):
        return Dossier(
            dossier_id=dossier_id,
            mission="Build the strongest possible case FOR the user's query.",
            status="AWAITING_VERIFICATION",
            research_plan=ResearchPlan(
                plan_id=f"plan-{dossier_id}",
                steps=[
                    {
                        "step_id": "step-001",
                        "description": "Analyze positive market indicators",
                        "status": "COMPLETED",
                        "tool_used": "market-data-api",
                        "tool_selection_justification": "Market data is essential for understanding positive trends",
                        "tool_query_rationale": "Focusing on growth metrics and positive sentiment indicators"
                    },
                    {
                        "step_id": "step-002", 
                        "description": "Review favorable expert opinions",
                        "status": "COMPLETED",
                        "tool_used": "expert-analysis-db",
                        "tool_selection_justification": "Expert opinions provide credibility to the thesis",
                        "tool_query_rationale": "Searching for bullish analyst reports and positive forecasts"
                    }
                ]
            ),
            evidence_items=[
                EvidenceItem(
                    id="ev-001",
                    title="Strong Market Growth Indicators",
                    content="Recent market analysis shows consistent growth patterns with 15% year-over-year increase in key metrics.",
                    source="Market Analysis Report 2024",
                    confidence=0.85
                ),
                EvidenceItem(
                    id="ev-002", 
                    title="Expert Bullish Sentiment",
                    content="Leading industry experts maintain positive outlook with 80% of surveyed analysts recommending strong buy positions.",
                    source="Expert Consensus Survey",
                    confidence=0.90
                )
            ],
            summary_of_findings="The evidence strongly supports a positive outlook with robust market fundamentals and expert consensus backing the thesis."
        )
    else:
        # Antithesis dossier
        return Dossier(
            dossier_id=dossier_id,
            mission="Build the strongest possible case AGAINST the user's query.",
            status="AWAITING_VERIFICATION", 
            research_plan=ResearchPlan(
                plan_id=f"plan-{dossier_id}",
                steps=[
                    {
                        "step_id": "step-001",
                        "description": "Identify market risks and challenges",
                        "status": "COMPLETED",
                        "tool_used": "risk-assessment-api",
                        "tool_selection_justification": "Risk analysis is crucial for understanding potential downsides",
                        "tool_query_rationale": "Focusing on volatility indicators and negative market signals"
                    },
                    {
                        "step_id": "step-002",
                        "description": "Review bearish expert opinions", 
                        "status": "COMPLETED",
                        "tool_used": "expert-analysis-db",
                        "tool_selection_justification": "Contrary expert opinions provide balance to the analysis",
                        "tool_query_rationale": "Searching for bearish analyst reports and risk warnings"
                    }
                ]
            ),
            evidence_items=[
                EvidenceItem(
                    id="ev-003",
                    title="Market Volatility Concerns",
                    content="Recent market volatility has increased by 25% with several concerning indicators pointing to potential instability.",
                    source="Volatility Analysis Report",
                    confidence=0.80
                ),
                EvidenceItem(
                    id="ev-004",
                    title="Expert Risk Warnings", 
                    content="20% of industry experts have issued cautionary statements about current market conditions and potential downside risks.",
                    source="Risk Assessment Survey",
                    confidence=0.75
                )
            ],
            summary_of_findings="Significant risks and challenges exist that warrant careful consideration, with multiple experts highlighting potential downside scenarios."
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 