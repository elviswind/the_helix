import uuid
import json
import requests
from sqlalchemy.orm import Session
from models import (
    EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem,
    DossierStatus, StepStatus, SessionLocal, LLMRequest, LLMRequestStatus, LLMRequestType,
    ToolRequest, ToolRequestStatus, ToolRequestType, JobStatus, Job
)
from celery_app import celery_app
from datetime import datetime

class MCPClient:
    """Client for interacting with the MCP server"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    def get_manifest(self):
        """Get the MCP server manifest"""
        try:
            response = requests.get(f"{self.base_url}/manifest")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"MCP manifest error: {e}")
            return None
    
    def search(self, query: str, tool_name: str = None, max_results: int = 10):
        """Search for data using the MCP server"""
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "tool_name": tool_name,
                    "max_results": max_results
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"MCP search error: {e}")
            return {"results": [], "total_count": 0}

class TrackingMCPClient:
    """Client for interacting with the MCP server with request tracking"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    def get_manifest(self, job_id: str, dossier_id: str = None, step_id: str = None):
        """Get the MCP server manifest with request tracking"""
        
        # Create tool request record
        db = SessionLocal()
        try:
            tool_request = ToolRequest(
                id=f"tool-{uuid.uuid4().hex[:8]}",
                job_id=job_id,
                dossier_id=dossier_id,
                step_id=step_id,
                request_type=ToolRequestType.MCP_MANIFEST,
                tool_name="mcp-manifest",
                status=ToolRequestStatus.PENDING
            )
            db.add(tool_request)
            db.commit()
            
            # Update status to in progress
            tool_request.status = ToolRequestStatus.IN_PROGRESS
            tool_request.started_at = datetime.utcnow()
            db.commit()
            
            try:
                response = requests.get(f"{self.base_url}/manifest", timeout=30)
                response.raise_for_status()
                result = response.json()
                
                # Update request as completed
                tool_request.status = ToolRequestStatus.COMPLETED
                tool_request.response = json.dumps(result)
                tool_request.completed_at = datetime.utcnow()
                db.commit()
                
                return result
                
            except Exception as e:
                # Update request as failed
                tool_request.status = ToolRequestStatus.FAILED
                tool_request.error_message = str(e)
                tool_request.completed_at = datetime.utcnow()
                db.commit()
                print(f"MCP manifest error: {e}")
                return None
                
        finally:
            db.close()
    
    def search(self, query: str, tool_name: str, job_id: str, dossier_id: str = None, 
               step_id: str = None, max_results: int = 10):
        """Search for data using the MCP server with request tracking"""
        
        # Create tool request record
        db = SessionLocal()
        try:
            tool_request = ToolRequest(
                id=f"tool-{uuid.uuid4().hex[:8]}",
                job_id=job_id,
                dossier_id=dossier_id,
                step_id=step_id,
                request_type=ToolRequestType.MCP_SEARCH,
                tool_name=tool_name,
                query=query,
                status=ToolRequestStatus.PENDING
            )
            db.add(tool_request)
            db.commit()
            
            # Update status to in progress
            tool_request.status = ToolRequestStatus.IN_PROGRESS
            tool_request.started_at = datetime.utcnow()
            db.commit()
            
            try:
                response = requests.post(
                    f"{self.base_url}/search",
                    json={
                        "query": query,
                        "tool_name": tool_name,
                        "max_results": max_results
                    },
                    timeout=60  # 1 minute timeout for search
                )
                response.raise_for_status()
                result = response.json()
                
                # Update request as completed
                tool_request.status = ToolRequestStatus.COMPLETED
                tool_request.response = json.dumps(result)
                tool_request.completed_at = datetime.utcnow()
                db.commit()
                
                return result
                
            except Exception as e:
                # Update request as failed
                tool_request.status = ToolRequestStatus.FAILED
                tool_request.error_message = str(e)
                tool_request.completed_at = datetime.utcnow()
                db.commit()
                print(f"MCP search error: {e}")
                return {"results": [], "total_count": 0}
                
        finally:
            db.close()

class TrackingLLMClient:
    """Client for interacting with the LLM via Ollama with request tracking"""
    
    def __init__(self, base_url="http://192.168.1.15:11434", model="gemma3:27b"):
        self.base_url = base_url
        self.model = model
    
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
                    }
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
                
                print(f"LLM API error: {e}")
                # Fallback to mock response for development
                return self._mock_response(prompt)
                
        finally:
            db.close()
    
    def _mock_response(self, prompt: str) -> str:
        """Mock response for development when LLM is not available"""
        if "tool selection" in prompt.lower():
            return "market-data-api"
        elif "query formulation" in prompt.lower():
            return "growth trends and market indicators"
        else:
            return "Mock response for development"

class LLMClient:
    """Legacy client for backward compatibility"""
    
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
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Mock response for development when LLM is not available"""
        if "tool selection" in prompt.lower():
            return "market-data-api"
        elif "query formulation" in prompt.lower():
            return "growth trends and market indicators"
        else:
            return "Mock response for development"

class ResearchAgent:
    """Research Agent that executes research plans using LLM and MCP tools"""
    
    def __init__(self):
        self.llm_client = TrackingLLMClient()
        self.mcp_client = TrackingMCPClient()
    
    def select_tool(self, step_description: str, available_tools: list, job_id: str, dossier_id: str) -> str:
        """Use LLM to select the best tool for a research step"""
        
        # Create a prompt for tool selection
        tools_text = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
        
        prompt = f"""You are a research agent that needs to select the best tool for a research step.

Available tools:
{tools_text}

Research step: {step_description}

Based on the research step description, select the most appropriate tool from the list above. 
Respond with ONLY the tool name (e.g., "market-data-api").

Selected tool:"""
        
        response = self.llm_client.generate(
            prompt=prompt,
            job_id=job_id,
            request_type=LLMRequestType.TOOL_SELECTION,
            dossier_id=dossier_id
        )
        
        # Extract tool name from response
        tool_name = response.strip().split('\n')[0].strip()
        
        # Validate that the tool exists
        available_tool_names = [tool['name'] for tool in available_tools]
        if tool_name not in available_tool_names:
            # Fallback to first available tool
            tool_name = available_tool_names[0] if available_tool_names else "market-data-api"
        
        return tool_name
    
    def formulate_query(self, step_description: str, tool_name: str, job_id: str, dossier_id: str) -> str:
        """Use LLM to formulate a query for the selected tool"""
        
        prompt = f"""You are a research agent that needs to formulate a search query for a tool.

Research step: {step_description}
Selected tool: {tool_name}

Formulate a specific, focused search query that will help gather evidence for this research step.
The query should be clear and targeted to get relevant results from the tool.

Query:"""
        
        response = self.llm_client.generate(
            prompt=prompt,
            job_id=job_id,
            request_type=LLMRequestType.QUERY_FORMULATION,
            dossier_id=dossier_id
        )
        
        # Extract query from response
        query = response.strip().split('\n')[0].strip()
        return query
    
    def execute_step(self, db: Session, step: ResearchPlanStep, dossier: EvidenceDossier):
        """Execute a single research plan step"""
        
        # Get the job ID for tracking
        job_id = dossier.job_id
        
        # Get available tools from MCP server with tracking
        manifest = self.mcp_client.get_manifest(job_id, dossier.id, step.id)
        if not manifest:
            # Fallback to default tools if MCP server is unavailable
            available_tools = [
                {"name": "market-data-api", "description": "Market data and trends"},
                {"name": "expert-analysis-db", "description": "Expert opinions and analysis"},
                {"name": "competitive-analysis-api", "description": "Competitive analysis"},
                {"name": "financial-data-api", "description": "Financial data and metrics"}
            ]
        else:
            available_tools = manifest.get("tools", [])
        
        # Step 1: Tool Selection
        tool_name = self.select_tool(step.description, available_tools, job_id, dossier.id)
        tool_selection_justification = f"Selected {tool_name} because it is most appropriate for: {step.description}"
        
        # Step 2: Query Formulation
        query = self.formulate_query(step.description, tool_name, job_id, dossier.id)
        tool_query_rationale = f"Formulated query '{query}' to gather evidence for: {step.description}"
        
        # Step 3: Execute the search with tracking
        search_results = self.mcp_client.search(query, tool_name, job_id, dossier.id, step.id)
        
        # Step 4: Update the step with results and justifications
        step.tool_used = tool_name
        step.tool_selection_justification = tool_selection_justification
        step.tool_query_rationale = tool_query_rationale
        step.status = StepStatus.COMPLETED
        
        # Step 5: Create evidence items from search results
        for result in search_results.get("results", []):
            evidence_item = EvidenceItem(
                id=f"ev-{uuid.uuid4().hex[:8]}",
                dossier_id=dossier.id,
                title=result["title"],
                content=result["content"],
                source=result["source"],
                confidence=result["confidence"]
            )
            db.add(evidence_item)
        
        db.commit()
        
        return search_results
    
    def execute_research_plan(self, db: Session, dossier_id: str):
        """Execute the complete research plan for a dossier"""
        
        # Get the dossier
        dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
        if not dossier:
            raise ValueError(f"Dossier {dossier_id} not found")
        
        # Update dossier status
        dossier.status = DossierStatus.RESEARCHING
        db.commit()
        
        # Get the research plan
        research_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == dossier_id).first()
        if not research_plan:
            raise ValueError(f"Research plan not found for dossier {dossier_id}")
        
        # Get all steps
        steps = db.query(ResearchPlanStep).filter(
            ResearchPlanStep.research_plan_id == research_plan.id
        ).order_by(ResearchPlanStep.step_number).all()
        
        # Execute each step
        for step in steps:
            if step.status == StepStatus.PENDING:
                self.execute_step(db, step, dossier)
        
        # Generate summary of findings
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == dossier_id).all()
        
        if evidence_items:
            # Create a simple summary based on evidence
            summary = f"Research completed with {len(evidence_items)} evidence items gathered. "
            summary += f"The evidence supports the mission: {dossier.mission}"
        else:
            summary = f"Research completed but no evidence was found for: {dossier.mission}"
        
        # Update dossier status and summary
        dossier.status = DossierStatus.AWAITING_VERIFICATION
        dossier.summary_of_findings = summary
        db.commit()

@celery_app.task(bind=True)
def research_agent_task(self, dossier_id: str):
    """Celery task for the Research Agent"""
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting research execution'})
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Create research agent and execute plan
            agent = ResearchAgent()
            
            self.update_state(state='PROGRESS', meta={'status': 'Executing research plan'})
            
            agent.execute_research_plan(db, dossier_id)
            
            # Check if all dossiers for this job are complete
            dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
            if dossier:
                job_id = dossier.job_id
                all_dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
                
                # Check if all dossiers are in AWAITING_VERIFICATION status
                all_complete = all(d.status == DossierStatus.AWAITING_VERIFICATION for d in all_dossiers)
                
                print(f"Research agent task for dossier {dossier_id}: all_complete={all_complete}, dossier_count={len(all_dossiers)}")
                
                if all_complete:
                    # Update job status to AWAITING_VERIFICATION
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if job:
                        try:
                            job.status = JobStatus.AWAITING_VERIFICATION
                            db.commit()
                            print(f"Job {job_id} updated to AWAITING_VERIFICATION - all dossiers complete")
                        except Exception as e:
                            print(f"Error updating job status: {e}")
                            db.rollback()
                            raise
                    else:
                        print(f"Warning: Job {job_id} not found when trying to update status")
                else:
                    print(f"Not all dossiers complete for job {job_id}. Dossier statuses: {[d.status.value for d in all_dossiers]}")
            
            self.update_state(state='SUCCESS', meta={'status': 'Research completed'})
            
            return {
                'status': 'success',
                'dossier_id': dossier_id,
                'message': 'Research plan executed successfully'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Research agent task failed for dossier {dossier_id}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise 