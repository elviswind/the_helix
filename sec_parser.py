import os
import re
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

class SEC10KParser:
    """Parser for SEC 10-K filings"""
    
    def __init__(self, base_path="/mnt/d/Orca/Data/sec_forms"):
        self.base_path = base_path
        
    def get_available_companies(self) -> List[str]:
        """Get list of available companies"""
        if not os.path.exists(self.base_path):
            return []
        
        companies = []
        for item in os.listdir(self.base_path):
            item_path = os.path.join(self.base_path, item)
            if os.path.isdir(item_path):
                # Check if it contains 10-K files
                files = os.listdir(item_path)
                if any(f.startswith("10-K_") and f.endswith(".html") for f in files):
                    companies.append(item)
        
        return companies
    
    def get_available_years(self, company: str) -> List[int]:
        """Get available years for a company"""
        company_path = os.path.join(self.base_path, company)
        if not os.path.exists(company_path):
            return []
        
        years = []
        for file in os.listdir(company_path):
            if file.startswith("10-K_") and file.endswith(".html"):
                try:
                    year = int(file.replace("10-K_", "").replace(".html", ""))
                    years.append(year)
                except ValueError:
                    continue
        
        return sorted(years)
    
    def get_filing_path(self, company: str, year: int) -> Optional[str]:
        """Get the file path for a specific filing"""
        company_path = os.path.join(self.base_path, company)
        file_name = f"10-K_{year}.html"
        file_path = os.path.join(company_path, file_name)
        
        if os.path.exists(file_path):
            return file_path
        return None
    
    def parse_filing(self, company: str, year: int) -> Dict[str, Any]:
        """Parse a complete 10-K filing"""
        file_path = self.get_filing_path(company, year)
        if not file_path:
            return {"error": f"Filing not found for {company} {year}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract basic filing info
            filing_info = self._extract_filing_info(soup)
            
            # Extract sections
            sections = self._extract_sections(soup)
            
            # Extract financial data
            financial_data = self._extract_financial_data(soup)
            
            return {
                "company": company,
                "year": year,
                "filing_info": filing_info,
                "sections": sections,
                "financial_data": financial_data,
                "raw_content": content[:10000]  # First 10k chars for reference
            }
            
        except Exception as e:
            return {"error": f"Failed to parse filing: {str(e)}"}
    
    def get_section_content(self, company: str, year: int, section: str) -> Dict[str, Any]:
        """Get content for a specific section"""
        file_path = self.get_filing_path(company, year)
        if not file_path:
            return {"error": f"Filing not found for {company} {year}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get the full text content
            full_text = soup.get_text()
            
            # Try to find the section using various patterns
            section_content = self._find_section_improved(full_text, section)
            
            if section_content:
                return {
                    "company": company,
                    "year": year,
                    "section": section,
                    "content": section_content,
                    "source": f"10-K Filing {year}",
                    "page": "N/A"
                }
            else:
                return {
                    "error": f"Section {section} not found in {company} {year} filing"
                }
                
        except Exception as e:
            return {"error": f"Failed to extract section: {str(e)}"}
    
    def _extract_filing_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract basic filing information"""
        info = {}
        
        # Try to find filing date
        date_patterns = [
            r"filing date[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})",
            r"filed[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})",
            r"([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})"
        ]
        
        text = soup.get_text().lower()
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                info["filing_date"] = match.group(1)
                break
        
        # Try to find company name
        title_tag = soup.find('title')
        if title_tag:
            info["company_name"] = title_tag.get_text().strip()
        
        return info
    
    def _extract_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all major sections"""
        sections = {}
        
        # Common section headers with variations
        section_patterns = {
            "1": [r"item\s*1[^a-zA-Z]*", r"business\s*overview", r"business\s*description"],
            "1A": [r"item\s*1a[^a-zA-Z]*", r"risk\s*factors?", r"risk\s*factor"],
            "2": [r"item\s*2[^a-zA-Z]*", r"properties"],
            "3": [r"item\s*3[^a-zA-Z]*", r"legal\s*proceedings"],
            "4": [r"item\s*4[^a-zA-Z]*", r"mine\s*safety"],
            "5": [r"item\s*5[^a-zA-Z]*", r"market", r"market\s*for\s*registrant"],
            "6": [r"item\s*6[^a-zA-Z]*", r"selected\s*financial\s*data"],
            "7": [r"item\s*7[^a-zA-Z]*", r"management", r"management's\s*discussion"],
            "7A": [r"item\s*7a[^a-zA-Z]*", r"quantitative\s*and\s*qualitative"],
            "8": [r"item\s*8[^a-zA-Z]*", r"financial\s*statements"],
            "9": [r"item\s*9[^a-zA-Z]*", r"changes\s*in\s*and\s*disagreements"],
            "9A": [r"item\s*9a[^a-zA-Z]*", r"controls\s*and\s*procedures"],
            "9B": [r"item\s*9b[^a-zA-Z]*", r"other\s*information"],
            "10": [r"item\s*10[^a-zA-Z]*", r"directors", r"executive\s*officers"],
            "11": [r"item\s*11[^a-zA-Z]*", r"executive\s*compensation"],
            "12": [r"item\s*12[^a-zA-Z]*", r"security\s*ownership"],
            "13": [r"item\s*13[^a-zA-Z]*", r"certain\s*relationships"],
            "14": [r"item\s*14[^a-zA-Z]*", r"principal\s*accountant"],
            "15": [r"item\s*15[^a-zA-Z]*", r"exhibits"]
        }
        
        text = soup.get_text()
        
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                # Look for section content
                section_match = re.search(pattern, text, re.IGNORECASE)
                if section_match:
                    # Try to extract content after the section header
                    start_pos = section_match.end()
                    # Look for next section or end of document
                    next_section = re.search(r"item\s*\d", text[start_pos:], re.IGNORECASE)
                    if next_section:
                        end_pos = start_pos + next_section.start()
                    else:
                        end_pos = len(text)
                    
                    content = text[start_pos:end_pos].strip()
                    if len(content) > 200:  # Only include substantial content
                        sections[section_name] = content[:5000]  # Limit to 5000 chars
                    break
        
        return sections
    
    def _extract_financial_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract financial data from tables"""
        financial_data = {}
        
        # Find tables that might contain financial data
        tables = soup.find_all('table')
        
        for table in tables:
            # Look for common financial terms
            table_text = table.get_text().lower()
            if any(term in table_text for term in ['revenue', 'income', 'assets', 'liabilities', 'cash']):
                # Extract table data
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text().strip()
                        value = cells[1].get_text().strip()
                        if key and value:
                            financial_data[key] = value
        
        return financial_data
    
    def _find_section_improved(self, text: str, section: str) -> Optional[str]:
        """Improved section finding with multiple patterns"""
        
        # Map section names to search patterns
        section_patterns = {
            "1": [
                r"item\s*1[^a-zA-Z]*([^I]*?)(?=item\s*[2-9]|item\s*1[^a-zA-Z]|$)",
                r"business\s*overview[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)",
                r"business\s*description[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)"
            ],
            "1A": [
                r"item\s*1a[^a-zA-Z]*([^I]*?)(?=item\s*[2-9]|item\s*1[^a-zA-Z]|$)",
                r"risk\s*factors?[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)",
                r"risk\s*factor[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)"
            ],
            "7": [
                r"item\s*7[^a-zA-Z]*([^I]*?)(?=item\s*[8-9]|item\s*7[^a-zA-Z]|$)",
                r"management's\s*discussion[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)",
                r"management\s*discussion[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)"
            ],
            "1B": [
                r"item\s*1b[^a-zA-Z]*([^I]*?)(?=item\s*[2-9]|item\s*1[^a-zA-Z]|$)",
                r"unresolved\s*staff\s*comments[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)"
            ]
        }
        
        patterns = section_patterns.get(section, [rf"{section}[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)"])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 100:
                    return content[:10000]  # Limit to 10k chars
        
        # If no match found, try a more general approach
        # Look for any mention of the section
        general_patterns = [
            rf"{section}[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)",
            rf"item\s*{section}[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)",
            rf"section\s*{section}[^a-zA-Z]*([^I]*?)(?=item\s*\d|$)"
        ]
        
        for pattern in general_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 100:
                    return content[:10000]
        
        return None

# Global parser instance
sec_parser = SEC10KParser()

def get_10k_section(company: str, year: int, section: str) -> Dict[str, Any]:
    """Get a specific section from a 10-K filing"""
    return sec_parser.get_section_content(company, year, section)

def get_10k_filing(company: str, year: int) -> Dict[str, Any]:
    """Get a complete 10-K filing"""
    return sec_parser.parse_filing(company, year)

def get_available_companies() -> List[str]:
    """Get list of available companies"""
    return sec_parser.get_available_companies()

def get_available_years(company: str) -> List[int]:
    """Get available years for a company"""
    return sec_parser.get_available_years(company) 