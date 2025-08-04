import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import (
    Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, 
    JobStatus, DossierStatus, DossierType, SessionLocal
)
from pydantic_models import ResearchJob, EvidenceDossier as PydanticEvidenceDossier
from celery_app import celery_app
from research_agent import research_agent_task
from synthesis_agent import synthesis_agent_task
from orchestrator_agent import orchestrator_task

def start_dialectical_research(query: str, user_id: str, background_tasks=None):
    """
    The Orchestrator Agent's primary function.
    1. Creates the job record in the DB.
    2. Decomposes the query using the existing orchestrator agent.
    3. Launches two parallel background tasks.
    """
    job_id = str(uuid.uuid4())
    
    # 1. Create job in database
    thesis_dossier_id, antithesis_dossier_id = create_new_job(job_id, query, user_id)

    # 2. Use the existing orchestrator agent to decompose the query and create plans
    if background_tasks:
        # For FastAPI background tasks
        background_tasks.add_task(orchestrator_task, job_id)
    else:
        # For direct Celery tasks
        orchestrator_task.delay(job_id)
    
    return job_id

def create_new_job(job_id: str, query: str, user_id: str):
    """Create a new research job with thesis and antithesis dossiers"""
    db = SessionLocal()
    try:
        # Create the main job
        job = Job(
            id=job_id,
            query=query,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(job)
        
        # Create thesis dossier
        thesis_dossier_id = str(uuid.uuid4())
        thesis_dossier = EvidenceDossier(
            id=thesis_dossier_id,
            job_id=job_id,
            dossier_type=DossierType.THESIS,
            mission=f"Build the strongest possible, evidence-based case FOR the following: {query}",
            status=DossierStatus.PENDING
        )
        db.add(thesis_dossier)
        
        # Create antithesis dossier
        antithesis_dossier_id = str(uuid.uuid4())
        antithesis_dossier = EvidenceDossier(
            id=antithesis_dossier_id,
            job_id=job_id,
            dossier_type=DossierType.ANTITHESIS,
            mission=f"Build the strongest possible, evidence-based case AGAINST the following: {query}",
            status=DossierStatus.PENDING
        )
        db.add(antithesis_dossier)
        
        # Create research plans for both dossiers
        thesis_plan = ResearchPlan(
            id=str(uuid.uuid4()),
            dossier_id=thesis_dossier_id
        )
        db.add(thesis_plan)
        
        antithesis_plan = ResearchPlan(
            id=str(uuid.uuid4()),
            dossier_id=antithesis_dossier_id
        )
        db.add(antithesis_plan)
        
        db.commit()
        return thesis_dossier_id, antithesis_dossier_id
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def run_research_agent_task(dossier_id: str):
    """Wrapper function for research agent task"""
    research_agent_task.delay(dossier_id)

def trigger_synthesis_if_ready(job_id: str, background_tasks=None):
    """Called after a dossier is approved to check if both are ready."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False
            
        # Check if both dossiers are approved
        thesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job_id,
            EvidenceDossier.dossier_type == DossierType.THESIS
        ).first()
        
        antithesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job_id,
            EvidenceDossier.dossier_type == DossierType.ANTITHESIS
        ).first()
        
        if (thesis_dossier and antithesis_dossier and 
            thesis_dossier.status == DossierStatus.APPROVED and 
            antithesis_dossier.status == DossierStatus.APPROVED):
            
            # Update job status
            job.status = JobStatus.COMPLETE
            db.commit()
            
            # Trigger synthesis
            if background_tasks:
                background_tasks.add_task(run_synthesis_agent_task, job_id)
            else:
                synthesis_agent_task.delay(job_id)
            
            return True
            
        return False
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def run_synthesis_agent_task(job_id: str):
    """Wrapper function for synthesis agent task"""
    synthesis_agent_task.delay(job_id)

def get_job_status(job_id: str):
    """Get the current status of a research job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None
            
        thesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job_id,
            EvidenceDossier.dossier_type == DossierType.THESIS
        ).first()
        
        antithesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job_id,
            EvidenceDossier.dossier_type == DossierType.ANTITHESIS
        ).first()
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "initial_query": job.query,
            "thesis_dossier_id": thesis_dossier.id if thesis_dossier else None,
            "antithesis_dossier_id": antithesis_dossier.id if antithesis_dossier else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        }
        
    finally:
        db.close()

def get_dossiers(job_id: str):
    """Get both thesis and antithesis dossiers for a job"""
    db = SessionLocal()
    try:
        thesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job_id,
            EvidenceDossier.dossier_type == DossierType.THESIS
        ).first()
        
        antithesis_dossier = db.query(EvidenceDossier).filter(
            EvidenceDossier.job_id == job_id,
            EvidenceDossier.dossier_type == DossierType.ANTITHESIS
        ).first()
        
        return {
            "thesis_dossier": thesis_dossier,
            "antithesis_dossier": antithesis_dossier
        }
        
    finally:
        db.close()

def record_approval(dossier_id: str, background_tasks=None):
    """Record human approval for a dossier and may trigger synthesis"""
    db = SessionLocal()
    try:
        dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
        if not dossier:
            return {"success": False, "message": "Dossier not found"}
            
        dossier.status = DossierStatus.APPROVED
        db.commit()
        
        # Check if both dossiers are now approved
        if trigger_synthesis_if_ready(dossier.job_id, background_tasks):
            return {
                "success": True, 
                "message": "Dossier approved. Both dossiers approved - synthesis started.",
                "job_status": "SYNTHESIZING"
            }
        else:
            return {
                "success": True, 
                "message": "Dossier approved. Waiting for other dossier approval.",
                "job_status": "AWAITING_APPROVAL"
            }
            
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error recording approval: {str(e)}"}
    finally:
        db.close() 