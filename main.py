from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import time
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import threading
from celery.result import AsyncResult

from models import get_db, create_tables, Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem, SessionLocal, LLMRequest, LLMRequestStatus, LLMRequestType, ToolRequest, ToolRequestStatus, ToolRequestType, DossierStatus, JobStatus, RevisionFeedback, SynthesisReport
from services import CannedResearchService
from orchestrator_agent import orchestrator_task
from synthesis_agent import synthesis_agent_task
from config import config

app = FastAPI(title=config.API_TITLE, version=config.API_VERSION)

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

# Create database tables on startup
create_tables()

class ResearchQuery(BaseModel):
    query: str

class JobResponse(BaseModel):
    job_id: str

class JobStatusResponse(BaseModel):
    status: str
    original_query: str | None = None
    thesis_dossier_id: str | None = None
    antithesis_dossier_id: str | None = None
    task_status: str | None = None
    task_progress: str | None = None

class EvidenceItemResponse(BaseModel):
    id: str
    title: str
    content: str
    source: str
    confidence: float
    tags: Optional[List[str]] = None  # New field for proxy evidence tags

class ResearchPlanStepResponse(BaseModel):
    step_id: str
    step_number: int
    description: str
    status: str
    tool_used: str | None = None
    tool_selection_justification: str | None = None
    tool_query_rationale: str | None = None
    # New fields for Deductive Proxy Framework
    data_gap_identified: str | None = None
    proxy_hypothesis: Dict[str, str] | None = None

class ResearchPlanResponse(BaseModel):
    plan_id: str
    steps: List[ResearchPlanStepResponse]

class DossierResponse(BaseModel):
    dossier_id: str
    mission: str
    status: str
    research_plan: ResearchPlanResponse
    evidence_items: List[EvidenceItemResponse]
    summary_of_findings: str

# New models for Checkpoint 6 - Human Adjudicator
class DossierReviewRequest(BaseModel):
    action: str  # "APPROVE" or "REVISE"
    feedback: str | None = None  # Required for REVISE action

class DossierReviewResponse(BaseModel):
    success: bool
    message: str
    job_status: str | None = None

class VerificationChecklist(BaseModel):
    review_summary: bool = False
    validate_proxy_logic: bool = False
    spot_check_evidence: bool = False
    audit_reasoning: bool = False

class LLMRequestResponse(BaseModel):
    id: str
    request_type: str
    status: str
    prompt: str
    response: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str
    dossier_id: str | None = None

class LLMRequestsResponse(BaseModel):
    pending_requests: List[LLMRequestResponse]
    in_progress_requests: List[LLMRequestResponse]
    completed_requests: List[LLMRequestResponse]
    failed_requests: List[LLMRequestResponse]

class ToolRequestResponse(BaseModel):
    id: str
    request_type: str
    tool_name: str
    query: str | None = None
    status: str
    response: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str
    dossier_id: str | None = None
    step_id: str | None = None

class ToolRequestsResponse(BaseModel):
    pending_requests: List[ToolRequestResponse]
    in_progress_requests: List[ToolRequestResponse]
    completed_requests: List[ToolRequestResponse]
    failed_requests: List[ToolRequestResponse]

@app.post("/v2/research", response_model=JobResponse)
async def create_research_job(query: ResearchQuery, db: Session = Depends(get_db)):
    """CP3-T301: Create a real job and enqueue Orchestrator Agent task"""
    
    # Create job and dossiers (still using the service for job/dossier creation)
    job = CannedResearchService.create_job_with_dossiers(db, query.query)
    
    # Enqueue the Orchestrator Agent task instead of using canned processing
    orchestrator_task.delay(job.id)
    
    return JobResponse(job_id=job.id)

@app.get("/")
async def read_root():
    """Serve the main research initiation page"""
    return FileResponse("static/index.html")

@app.get("/research/{job_id}")
async def read_research_results(job_id: str):
    """Serve the research results page"""
    return FileResponse("static/research.html")

@app.get("/report")
async def read_report_viewer():
    """Serve the synthesis report viewer page"""
    return FileResponse("static/report.html")

@app.get("/v2/research/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of a research job from database and Celery task"""
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get dossier IDs
    dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
    thesis_dossier_id = None
    antithesis_dossier_id = None
    
    for dossier in dossiers:
        if dossier.dossier_type.value == "THESIS":
            thesis_dossier_id = dossier.id
        else:
            antithesis_dossier_id = dossier.id
    
    # Check Celery task status (for jobs that are still processing)
    task_status = None
    task_progress = None
    
    if job.status.value in ["PENDING", "RESEARCHING"]:
        # Try to get task result (this is a simplified approach)
        # In a real implementation, you'd store the task ID with the job
        try:
            # For now, we'll just indicate that the task is running
            task_status = "PROGRESS"
            task_progress = "Orchestrator Agent is generating dialectical missions and research plans"
        except:
            task_status = "UNKNOWN"
    
    return JobStatusResponse(
        status=job.status.value,
        original_query=job.query,
        thesis_dossier_id=thesis_dossier_id,
        antithesis_dossier_id=antithesis_dossier_id,
        task_status=task_status,
        task_progress=task_progress
    )

@app.get("/v2/dossiers/{dossier_id}", response_model=DossierResponse)
async def get_dossier(dossier_id: str, db: Session = Depends(get_db)):
    """CP2-T203: Get a real dossier with data from the database"""
    
    dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")
    
    # Get research plan
    research_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == dossier_id).first()
    if not research_plan:
        raise HTTPException(status_code=404, detail="Research plan not found")
    
    # Get plan steps
    steps = db.query(ResearchPlanStep).filter(ResearchPlanStep.research_plan_id == research_plan.id).order_by(ResearchPlanStep.step_number).all()
    
    # Get evidence items
    evidence_items = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == dossier_id).all()
    
    return DossierResponse(
        dossier_id=dossier.id,
        mission=dossier.mission,
        status=dossier.status.value,
        research_plan=ResearchPlanResponse(
            plan_id=research_plan.id,
            steps=[
                ResearchPlanStepResponse(
                    step_id=step.id,
                    step_number=step.step_number,
                    description=step.description,
                    status=step.status.value,
                    tool_used=step.tool_used,
                    tool_selection_justification=step.tool_selection_justification,
                    tool_query_rationale=step.tool_query_rationale,
                    data_gap_identified=step.data_gap_identified,
                    proxy_hypothesis=step.proxy_hypothesis
                ) for step in steps
            ]
        ),
        evidence_items=[
            EvidenceItemResponse(
                id=item.id,
                title=item.title,
                content=item.content,
                source=item.source,
                confidence=item.confidence,
                tags=item.tags
            ) for item in evidence_items
        ],
        summary_of_findings=dossier.summary_of_findings or ""
    )

@app.get("/v2/research/{job_id}/llm-requests", response_model=LLMRequestsResponse)
async def get_llm_requests(job_id: str, db: Session = Depends(get_db)):
    """Get all LLM requests for a specific job"""
    
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all LLM requests for this job
    llm_requests = db.query(LLMRequest).filter(LLMRequest.job_id == job_id).order_by(LLMRequest.created_at.desc()).all()
    
    # Categorize requests by status
    pending_requests = []
    in_progress_requests = []
    completed_requests = []
    failed_requests = []
    
    for req in llm_requests:
        request_data = LLMRequestResponse(
            id=req.id,
            request_type=req.request_type.value,
            status=req.status.value,
            prompt=req.prompt[:200] + "..." if len(req.prompt) > 200 else req.prompt,  # Truncate long prompts
            response=req.response,
            error_message=req.error_message,
            started_at=req.started_at.isoformat() if req.started_at else None,
            completed_at=req.completed_at.isoformat() if req.completed_at else None,
            created_at=req.created_at.isoformat(),
            dossier_id=req.dossier_id
        )
        
        if req.status == LLMRequestStatus.PENDING:
            pending_requests.append(request_data)
        elif req.status == LLMRequestStatus.IN_PROGRESS:
            in_progress_requests.append(request_data)
        elif req.status == LLMRequestStatus.COMPLETED:
            completed_requests.append(request_data)
        elif req.status == LLMRequestStatus.FAILED:
            failed_requests.append(request_data)
    
    return LLMRequestsResponse(
        pending_requests=pending_requests,
        in_progress_requests=in_progress_requests,
        completed_requests=completed_requests,
        failed_requests=failed_requests
    )

@app.get("/v2/research/{job_id}/tool-requests", response_model=ToolRequestsResponse)
async def get_tool_requests(job_id: str, db: Session = Depends(get_db)):
    """Get all tool requests for a job, grouped by status"""
    
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all tool requests for the job
    tool_requests = db.query(ToolRequest).filter(ToolRequest.job_id == job_id).all()
    
    # Group by status
    pending_requests = []
    in_progress_requests = []
    completed_requests = []
    failed_requests = []
    
    for req in tool_requests:
        response = ToolRequestResponse(
            id=req.id,
            request_type=req.request_type.value,
            tool_name=req.tool_name,
            query=req.query,
            status=req.status.value,
            response=req.response,
            error_message=req.error_message,
            started_at=req.started_at.isoformat() if req.started_at else None,
            completed_at=req.completed_at.isoformat() if req.completed_at else None,
            created_at=req.created_at.isoformat(),
            dossier_id=req.dossier_id,
            step_id=req.step_id
        )
        
        if req.status == ToolRequestStatus.PENDING:
            pending_requests.append(response)
        elif req.status == ToolRequestStatus.IN_PROGRESS:
            in_progress_requests.append(response)
        elif req.status == ToolRequestStatus.COMPLETED:
            completed_requests.append(response)
        elif req.status == ToolRequestStatus.FAILED:
            failed_requests.append(response)
    
    return ToolRequestsResponse(
        pending_requests=pending_requests,
        in_progress_requests=in_progress_requests,
        completed_requests=completed_requests,
        failed_requests=failed_requests
    )

@app.get("/v2/research/recent")
async def get_recent_jobs(db: Session = Depends(get_db)):
    """Get recent jobs for testing purposes"""
    
    # Get the 5 most recent jobs
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(5).all()
    
    return [
        {
            "id": job.id,
            "query": job.query,
            "status": job.status.value,
            "created_at": job.created_at.isoformat()
        }
        for job in jobs
    ]

# Checkpoint 6 - Human Adjudicator API Endpoints

@app.post("/v3/dossiers/{dossier_id}/review", response_model=DossierReviewResponse)
async def review_dossier(dossier_id: str, review_request: DossierReviewRequest, db: Session = Depends(get_db)):
    """Review and approve or request revision for a dossier"""
    
    # Verify dossier exists
    dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")
    
    # Verify dossier is in correct status
    if dossier.status != DossierStatus.AWAITING_VERIFICATION:
        raise HTTPException(status_code=400, detail=f"Dossier is in {dossier.status.value} status, cannot be reviewed")
    
    if review_request.action == "APPROVE":
        # Approve the dossier
        dossier.status = DossierStatus.APPROVED
        db.commit()
        
        # Check if both dossiers are now approved
        job = dossier.job
        thesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job.id,
            EvidenceDossier.dossier_type == "THESIS"
        ).first()
        antithesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job.id,
            EvidenceDossier.dossier_type == "ANTITHESIS"
        ).first()
        
        if thesis_dossier.status == DossierStatus.APPROVED and antithesis_dossier.status == DossierStatus.APPROVED:
            # Both dossiers approved - trigger synthesis
            job.status = JobStatus.COMPLETE
            db.commit()
            
            # Trigger synthesis agent task
            synthesis_agent_task.delay(job.id)
            
            return DossierReviewResponse(
                success=True,
                message="Dossier approved. Both dossiers approved - synthesis will begin.",
                job_status="COMPLETE"
            )
        else:
            return DossierReviewResponse(
                success=True,
                message="Dossier approved. Awaiting approval of other dossier.",
                job_status="AWAITING_VERIFICATION"
            )
    
    elif review_request.action == "REVISE":
        if not review_request.feedback:
            raise HTTPException(status_code=400, detail="Feedback is required for revision requests")
        
        # Store revision feedback
        revision_feedback = RevisionFeedback(
            id=f"rev-{uuid.uuid4().hex[:8]}",
            dossier_id=dossier_id,
            feedback=review_request.feedback
        )
        db.add(revision_feedback)
        
        # Request revision
        dossier.status = DossierStatus.REVISION_REQUESTED
        db.commit()
        
        # Re-enqueue research agent task
        from research_agent import research_agent_task
        research_agent_task.delay(dossier_id)
        
        return DossierReviewResponse(
            success=True,
            message="Revision requested. Research agent will be re-enqueued with feedback.",
            job_status="REVISING"
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'APPROVE' or 'REVISE'")

@app.get("/v3/jobs/{job_id}/verification-status")
async def get_verification_status(job_id: str, db: Session = Depends(get_db)):
    """Get the verification status for both dossiers in a job"""
    
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get both dossiers
    thesis_dossier = db.query(EvidenceDossier).filter(
        EvidenceDossier.job_id == job_id,
        EvidenceDossier.dossier_type == "THESIS"
    ).first()
    antithesis_dossier = db.query(EvidenceDossier).filter(
        EvidenceDossier.job_id == job_id,
        EvidenceDossier.dossier_type == "ANTITHESIS"
    ).first()
    
    if not thesis_dossier or not antithesis_dossier:
        raise HTTPException(status_code=404, detail="Dossiers not found")
    
    return {
        "job_id": job_id,
        "job_status": job.status.value,
        "thesis_dossier": {
            "id": thesis_dossier.id,
            "status": thesis_dossier.status.value,
            "mission": thesis_dossier.mission
        },
        "antithesis_dossier": {
            "id": antithesis_dossier.id,
            "status": antithesis_dossier.status.value,
            "mission": antithesis_dossier.mission
        }
    }

@app.get("/v3/jobs/{job_id}/report")
async def get_final_report(job_id: str, db: Session = Depends(get_db)):
    """Get the final synthesis report for a completed job"""
    
    # Verify job exists and is complete
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Job is not complete. Synthesis report not available yet.")
    
    # Get the synthesis report
    synthesis_report = db.query(SynthesisReport).filter(SynthesisReport.job_id == job_id).first()
    if not synthesis_report:
        raise HTTPException(status_code=404, detail="Synthesis report not found")
    
    return {
        "job_id": job_id,
        "original_query": job.query,
        "report_id": synthesis_report.id,
        "content": synthesis_report.content,
        "created_at": synthesis_report.created_at.isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.get_port("fastapi_main"),
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL
    ) 