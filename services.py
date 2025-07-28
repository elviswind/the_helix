import uuid
import time
from sqlalchemy.orm import Session
from models import (
    Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem,
    JobStatus, DossierStatus, DossierType, StepStatus
)

class CannedResearchService:
    """Service to populate dossiers with predefined, 'canned' evidence"""
    
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
    
    @staticmethod
    def populate_thesis_dossier(db: Session, dossier_id: str):
        """Populate thesis dossier with predefined positive evidence"""
        
        # Create research plan
        plan_id = f"plan-{dossier_id}"
        research_plan = ResearchPlan(
            id=plan_id,
            dossier_id=dossier_id
        )
        db.add(research_plan)
        
        # Create plan steps
        steps = [
            {
                "step_number": 1,
                "description": "Analyze positive market indicators and growth trends",
                "tool_used": "market-data-api",
                "tool_selection_justification": "Market data is essential for understanding positive trends and growth potential",
                "tool_query_rationale": "Focusing on growth metrics, positive sentiment indicators, and upward trends"
            },
            {
                "step_number": 2,
                "description": "Review favorable expert opinions and analyst reports",
                "tool_used": "expert-analysis-db",
                "tool_selection_justification": "Expert opinions provide credibility and validation to the thesis",
                "tool_query_rationale": "Searching for bullish analyst reports, positive forecasts, and expert endorsements"
            },
            {
                "step_number": 3,
                "description": "Examine competitive advantages and market position",
                "tool_used": "competitive-analysis-api",
                "tool_selection_justification": "Understanding competitive position is crucial for long-term success",
                "tool_query_rationale": "Analyzing market share, competitive moats, and strategic advantages"
            }
        ]
        
        for step_data in steps:
            step = ResearchPlanStep(
                id=f"step-{uuid.uuid4().hex[:8]}",
                research_plan_id=plan_id,
                status=StepStatus.COMPLETED,
                **step_data
            )
            db.add(step)
        
        # Create evidence items
        evidence_items = [
            {
                "title": "Strong Market Growth Indicators",
                "content": "Recent market analysis shows consistent growth patterns with 15% year-over-year increase in key metrics. Revenue growth has been steady and sustainable, indicating strong market demand and execution capability.",
                "source": "Market Analysis Report 2024",
                "confidence": 0.85
            },
            {
                "title": "Expert Bullish Sentiment",
                "content": "Leading industry experts maintain positive outlook with 80% of surveyed analysts recommending strong buy positions. Consensus estimates project continued growth trajectory over the next 3-5 years.",
                "source": "Expert Consensus Survey",
                "confidence": 0.90
            },
            {
                "title": "Competitive Market Position",
                "content": "Analysis reveals strong competitive advantages including brand recognition, proprietary technology, and established customer relationships. Market share has grown consistently over the past 24 months.",
                "source": "Competitive Analysis Database",
                "confidence": 0.88
            },
            {
                "title": "Financial Health Indicators",
                "content": "Strong balance sheet with healthy cash flow, manageable debt levels, and consistent profitability. Key financial ratios are well within industry benchmarks and show improving trends.",
                "source": "Financial Health Assessment",
                "confidence": 0.82
            }
        ]
        
        for evidence_data in evidence_items:
            evidence = EvidenceItem(
                id=f"ev-{uuid.uuid4().hex[:8]}",
                dossier_id=dossier_id,
                **evidence_data
            )
            db.add(evidence)
        
        # Update dossier status and summary
        dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
        dossier.status = DossierStatus.AWAITING_VERIFICATION
        dossier.summary_of_findings = "The evidence strongly supports a positive outlook with robust market fundamentals, expert consensus backing, and strong competitive positioning. Financial health indicators are favorable and growth trends are sustainable."
        
        db.commit()
    
    @staticmethod
    def populate_antithesis_dossier(db: Session, dossier_id: str):
        """Populate antithesis dossier with predefined negative evidence"""
        
        # Create research plan
        plan_id = f"plan-{dossier_id}"
        research_plan = ResearchPlan(
            id=plan_id,
            dossier_id=dossier_id
        )
        db.add(research_plan)
        
        # Create plan steps
        steps = [
            {
                "step_number": 1,
                "description": "Identify market risks and potential challenges",
                "tool_used": "risk-assessment-api",
                "tool_selection_justification": "Risk analysis is crucial for understanding potential downsides and vulnerabilities",
                "tool_query_rationale": "Focusing on volatility indicators, negative market signals, and potential disruption factors"
            },
            {
                "step_number": 2,
                "description": "Review bearish expert opinions and cautionary reports",
                "tool_used": "expert-analysis-db",
                "tool_selection_justification": "Contrary expert opinions provide balance and highlight potential blind spots",
                "tool_query_rationale": "Searching for bearish analyst reports, risk warnings, and skeptical viewpoints"
            },
            {
                "step_number": 3,
                "description": "Analyze competitive threats and market disruption risks",
                "tool_used": "competitive-analysis-api",
                "tool_selection_justification": "Understanding competitive threats is essential for risk assessment",
                "tool_query_rationale": "Analyzing emerging competitors, disruptive technologies, and market share erosion risks"
            }
        ]
        
        for step_data in steps:
            step = ResearchPlanStep(
                id=f"step-{uuid.uuid4().hex[:8]}",
                research_plan_id=plan_id,
                status=StepStatus.COMPLETED,
                **step_data
            )
            db.add(step)
        
        # Create evidence items
        evidence_items = [
            {
                "title": "Market Volatility Concerns",
                "content": "Recent market volatility has increased by 25% with several concerning indicators pointing to potential instability. Economic uncertainty and geopolitical factors create significant headwinds.",
                "source": "Volatility Analysis Report",
                "confidence": 0.80
            },
            {
                "title": "Expert Risk Warnings",
                "content": "20% of industry experts have issued cautionary statements about current market conditions and potential downside risks. Several analysts have downgraded growth projections.",
                "source": "Risk Assessment Survey",
                "confidence": 0.75
            },
            {
                "title": "Competitive Threat Analysis",
                "content": "Emerging competitors are gaining market share rapidly, particularly in key growth segments. Disruptive technologies could potentially undermine current competitive advantages.",
                "source": "Competitive Threat Assessment",
                "confidence": 0.78
            },
            {
                "title": "Financial Risk Indicators",
                "content": "Several financial metrics show concerning trends including increasing debt levels, declining cash flow margins, and potential liquidity constraints in adverse scenarios.",
                "source": "Financial Risk Analysis",
                "confidence": 0.72
            }
        ]
        
        for evidence_data in evidence_items:
            evidence = EvidenceItem(
                id=f"ev-{uuid.uuid4().hex[:8]}",
                dossier_id=dossier_id,
                **evidence_data
            )
            db.add(evidence)
        
        # Update dossier status and summary
        dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
        dossier.status = DossierStatus.AWAITING_VERIFICATION
        dossier.summary_of_findings = "Significant risks and challenges exist that warrant careful consideration. Market volatility, competitive threats, and financial concerns create substantial downside potential that should not be ignored."
        
        db.commit()
    
    @staticmethod
    def process_job(db: Session, job_id: str):
        """Process a job by populating both dossiers with canned evidence"""
        
        # Get the job and its dossiers
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
        
        # Update job status to researching
        job.status = JobStatus.RESEARCHING
        db.commit()
        
        # Simulate processing time
        time.sleep(3)
        
        # Populate each dossier
        for dossier in dossiers:
            if dossier.dossier_type == DossierType.THESIS:
                CannedResearchService.populate_thesis_dossier(db, dossier.id)
            else:
                CannedResearchService.populate_antithesis_dossier(db, dossier.id)
        
        # Update job status to awaiting verification
        job.status = JobStatus.AWAITING_VERIFICATION
        db.commit() 