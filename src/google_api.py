import re
import json
import logging
import time
import ssl
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from google.oauth2 import service_account
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import Config

logger = logging.getLogger(__name__)

# Try to import streamlit for cloud deployment
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

class GoogleAPIHandler:
    def __init__(self):
        # Get credentials based on environment
        if HAS_STREAMLIT:
            try:
                # Try to get service account from Streamlit secrets
                if "gcp_service_account" in st.secrets:
                    service_account_info = dict(st.secrets["gcp_service_account"])
                    self.creds = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=Config.SCOPES
                    )
                else:
                    # Fall back to file
                    self.creds = service_account.Credentials.from_service_account_file(
                        Config.SERVICE_ACCOUNT_FILE,
                        scopes=Config.SCOPES
                    )
            except (AttributeError, FileNotFoundError, KeyError):
                # Fall back to file
                self.creds = service_account.Credentials.from_service_account_file(
                    Config.SERVICE_ACCOUNT_FILE,
                    scopes=Config.SCOPES
                )
        else:
            # Local environment - use file
            self.creds = service_account.Credentials.from_service_account_file(
                Config.SERVICE_ACCOUNT_FILE,
                scopes=Config.SCOPES
            )
        
        # Lazy initialization of services
        self._sheets_service = None
        self._docs_service = None
        self._drive_service = None
        logger.info("Google API handler initialized")
    
    def _rebuild_sheets_service(self):
        """Rebuild sheets service connection (helps with SSL errors)"""
        logger.warning("Rebuilding sheets service due to connection error")
        self._sheets_service = None
        time.sleep(2)  # Brief pause before rebuild
        return self.sheets_service
    
    @property
    def sheets_service(self):
        if self._sheets_service is None:
            self._sheets_service = build("sheets", "v4", credentials=self.creds, cache_discovery=False)
        return self._sheets_service
    
    @property
    def docs_service(self):
        if self._docs_service is None:
            self._docs_service = build("docs", "v1", credentials=self.creds, cache_discovery=False)
        return self._docs_service
    
    @property
    def drive_service(self):
        if self._drive_service is None:
            self._drive_service = build("drive", "v3", credentials=self.creds, cache_discovery=False)
        return self._drive_service
    
    @staticmethod
    def extract_doc_id(url: str) -> Optional[str]:
        """Extract document ID from Google Docs URL"""
        patterns = [
            r"/d/([a-zA-Z0-9-_]+)",
            r"id=([a-zA-Z0-9-_]+)",
            r"^([a-zA-Z0-9-_]+)$"  # Direct ID
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def read_sheet_rows(self, range_name: str) -> List[List[str]]:
        """Read rows from Google Sheet with retry logic"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            rows = result.get("values", [])
            logger.info(f"Read {len(rows)} rows from sheet")
            return rows
        except (ssl.SSLError, ConnectionError, OSError) as e:
            logger.warning(f"Connection error reading sheet, rebuilding service: {e}")
            self._rebuild_sheets_service()
            raise
        except Exception as e:
            logger.error(f"Error reading sheet: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_doc_text(self, doc_id: str) -> str:
        """Extract full text from Google Doc"""
        try:
            doc = self.docs_service.documents().get(documentId=doc_id).execute()
            text_parts = []
            
            for element in doc.get("body", {}).get("content", []):
                if "paragraph" in element:
                    for text_run in element["paragraph"].get("elements", []):
                        content = text_run.get("textRun", {}).get("content", "")
                        if content.strip():
                            text_parts.append(content)
                
                elif "table" in element:
                    for row in element["table"].get("tableRows", []):
                        for cell in row.get("tableCells", []):
                            for cell_content in cell.get("content", []):
                                if "paragraph" in cell_content:
                                    for text_run in cell_content["paragraph"].get("elements", []):
                                        content = text_run.get("textRun", {}).get("content", "")
                                        if content.strip():
                                            text_parts.append(content)
            
            full_text = "".join(text_parts).strip()
            logger.info(f"Extracted {len(full_text)} characters from doc {doc_id}")
            return full_text
        
        except Exception as e:
            logger.error(f"Error extracting text from doc {doc_id}: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((ssl.SSLError, ConnectionError, OSError))
    )
    def write_to_sheet(self, row_number: int, score: str, feedback: str):
        """Write evaluation results back to sheet with aggressive retry"""
        try:
            range_name = f"{Config.SCORE_COLUMN}{row_number}:{Config.FEEDBACK_COLUMN}{row_number}"
            
            # Truncate feedback if too long (Google Sheets cell limit is 50,000 chars)
            if len(feedback) > 5000:
                feedback = feedback[:4997] + "..."
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=range_name,
                valueInputOption="RAW",
                body={"values": [[score, feedback]]}
            ).execute()
            
            logger.info(f"Updated row {row_number} with results")
            
        except (ssl.SSLError, ConnectionError, OSError) as e:
            logger.warning(f"SSL/Connection error writing to row {row_number}, rebuilding and retrying: {e}")
            self._rebuild_sheets_service()
            raise  # Let retry decorator handle it
            
        except Exception as e:
            logger.error(f"Error writing to sheet row {row_number}: {e}")
            # Don't raise on other errors to avoid crash - just log
            logger.error(f"Failed to write score={score}, feedback length={len(feedback)}")
    
    def get_doc_metadata(self, doc_id: str) -> Dict:
        """Get document metadata including title and last modified"""
        try:
            file = self.drive_service.files().get(
                fileId=doc_id,
                fields="name,modifiedTime,createdTime,owners"
            ).execute()
            return file
        except Exception as e:
            logger.warning(f"Could not fetch metadata for doc {doc_id}: {e}")
            return {}
