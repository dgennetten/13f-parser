"""
Filing Parser

This module parses 13F filing documents downloaded from SEC EDGAR
and extracts structured data about portfolio holdings.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class FilingParser:
    """Parser for 13F filing documents."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the filing parser."""
        self.min_position_value = config.get('min_position_value', 10000)
        self.include_zero_positions = config.get('include_zero_positions', False)
        self.track_position_changes = config.get('track_position_changes', True)
        self.save_raw_xml = config.get('save_raw_xml', False)
    
    def parse_13f_filing(self, filing_content: str) -> Optional[Dict[str, Any]]:
        """
        Parse a 13F filing document and extract portfolio data.
        
        Args:
            filing_content: Raw filing content as string
            
        Returns:
            Parsed filing data dictionary, or None if parsing failed
        """
        try:
            logger.info("Starting to parse 13F filing")
            
            # Extract the XML portion of the filing
            xml_content = self._extract_xml_content(filing_content)
            
            if not xml_content:
                logger.error("No XML content found in filing")
                return None
            
            # Parse the XML content
            parsed_data = self._parse_xml_content(xml_content)
            
            if parsed_data:
                logger.info("Successfully parsed 13F filing")
                return parsed_data
            else:
                logger.error("Failed to parse XML content")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing 13F filing: {e}")
            return None
    
    def _extract_xml_content(self, filing_content: str) -> Optional[str]:
        """Extract XML content from the filing document."""
        try:
            # Look for XML content markers
            xml_start_markers = [
                '<?xml',
                '<XML>',
                '<informationTable>',
                '<ns1:informationTable>'
            ]
            
            xml_end_markers = [
                '</XML>',
                '</informationTable>',
                '</ns1:informationTable>'
            ]
            
            # Find XML start
            xml_start = -1
            for marker in xml_start_markers:
                pos = filing_content.find(marker)
                if pos != -1:
                    xml_start = pos
                    break
            
            if xml_start == -1:
                logger.warning("No XML start marker found")
                return None
            
            # Find XML end
            xml_end = -1
            for marker in xml_end_markers:
                pos = filing_content.find(marker, xml_start)
                if pos != -1:
                    xml_end = pos + len(marker)
                    break
            
            if xml_end == -1:
                logger.warning("No XML end marker found, using end of content")
                xml_end = len(filing_content)
            
            xml_content = filing_content[xml_start:xml_end]
            logger.info(f"Extracted XML content: {len(xml_content)} characters")
            
            return xml_content
            
        except Exception as e:
            logger.error(f"Error extracting XML content: {e}")
            return None
    
    def _parse_xml_content(self, xml_content: str) -> Optional[Dict[str, Any]]:
        """Parse the XML content and extract portfolio data."""
        try:
            # Try to parse as XML first
            try:
                root = ET.fromstring(xml_content)
                return self._parse_xml_tree(root)
            except ET.ParseError:
                logger.info("XML parsing failed, trying BeautifulSoup")
                return self._parse_with_beautifulsoup(xml_content)
                
        except Exception as e:
            logger.error(f"Error parsing XML content: {e}")
            return None
    
    def _parse_xml_tree(self, root: ET.Element) -> Dict[str, Any]:
        """Parse XML using ElementTree."""
        try:
            parsed_data = {
                'total_value': 0,
                'holdings': [],
                'filing_period': None,
                'manager_info': {}
            }
            
            # Extract filing period
            period_elem = root.find('.//reportCalendarOrQuarter')
            if period_elem is not None:
                parsed_data['filing_period'] = period_elem.text
            
            # Extract manager information
            manager_elem = root.find('.//nameOfIssuer')
            if manager_elem is not None:
                parsed_data['manager_info']['name'] = manager_elem.text
            
            # Extract holdings
            holdings = root.findall('.//infoTable')
            if not holdings:
                holdings = root.findall('.//ns1:infoTable')
            
            total_value = 0
            for holding in holdings:
                holding_data = self._extract_holding_data(holding)
                if holding_data:
                    parsed_data['holdings'].append(holding_data)
                    total_value += holding_data.get('value', 0)
            
            parsed_data['total_value'] = total_value
            logger.info(f"Parsed {len(parsed_data['holdings'])} holdings")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing XML tree: {e}")
            return None
    
    def _parse_with_beautifulsoup(self, xml_content: str) -> Optional[Dict[str, Any]]:
        """Parse XML using BeautifulSoup as fallback."""
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            
            parsed_data = {
                'total_value': 0,
                'holdings': [],
                'filing_period': None,
                'manager_info': {}
            }
            
            # Extract filing period
            period_elem = soup.find('reportCalendarOrQuarter')
            if period_elem:
                parsed_data['filing_period'] = period_elem.get_text(strip=True)
            
            # Extract manager information
            manager_elem = soup.find('nameOfIssuer')
            if manager_elem:
                parsed_data['manager_info']['name'] = manager_elem.get_text(strip=True)
            
            # Extract holdings
            holdings = soup.find_all('infoTable')
            if not holdings:
                holdings = soup.find_all('ns1:infoTable')
            
            total_value = 0
            for holding in holdings:
                holding_data = self._extract_holding_data_bs(holding)
                if holding_data:
                    parsed_data['holdings'].append(holding_data)
                    total_value += holding_data.get('value', 0)
            
            parsed_data['total_value'] = total_value
            logger.info(f"Parsed {len(parsed_data['holdings'])} holdings using BeautifulSoup")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing with BeautifulSoup: {e}")
            return None
    
    def _extract_holding_data(self, holding_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract holding data from XML element."""
        try:
            holding_data = {}
            
            # Extract security name
            name_elem = holding_elem.find('nameOfIssuer')
            if name_elem is not None:
                holding_data['security_name'] = name_elem.text.strip()
            
            # Extract CUSIP
            cusip_elem = holding_elem.find('titleOfClass')
            if cusip_elem is not None:
                holding_data['cusip'] = cusip_elem.text.strip()
            
            # Extract shares
            shares_elem = holding_elem.find('shrsOrPrnAmt/sshPrnamt')
            if shares_elem is not None:
                try:
                    shares = int(shares_elem.text.replace(',', ''))
                    holding_data['shares'] = shares
                except (ValueError, AttributeError):
                    holding_data['shares'] = 0
            
            # Extract value
            value_elem = holding_elem.find('putCall')
            if value_elem is not None:
                try:
                    value = int(value_elem.text.replace(',', ''))
                    holding_data['value'] = value
                except (ValueError, AttributeError):
                    holding_data['value'] = 0
            
            # Extract put/call information
            put_call_elem = holding_elem.find('putCall')
            if put_call_elem is not None:
                holding_data['put_call'] = put_call_elem.text.strip()
            
            # Filter by minimum position value
            if holding_data.get('value', 0) < self.min_position_value:
                return None
            
            return holding_data
            
        except Exception as e:
            logger.error(f"Error extracting holding data: {e}")
            return None
    
    def _extract_holding_data_bs(self, holding_elem) -> Optional[Dict[str, Any]]:
        """Extract holding data from BeautifulSoup element."""
        try:
            holding_data = {}
            
            # Extract security name
            name_elem = holding_elem.find('nameOfIssuer')
            if name_elem:
                holding_data['security_name'] = name_elem.get_text(strip=True)
            
            # Extract CUSIP
            cusip_elem = holding_elem.find('titleOfClass')
            if cusip_elem:
                holding_data['cusip'] = cusip_elem.get_text(strip=True)
            
            # Extract shares
            shares_elem = holding_elem.find('shrsOrPrnAmt')
            if shares_elem:
                shares_text = shares_elem.get_text(strip=True)
                try:
                    shares = int(shares_text.replace(',', ''))
                    holding_data['shares'] = shares
                except (ValueError, AttributeError):
                    holding_data['shares'] = 0
            
            # Extract value
            value_elem = holding_elem.find('value')
            if value_elem:
                value_text = value_elem.get_text(strip=True)
                try:
                    value = int(value_text.replace(',', ''))
                    holding_data['value'] = value
                except (ValueError, AttributeError):
                    holding_data['value'] = 0
            
            # Extract put/call information
            put_call_elem = holding_elem.find('putCall')
            if put_call_elem:
                holding_data['put_call'] = put_call_elem.get_text(strip=True)
            
            # Filter by minimum position value
            if holding_data.get('value', 0) < self.min_position_value:
                return None
            
            return holding_data
            
        except Exception as e:
            logger.error(f"Error extracting holding data with BeautifulSoup: {e}")
            return None
    
    def calculate_position_changes(self, current_holdings: List[Dict], 
                                 previous_holdings: List[Dict]) -> List[Dict]:
        """Calculate position changes between two filing periods."""
        try:
            changes = []
            
            # Create lookup dictionaries
            current_lookup = {h['cusip']: h for h in current_holdings if 'cusip' in h}
            previous_lookup = {h['cusip']: h for h in previous_holdings if 'cusip' in h}
            
            # Find new positions
            for cusip, holding in current_lookup.items():
                if cusip not in previous_lookup:
                    holding['change'] = 'NEW'
                    changes.append(holding)
                else:
                    # Calculate change
                    prev_holding = previous_lookup[cusip]
                    current_shares = holding.get('shares', 0)
                    prev_shares = prev_holding.get('shares', 0)
                    
                    if current_shares > prev_shares:
                        holding['change'] = 'INCREASED'
                        holding['shares_change'] = current_shares - prev_shares
                        changes.append(holding)
                    elif current_shares < prev_shares:
                        holding['change'] = 'DECREASED'
                        holding['shares_change'] = current_shares - prev_shares
                        changes.append(holding)
                    # No change in shares - don't include
            
            # Find exited positions
            for cusip, holding in previous_lookup.items():
                if cusip not in current_lookup:
                    holding['change'] = 'EXITED'
                    holding['shares'] = 0
                    changes.append(holding)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error calculating position changes: {e}")
            return []
