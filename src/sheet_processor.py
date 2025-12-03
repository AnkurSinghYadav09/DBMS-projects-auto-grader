import logging
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .google_api import GoogleAPIHandler
from .evaluator import DocumentEvaluator
from .config import Config

logger = logging.getLogger(__name__)

class SheetProcessor:
    def __init__(self):
        self.google_api = GoogleAPIHandler()
        self.evaluator = DocumentEvaluator()
        logger.info("Sheet processor initialized")
    
    def process_all_documents(self, start_row: int = 2):
        """Process all documents in the sheet"""
        try:
            # Read all rows with document links
            range_name = f"{Config.DOC_LINK_COLUMN}{start_row}:{Config.STUDENT_NAME_COLUMN}"
            rows = self.google_api.read_sheet_rows(range_name)
            
            if not rows:
                logger.warning("No rows found to process")
                return
            
            logger.info(f"Found {len(rows)} documents to evaluate")
            
            # Process documents
            results = []
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = {
                    executor.submit(
                        self.process_single_document,
                        i + start_row,
                        row
                    ): i for i, row in enumerate(rows)
                }
                
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed {idx + 1}/{len(rows)}")
                    except Exception as e:
                        logger.error(f"Failed to process row {idx + start_row}: {e}")
            
            # Summary
            successful = sum(1 for r in results if r[0])
            logger.info(f"Processing complete: {successful}/{len(rows)} successful")
            
        except Exception as e:
            logger.error(f"Fatal error in sheet processing: {e}")
            raise
    
    def process_single_document(self, row_number: int, row_data: List[str]) -> Tuple[bool, str]:
        """Process a single document"""
        try:
            # Extract data from row
            doc_url = row_data[0] if len(row_data) > 0 else ""
            student_name = row_data[1] if len(row_data) > 1 else "Unknown"
            
            if not doc_url:
                logger.warning(f"Row {row_number}: No document URL found")
                return (False, "No URL")
            
            # Extract doc ID
            doc_id = self.google_api.extract_doc_id(doc_url)
            if not doc_id:
                logger.error(f"Row {row_number}: Invalid document URL")
                self.google_api.write_to_sheet(row_number, "ERROR", "Invalid document URL")
                return (False, "Invalid URL")
            
            logger.info(f"Processing row {row_number}: {student_name}")
            
            # Extract document text
            doc_text = self.google_api.extract_doc_text(doc_id)
            if not doc_text or len(doc_text) < 100:
                logger.warning(f"Row {row_number}: Document too short or empty")
                self.google_api.write_to_sheet(row_number, "N/A", "Document empty or too short")
                return (False, "Empty doc")
            
            # Evaluate document
            evaluation = self.evaluator.evaluate(doc_text, student_name)
            
            # Format results
            score = str(evaluation.get("total_score", "ERROR"))
            feedback = self.evaluator.format_feedback(evaluation)
            
            # Write back to sheet
            self.google_api.write_to_sheet(row_number, score, feedback)
            
            logger.info(f"Row {row_number} completed: Score {score}")
            return (True, score)
        
        except Exception as e:
            logger.error(f"Error processing row {row_number}: {e}")
            try:
                self.google_api.write_to_sheet(row_number, "ERROR", f"Processing failed: {str(e)[:200]}")
            except:
                pass
            return (False, str(e))
