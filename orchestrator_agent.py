import uuid
import json
import requests
from sqlalchemy.orm import Session
from models import (
    Job, EvidenceDossier, ResearchPlan, ResearchPlanStep,
    JobStatus, DossierStatus, DossierType, StepStatus, SessionLocal
)
from celery_app import celery_app

class LLMClient:
    """Client for interacting with the LLM via Ollama"""
    
    def __init__(self, base_url="http://192.168.1.15:11434", model="gemma3:27b"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using the LLM"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                #       "top_p": 0.9,
                #       "max_tokens": max_tokens
                    }
                },
                #timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"LLM API error: {e}")
            # Fallback to mock response for development
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Mock response for development when LLM is not available"""
        if "thesis" in prompt.lower() and "antithesis" in prompt.lower():
            return """
{
  "thesis_mission": "Build the strongest possible case FOR the investment opportunity by analyzing positive market indicators, growth potential, competitive advantages, and favorable expert opinions.",
  "antithesis_mission": "Build the strongest possible case AGAINST the investment opportunity by examining market risks, competitive threats, financial concerns, and bearish expert opinions.",
  "thesis_plan": [
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
  ],
  "antithesis_plan": [
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
}
"""
        return "Mock response for development"

class OrchestratorAgent:
    """Agent responsible for creating dialectical research missions and plans"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def create_dialectical_missions(self, user_query: str) -> dict:
        """Generate thesis and antithesis missions using LLM"""
        
        prompt = f"""
You are an expert research orchestrator. Given a user's research query, you need to create two opposing research missions that will be executed in parallel.

User Query: "{user_query}"

Your task is to:
1. Create a THESIS mission that builds the strongest possible case FOR the proposition
2. Create an ANTITHESIS mission that builds the strongest possible case AGAINST the proposition
3. Generate a detailed research plan for each mission with 3-5 steps

Please respond with a JSON object in this exact format:
{{
  "thesis_mission": "Detailed mission statement for the thesis case",
  "antithesis_mission": "Detailed mission statement for the antithesis case",
  "thesis_plan": [
    {{
      "step_number": 1,
      "description": "Description of the research step",
      "tool_used": "suggested-tool-name",
      "tool_selection_justification": "Why this tool is appropriate",
      "tool_query_rationale": "How the query should be formulated"
    }}
  ],
  "antithesis_plan": [
    {{
      "step_number": 1,
      "description": "Description of the research step",
      "tool_used": "suggested-tool-name",
      "tool_selection_justification": "Why this tool is appropriate",
      "tool_query_rationale": "How the query should be formulated"
    }}
  ]
}}

Ensure both missions are equally rigorous and the plans are detailed enough for execution.
"""
        
        response = self.llm_client.generate(prompt)
        
        try:
            # Try to parse the response as JSON
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from the response
            try:
                # Look for JSON-like content between curly braces
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    result = json.loads(json_str)
                    return result
            except:
                pass
            
            # If all parsing fails, return a default structure
            print(f"Failed to parse LLM response: {response}")
            return self._default_missions(user_query)
    
    def _default_missions(self, user_query: str) -> dict:
        """Default missions when LLM parsing fails"""
        return {
            "thesis_mission": f"Build the strongest possible case FOR: {user_query}",
            "antithesis_mission": f"Build the strongest possible case AGAINST: {user_query}",
            "thesis_plan": [
                {
                    "step_number": 1,
                    "description": "Analyze positive market indicators and growth trends",
                    "tool_used": "market-data-api",
                    "tool_selection_justification": "Market data is essential for understanding positive trends",
                    "tool_query_rationale": "Focusing on growth metrics and positive indicators"
                }
            ],
            "antithesis_plan": [
                {
                    "step_number": 1,
                    "description": "Identify market risks and potential challenges",
                    "tool_used": "risk-assessment-api",
                    "tool_selection_justification": "Risk analysis is crucial for understanding downsides",
                    "tool_query_rationale": "Focusing on volatility indicators and negative signals"
                }
            ]
        }
    
    def create_research_plans(self, db: Session, job_id: str, missions_data: dict):
        """Create research plans for both thesis and antithesis dossiers"""
        
        # Get the dossiers for this job
        dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
        
        for dossier in dossiers:
            # Determine which plan to use based on dossier type
            if dossier.dossier_type == DossierType.THESIS:
                mission = missions_data["thesis_mission"]
                plan_steps = missions_data["thesis_plan"]
            else:
                mission = missions_data["antithesis_mission"]
                plan_steps = missions_data["antithesis_plan"]
            
            # Update dossier mission
            dossier.mission = mission
            dossier.status = DossierStatus.RESEARCHING
            
            # Create research plan
            plan_id = f"plan-{dossier.id}"
            research_plan = ResearchPlan(
                id=plan_id,
                dossier_id=dossier.id
            )
            db.add(research_plan)
            
            # Create plan steps
            for step_data in plan_steps:
                step = ResearchPlanStep(
                    id=f"step-{uuid.uuid4().hex[:8]}",
                    research_plan_id=plan_id,
                    status=StepStatus.COMPLETED,  # Mark as completed for this checkpoint
                    **step_data
                )
                db.add(step)
        
        db.commit()

@celery_app.task(bind=True)
def orchestrator_task(self, job_id: str):
    """Celery task for the Orchestrator Agent"""
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting orchestration'})
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get the job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update job status
            job.status = JobStatus.RESEARCHING
            db.commit()
            
            self.update_state(state='PROGRESS', meta={'status': 'Generating dialectical missions'})
            
            # Create orchestrator agent and generate missions
            orchestrator = OrchestratorAgent()
            missions_data = orchestrator.create_dialectical_missions(job.query)
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating research plans'})
            
            # Create research plans
            orchestrator.create_research_plans(db, job_id, missions_data)
            
            # Update job status to awaiting verification
            job.status = JobStatus.AWAITING_VERIFICATION
            db.commit()
            
            self.update_state(state='SUCCESS', meta={'status': 'Orchestration completed'})
            
            return {
                'status': 'success',
                'job_id': job_id,
                'message': 'Dialectical missions and research plans created successfully'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise 