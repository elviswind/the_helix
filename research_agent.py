import uuid
import json
import requests
from sqlalchemy.orm import Session
from models import (
    EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem,
    DossierStatus, StepStatus, SessionLocal
)
from celery_app import celery_app

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
    """Agent responsible for executing research plans and gathering evidence"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.mcp_client = MCPClient()
    
    def select_tool(self, step_description: str, available_tools: list) -> str:
        """Use LLM to select the best tool for a research step"""
        
        tools_info = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
        
        prompt = f"""
You are a research agent that needs to select the most appropriate tool for a research step.

Available tools:
{tools_info}

Research step: {step_description}

Based on the research step description, which tool would be most appropriate? 
Respond with only the tool name (e.g., "market-data-api").
"""
        
        response = self.llm_client.generate(prompt)
        # Clean up the response to get just the tool name
        tool_name = response.strip().split('\n')[0].strip()
        
        # Validate that the tool exists
        available_tool_names = [tool['name'] for tool in available_tools]
        if tool_name not in available_tool_names:
            # Fallback to first available tool
            tool_name = available_tool_names[0] if available_tool_names else "market-data-api"
        
        return tool_name
    
    def formulate_query(self, step_description: str, tool_name: str) -> str:
        """Use LLM to formulate an appropriate query for the selected tool"""
        
        prompt = f"""
You are a research agent that needs to formulate a search query for a specific tool.

Research step: {step_description}
Selected tool: {tool_name}

Based on the research step and the tool, formulate a specific search query that will help gather relevant evidence.
The query should be focused and specific to the research objective.

Respond with only the search query (e.g., "growth trends market indicators").
"""
        
        response = self.llm_client.generate(prompt)
        return response.strip()
    
    def execute_step(self, db: Session, step: ResearchPlanStep, dossier: EvidenceDossier):
        """Execute a single research plan step"""
        
        # Get available tools from MCP server
        manifest = self.mcp_client.get_manifest()
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
        tool_name = self.select_tool(step.description, available_tools)
        tool_selection_justification = f"Selected {tool_name} because it is most appropriate for: {step.description}"
        
        # Step 2: Query Formulation
        query = self.formulate_query(step.description, tool_name)
        tool_query_rationale = f"Formulated query '{query}' to gather evidence for: {step.description}"
        
        # Step 3: Execute the search
        search_results = self.mcp_client.search(query, tool_name)
        
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
            
            self.update_state(state='SUCCESS', meta={'status': 'Research completed'})
            
            return {
                'status': 'success',
                'dossier_id': dossier_id,
                'message': 'Research plan executed successfully'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise 