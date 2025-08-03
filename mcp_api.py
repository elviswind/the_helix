from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from models import get_db, create_tables, Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem, SessionLocal, JobStatus, DossierStatus, DossierType
from pydantic_models import (
    ResearchRequest, ResearchResponse, JobStatusResponse, 
    DossierApprovalRequest, DossierApprovalResponse,
    ToolExecutionRequest, ToolExecutionResponse,
    SynthesisRequest, SynthesisResponse,
    VerificationStatus, VerificationChecklist
)
from orchestrator import (
    start_dialectical_research, get_job_status, get_dossiers, 
    record_approval, trigger_synthesis_if_ready
)
from tools import execute_tool, get_tool_by_name, XBRLFactTool, DocumentSectionTool, MCPTool, LLMTool, SECDataTool
from synthesis_agent import synthesis_agent_task

app = FastAPI(title="AR v3.0 MCP Server", version="3.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
create_tables()

# Add manifest endpoint
@app.get("/manifest")
async def get_manifest():
    """Return the MCP server manifest with available tools"""
    return {
        "name": "AR v3.0 MCP Server",
        "version": "3.0.0",
        "description": "Master Control Program server for Agentic Retrieval system",
        "tools": [
            {
                "name": XBRLFactTool.name,
                "description": XBRLFactTool.description
            },
            {
                "name": DocumentSectionTool.name,
                "description": DocumentSectionTool.description
            },
            {
                "name": MCPTool.name,
                "description": MCPTool.description
            },
            {
                "name": LLMTool.name,
                "description": LLMTool.description
            },
            {
                "name": SECDataTool.name,
                "description": SECDataTool.description
            }
        ]
    }

# Serve the main research interface
@app.get("/research-interface")
async def serve_research_interface():
    """Serve the dialectical review interface"""
    return FileResponse("static/research.html")

@app.get("/")
async def serve_index():
    """Serve the main index page"""
    return FileResponse("static/index.html")

@app.post("/research/start", response_model=ResearchResponse, status_code=202)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Initiates a new dialectical research job."""
    try:
        job_id = start_dialectical_research(request.query, request.user_id, background_tasks)
        return ResearchResponse(
            message="Research job initiated.", 
            job_id=job_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")

@app.get("/research/{job_id}/status", response_model=JobStatusResponse)
async def check_status(job_id: str):
    """Checks the status of a research job."""
    status_data = get_job_status(job_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(**status_data)

@app.get("/research/{job_id}/dossiers")
async def fetch_dossiers(job_id: str):
    """Fetches the Thesis and Antithesis dossiers for review."""
    dossiers = get_dossiers(job_id)
    if not dossiers["thesis_dossier"] or not dossiers["antithesis_dossier"]:
        raise HTTPException(status_code=404, detail="Dossiers not found")
    
    # Convert to Pydantic models for response
    from pydantic_models import EvidenceDossier as PydanticEvidenceDossier
    
    thesis_dossier = dossiers["thesis_dossier"]
    antithesis_dossier = dossiers["antithesis_dossier"]
    
    # Get research plan and evidence items for thesis
    db = SessionLocal()
    try:
        thesis_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == thesis_dossier.id).first()
        thesis_steps = db.query(ResearchPlanStep).filter(ResearchPlanStep.research_plan_id == thesis_plan.id).all() if thesis_plan else []
        thesis_evidence = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == thesis_dossier.id).all()
        
        antithesis_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == antithesis_dossier.id).first()
        antithesis_steps = db.query(ResearchPlanStep).filter(ResearchPlanStep.research_plan_id == antithesis_plan.id).all() if antithesis_plan else []
        antithesis_evidence = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == antithesis_dossier.id).all()
        
        return {
            "thesis_dossier": {
                "dossier_id": thesis_dossier.id,
                "mission": thesis_dossier.mission,
                "is_approved": thesis_dossier.status == DossierStatus.APPROVED,
                "plan": [
                    {
                        "step_id": step.id,
                        "description": step.description,
                        "status": step.status.value,
                        "data_gap_identified": step.data_gap_identified,
                        "proxy_hypothesis": step.proxy_hypothesis,
                        "tool_used": step.tool_used,
                        "tool_input": step.tool_input,
                        "tool_output_summary": step.tool_output_summary,
                        "evidence_ids": []  # Would need to be populated
                    } for step in thesis_steps
                ],
                "evidence": [
                    {
                        "evidence_id": item.id,
                        "finding": item.content,
                        "source_document_id": item.source,
                        "source_location": "N/A",
                        "tags": item.tags or []
                    } for item in thesis_evidence
                ],
                "summary": thesis_dossier.summary_of_findings
            },
            "antithesis_dossier": {
                "dossier_id": antithesis_dossier.id,
                "mission": antithesis_dossier.mission,
                "is_approved": antithesis_dossier.status == DossierStatus.APPROVED,
                "plan": [
                    {
                        "step_id": step.id,
                        "description": step.description,
                        "status": step.status.value,
                        "data_gap_identified": step.data_gap_identified,
                        "proxy_hypothesis": step.proxy_hypothesis,
                        "tool_used": step.tool_used,
                        "tool_input": step.tool_input,
                        "tool_output_summary": step.tool_output_summary,
                        "evidence_ids": []  # Would need to be populated
                    } for step in antithesis_steps
                ],
                "evidence": [
                    {
                        "evidence_id": item.id,
                        "finding": item.content,
                        "source_document_id": item.source,
                        "source_location": "N/A",
                        "tags": item.tags or []
                    } for item in antithesis_evidence
                ],
                "summary": antithesis_dossier.summary_of_findings
            }
        }
    finally:
        db.close()

@app.post("/dossiers/{dossier_id}/approve", response_model=DossierApprovalResponse)
async def approve_dossier(dossier_id: str, request: DossierApprovalRequest, background_tasks: BackgroundTasks):
    """Records human approval for a dossier and may trigger synthesis."""
    if not request.approved:
        raise HTTPException(status_code=400, detail="Only approval is supported in this endpoint")
    
    result = record_approval(dossier_id, background_tasks)
    return DossierApprovalResponse(**result)

@app.post("/tools/execute", response_model=ToolExecutionResponse)
async def execute_tool_endpoint(request: ToolExecutionRequest):
    """Execute a tool with given parameters."""
    try:
        result = execute_tool(request.tool_name, **request.parameters)
        return ToolExecutionResponse(
            success=True,
            result=result
        )
    except Exception as e:
        return ToolExecutionResponse(
            success=False,
            error=str(e)
        )

@app.get("/tools/available")
async def get_available_tools():
    """Get list of available tools."""
    from tools import tool_registry
    return {
        "tools": [
            {
                "name": name,
                "description": tool.description,
                "args_schema": tool.args_schema.schema() if hasattr(tool, 'args_schema') else None
            }
            for name, tool in tool_registry.items()
        ]
    }

@app.get("/research/{job_id}/verification-status", response_model=VerificationStatus)
async def get_verification_status(job_id: str):
    """Get verification status for a job."""
    dossiers = get_dossiers(job_id)
    if not dossiers["thesis_dossier"] or not dossiers["antithesis_dossier"]:
        raise HTTPException(status_code=404, detail="Job not found")
    
    thesis_approved = dossiers["thesis_dossier"].status == DossierStatus.APPROVED
    antithesis_approved = dossiers["antithesis_dossier"].status == DossierStatus.APPROVED
    
    return VerificationStatus(
        job_id=job_id,
        thesis_approved=thesis_approved,
        antithesis_approved=antithesis_approved,
        can_proceed_to_synthesis=thesis_approved and antithesis_approved
    )

@app.get("/research/{job_id}/final-report")
async def get_final_report(job_id: str):
    """Get the final synthesis report for a completed job."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        # Get synthesis report
        from models import SynthesisReport
        synthesis_report = db.query(SynthesisReport).filter(SynthesisReport.job_id == job_id).first()
        
        if not synthesis_report:
            raise HTTPException(status_code=404, detail="Synthesis report not found")
        
        return {
            "job_id": job_id,
            "final_report": synthesis_report.content,
            "created_at": synthesis_report.created_at.isoformat() if synthesis_report.created_at else None
        }
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "AR v3.0 MCP Server is running",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AR v3.0 MCP Server",
        "version": "3.0.0",
        "description": "Master Control Program for Agentic Retrieval System",
        "endpoints": {
            "start_research": "/research/start",
            "check_status": "/research/{job_id}/status",
            "fetch_dossiers": "/research/{job_id}/dossiers",
            "approve_dossier": "/dossiers/{dossier_id}/approve",
            "execute_tool": "/tools/execute",
            "available_tools": "/tools/available",
            "verification_status": "/research/{job_id}/verification-status",
            "final_report": "/research/{job_id}/final-report"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 