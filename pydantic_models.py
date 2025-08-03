from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    SYNTHESIZING = "SYNTHESIZING"
    COMPLETED = "COMPLETED"

class DossierStatus(str, Enum):
    PENDING = "PENDING"
    RESEARCHING = "RESEARCHING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"

class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProxyHypothesis(BaseModel):
    unobservable_claim: str
    deductive_chain: str
    observable_proxy: str

class ResearchStep(BaseModel):
    step_id: str
    description: str
    status: str  # e.g., PENDING, RUNNING, COMPLETED, FAILED
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
    status: str  # e.g., PENDING, RUNNING, AWAITING_APPROVAL, SYNTHESIZING, COMPLETED
    thesis_dossier: EvidenceDossier
    antithesis_dossier: EvidenceDossier
    final_report: Optional[str] = None

# API Request/Response Models
class ResearchRequest(BaseModel):
    query: str
    user_id: str

class ResearchResponse(BaseModel):
    message: str
    job_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    initial_query: str
    thesis_dossier_id: Optional[str] = None
    antithesis_dossier_id: Optional[str] = None
    final_report: Optional[str] = None

class DossierApprovalRequest(BaseModel):
    dossier_id: str
    approved: bool
    feedback: Optional[str] = None

class DossierApprovalResponse(BaseModel):
    success: bool
    message: str
    job_status: Optional[str] = None

# Tool-related models
class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Synthesis models
class SynthesisRequest(BaseModel):
    job_id: str
    thesis_dossier: EvidenceDossier
    antithesis_dossier: EvidenceDossier

class SynthesisResponse(BaseModel):
    job_id: str
    final_report: str
    status: str

# Verification models
class VerificationChecklist(BaseModel):
    review_summary: bool = False
    validate_proxy_logic: bool = False
    spot_check_evidence: bool = False
    audit_reasoning: bool = False

class VerificationStatus(BaseModel):
    job_id: str
    thesis_approved: bool
    antithesis_approved: bool
    thesis_checklist: Optional[VerificationChecklist] = None
    antithesis_checklist: Optional[VerificationChecklist] = None
    can_proceed_to_synthesis: bool = False 