from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum
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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dossier = relationship("EvidenceDossier", back_populates="evidence_items")

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