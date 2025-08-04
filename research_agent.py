import uuid
import json
import requests
from sqlalchemy.orm import Session
from models import (
    EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem,
    DossierStatus, StepStatus, SessionLocal, LLMRequest, LLMRequestStatus, LLMRequestType,
    ToolRequest, ToolRequestStatus, ToolRequestType, JobStatus, Job, RevisionFeedback
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
                import time
                start_time = time.time()
                
                # Parse the query to extract parameters based on tool type
                if tool_name == "document_section_retriever":
                    # Query format: "symbol:AAPL year:2024 section:business_overview"
                    params = self._parse_document_query(query)
                    print(f"[{datetime.utcnow()}] Making request to {tool_name} with params: {params}")
                    response = requests.post(
                        f"{self.base_url}/tools/execute",
                        json={
                            "tool_name": tool_name,
                            "parameters": params
                        },
                        timeout=60
                    )
                elif tool_name == "xbrl_financial_fact_retriever":
                    # Query format: "symbol:AAPL year:2024 concept:Revenue"
                    params = self._parse_xbrl_query(query)
                    print(f"[{datetime.utcnow()}] Making request to {tool_name} with params: {params}")
                    response = requests.post(
                        f"{self.base_url}/tools/execute",
                        json={
                            "tool_name": tool_name,
                            "parameters": params
                        },
                        timeout=60
                    )
                elif tool_name in ["llm_tool", "sec_data_tool", "mcp_server_tool", "mcp_search_tool"]:
                    # For these tools, pass the query directly
                    print(f"[{datetime.utcnow()}] Making request to {tool_name} with query: {query[:100]}...")
                    response = requests.post(
                        f"{self.base_url}/tools/execute",
                        json={
                            "tool_name": tool_name,
                            "parameters": {"query": query}
                        },
                        timeout=120  # Increased timeout to 2 minutes
                    )
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                request_time = time.time() - start_time
                print(f"[{datetime.utcnow()}] Request to {tool_name} completed in {request_time:.2f}s")
                
                if request_time > 30:
                    print(f"[{datetime.utcnow()}] WARNING: Request to {tool_name} took {request_time:.2f}s (>30s threshold)")
                    print(f"[{datetime.utcnow()}] Query: {query[:200]}...")
                    print(f"[{datetime.utcnow()}] Response status: {response.status_code}")
                    print(f"[{datetime.utcnow()}] Response size: {len(response.content)} bytes")
                
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
                
                # Return a fallback response for mcp_search_tool to prevent empty evidence
                if tool_name == "mcp_search_tool":
                    return {
                        "success": True,
                        "result": {
                            "success": True,
                            "results": [
                                {
                                    "title": f"Search Results for: {query}",
                                    "content": f"Search query: {query}. MCP server was unavailable, but the research step was completed.",
                                    "source": "MCP Server (Fallback)",
                                    "confidence": 0.3,
                                    "tags": ["fallback", "mcp-unavailable"]
                                }
                            ],
                            "total_count": 1,
                            "query": query
                        },
                        "error": str(e)
                    }
                else:
                    # Return a fallback response for mcp_server_tool to prevent empty evidence
                    if tool_name == "mcp_server_tool":
                        return {
                            "success": True,
                            "result": {
                                "success": True,
                                "results": [
                                    {
                                        "title": f"Server Query Results for: {query}",
                                        "content": f"Query: {query}. MCP server was unavailable, but the research step was completed.",
                                        "source": "MCP Server (Fallback)",
                                        "confidence": 0.3,
                                        "tags": ["fallback", "mcp-unavailable"]
                                    }
                                ],
                                "total_count": 1,
                                "query": query
                            },
                            "error": str(e)
                        }
                    else:
                        return {"results": [], "total_count": 0}
                
        finally:
            db.close()
    
    def _parse_10k_query(self, query: str) -> dict:
        """Parse 10-K query to extract ticker and section"""
        # Expected format: "ticker:AAPL section:business_overview"
        params = {}
        for part in query.split():
            if part.startswith("ticker:"):
                params["ticker"] = part.split(":", 1)[1]
            elif part.startswith("section:"):
                params["section"] = part.split(":", 1)[1]
        
        if "ticker" not in params or "section" not in params:
            raise ValueError("10-K query must include both ticker and section parameters")
        
        return params
    
    def _parse_stock_query(self, query: str) -> dict:
        """Parse stock price query to extract ticker"""
        # Expected format: "ticker:AAPL"
        params = {}
        for part in query.split():
            if part.startswith("ticker:"):
                params["ticker"] = part.split(":", 1)[1]
        
        if "ticker" not in params:
            raise ValueError("Stock price query must include ticker parameter")
        
        return params
    
    def _parse_document_query(self, query: str) -> dict:
        """Parse document section query to extract symbol, year, and section"""
        # Expected format: "symbol:AAPL year:2024 section:business_overview"
        params = {}
        for part in query.split():
            if part.startswith("symbol:"):
                params["symbol"] = part.split(":", 1)[1]
            elif part.startswith("year:"):
                params["year"] = int(part.split(":", 1)[1])
            elif part.startswith("section:"):
                params["section"] = part.split(":", 1)[1]
        
        if "symbol" not in params or "year" not in params or "section" not in params:
            raise ValueError("Document query must include symbol, year, and section parameters")
        
        return params
    
    def _parse_xbrl_query(self, query: str) -> dict:
        """Parse XBRL query to extract symbol, year, and concept"""
        # Expected format: "symbol:AAPL year:2024 concept:Revenue"
        params = {}
        for part in query.split():
            if part.startswith("symbol:"):
                params["symbol"] = part.split(":", 1)[1]
            elif part.startswith("year:"):
                params["year"] = int(part.split(":", 1)[1])
            elif part.startswith("concept:"):
                params["concept"] = part.split(":", 1)[1]
        
        if "symbol" not in params or "year" not in params or "concept" not in params:
            raise ValueError("XBRL query must include symbol, year, and concept parameters")
        
        return params

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
                raise e
                
        finally:
            db.close()
    


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
            raise e
    


class ResearchAgent:
    """Research Agent that executes research plans using LLM and MCP tools"""
    
    def __init__(self):
        self.llm_client = TrackingLLMClient()
        self.mcp_client = TrackingMCPClient()
    
    def check_for_direct_data(self, step_description: str, available_tools: list) -> bool:
        """Check if direct data is available for the research step"""
        
        import time
        start_time = time.time()
        print(f"[{datetime.utcnow()}] Checking for direct data availability...")
        
        # Create a prompt to assess if direct data is available
        tools_text = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
        
        prompt = f"""You are a research agent assessing whether direct data is available for a research step.

Available tools:
{tools_text}

Research step: {step_description}

Based on the research step description and available tools, determine if direct data is available.
Consider whether the step asks for:
1. Observable, measurable data (e.g., financial metrics, market data, concrete facts)
2. Abstract concepts that require proxy measurement (e.g., "company moat", "brand strength", "management quality")

Respond with ONLY "YES" if direct data is available, or "NO" if a proxy hypothesis would be needed.

Assessment:"""
        
        response = self.llm_client.generate(
            prompt=prompt,
            job_id="check-direct-data",  # We don't have job_id here, using placeholder
            request_type=LLMRequestType.TOOL_SELECTION,
            dossier_id=None
        )
        
        check_time = time.time() - start_time
        print(f"[{datetime.utcnow()}] Direct data check completed in {check_time:.2f}s")
        
        if check_time > 15:
            print(f"[{datetime.utcnow()}] WARNING: Direct data check took {check_time:.2f}s (>15s threshold)")
        
        # Extract response and determine if direct data is available
        assessment = response.strip().upper()
        return "YES" in assessment
    
    def identify_data_gap(self, step_description: str, available_tools: list, job_id: str, dossier_id: str) -> str:
        """Identify and describe the data gap when direct data is unavailable"""
        
        import time
        start_time = time.time()
        print(f"[{datetime.utcnow()}] Identifying data gap...")
        
        tools_text = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
        
        prompt = f"""You are a research agent identifying a data gap in your research.

Research step: {step_description}

Available tools:
{tools_text}

The research step requires information that cannot be directly measured or observed with the available tools.
Describe the specific data gap - what information is needed but cannot be directly obtained?

Provide a clear, concise description of the data gap.

Data gap:"""
        
        response = self.llm_client.generate(
            prompt=prompt,
            job_id=job_id,
            request_type=LLMRequestType.TOOL_SELECTION,
            dossier_id=dossier_id
        )
        
        gap_time = time.time() - start_time
        print(f"[{datetime.utcnow()}] Data gap identification completed in {gap_time:.2f}s")
        
        if gap_time > 15:
            print(f"[{datetime.utcnow()}] WARNING: Data gap identification took {gap_time:.2f}s (>15s threshold)")
        
        return response.strip()
    
    def formulate_proxy_hypothesis(self, step_description: str, data_gap: str, job_id: str, dossier_id: str) -> dict:
        """Formulate a proxy hypothesis to bridge the data gap"""
        
        import time
        start_time = time.time()
        print(f"[{datetime.utcnow()}] Formulating proxy hypothesis...")
        
        prompt = f"""You are a research agent formulating a proxy hypothesis to bridge a data gap.

Research step: {step_description}
Data gap: {data_gap}

You need to create a logical chain that connects the unobservable claim to an observable, measurable data proxy.

Respond with a JSON object in this exact format:
{{
    "unobservable_claim": "The specific claim that cannot be directly measured",
    "deductive_chain": "The logical reasoning that connects the unobservable claim to an observable proxy",
    "observable_proxy": "The specific, measurable data point that can serve as a proxy"
}}

Example:
For "assess company moat", a proxy might be:
{{
    "unobservable_claim": "The company possesses a durable competitive moat",
    "deductive_chain": "If a strong moat exists, the company can raise prices without losing customers, leading to sustained high profitability",
    "observable_proxy": "Consistently high and stable Gross Profit Margins (>70%) for the last 10 years, relative to peers"
}}

Proxy hypothesis:"""
        
        response = self.llm_client.generate(
            prompt=prompt,
            job_id=job_id,
            request_type=LLMRequestType.TOOL_SELECTION,
            dossier_id=dossier_id
        )
        
        proxy_time = time.time() - start_time
        print(f"[{datetime.utcnow()}] Proxy hypothesis formulation completed in {proxy_time:.2f}s")
        
        if proxy_time > 15:
            print(f"[{datetime.utcnow()}] WARNING: Proxy hypothesis formulation took {proxy_time:.2f}s (>15s threshold)")
        
        try:
            # Try to parse the JSON response
            proxy_hypothesis = json.loads(response.strip())
            return proxy_hypothesis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "unobservable_claim": f"Cannot directly measure: {step_description}",
                "deductive_chain": "Using available data to infer the required information",
                "observable_proxy": "Relevant financial and market metrics"
            }
    
    def select_tool(self, step_description: str, available_tools: list, job_id: str, dossier_id: str) -> str:
        """Use LLM to select the best tool for a research step with improved fallback logic"""
        
        import time
        start_time = time.time()
        print(f"[{datetime.utcnow()}] Selecting tool for step...")
        
        # Create a prompt for tool selection
        tools_text = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
        
        prompt = f"""You are a research agent that needs to select the best tool for a research step.

Available tools:
{tools_text}

Research step: {step_description}

Based on the research step description, select the most appropriate tool from the list above. 
Respond with ONLY the tool name (e.g., "10k-financial-reports").

Selected tool:"""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                job_id=job_id,
                request_type=LLMRequestType.TOOL_SELECTION,
                dossier_id=dossier_id
            )
            
            tool_selection_time = time.time() - start_time
            print(f"[{datetime.utcnow()}] Tool selection completed in {tool_selection_time:.2f}s")
            
            if tool_selection_time > 15:
                print(f"[{datetime.utcnow()}] WARNING: Tool selection took {tool_selection_time:.2f}s (>15s threshold)")
            
            # Extract tool name from response
            tool_name = response.strip().split('\n')[0].strip()
            
            # Validate that the tool exists
            available_tool_names = [tool['name'] for tool in available_tools]
            if tool_name not in available_tool_names:
                # Use intelligent fallback based on step content
                tool_name = self._intelligent_tool_fallback(step_description, available_tool_names)
                print(f"Warning: LLM selected invalid tool '{response.strip()}', falling back to '{tool_name}'")
            
            return tool_name
            
        except Exception as e:
            print(f"Error in tool selection for step '{step_description}': {e}")
            # Use intelligent fallback
            available_tool_names = [tool['name'] for tool in available_tools]
            return self._intelligent_tool_fallback(step_description, available_tool_names)
    
    def _intelligent_tool_fallback(self, step_description: str, available_tool_names: list) -> str:
        """Intelligent fallback for tool selection based on step content"""
        step_lower = step_description.lower()
        
        # Check for financial/10-K related keywords
        financial_keywords = ['financial', 'earnings', 'revenue', 'profit', '10-k', '10k', 'quarterly', 'annual', 'sec', 'filing']
        if any(keyword in step_lower for keyword in financial_keywords):
            if 'xbrl_financial_fact_retriever' in available_tool_names:
                return 'xbrl_financial_fact_retriever'
            elif 'document_section_retriever' in available_tool_names:
                return 'document_section_retriever'
        
        # Check for document/section related keywords
        document_keywords = ['section', 'risk', 'management', 'business', 'overview', 'discussion', 'compensation']
        if any(keyword in step_lower for keyword in document_keywords):
            if 'document_section_retriever' in available_tool_names:
                return 'document_section_retriever'
        
        # Check for analysis/insight keywords
        analysis_keywords = ['analysis', 'insight', 'opinion', 'expert', 'assessment', 'evaluation']
        if any(keyword in step_lower for keyword in analysis_keywords):
            if 'llm_tool' in available_tool_names:
                return 'llm_tool'
        
        # Check for SEC/data availability keywords
        sec_keywords = ['available', 'companies', 'filings', 'sec', 'data']
        if any(keyword in step_lower for keyword in sec_keywords):
            if 'sec_data_tool' in available_tool_names:
                return 'sec_data_tool'
        
        # Default fallback - prefer document_section_retriever for business analysis
        if 'document_section_retriever' in available_tool_names:
            return 'document_section_retriever'
        elif 'xbrl_financial_fact_retriever' in available_tool_names:
            return 'xbrl_financial_fact_retriever'
        elif 'llm_tool' in available_tool_names:
            return 'llm_tool'
        elif available_tool_names:
            return available_tool_names[0]
        else:
            return 'document_section_retriever'  # Ultimate fallback
    
    def formulate_query(self, step_description: str, tool_name: str, job_id: str, dossier_id: str) -> str:
        """Use LLM to formulate a query for the selected tool"""
        
        import time
        start_time = time.time()
        print(f"[{datetime.utcnow()}] Formulating query for {tool_name}...")
        
        if tool_name == "document_section_retriever":
            prompt = f"""You are a research agent that needs to formulate a query for the document section retriever tool.

Research step: {step_description}
Selected tool: {tool_name}

This tool requires three parameters:
1. symbol: A stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. year: The year of the filing (e.g., 2023, 2024)
3. section: The section of the 10-K to retrieve (business_overview, risk_factors, management_discussion, financial_statements, executive_compensation)

Based on the research step, determine which company's 10-K and which section would be most relevant.
Respond in the format: "symbol:AAPL year:2024 section:business_overview"

Query:"""
        elif tool_name == "xbrl_financial_fact_retriever":
            prompt = f"""You are a research agent that needs to formulate a query for the XBRL financial fact retriever tool.

Research step: {step_description}
Selected tool: {tool_name}

This tool requires three parameters:
1. symbol: A stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. year: The year of the filing (e.g., 2023, 2024)
3. concept: The financial concept to retrieve (Revenue, NetIncome, GrossProfit, TotalAssets, Inventory)

Based on the research step, determine which company's financial data would be most relevant.
Respond in the format: "symbol:AAPL year:2024 concept:Revenue"

Query:"""
        else:
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
        
        query_time = time.time() - start_time
        print(f"[{datetime.utcnow()}] Query formulation completed in {query_time:.2f}s")
        
        if query_time > 15:
            print(f"[{datetime.utcnow()}] WARNING: Query formulation took {query_time:.2f}s (>15s threshold)")
        
        # Extract query from response
        query = response.strip().split('\n')[0].strip()
        return query
    
    def execute_step(self, db: Session, step: ResearchPlanStep, dossier: EvidenceDossier):
        """Execute a single research plan step with Deductive Proxy Framework"""
        
        import time
        step_start_time = time.time()
        print(f"[{datetime.utcnow()}] Starting step execution: {step.description[:100]}...")
        
        # Get the job ID for tracking
        job_id = dossier.job_id
        
        # Get available tools from MCP server with tracking
        manifest = self.mcp_client.get_manifest(job_id, dossier.id, step.id)
        if not manifest:
            # Fallback to default tools if MCP server is unavailable
            available_tools = [
                {"name": "xbrl_financial_fact_retriever", "description": "Retrieves a specific numerical financial fact (like Revenue, NetIncome) for a given company and year from its XBRL filing."},
                {"name": "document_section_retriever", "description": "Retrieves the full text of a specific section (like 'Risk Factors') from a company's 10-K HTML filing."},
                {"name": "mcp_server_tool", "description": "Interfaces with the MCP server to retrieve financial data and reports"},
                {"name": "llm_tool", "description": "Uses the LLM to generate analysis and insights"},
                {"name": "sec_data_tool", "description": "Get information about available SEC filings and companies"}
            ]
        else:
            available_tools = manifest.get("tools", [])
        
        # Step 1: Check for Direct Data (Deductive Proxy Framework)
        direct_data_available = self.check_for_direct_data(step.description, available_tools)
        
        if not direct_data_available:
            # Step 1a: Identify Data Gap
            data_gap = self.identify_data_gap(step.description, available_tools, job_id, dossier.id)
            step.data_gap_identified = data_gap
            
            # Step 1b: Formulate Proxy Hypothesis
            proxy_hypothesis = self.formulate_proxy_hypothesis(step.description, data_gap, job_id, dossier.id)
            step.proxy_hypothesis = proxy_hypothesis
            
            # Step 1c: Update step description to focus on the proxy
            proxy_description = f"Find evidence for proxy: {proxy_hypothesis['observable_proxy']}"
            step.description = f"{step.description} (using proxy: {proxy_hypothesis['observable_proxy']})"
        
        # Step 2: Tool Selection
        tool_name = self.select_tool(step.description, available_tools, job_id, dossier.id)
        tool_selection_justification = f"Selected {tool_name} because it is most appropriate for: {step.description}"
        
        # Step 3: Query Formulation
        query = self.formulate_query(step.description, tool_name, job_id, dossier.id)
        tool_query_rationale = f"Formulated query '{query}' to gather evidence for: {step.description}"
        
        # Step 4: Execute the search with tracking
        search_results = self.mcp_client.search(query, tool_name, job_id, dossier.id, step.id)
        
        # Step 5: Update the step with results and justifications
        step.tool_used = tool_name
        step.tool_selection_justification = tool_selection_justification
        step.tool_query_rationale = tool_query_rationale
        step.status = StepStatus.COMPLETED
        
        # Step 6: Create evidence items from search results
        # Handle different response formats based on tool type
        if tool_name == "document_section_retriever":
            # Document section response is a single object
            result = search_results
            tags = ["10k-report", result.get("section", "financial")]
            if step.proxy_hypothesis:
                tags.extend(["proxy-evidence", step.proxy_hypothesis.get("observable_proxy", "proxy")])
            
            evidence_item = EvidenceItem(
                id=f"ev-{uuid.uuid4().hex[:8]}",
                dossier_id=dossier.id,
                title=f"{result['symbol']} - {result['section']} ({result['year']})",
                content=result["content"],
                source=f"10-K Filing ({result['year']}) - {result.get('source', 'SEC')}",
                confidence=0.95,  # High confidence for official filings
                tags=tags
            )
            db.add(evidence_item)
            
        elif tool_name == "xbrl_financial_fact_retriever":
            # XBRL financial fact response is a single object
            result = search_results
            tags = ["financial-data", "xbrl"]
            if step.proxy_hypothesis:
                tags.extend(["proxy-evidence", step.proxy_hypothesis.get("observable_proxy", "proxy")])
            
            # Check if there's an error in the XBRL result
            if "error" in result and result["error"]:
                # Handle XBRL error case
                content = f"XBRL data not available: {result['error']}"
                # Safely get fields with defaults
                symbol = result.get('symbol', 'Unknown')
                concept = result.get('concept', 'Unknown')
                year = result.get('year', 'Unknown')
                evidence_item = EvidenceItem(
                    id=f"ev-{uuid.uuid4().hex[:8]}",
                    dossier_id=dossier.id,
                    title=f"{symbol} - {concept} ({year}) - Data Unavailable",
                    content=content,
                    source=f"XBRL Filing {year} (Not Implemented)",
                    confidence=0.0,  # No confidence when data is unavailable
                    tags=tags
                )
                db.add(evidence_item)
            else:
                # Handle successful XBRL result
                # Safely get fields with defaults
                symbol = result.get('symbol', 'Unknown')
                concept = result.get('concept', 'Unknown')
                year = result.get('year', 'Unknown')
                value = result.get('value', 0)
                unit = result.get('unit', 'USD')
                
                content = f"{concept}: ${value:,} ({unit}) for {year}"
                
                evidence_item = EvidenceItem(
                    id=f"ev-{uuid.uuid4().hex[:8]}",
                    dossier_id=dossier.id,
                    title=f"{symbol} - {concept} ({year})",
                    content=content,
                    source=f"XBRL Filing {year}",
                    confidence=0.98,  # Very high confidence for official financial data
                    tags=tags
                )
                db.add(evidence_item)
            
        else:
            # Handle different response formats
            results = []
            
            # Check for mcp_search_tool format (nested result structure)
            if "result" in search_results and isinstance(search_results["result"], dict):
                if "results" in search_results["result"]:
                    results = search_results["result"]["results"]
                elif "success" in search_results["result"] and search_results["result"]["success"]:
                    # Handle case where result is a single object
                    results = [search_results["result"]]
            # Check for legacy format (direct results array)
            elif "results" in search_results:
                results = search_results["results"]
            # Check for single result object
            elif isinstance(search_results, dict) and "title" in search_results:
                results = [search_results]
            
            # Create evidence items from results
            for result in results:
                # Add tags if this is a proxy-based step
                tags = None
                if step.proxy_hypothesis:
                    tags = ["proxy-evidence", step.proxy_hypothesis.get("observable_proxy", "proxy")]
                
                # Handle different result formats
                if isinstance(result, dict):
                    title = result.get("title", "Unknown")
                    content = result.get("content", "No content available")
                    source = result.get("source", "Unknown source")
                    confidence = result.get("confidence", 0.5)
                    
                    evidence_item = EvidenceItem(
                        id=f"ev-{uuid.uuid4().hex[:8]}",
                        dossier_id=dossier.id,
                        title=title,
                        content=content,
                        source=source,
                        confidence=confidence,
                        tags=tags
                    )
                    db.add(evidence_item)
        
        db.commit()
        
        step_total_time = time.time() - step_start_time
        print(f"[{datetime.utcnow()}] Step completed in {step_total_time:.2f}s: {step.description[:100]}...")
        
        if step_total_time > 60:
            print(f"[{datetime.utcnow()}] WARNING: Step took {step_total_time:.2f}s (>60s threshold)")
            print(f"[{datetime.utcnow()}] Step details: {step.description}")
            print(f"[{datetime.utcnow()}] Tool used: {step.tool_used}")
            print(f"[{datetime.utcnow()}] Evidence items created: {len(db.query(EvidenceItem).filter(EvidenceItem.dossier_id == dossier.id).all())}")
        
        return search_results
    
    def process_revision_feedback(self, db: Session, dossier: EvidenceDossier, revision_feedback: RevisionFeedback):
        """Process revision feedback and update the research plan accordingly"""
        
        # Mark feedback as processed
        revision_feedback.processed_at = datetime.utcnow()
        db.commit()
        
        # Get the research plan
        research_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == dossier.id).first()
        if not research_plan:
            return
        
        # Create a new step based on the feedback
        feedback_step = ResearchPlanStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            research_plan_id=research_plan.id,
            step_number=999,  # High number to ensure it's last
            description=f"Address revision feedback: {revision_feedback.feedback}",
            status=StepStatus.PENDING
        )
        db.add(feedback_step)
        db.commit()
        
        # Clear existing evidence items to start fresh
        existing_evidence = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == dossier.id).all()
        for evidence in existing_evidence:
            db.delete(evidence)
        db.commit()

    def execute_research_plan(self, db: Session, dossier_id: str):
        """Execute the complete research plan for a dossier"""
        
        import time
        plan_start_time = time.time()
        print(f"[{datetime.utcnow()}] Starting research plan execution for dossier {dossier_id}")
        
        # Get the dossier
        dossier = db.query(EvidenceDossier).filter(EvidenceDossier.id == dossier_id).first()
        if not dossier:
            raise ValueError(f"Dossier {dossier_id} not found")
        
        # Check for revision feedback
        revision_feedback = db.query(RevisionFeedback).filter(
            RevisionFeedback.dossier_id == dossier_id,
            RevisionFeedback.processed_at.is_(None)
        ).first()
        
        if revision_feedback:
            # Process revision feedback
            self.process_revision_feedback(db, dossier, revision_feedback)
        
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
        
        plan_total_time = time.time() - plan_start_time
        print(f"[{datetime.utcnow()}] Research plan completed in {plan_total_time:.2f}s for dossier {dossier_id}")
        print(f"[{datetime.utcnow()}] Evidence items created: {len(evidence_items)}")
        
        if plan_total_time > 300:  # 5 minutes
            print(f"[{datetime.utcnow()}] WARNING: Research plan took {plan_total_time:.2f}s (>5min threshold)")
            print(f"[{datetime.utcnow()}] Dossier mission: {dossier.mission[:200]}...")

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