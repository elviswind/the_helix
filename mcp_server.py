from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import uuid

app = FastAPI(title="Mock MCP Server", version="1.0.0")

# Mock data store
mock_data = {
    "market-data": [
        {
            "id": "md-001",
            "title": "Market Growth Analysis Q4 2024",
            "content": "Market analysis shows strong growth indicators with 15% year-over-year increase in key metrics. Revenue growth has been steady and sustainable, indicating strong market demand.",
            "source": "Market Analysis Report 2024",
            "confidence": 0.85,
            "tags": ["growth", "revenue", "market-trends"]
        },
        {
            "id": "md-002", 
            "title": "Market Volatility Assessment",
            "content": "Recent market volatility has increased by 25% with several concerning indicators pointing to potential instability. Economic uncertainty creates significant headwinds.",
            "source": "Volatility Analysis Report",
            "confidence": 0.80,
            "tags": ["volatility", "risk", "uncertainty"]
        }
    ],
    "expert-analysis": [
        {
            "id": "ea-001",
            "title": "Bullish Analyst Consensus",
            "content": "Leading industry experts maintain positive outlook with 80% of surveyed analysts recommending strong buy positions. Consensus estimates project continued growth trajectory.",
            "source": "Expert Consensus Survey",
            "confidence": 0.90,
            "tags": ["bullish", "expert-opinion", "growth"]
        },
        {
            "id": "ea-002",
            "title": "Risk Warning Reports",
            "content": "20% of industry experts have issued cautionary statements about current market conditions and potential downside risks. Several analysts have downgraded growth projections.",
            "source": "Risk Assessment Survey", 
            "confidence": 0.75,
            "tags": ["bearish", "risk-warnings", "downgrades"]
        }
    ],
    "competitive-analysis": [
        {
            "id": "ca-001",
            "title": "Competitive Market Position",
            "content": "Analysis reveals strong competitive advantages including brand recognition, proprietary technology, and established customer relationships. Market share has grown consistently.",
            "source": "Competitive Analysis Database",
            "confidence": 0.88,
            "tags": ["competitive-advantage", "market-share", "brand"]
        },
        {
            "id": "ca-002",
            "title": "Emerging Competitive Threats",
            "content": "Emerging competitors are gaining market share rapidly, particularly in key growth segments. Disruptive technologies could potentially undermine current competitive advantages.",
            "source": "Competitive Threat Assessment",
            "confidence": 0.78,
            "tags": ["competitive-threats", "disruption", "market-share-loss"]
        }
    ],
    "financial-data": [
        {
            "id": "fd-001",
            "title": "Strong Financial Health Indicators",
            "content": "Strong balance sheet with healthy cash flow, manageable debt levels, and consistent profitability. Key financial ratios are well within industry benchmarks.",
            "source": "Financial Health Assessment",
            "confidence": 0.82,
            "tags": ["financial-health", "cash-flow", "profitability"]
        },
        {
            "id": "fd-002",
            "title": "Financial Risk Indicators",
            "content": "Several financial metrics show concerning trends including increasing debt levels, declining cash flow margins, and potential liquidity constraints in adverse scenarios.",
            "source": "Financial Risk Analysis",
            "confidence": 0.72,
            "tags": ["financial-risk", "debt", "liquidity"]
        }
    ]
}

class MCPManifest(BaseModel):
    name: str
    version: str
    description: str
    tools: List[Dict[str, Any]]

class MCPSearchRequest(BaseModel):
    query: str
    tool_name: Optional[str] = None
    max_results: Optional[int] = 10

class MCPSearchResult(BaseModel):
    id: str
    title: str
    content: str
    source: str
    confidence: float
    tags: List[str]

class MCPSearchResponse(BaseModel):
    results: List[MCPSearchResult]
    total_count: int

@app.get("/manifest", response_model=MCPManifest)
async def get_manifest():
    """Return the MCP server manifest with available tools"""
    return MCPManifest(
        name="Mock MCP Server",
        version="1.0.0",
        description="A mock MCP server for testing the Research Agent with predefined data sources",
        tools=[
            {
                "name": "market-data-api",
                "description": "Access to market data and trends analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for market data"
                        }
                    }
                }
            },
            {
                "name": "expert-analysis-db", 
                "description": "Database of expert opinions and analyst reports",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for expert analysis"
                        }
                    }
                }
            },
            {
                "name": "competitive-analysis-api",
                "description": "Competitive analysis and market position data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for competitive analysis"
                        }
                    }
                }
            },
            {
                "name": "risk-assessment-api",
                "description": "Risk assessment and volatility analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for risk assessment"
                        }
                    }
                }
            },
            {
                "name": "financial-data-api",
                "description": "Financial health and risk indicators",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for financial data"
                        }
                    }
                }
            }
        ]
    )

@app.post("/search", response_model=MCPSearchResponse)
async def search_data(request: MCPSearchRequest):
    """Search for data based on query and tool selection"""
    
    # Determine which data source to search based on tool_name
    data_source = None
    if request.tool_name == "market-data-api":
        data_source = "market-data"
    elif request.tool_name == "expert-analysis-db":
        data_source = "expert-analysis"
    elif request.tool_name == "competitive-analysis-api":
        data_source = "competitive-analysis"
    elif request.tool_name == "risk-assessment-api":
        # Risk assessment can search across multiple sources
        data_source = None
    elif request.tool_name == "financial-data-api":
        data_source = "financial-data"
    else:
        # If no specific tool, search across all sources
        data_source = None
    
    # Search logic
    results = []
    query_lower = request.query.lower()
    
    if data_source:
        # Search in specific data source
        for item in mock_data[data_source]:
            if (query_lower in item["title"].lower() or 
                query_lower in item["content"].lower() or
                any(query_lower in tag.lower() for tag in item["tags"])):
                results.append(MCPSearchResult(**item))
    else:
        # Search across all data sources
        for source_name, source_data in mock_data.items():
            for item in source_data:
                if (query_lower in item["title"].lower() or 
                    query_lower in item["content"].lower() or
                    any(query_lower in tag.lower() for tag in item["tags"])):
                    results.append(MCPSearchResult(**item))
    
    # Limit results
    results = results[:request.max_results]
    
    return MCPSearchResponse(
        results=results,
        total_count=len(results)
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Mock MCP Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 