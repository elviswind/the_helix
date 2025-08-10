import uuid
import time
from sqlalchemy.orm import Session
from models import (
    Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem,
    JobStatus, DossierStatus, DossierType, StepStatus
)

class CannedResearchService:
    """Service to create jobs and dossiers - actual research is done by the research agent"""
    
    @staticmethod
    def create_job_with_dossiers(db: Session, query: str) -> Job:
        """Create a job and two associated dossiers (thesis and antithesis)"""
        job_id = f"job-v2-{uuid.uuid4().hex[:8]}"
        
        # Create job
        job = Job(
            id=job_id,
            query=query,
            status=JobStatus.PENDING
        )
        db.add(job)
        
        # Create thesis dossier
        thesis_dossier_id = f"dossier-thesis-{uuid.uuid4().hex[:8]}"
        thesis_dossier = EvidenceDossier(
            id=thesis_dossier_id,
            job_id=job_id,
            dossier_type=DossierType.THESIS,
            mission=f"Build the strongest possible case FOR: {query}",
            status=DossierStatus.PENDING
        )
        db.add(thesis_dossier)
        
        # Create antithesis dossier
        antithesis_dossier_id = f"dossier-antithesis-{uuid.uuid4().hex[:8]}"
        antithesis_dossier = EvidenceDossier(
            id=antithesis_dossier_id,
            job_id=job_id,
            dossier_type=DossierType.ANTITHESIS,
            mission=f"Build the strongest possible case AGAINST: {query}",
            status=DossierStatus.PENDING
        )
        db.add(antithesis_dossier)
        
        db.commit()
        return job 