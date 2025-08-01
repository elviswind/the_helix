from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import uuid
import time
import asyncio
from datetime import datetime, timedelta
import random

app = FastAPI(title="Mock MCP Server", version="1.0.0")

# Mock 10-K financial report data
mock_10k_data = {
    "AAPL": {
        "company_name": "Apple Inc.",
        "filing_date": "2024-10-28",
        "sections": {
            "business_overview": {
                "title": "Business Overview",
                "content": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables and accessories, and sells a variety of related services. The Company's fiscal year is the 52 or 53-week period that ends on the last Saturday of September. The Company's net sales for fiscal 2024 were $383.3 billion, an increase of 2% compared to fiscal 2023. The Company's net income for fiscal 2024 was $97.0 billion, a decrease of 2% compared to fiscal 2023.",
                "page": 1
            },
            "risk_factors": {
                "title": "Risk Factors",
                "content": "The Company's business and financial results are subject to various risks and uncertainties, including but not limited to: global and regional economic conditions that could materially adversely affect the Company's business, results of operations, financial condition, and stock price; the Company's reliance on third-party suppliers and manufacturers; the Company's ability to compete effectively in the highly competitive consumer electronics industry; and the Company's ability to develop and maintain successful relationships with carriers and other distribution partners.",
                "page": 15
            },
            "management_discussion": {
                "title": "Management's Discussion and Analysis",
                "content": "Net sales increased 2% during fiscal 2024 compared to fiscal 2023. The increase in net sales was primarily driven by higher net sales of iPhone, Services, and Mac, partially offset by lower net sales of iPad and Wearables, Home and Accessories. iPhone net sales increased 6% during fiscal 2024 compared to fiscal 2023, primarily due to higher net sales of iPhone 15 Pro and iPhone 15 Pro Max models.",
                "page": 25
            },
            "financial_statements": {
                "title": "Financial Statements",
                "content": "As of September 28, 2024, the Company had total assets of $352.8 billion, including cash and cash equivalents of $29.9 billion, short-term marketable securities of $31.9 billion, and long-term marketable securities of $100.9 billion. Total liabilities were $287.9 billion, including accounts payable of $64.1 billion and long-term debt of $95.9 billion.",
                "page": 45
            },
            "executive_compensation": {
                "title": "Executive Compensation",
                "content": "The Company's executive compensation program is designed to attract, retain, and motivate talented executives who can drive the Company's long-term success. The program includes base salary, annual cash incentives, and long-term equity awards. For fiscal 2024, the total compensation for the CEO was $63.2 million, including salary of $3.0 million, bonus of $12.0 million, and equity awards of $48.2 million.",
                "page": 65
            }
        }
    },
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "filing_date": "2024-07-30",
        "sections": {
            "business_overview": {
                "title": "Business Overview",
                "content": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide. The Company's segments include Productivity and Business Processes, Intelligent Cloud, and More Personal Computing. The Company's net income for fiscal 2024 was $72.4 billion, an increase of 20% compared to fiscal 2023. Revenue was $211.9 billion, an increase of 15% compared to fiscal 2023.",
                "page": 1
            },
            "risk_factors": {
                "title": "Risk Factors",
                "content": "The Company faces various risks including: intense competition in the software and cloud services industries; the need to continue to develop and market products and services that meet customer needs; the Company's ability to maintain and enhance its brand and reputation; and the Company's ability to protect its intellectual property rights.",
                "page": 12
            },
            "management_discussion": {
                "title": "Management's Discussion and Analysis",
                "content": "Revenue increased 15% during fiscal 2024 compared to fiscal 2023. The increase was driven by growth in all three segments. Productivity and Business Processes revenue increased 13%, Intelligent Cloud revenue increased 21%, and More Personal Computing revenue increased 4%. The growth was primarily driven by increased demand for cloud services and productivity solutions.",
                "page": 22
            },
            "financial_statements": {
                "title": "Financial Statements",
                "content": "As of June 30, 2024, the Company had total assets of $470.6 billion, including cash and cash equivalents of $34.7 billion, short-term investments of $76.7 billion, and long-term investments of $89.9 billion. Total liabilities were $198.3 billion, including accounts payable of $23.1 billion and long-term debt of $59.7 billion.",
                "page": 40
            }
        }
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "filing_date": "2024-02-02",
        "sections": {
            "business_overview": {
                "title": "Business Overview",
                "content": "Alphabet Inc. is a holding company that conducts business through its subsidiaries, including Google LLC. The Company generates revenue primarily by delivering online advertising and by selling apps and in-app purchases, digital content, cloud services, and hardware. The Company's net income for fiscal 2023 was $73.8 billion, an increase of 23% compared to fiscal 2022. Revenue was $307.4 billion, an increase of 9% compared to fiscal 2022.",
                "page": 1
            },
            "risk_factors": {
                "title": "Risk Factors",
                "content": "The Company faces risks including: intense competition in the online advertising and technology industries; the Company's ability to maintain and enhance its brand and reputation; the Company's ability to protect its intellectual property rights; and the Company's ability to attract and retain talented employees.",
                "page": 18
            },
            "management_discussion": {
                "title": "Management's Discussion and Analysis",
                "content": "Revenue increased 9% during fiscal 2023 compared to fiscal 2022. The increase was driven by growth in Google Services revenue, which increased 8%, and Google Cloud revenue, which increased 26%. The growth in Google Services was primarily driven by increased advertising revenue, while the growth in Google Cloud was driven by increased demand for cloud infrastructure and platform services.",
                "page": 28
            },
            "financial_statements": {
                "title": "Financial Statements",
                "content": "As of December 31, 2023, the Company had total assets of $402.4 billion, including cash and cash equivalents of $24.0 billion, marketable securities of $108.9 billion, and long-term investments of $12.8 billion. Total liabilities were $119.7 billion, including accounts payable of $8.2 billion and long-term debt of $12.7 billion.",
                "page": 50
            }
        }
    }
}

# Mock EOD stock price data
mock_stock_prices = {
    "AAPL": {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "current_price": 175.43,
        "previous_close": 173.50,
        "change": 1.93,
        "change_percent": 1.11,
        "volume": 45678900,
        "market_cap": 2750000000000,
        "pe_ratio": 28.5,
        "dividend_yield": 0.51,
        "last_updated": "2024-12-19 16:00:00"
    },
    "MSFT": {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "current_price": 374.58,
        "previous_close": 372.17,
        "change": 2.41,
        "change_percent": 0.65,
        "volume": 23456700,
        "market_cap": 2785000000000,
        "pe_ratio": 35.2,
        "dividend_yield": 0.75,
        "last_updated": "2024-12-19 16:00:00"
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "company_name": "Alphabet Inc.",
        "current_price": 142.56,
        "previous_close": 141.80,
        "change": 0.76,
        "change_percent": 0.54,
        "volume": 34567800,
        "market_cap": 1798000000000,
        "pe_ratio": 24.3,
        "dividend_yield": 0.00,
        "last_updated": "2024-12-19 16:00:00"
    },
    "TSLA": {
        "symbol": "TSLA",
        "company_name": "Tesla, Inc.",
        "current_price": 248.42,
        "previous_close": 252.08,
        "change": -3.66,
        "change_percent": -1.45,
        "volume": 67890100,
        "market_cap": 789000000000,
        "pe_ratio": 78.9,
        "dividend_yield": 0.00,
        "last_updated": "2024-12-19 16:00:00"
    },
    "AMZN": {
        "symbol": "AMZN",
        "company_name": "Amazon.com, Inc.",
        "current_price": 151.94,
        "previous_close": 150.18,
        "change": 1.76,
        "change_percent": 1.17,
        "volume": 56789000,
        "market_cap": 1578000000000,
        "pe_ratio": 62.1,
        "dividend_yield": 0.00,
        "last_updated": "2024-12-19 16:00:00"
    }
}

class MCPManifest(BaseModel):
    name: str
    version: str
    description: str
    tools: List[Dict[str, Any]]

class MCP10KRequest(BaseModel):
    ticker: str
    section: str

class MCP10KResponse(BaseModel):
    ticker: str
    company_name: str
    filing_date: str
    section: str
    title: str
    content: str
    page: int

class MCPStockPriceRequest(BaseModel):
    ticker: str

class MCPStockPriceResponse(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    market_cap: int
    pe_ratio: float
    dividend_yield: float
    last_updated: str

@app.get("/manifest", response_model=MCPManifest)
async def get_manifest():
    """Get the MCP server manifest with available tools"""
    
    # Add a small delay to simulate network latency
    await asyncio.sleep(0.5)
    
    return MCPManifest(
        name="Mock MCP Server",
        version="1.0.0",
        description="A mock MCP server providing 10-K financial report sections and EOD stock prices",
        tools=[
            {
                "name": "10k-financial-reports",
                "description": "Retrieve specific sections from 10-K financial reports",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
                        },
                        "section": {
                            "type": "string",
                            "description": "Section to retrieve (business_overview, risk_factors, management_discussion, financial_statements, executive_compensation)"
                        }
                    },
                    "required": ["ticker", "section"]
                }
            },
            {
                "name": "eod-stock-prices",
                "description": "Get end-of-day stock price and financial data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol (e.g., AAPL, MSFT, GOOGL, TSLA, AMZN)"
                        }
                    },
                    "required": ["ticker"]
                }
            }
        ]
    )

@app.post("/10k-report", response_model=MCP10KResponse)
async def get_10k_section(request: MCP10KRequest):
    """Retrieve a specific section from a 10-K financial report"""
    
    # Add a delay to simulate processing time (1-3 seconds)
    delay = 1 + (hash(request.ticker + request.section) % 3)
    await asyncio.sleep(delay)
    
    ticker = request.ticker.upper()
    section = request.section.lower()
    
    # Check if ticker exists
    if ticker not in mock_10k_data:
        raise HTTPException(
            status_code=404, 
            detail=f"10-K data not available for ticker {ticker}. Available tickers: {list(mock_10k_data.keys())}"
        )
    
    # Check if section exists
    if section not in mock_10k_data[ticker]["sections"]:
        available_sections = list(mock_10k_data[ticker]["sections"].keys())
        raise HTTPException(
            status_code=404,
            detail=f"Section '{section}' not found for {ticker}. Available sections: {available_sections}"
        )
    
    # Get the section data
    section_data = mock_10k_data[ticker]["sections"][section]
    
    return MCP10KResponse(
        ticker=ticker,
        company_name=mock_10k_data[ticker]["company_name"],
        filing_date=mock_10k_data[ticker]["filing_date"],
        section=section,
        title=section_data["title"],
        content=section_data["content"],
        page=section_data["page"]
    )

@app.post("/stock-price", response_model=MCPStockPriceResponse)
async def get_stock_price(request: MCPStockPriceRequest):
    """Get end-of-day stock price and financial data"""
    
    # Add a delay to simulate processing time (1-2 seconds)
    delay = 1 + (hash(request.ticker) % 2)
    await asyncio.sleep(delay)
    
    ticker = request.ticker.upper()
    
    # Check if ticker exists
    if ticker not in mock_stock_prices:
        raise HTTPException(
            status_code=404,
            detail=f"Stock price data not available for ticker {ticker}. Available tickers: {list(mock_stock_prices.keys())}"
        )
    
    # Get the stock price data
    price_data = mock_stock_prices[ticker]
    
    return MCPStockPriceResponse(**price_data)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "message": "Mock MCP Server is running",
        "available_10k_tickers": list(mock_10k_data.keys()),
        "available_stock_tickers": list(mock_stock_prices.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 