"""
Data Manager

This module handles saving, loading, and managing parsed 13F filing data
with backup and versioning capabilities.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data storage and retrieval for parsed 13F filings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the data manager."""
        self.output_dir = config['output_dir']
        self.file_format = config['file_format']
        self.backup_enabled = config.get('backup_enabled', True)
        self.max_backups = config.get('max_backups', 10)
        
        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.filings_dir = Path(self.output_dir) / "filings"
        self.summaries_dir = Path(self.output_dir) / "summaries"
        self.backups_dir = Path(self.output_dir) / "backups"
        
        for directory in [self.filings_dir, self.summaries_dir, self.backups_dir]:
            directory.mkdir(exist_ok=True)
        
        # Track processed filings
        self.processed_filings_file = Path(self.output_dir) / "processed_filings.json"
        self.processed_filings = self._load_processed_filings()
    
    def _load_processed_filings(self) -> set:
        """Load the set of already processed filing accession numbers."""
        try:
            if self.processed_filings_file.exists():
                with open(self.processed_filings_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_filings', []))
            return set()
        except Exception as e:
            logger.error(f"Error loading processed filings: {e}")
            return set()
    
    def _save_processed_filings(self):
        """Save the set of processed filing accession numbers."""
        try:
            data = {
                'processed_filings': list(self.processed_filings),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processed_filings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed filings: {e}")
    
    def filing_already_processed(self, accession_number: str) -> bool:
        """Check if a filing has already been processed."""
        return accession_number in self.processed_filings
    
    def save_filing_data(self, filing_data: Dict[str, Any], accession_number: str):
        """Save parsed filing data to disk."""
        try:
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{accession_number}_{timestamp}.{self.file_format}"
            filepath = self.filings_dir / filename
            
            # Save the data
            if self.file_format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(filing_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported file format: {self.file_format}")
            
            # Mark as processed
            self.processed_filings.add(accession_number)
            self._save_processed_filings()
            
            # Create backup if enabled
            if self.backup_enabled:
                self._create_backup(filepath, accession_number)
            
            # Update fund summary
            self._update_fund_summary(filing_data)
            
            logger.info(f"Saved filing data to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving filing data: {e}")
            raise
    
    def _create_backup(self, filepath: Path, accession_number: str):
        """Create a backup of the filing data."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{accession_number}_{timestamp}_backup.{self.file_format}"
            backup_path = self.backups_dir / backup_filename
            
            # Copy the file
            shutil.copy2(filepath, backup_path)
            
            # Clean up old backups
            self._cleanup_old_backups(accession_number)
            
            logger.info(f"Created backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def _cleanup_old_backups(self, accession_number: str):
        """Remove old backup files beyond the maximum limit."""
        try:
            # Find all backup files for this accession number
            backup_files = list(self.backups_dir.glob(f"{accession_number}_*_backup.{self.file_format}"))
            
            if len(backup_files) > self.max_backups:
                # Sort by modification time (oldest first)
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                
                # Remove oldest files
                files_to_remove = backup_files[:-self.max_backups]
                for file in files_to_remove:
                    file.unlink()
                    logger.info(f"Removed old backup: {file}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def _update_fund_summary(self, filing_data: Dict[str, Any]):
        """Update the fund summary with new filing data."""
        try:
            fund_name = filing_data.get('fund_name', 'Unknown')
            summary_file = self.summaries_dir / f"{fund_name.replace(' ', '_')}_summary.json"
            
            # Load existing summary or create new one
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
            else:
                summary = {
                    'fund_name': fund_name,
                    'manager': filing_data.get('manager', 'Unknown'),
                    'filings': [],
                    'total_holdings': 0,
                    'last_updated': None
                }
            
            # Add new filing
            filing_summary = {
                'filing_date': filing_data.get('filing_date'),
                'accession_number': filing_data.get('accession_number'),
                'total_value': filing_data.get('total_value', 0),
                'holdings_count': len(filing_data.get('holdings', [])),
                'processed_at': filing_data.get('processed_at')
            }
            
            summary['filings'].append(filing_summary)
            summary['total_holdings'] = len(filing_data.get('holdings', []))
            summary['last_updated'] = datetime.now().isoformat()
            
            # Save updated summary
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Updated fund summary for {fund_name}")
            
        except Exception as e:
            logger.error(f"Error updating fund summary: {e}")
    
    def get_fund_summary(self, fund_name: str) -> Dict[str, Any]:
        """Get a summary of all filings for a specific fund."""
        try:
            summary_file = self.summaries_dir / f"{fund_name.replace(' ', '_')}_summary.json"
            
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'fund_name': fund_name,
                    'filings': [],
                    'total_holdings': 0,
                    'last_updated': None
                }
                
        except Exception as e:
            logger.error(f"Error getting fund summary: {e}")
            return {}
    
    def get_all_fund_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries for all funds."""
        try:
            summaries = []
            for summary_file in self.summaries_dir.glob("*_summary.json"):
                with open(summary_file, 'r') as f:
                    summaries.append(json.load(f))
            return summaries
        except Exception as e:
            logger.error(f"Error getting all fund summaries: {e}")
            return []
    
    def get_filing_data(self, accession_number: str) -> Optional[Dict[str, Any]]:
        """Get the parsed data for a specific filing."""
        try:
            # Find the filing file
            filing_files = list(self.filings_dir.glob(f"{accession_number}_*.{self.file_format}"))
            
            if filing_files:
                # Get the most recent one
                latest_file = max(filing_files, key=lambda x: x.stat().st_mtime)
                
                with open(latest_file, 'r') as f:
                    if self.file_format == 'json':
                        return json.load(f)
                    else:
                        raise ValueError(f"Unsupported file format: {self.file_format}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting filing data: {e}")
            return None
    
    def get_fund_holdings_history(self, fund_name: str) -> List[Dict[str, Any]]:
        """Get the holdings history for a specific fund."""
        try:
            summary = self.get_fund_summary(fund_name)
            holdings_history = []
            
            for filing in summary.get('filings', []):
                filing_data = self.get_filing_data(filing['accession_number'])
                if filing_data:
                    holdings_history.append(filing_data)
            
            # Sort by filing date
            holdings_history.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
            
            return holdings_history
            
        except Exception as e:
            logger.error(f"Error getting fund holdings history: {e}")
            return []
    
    def export_data(self, export_format: str = 'json', output_path: Optional[str] = None) -> str:
        """Export all data in the specified format."""
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"13f_data_export_{timestamp}.{export_format}"
            
            if export_format == 'json':
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'fund_summaries': self.get_all_fund_summaries(),
                    'processed_filings': list(self.processed_filings)
                }
                
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                logger.info(f"Data exported to {output_path}")
                return output_path
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old data files beyond the specified age."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # Clean up old filing files
            for file_path in self.filings_dir.glob(f"*.{self.file_format}"):
                if file_path.stat().st_mtime < cutoff_timestamp:
                    file_path.unlink()
                    logger.info(f"Removed old filing file: {file_path}")
            
            # Clean up old backup files
            for file_path in self.backups_dir.glob(f"*.{self.file_format}"):
                if file_path.stat().st_mtime < cutoff_timestamp:
                    file_path.unlink()
                    logger.info(f"Removed old backup file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about the stored data."""
        try:
            stats = {
                'total_filings': len(self.processed_filings),
                'total_funds': len(self.get_all_fund_summaries()),
                'data_directory_size': self._get_directory_size(self.output_dir),
                'last_updated': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            return {}
    
    def _get_directory_size(self, directory_path: str) -> int:
        """Calculate the total size of a directory in bytes."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")
            return 0
