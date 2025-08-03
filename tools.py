import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Import the real SEC parser
from sec_parser import get_10k_section, get_10k_filing, get_available_companies, get_available_years

# Import the existing LLM client
from orchestrator_agent import TrackingLLMClient

def get_financial_fact(symbol: str, year: int, concept: str):
    """Get financial fact from XBRL data"""
    # Mock data for development - replace with actual XBRL data sources in production
    mock_data = {
        "AAPL": {
            "Revenue": {
                2024: 394328000000,  # $394.3B
                2023: 383285000000,  # $383.3B
                2022: 394328000000,  # $394.3B
            },
            "NetIncome": {
                2024: 96995000000,   # $97.0B
                2023: 96995000000,   # $97.0B
                2022: 96995000000,   # $97.0B
            },
            "GrossProfit": {
                2024: 169148000000,  # $169.1B
                2023: 169148000000,  # $169.1B
                2022: 169148000000,  # $169.1B
            }
        }
    }
    
    # Check if we have mock data for this symbol and concept
    if symbol.upper() in mock_data and concept in mock_data[symbol.upper()]:
        if year in mock_data[symbol.upper()][concept]:
            return {
                "symbol": symbol,
                "year": year,
                "concept": concept,
                "value": mock_data[symbol.upper()][concept][year],
                "unit": "USD",
                "source": "Mock XBRL Data (Development)"
            }
    
    # Return error for unavailable data
    return {
        "symbol": symbol,
        "year": year,
        "concept": concept,
        "value": None,
        "error": f"XBRL data not available for {symbol} {concept} {year}",
        "unit": "USD"
    }

def get_section_text(symbol: str, year: int, section: str):
    """Get section text from real 10-K filings"""
    # Map symbol to company directory name
    company_map = {
        "AAPL": "AAPL",
        "MSFT": "MSFT",
        "GOOGL": "GOOGL",
        "AMZN": "AMZN",
        "TSLA": "TSLA"
    }
    
    company = company_map.get(symbol.upper(), symbol.upper())
    
    # Get the section content from real SEC filings
    result = get_10k_section(company, year, section)
    
    if "error" in result:
        return {
            "symbol": symbol,
            "year": year,
            "section": section,
            "content": None,
            "error": result["error"]
        }
    
    return {
        "symbol": symbol,
        "year": year,
        "section": section,
        "content": result["content"],
        "source": result["source"],
        "page": result["page"]
    }

# Simple tool classes without LangChain dependency
class XBRLFactTool:
    name = "xbrl_financial_fact_retriever"
    description = "Retrieves a specific numerical financial fact (like Revenue, NetIncome) for a given company and year from its XBRL filing."

    def run(self, symbol: str, year: int, concept: str):
        return get_financial_fact(symbol, year, concept)

class DocumentSectionTool:
    name = "document_section_retriever"
    description = "Retrieves the full text of a specific section (like 'Risk Factors') from a company's 10-K HTML filing."

    def run(self, symbol: str, year: int, section: str):
        return get_section_text(symbol, year, section)

class MCPTool:
    name = "mcp_server_tool"
    description = "Interfaces with the MCP server to retrieve financial data and reports"

    def run(self, query: str = None, tool_name: str = None, parameters: dict = None):
        """
        Run MCP tool with flexible parameter handling.
        Can be called with either:
        - query: str (for search queries)
        - tool_name: str, parameters: dict (for specific tool calls)
        """
        mcp_server_url = "http://localhost:8001"
        
        try:
            # Handle search query case
            if query:
                # For search queries, we'll use the tools/execute endpoint with a search tool
                response = requests.post(
                    f"{mcp_server_url}/tools/execute",
                    json={
                        "tool_name": "mcp_search_tool",
                        "parameters": {"query": query}
                    },
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            
            # Handle specific tool calls
            elif tool_name and parameters:
                response = requests.post(
                    f"{mcp_server_url}/tools/execute",
                    json={
                        "tool_name": tool_name,
                        "parameters": parameters
                    },
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            
            else:
                return {"error": "MCPTool requires either 'query' or both 'tool_name' and 'parameters'"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"MCP server request failed: {str(e)}"}

class LLMTool:
    name = "llm_tool"
    description = "Uses the LLM to generate analysis and insights"

    def __init__(self):
        self.llm_client = TrackingLLMClient()
    
    def run(self, prompt: str, job_id: str, request_type: str, dossier_id: str = None):
        """Run LLM analysis"""
        from models import LLMRequestType
        
        # Map request type string to enum
        type_map = {
            "orchestrator_mission": LLMRequestType.ORCHESTRATOR_MISSION,
            "tool_selection": LLMRequestType.TOOL_SELECTION,
            "query_formulation": LLMRequestType.QUERY_FORMULATION,
            "synthesis": LLMRequestType.SYNTHESIS
        }
        
        llm_request_type = type_map.get(request_type, LLMRequestType.ORCHESTRATOR_MISSION)
        
        try:
            result = self.llm_client.generate(prompt, job_id, llm_request_type, dossier_id)
            return {
                "success": True,
                "response": result,
                "request_type": request_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "request_type": request_type
            }

class MCPSearchTool:
    name = "mcp_search_tool"
    description = "Search for financial data and reports using the MCP server"

    def run(self, query: str):
        """Search for financial data based on query"""
        # For now, return a mock response that simulates search results
        # In a real implementation, this would search through financial databases
        return {
            "success": True,
            "results": [
                {
                    "title": "Apple Inc. Financial Performance Analysis",
                    "content": "Apple's revenue growth has been consistent over the past 5 years, with strong performance in the mobile phone market.",
                    "source": "Financial Analysis Report",
                    "confidence": 0.85,
                    "tags": ["financial", "revenue", "mobile"]
                },
                {
                    "title": "Mobile Phone Market Share Analysis",
                    "content": "Apple maintains a strong position in the premium smartphone segment with approximately 20% global market share.",
                    "source": "Market Research Report",
                    "confidence": 0.78,
                    "tags": ["market_share", "mobile", "premium"]
                },
                {
                    "title": "Competitive Analysis: Apple vs Android",
                    "content": "While Apple leads in profitability and brand loyalty, Android manufacturers are gaining ground in emerging markets and innovation areas like foldable displays.",
                    "source": "Competitive Intelligence",
                    "confidence": 0.72,
                    "tags": ["competition", "android", "innovation"]
                }
            ],
            "total_count": 3,
            "query": query
        }

class SECDataTool:
    name = "sec_data_tool"
    description = "Get information about available SEC filings and companies"

    def run(self, action: str, company: str = None):
        """Get SEC data information"""
        if action == "list_companies":
            companies = get_available_companies()
            return {
                "action": action,
                "companies": companies,
                "count": len(companies)
            }
        elif action == "list_years" and company:
            years = get_available_years(company)
            return {
                "action": action,
                "company": company,
                "years": years,
                "count": len(years)
            }
        elif action == "get_filing" and company:
            # Get the most recent year available
            years = get_available_years(company)
            if years:
                latest_year = max(years)
                filing_data = get_10k_filing(company, latest_year)
                return {
                    "action": action,
                    "company": company,
                    "year": latest_year,
                    "filing_info": filing_data.get("filing_info", {}),
                    "sections_available": list(filing_data.get("sections", {}).keys())
                }
            else:
                return {
                    "action": action,
                    "company": company,
                    "error": "No filings available for this company"
                }
        else:
            return {
                "error": f"Invalid action: {action}. Valid actions: list_companies, list_years, get_filing"
            }

# Tool registry for easy access
tool_registry = {
    "xbrl_financial_fact_retriever": XBRLFactTool(),
    "document_section_retriever": DocumentSectionTool(),
    "mcp_server_tool": MCPTool(),
    "mcp_search_tool": MCPSearchTool(),
    "llm_tool": LLMTool(),
    "sec_data_tool": SECDataTool()
}

def get_tool_by_name(tool_name: str):
    """Get a tool instance by name"""
    return tool_registry.get(tool_name)

def execute_tool(tool_name: str, **kwargs):
    """Execute a tool with given parameters"""
    tool = get_tool_by_name(tool_name)
    if tool:
        return tool.run(**kwargs)
    else:
        return {"error": f"Tool {tool_name} not found"}

# Available tools list
available_tools = list(tool_registry.values()) 