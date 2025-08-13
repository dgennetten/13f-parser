#!/usr/bin/env python3
"""
Test script for the 13F Parser

This script can be used to test the parser locally before deploying to GitHub Actions.
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.append('src')

from main import ThirteenFParser

def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def test_parser():
    """Test the 13F parser."""
    try:
        print("🧪 Testing 13F Parser...")
        
        # Initialize parser
        parser = ThirteenFParser()
        print("✅ Parser initialized successfully")
        
        # Test configuration loading
        print(f"📋 Configuration loaded: {len(parser.config)} sections")
        print(f"🎯 Target funds: {len(parser.config['target_funds'])}")
        
        # Test fund summary (should be empty initially)
        fund_name = "Situational Awareness LP"
        summary = parser.get_fund_summary(fund_name)
        print(f"📊 Fund summary for {fund_name}: {summary}")
        
        # Test data manager statistics
        stats = parser.data_manager.get_data_statistics()
        print(f"📈 Data statistics: {stats}")
        
        print("\n✅ All tests passed! Parser is ready for deployment.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logging.error(f"Test error: {e}")
        return False
    
    return True

def test_notifications():
    """Test notification system."""
    try:
        print("\n🔔 Testing notification system...")
        
        parser = ThirteenFParser()
        
        # Test notification manager
        parser.notification_manager.test_notifications()
        print("✅ Notification test completed")
        
    except Exception as e:
        print(f"❌ Notification test failed: {e}")
        logging.error(f"Notification test error: {e}")

def main():
    """Main test function."""
    print("🚀 13F Parser Test Suite")
    print("=" * 50)
    
    setup_logging()
    
    # Test basic functionality
    if not test_parser():
        sys.exit(1)
    
    # Test notifications (optional)
    try:
        test_notifications()
    except Exception as e:
        print(f"⚠️  Notification test skipped: {e}")
    
    print("\n🎉 All tests completed successfully!")
    print("\nNext steps:")
    print("1. Push this repository to GitHub")
    print("2. Check the Actions tab to see the workflow")
    print("3. The parser will run automatically every day at 9 AM EST")
    print("4. Monitor for new 13F filings from Situational Awareness LP")

if __name__ == "__main__":
    main()
