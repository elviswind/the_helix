import requests
import json
import uuid
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from bs4 import BeautifulSoup

# Import the real SEC parser
from sec_parser import get_10k_section, get_10k_filing, get_available_companies, get_available_years

# Import the existing LLM client
from orchestrator_agent import TrackingLLMClient

def parse_ixbrl_filing(file_path: str) -> Dict[str, Any]:
    """
    Parse an iXBRL filing using BeautifulSoup and extract financial facts
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract facts from ix:nonnumeric and ix:nonfraction tags
        facts = {}
        contexts = {}
        
        # Find all ix:nonnumeric tags (text facts)
        for tag in soup.find_all(['ix:nonnumeric', 'ix:nonfraction']):
            if tag.get('name') and tag.get('contextref'):
                concept_name = tag.get('name')
                context_ref = tag.get('contextref')
                value = tag.get_text(strip=True)
                unit = tag.get('unitref')
                
                # Store context information
                if context_ref not in contexts:
                    contexts[context_ref] = {
                        "context_id": context_ref,
                        "unit": unit
                    }
                
                # Store fact
                if concept_name not in facts:
                    facts[concept_name] = []
                
                facts[concept_name].append({
                    "value": value,
                    "context": context_ref,
                    "unit": unit,
                    "tag_type": tag.name
                })
        
        # Also look for numeric facts in the visible HTML
        # These are often in tables with financial data
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    # Look for cells that might contain financial data
                    text = cell.get_text(strip=True)
                    if text and re.match(r'^\$?[\d,]+\.?\d*$', text):
                        # This looks like a financial number
                        # Try to find a label in nearby cells
                        for sibling in cell.find_previous_siblings():
                            if sibling.get_text(strip=True):
                                label = sibling.get_text(strip=True)
                                if label not in facts:
                                    facts[label] = []
                                facts[label].append({
                                    "value": text,
                                    "context": "visible_table",
                                    "unit": "USD",
                                    "tag_type": "table_cell"
                                })
                                break
        
        return {
            "success": True,
            "facts": facts,
            "contexts": contexts,
            "filing_date": os.path.basename(file_path)
        }
        
    except Exception as e:
        return {"error": f"Error parsing iXBRL filing: {str(e)}"}

def get_financial_fact(symbol: str, year: int, concept: str):
    """Get financial fact from real iXBRL data"""
    # Map symbol to company directory name
    company_map = {
        "AAPL": "AAPL",
        "MSFT": "MSFT", 
        "GOOGL": "GOOGL",
        "AMZN": "AMZN",
        "TSLA": "TSLA"
    }
    
    # Map common financial terms to their XBRL concept names
    concept_mapping = {
        "Revenue": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "NetIncome": "us-gaap:NetIncomeLoss",
        "GrossProfit": "us-gaap:GrossProfit",
        "TotalAssets": "us-gaap:Assets",
        "TotalLiabilities": "us-gaap:Liabilities",
        "CashAndCashEquivalents": "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "PropertyPlantAndEquipmentNet": "us-gaap:PropertyPlantAndEquipmentNet",
        "Goodwill": "us-gaap:Goodwill",
        "IntangibleAssetsNet": "us-gaap:IntangibleAssetsNet",
        "AccountsReceivableNet": "us-gaap:AccountsReceivableNetCurrent",
        "InventoryNet": "us-gaap:InventoryNet",
        "OperatingIncome": "us-gaap:OperatingIncomeLoss",
        "OperatingExpenses": "us-gaap:OperatingExpenses",
        "ResearchAndDevelopmentExpense": "us-gaap:ResearchAndDevelopmentExpense",
        "SellingGeneralAndAdministrativeExpense": "us-gaap:SellingGeneralAndAdministrativeExpense",
        "InterestExpense": "us-gaap:InterestExpense",
        "IncomeTaxExpense": "us-gaap:IncomeTaxExpenseBenefit",
        "EarningsPerShareBasic": "us-gaap:EarningsPerShareBasic",
        "EarningsPerShareDiluted": "us-gaap:EarningsPerShareDiluted",
        "WeightedAverageNumberOfSharesOutstandingBasic": "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
        "WeightedAverageNumberOfSharesOutstandingDiluted": "us-gaap:WeightedAverageNumberOfSharesOutstandingDiluted",
        "CommonStockValue": "us-gaap:CommonStockValue",
        "RetainedEarnings": "us-gaap:RetainedEarningsAccumulatedDeficit",
        "TotalStockholdersEquity": "us-gaap:StockholdersEquity",
        "NetCashProvidedByOperatingActivities": "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "NetCashUsedInInvestingActivities": "us-gaap:NetCashUsedInProvidedByInvestingActivities",
        "NetCashUsedInFinancingActivities": "us-gaap:NetCashUsedInProvidedByFinancingActivities"
    }
    
    # Use the mapping if the concept is a common term
    if concept in concept_mapping:
        concept = concept_mapping[concept]
    
    company = company_map.get(symbol.upper(), symbol.upper())
    
    # Construct the file path to the iXBRL filing
    file_path = f"/mnt/d/Orca/Data/sec_forms/{company}/10-K_{year}.html"
    
    if not os.path.exists(file_path):
        return {
            "symbol": symbol,
            "year": year,
            "concept": concept,
            "value": None,
            "error": f"iXBRL filing not found: {file_path}",
            "unit": "USD"
        }
    
    # Parse the iXBRL filing
    xbrl_data = parse_ixbrl_filing(file_path)
    
    if "error" in xbrl_data:
        return {
            "symbol": symbol,
            "year": year,
            "concept": concept,
            "value": None,
            "error": xbrl_data["error"],
            "unit": "USD"
        }
    
    # Look for the specific concept in the facts
    facts = xbrl_data.get("facts", {})
    
    # Try different variations of the concept name
    concept_variations = [
        concept,
        f"us-gaap:{concept}",
        f"aapl:{concept}",
        concept.upper(),
        concept.lower(),
        f"dei:{concept}",
        f"srt:{concept}"
    ]
    
    found_facts = []
    for concept_var in concept_variations:
        if concept_var in facts:
            found_facts.extend(facts[concept_var])
    
    if not found_facts:
        # Return available concepts for debugging
        available_concepts = list(facts.keys())
        return {
            "symbol": symbol,
            "year": year,
            "concept": concept,
            "value": None,
            "error": f"Concept '{concept}' not found in iXBRL filing. Available concepts: {available_concepts[:10]}...",
            "unit": "USD",
            "available_concepts": available_concepts[:20]  # First 20 for reference
        }
    
    # Return the most recent fact (assuming facts are ordered by date)
    latest_fact = found_facts[0]  # Take the first one for now
    
    return {
        "symbol": symbol,
        "year": year,
        "concept": concept,
        "value": latest_fact["value"],
        "unit": latest_fact.get("unit", "USD"),
        "context": latest_fact.get("context", {}),
        "source": f"Real iXBRL Data from {file_path}"
    }

def get_available_financial_concepts(symbol: str, year: int):
    """Get list of available financial concepts from iXBRL filing"""
    company_map = {
        "AAPL": "AAPL",
        "MSFT": "MSFT",
        "GOOGL": "GOOGL", 
        "AMZN": "AMZN",
        "TSLA": "TSLA"
    }
    
    company = company_map.get(symbol.upper(), symbol.upper())
    file_path = f"/mnt/d/Orca/Data/sec_forms/{company}/10-K_{year}.html"
    
    if not os.path.exists(file_path):
        return {
            "symbol": symbol,
            "year": year,
            "error": f"iXBRL filing not found: {file_path}"
        }
    
    xbrl_data = parse_ixbrl_filing(file_path)
    
    if "error" in xbrl_data:
        return {
            "symbol": symbol,
            "year": year,
            "error": xbrl_data["error"]
        }
    
    facts = xbrl_data.get("facts", {})
    concepts = list(facts.keys())
    
    # Filter to common financial concepts
    common_concepts = [
        "Revenue", "NetIncome", "GrossProfit", "TotalAssets", "TotalLiabilities",
        "CashAndCashEquivalents", "PropertyPlantAndEquipmentNet", "Goodwill",
        "IntangibleAssetsNet", "AccountsReceivableNet", "InventoryNet",
        "OperatingIncome", "OperatingExpenses", "ResearchAndDevelopmentExpense",
        "SellingGeneralAndAdministrativeExpense", "InterestExpense", "IncomeTaxExpense",
        "EarningsPerShareBasic", "EarningsPerShareDiluted", "WeightedAverageNumberOfSharesOutstandingBasic",
        "WeightedAverageNumberOfSharesOutstandingDiluted", "CommonStockValue",
        "RetainedEarnings", "TotalStockholdersEquity", "NetCashProvidedByOperatingActivities",
        "NetCashUsedInInvestingActivities", "NetCashUsedInFinancingActivities"
    ]
    
    available_common = [c for c in concepts if any(common in c for common in common_concepts)]
    
    return {
        "symbol": symbol,
        "year": year,
        "total_concepts": len(concepts),
        "common_financial_concepts": available_common,
        "all_concepts": concepts[:50]  # First 50 for reference
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

class XBRLConceptsTool:
    name = "xbrl_available_concepts_retriever"
    description = "Retrieves a list of available financial concepts from a company's XBRL filing for a given year."

    def run(self, symbol: str, year: int):
        return get_available_financial_concepts(symbol, year)

class DocumentSectionTool:
    name = "document_section_retriever"
    description = "Retrieves the full text of a specific section (like 'Risk Factors') from a company's 10-K HTML filing."

    def run(self, symbol: str, year: int, section: str):
        return get_section_text(symbol, year, section)

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
    "xbrl_available_concepts_retriever": XBRLConceptsTool(),
    "document_section_retriever": DocumentSectionTool(),
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