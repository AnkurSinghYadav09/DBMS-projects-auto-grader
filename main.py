#!/usr/bin/env python3
"""
Auto Evaluator - Main Entry Point
Automatically evaluates Google Docs linked in a Google Sheet
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.utils import setup_logging
from src.sheet_processor import SheetProcessor

def main():
    # Setup logging
    logger = setup_logging(Config.LOGS_DIR)
    logger.info("=" * 60)
    logger.info("Auto Evaluator Started")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize processor
        processor = SheetProcessor()
        
        # Process all documents
        logger.info(f"Processing spreadsheet: {Config.SPREADSHEET_ID}")
        processor.process_all_documents()
        
        logger.info("=" * 60)
        logger.info("Auto Evaluator Completed Successfully")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
