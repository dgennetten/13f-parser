#!/usr/bin/env python3
"""
13F Filing Parser - Main Script

This script automatically monitors and parses 13F filings from the SEC,
with a focus on tracking specific funds and managers.
"""

import os
import sys
import json
import logging
import requests
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import time
import re

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sec_edgar_client import SECEdgarClient
from filing_parser import FilingParser
from data_manager import DataManager
from notification_manager import NotificationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('13f_parser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ThirteenFParser:
    """Main class for parsing 13F filings."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the parser with configuration."""
        self.config = self._load_config(config_path)
        self.sec_client = SECEdgarClient(self.config['sec_edgar'])
        self.parser = FilingParser(self.config['parsing'])
        self.data_manager = DataManager(self.config['data'])
        self.notification_manager = NotificationManager(self.config['notifications'])
        
        # Ensure data directory exists
        Path(self.config['data']['output_dir']).mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def run(self):
        """Main execution method."""
        logger.info("Starting 13F filing parser...")
        
        try:
            # Get target fund information
            target_funds = self.config['target_funds']
            
            for fund in target_funds:
                logger.info(f"Processing fund: {fund['name']}")
                
                # Search for recent filings
                filings = self._search_fund_filings(fund)
                
                if filings:
                    logger.info(f"Found {len(filings)} filings for {fund['name']}")
                    
                    for filing in filings:
                        self._process_filing(filing, fund)
                else:
                    logger.info(f"No new filings found for {fund['name']}")
                    
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            self.notification_manager.send_error_notification(str(e))
            raise
    
    def _search_fund_filings(self, fund: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for filings from a specific fund."""
        try:
            # Search by fund name and manager
            search_terms = [fund['name']] + fund.get('aliases', [])
            
            filings = []
            for term in search_terms:
                results = self.sec_client.search_filings(
                    search_term=term,
                    filing_types=self.config['filing_types'],
                    days_back=30  # Check last 30 days
                )
                filings.extend(results)
            
            # Remove duplicates and sort by date
            unique_filings = {f['accession_number']: f for f in filings}.values()
            sorted_filings = sorted(unique_filings, key=lambda x: x['filing_date'], reverse=True)
            
            return sorted_filings
            
        except Exception as e:
            logger.error(f"Error searching filings for {fund['name']}: {e}")
            return []
    
    def _process_filing(self, filing: Dict[str, Any], fund: Dict[str, Any]):
        """Process a single filing."""
        try:
            logger.info(f"Processing filing: {filing['accession_number']}")
            
            # Check if we've already processed this filing
            if self.data_manager.filing_already_processed(filing['accession_number']):
                logger.info(f"Filing {filing['accession_number']} already processed, skipping")
                return
            
            # Download and parse the filing
            filing_content = self.sec_client.download_filing(filing['accession_number'])
            
            if filing_content:
                # Parse the filing content
                parsed_data = self.parser.parse_13f_filing(filing_content)
                
                if parsed_data:
                    # Add metadata
                    parsed_data.update({
                        'fund_name': fund['name'],
                        'manager': fund['manager'],
                        'filing_date': filing['filing_date'],
                        'accession_number': filing['accession_number'],
                        'processed_at': datetime.now().isoformat()
                    })
                    
                    # Save the parsed data
                    self.data_manager.save_filing_data(parsed_data, filing['accession_number'])
                    
                    # Send notification
                    self.notification_manager.send_filing_notification(fund['name'], filing, parsed_data)
                    
                    logger.info(f"Successfully processed filing {filing['accession_number']}")
                else:
                    logger.warning(f"Failed to parse filing {filing['accession_number']}")
            else:
                logger.warning(f"Failed to download filing {filing['accession_number']}")
                
        except Exception as e:
            logger.error(f"Error processing filing {filing['accession_number']}: {e}")
    
    def get_fund_summary(self, fund_name: str) -> Dict[str, Any]:
        """Get a summary of all filings for a specific fund."""
        try:
            return self.data_manager.get_fund_summary(fund_name)
        except Exception as e:
            logger.error(f"Error getting fund summary: {e}")
            return {}

def main():
    """Main entry point."""
    try:
        parser = ThirteenFParser()
        parser.run()
        logger.info("13F parser completed successfully")
    except Exception as e:
        logger.error(f"13F parser failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
