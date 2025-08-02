from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "PENDING"
    RESEARCHING = "RESEARCHING"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    COMPLETE = "COMPLETE"

class DossierStatus(enum.Enum):
    PENDING = "PENDING"
    RESEARCHING = "RESEARCHING"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"

class DossierType(enum.Enum):
    THESIS = "THESIS"
    ANTITHESIS = "ANTITHESIS"

class StepStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class LLMRequestStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class LLMRequestType(enum.Enum):
    ORCHESTRATOR_MISSION = "ORCHESTRATOR_MISSION"
    TOOL_SELECTION = "TOOL_SELECTION"
    QUERY_FORMULATION = "QUERY_FORMULATION"
    SYNTHESIS = "SYNTHESIS"

class ToolRequestStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ToolRequestType(enum.Enum):
    MCP_SEARCH = "MCP_SEARCH"
    MCP_MANIFEST = "MCP_MANIFEST"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    query = Column(Text, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to dossiers
    dossiers = relationship("EvidenceDossier", back_populates="job")

class EvidenceDossier(Base):
    __tablename__ = "evidence_dossiers"
    
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    dossier_type = Column(Enum(DossierType), nullable=False)
    mission = Column(Text, nullable=False)
    status = Column(Enum(DossierStatus), default=DossierStatus.PENDING)
    summary_of_findings = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="dossiers")
    research_plan = relationship("ResearchPlan", back_populates="dossier", uselist=False)
    evidence_items = relationship("EvidenceItem", back_populates="dossier")

class ResearchPlan(Base):
    __tablename__ = "research_plans"
    
    id = Column(String, primary_key=True)
    dossier_id = Column(String, ForeignKey("evidence_dossiers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dossier = relationship("EvidenceDossier", back_populates="research_plan")
    steps = relationship("ResearchPlanStep", back_populates="research_plan")

class ResearchPlanStep(Base):
    __tablename__ = "research_plan_steps"
    
    id = Column(String, primary_key=True)
    research_plan_id = Column(String, ForeignKey("research_plans.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(StepStatus), default=StepStatus.PENDING)
    tool_used = Column(String)
    tool_selection_justification = Column(Text)
    tool_query_rationale = Column(Text)
    dependencies = Column(Text)  # JSON string of step IDs
    # New fields for Deductive Proxy Framework
    data_gap_identified = Column(Text)  # Description of the data gap when direct data is unavailable
    proxy_hypothesis = Column(JSON)  # JSON object containing unobservable_claim, deductive_chain, observable_proxy
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    research_plan = relationship("ResearchPlan", back_populates="steps")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    
    id = Column(String, primary_key=True)
    dossier_id = Column(String, ForeignKey("evidence_dossiers.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    # New field for linking evidence to proxy hypotheses
    tags = Column(JSON)  # Array of strings to link evidence back to a proxy
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dossier = relationship("EvidenceDossier", back_populates="evidence_items")

class LLMRequest(Base):
    __tablename__ = "llm_requests"
    
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    dossier_id = Column(String, ForeignKey("evidence_dossiers.id"), nullable=True)  # Optional, for dossier-specific requests
    request_type = Column(Enum(LLMRequestType), nullable=False)
    status = Column(Enum(LLMRequestStatus), default=LLMRequestStatus.PENDING)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job")
    dossier = relationship("EvidenceDossier")

class ToolRequest(Base):
    __tablename__ = "tool_requests"
    
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    dossier_id = Column(String, ForeignKey("evidence_dossiers.id"), nullable=True)  # Optional, for dossier-specific requests
    step_id = Column(String, ForeignKey("research_plan_steps.id"), nullable=True)  # Optional, for step-specific requests
    request_type = Column(Enum(ToolRequestType), nullable=False)
    tool_name = Column(String, nullable=False)
    query = Column(Text, nullable=True)  # For search requests
    status = Column(Enum(ToolRequestStatus), default=ToolRequestStatus.PENDING)
    response = Column(Text, nullable=True)  # JSON string of results
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job")
    dossier = relationship("EvidenceDossier")
    step = relationship("ResearchPlanStep")

# New model for Checkpoint 6 - Revision Feedback
class RevisionFeedback(Base):
    __tablename__ = "revision_feedback"
    
    id = Column(String, primary_key=True)
    dossier_id = Column(String, ForeignKey("evidence_dossiers.id"), nullable=False)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    dossier = relationship("EvidenceDossier")

# Database setup
DATABASE_URL = "sqlite:///./ar_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 