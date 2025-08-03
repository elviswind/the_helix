import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Import the real SEC parser
from sec_parser import get_10k_section, get_10k_filing, get_available_companies, get_available_years

# Import the existing LLM client
from orchestrator_agent import TrackingLLMClient

# Mock XBRL data for now - this would be replaced with actual XBRL parsing
def get_financial_fact(symbol: str, year: int, concept: str):
    """Get financial fact from XBRL data"""
    # This would connect to actual XBRL data sources
    # For now, using mock data but this could be enhanced with Arelle or similar
    mock_data = {
        "AAPL": {
            "Revenue": {"2023": 383285000000, "2022": 394328000000, "2021": 365817000000},
            "NetIncome": {"2023": 96995000000, "2022": 99803000000, "2021": 94680000000},
            "Inventory": {"2023": 6331000000, "2022": 4946000000, "2021": 6580000000},
            "GrossProfit": {"2023": 169148000000, "2022": 170782000000, "2021": 152836000000},
            "TotalAssets": {"2023": 352755000000, "2022": 346747000000, "2021": 351002000000}
        },
        "MSFT": {
            "Revenue": {"2023": 211915000000, "2022": 198270000000, "2021": 168088000000},
            "NetIncome": {"2023": 72409000000, "2022": 72619000000, "2021": 61271000000},
            "Inventory": {"2023": 2500000000, "2022": 3744000000, "2021": 2600000000},
            "GrossProfit": {"2023": 146052000000, "2022": 135620000000, "2021": 115856000000},
            "TotalAssets": {"2023": 470558000000, "2022": 364840000000, "2021": 333779000000}
        }
    }
    
    if symbol in mock_data and concept in mock_data[symbol] and str(year) in mock_data[symbol][concept]:
        return {
            "symbol": symbol,
            "year": year,
            "concept": concept,
            "value": mock_data[symbol][concept][str(year)],
            "unit": "USD",
            "source": f"XBRL Filing {year}"
        }
    else:
        return {
            "symbol": symbol,
            "year": year,
            "concept": concept,
            "value": None,
            "error": f"Data not available for {symbol} {concept} {year}"
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

    def run(self, tool_name: str, parameters: dict):
        mcp_server_url = "http://localhost:8001"
        
        try:
            if tool_name == "10k-financial-reports":
                response = requests.post(
                    f"{mcp_server_url}/10k-report",
                    json=parameters,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            
            elif tool_name == "eod-stock-prices":
                response = requests.post(
                    f"{mcp_server_url}/stock-price",
                    json=parameters,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            
            else:
                return {"error": f"Unknown MCP tool: {tool_name}"}
                
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