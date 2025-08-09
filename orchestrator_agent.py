import uuid
import json
import requests
from logging_config import get_file_logger
from sqlalchemy.orm import Session
from models import (
    Job, EvidenceDossier, ResearchPlan, ResearchPlanStep,
    JobStatus, DossierStatus, DossierType, StepStatus, SessionLocal,
    LLMRequest, LLMRequestStatus, LLMRequestType
)
from celery_app import celery_app
from research_agent import research_agent_task
from datetime import datetime
import time

class TrackingLLMClient:
    """Client for interacting with the LLM via Ollama with request tracking"""
    
    def __init__(self, base_url="http://192.168.1.15:11434", model="gemma3:27b"):
        self.base_url = base_url
        self.model = model
        self.logger = get_file_logger("llm.tracking_client", "logs/llm_client.log")
    
    def generate(self, prompt: str, job_id: str, request_type: LLMRequestType, 
                 dossier_id: str = None, max_tokens: int = 2000) -> str:
        """Generate text using the LLM with request tracking"""
        
        # Create LLM request record
        db = SessionLocal()
        try:
            llm_request = LLMRequest(
                id=f"llm-{uuid.uuid4().hex[:8]}",
                job_id=job_id,
                dossier_id=dossier_id,
                request_type=request_type,
                status=LLMRequestStatus.PENDING,
                prompt=prompt
            )
            db.add(llm_request)
            db.commit()
            
            # Update status to in progress
            llm_request.status = LLMRequestStatus.IN_PROGRESS
            llm_request.started_at = datetime.utcnow()
            db.commit()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                        }
                    },
                )
                response.raise_for_status()
                result = response.json()["response"]
                
                # Update request as completed
                llm_request.status = LLMRequestStatus.COMPLETED
                llm_request.response = result
                llm_request.completed_at = datetime.utcnow()
                db.commit()
                
                return result
                
            except Exception as e:
                # Update request as failed
                llm_request.status = LLMRequestStatus.FAILED
                llm_request.error_message = str(e)
                llm_request.completed_at = datetime.utcnow()
                db.commit()
                self.logger.error("LLM API error: %s", e)
                raise e
                
        finally:
            db.close()
    


class LLMClient:
    """Legacy client for backward compatibility"""
    
    def __init__(self, base_url="http://192.168.1.15:11434", model="gemma3:27b"):
        self.base_url = base_url
        self.model = model
        self.logger = get_file_logger("llm.legacy_client", "logs/llm_client.log")
    
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
            self.logger.error("LLM API error: %s", e)
            raise e
    


class OrchestratorAgent:
    """Agent responsible for creating dialectical research missions and plans"""
    
    def __init__(self):
        self.llm_client = TrackingLLMClient()
    
    def create_dialectical_missions(self, user_query: str, job_id: str) -> dict:
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
        
        response = self.llm_client.generate(prompt, job_id, LLMRequestType.ORCHESTRATOR_MISSION)
        
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
            logger = get_file_logger("agent.orchestrator", "logs/agent.log")
            logger.warning("Failed to parse LLM response: %s", response)
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
                    status=StepStatus.PENDING,  # Mark as pending for Research Agent to execute
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
            missions_data = orchestrator.create_dialectical_missions(job.query, job_id)
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating research plans'})
            
            # Create research plans
            orchestrator.create_research_plans(db, job_id, missions_data)
            
            # CP4-T403: Enable parallel research job execution
            # Get the dossiers and enqueue research agent tasks
            dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
            
            # Enqueue research agent tasks for both dossiers in parallel
            for dossier in dossiers:
                research_agent_task.delay(dossier.id)
            
            # Update job status to researching (since research agents are now running)
            job.status = JobStatus.RESEARCHING
            db.commit()
            
            self.update_state(state='SUCCESS', meta={'status': 'Research agents enqueued for parallel execution'})
            
            return {
                'status': 'success',
                'job_id': job_id,
                'message': 'Dialectical missions and research plans created successfully. Research agents enqueued.'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise 