"""
SEC EDGAR Client

This module handles communication with the SEC's EDGAR database
to search for and download 13F filings.
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, quote
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SECEdgarClient:
    """Client for interacting with SEC EDGAR database."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the SEC EDGAR client."""
        self.base_url = config['base_url']
        self.user_agent = config['user_agent']
        self.rate_limit_delay = config['rate_limit_delay']
        
        # Session for maintaining cookies and headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xml,application/xhtml+xml,text/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # SEC EDGAR specific URLs
        self.search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        self.company_url = "https://www.sec.gov/cgi-bin/browse-edgar?company"
        
    def search_filings(self, search_term: str, filing_types: List[str], 
                      days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Search for filings by company name or manager.
        
        Args:
            search_term: Company name or manager to search for
            filing_types: List of filing types to search for
            days_back: Number of days back to search
            
        Returns:
            List of filing information dictionaries
        """
        try:
            logger.info(f"Searching for filings with term: {search_term}")
            
            filings = []
            
            for filing_type in filing_types:
                # Search for each filing type
                results = self._search_filing_type(search_term, filing_type, days_back)
                filings.extend(results)
                
                # Respect rate limiting
                time.sleep(self.rate_limit_delay)
            
            logger.info(f"Found {len(filings)} filings for {search_term}")
            return filings
            
        except Exception as e:
            logger.error(f"Error searching filings: {e}")
            return []
    
    def _search_filing_type(self, search_term: str, filing_type: str, 
                           days_back: int) -> List[Dict[str, Any]]:
        """Search for a specific filing type."""
        try:
            # Build search parameters
            params = {
                'action': 'getcompany',
                'company': search_term,
                'type': filing_type,
                'dateb': datetime.now().strftime('%Y%m%d'),
                'datea': (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d'),
                'owner': 'exclude',
                'output': 'xml',
                'count': '100'
            }
            
            # Make the request
            response = self.session.get(self.search_url, params=params)
            response.raise_for_status()
            
            # Parse the XML response
            filings = self._parse_search_results(response.text, filing_type)
            
            return filings
            
        except Exception as e:
            logger.error(f"Error searching filing type {filing_type}: {e}")
            return []
    
    def _parse_search_results(self, xml_content: str, filing_type: str) -> List[Dict[str, Any]]:
        """Parse the XML search results from SEC EDGAR."""
        try:
            filings = []
            soup = BeautifulSoup(xml_content, 'xml')
            
            # Find all company entries
            companies = soup.find_all('companyInfo')
            
            for company in companies:
                company_name = company.find('companyName')
                if company_name:
                    company_name = company_name.get_text(strip=True)
                    
                    # Get CIK number
                    cik_elem = company.find('cik')
                    cik = cik_elem.get_text(strip=True) if cik_elem else None
                    
                    # Find filings for this company
                    company_filings = company.find_all('filingHREF')
                    
                    for filing in company_filings:
                        filing_url = filing.get_text(strip=True)
                        
                        # Extract accession number from URL
                        accession_match = re.search(r'data/(\d+)/', filing_url)
                        if accession_match:
                            accession_number = accession_match.group(1)
                            
                            # Get filing date
                            filing_date = self._extract_filing_date(filing_url)
                            
                            filing_info = {
                                'company_name': company_name,
                                'cik': cik,
                                'filing_type': filing_type,
                                'filing_url': filing_url,
                                'accession_number': accession_number,
                                'filing_date': filing_date
                            }
                            
                            filings.append(filing_info)
            
            return filings
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return []
    
    def _extract_filing_date(self, filing_url: str) -> Optional[str]:
        """Extract filing date from filing URL."""
        try:
            # Extract date from URL path
            date_match = re.search(r'(\d{4})(\d{2})(\d{2})', filing_url)
            if date_match:
                year, month, day = date_match.groups()
                return f"{year}-{month}-{day}"
            return None
        except Exception as e:
            logger.error(f"Error extracting filing date: {e}")
            return None
    
    def download_filing(self, accession_number: str) -> Optional[str]:
        """
        Download the content of a specific filing.
        
        Args:
            accession_number: The SEC accession number for the filing
            
        Returns:
            Filing content as string, or None if failed
        """
        try:
            logger.info(f"Downloading filing: {accession_number}")
            
            # Construct the filing URL
            filing_url = f"{self.base_url}/{accession_number}/{accession_number}.txt"
            
            # Download the filing
            response = self.session.get(filing_url)
            response.raise_for_status()
            
            # Respect rate limiting
            time.sleep(self.rate_limit_delay)
            
            logger.info(f"Successfully downloaded filing {accession_number}")
            return response.text
            
        except Exception as e:
            logger.error(f"Error downloading filing {accession_number}: {e}")
            return None
    
    def get_company_info(self, cik: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed company information by CIK.
        
        Args:
            cik: Company CIK number
            
        Returns:
            Company information dictionary, or None if failed
        """
        try:
            logger.info(f"Getting company info for CIK: {cik}")
            
            # Build company search URL
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'output': 'xml'
            }
            
            response = self.session.get(self.company_url, params=params)
            response.raise_for_status()
            
            # Parse company information
            company_info = self._parse_company_info(response.text)
            
            # Respect rate limiting
            time.sleep(self.rate_limit_delay)
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error getting company info for CIK {cik}: {e}")
            return None
    
    def _parse_company_info(self, xml_content: str) -> Dict[str, Any]:
        """Parse company information from XML response."""
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            
            company_info = {}
            
            # Extract company name
            company_name = soup.find('companyName')
            if company_name:
                company_info['name'] = company_name.get_text(strip=True)
            
            # Extract CIK
            cik = soup.find('cik')
            if cik:
                company_info['cik'] = cik.get_text(strip=True)
            
            # Extract SIC
            sic = soup.find('assignedSic')
            if sic:
                company_info['sic'] = sic.get_text(strip=True)
            
            # Extract business description
            business = soup.find('businessDescription')
            if business:
                company_info['business_description'] = business.get_text(strip=True)
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error parsing company info: {e}")
            return {}
    
    def close(self):
        """Close the session."""
        self.session.close()
