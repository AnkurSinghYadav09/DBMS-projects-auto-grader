import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    CREDENTIALS_DIR = BASE_DIR / "credentials"
    LOGS_DIR = BASE_DIR / "logs"
    RUBRICS_DIR = BASE_DIR / "rubrics"
    
    # Ensure directories exist
    LOGS_DIR.mkdir(exist_ok=True)
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    RUBRICS_DIR.mkdir(exist_ok=True)
    
    # AI Provider Configuration
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Google Configuration
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials/service_account.json")
    
    # Column Configuration
    DOC_LINK_COLUMN = os.getenv("DOC_LINK_COLUMN", "A")
    STUDENT_NAME_COLUMN = os.getenv("STUDENT_NAME_COLUMN", "B")
    SCORE_COLUMN = os.getenv("SCORE_COLUMN", "C")
    FEEDBACK_COLUMN = os.getenv("FEEDBACK_COLUMN", "D")
    
    # Processing Configuration
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    INCLUDE_PLAGIARISM_CHECK = os.getenv("INCLUDE_PLAGIARISM_CHECK", "True").lower() == "true"
    
    # Google API Scopes
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents.readonly"
    ]
    
    @classmethod
    def validate(cls):
        errors = []
        
        # Check AI provider configuration
        if cls.AI_PROVIDER == "gemini":
            if not cls.GEMINI_API_KEY:
                errors.append("GEMINI_API_KEY not set (AI_PROVIDER is 'gemini')")
        elif cls.AI_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY not set (AI_PROVIDER is 'openai')")
        elif cls.AI_PROVIDER == "deepseek":
            if not cls.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY not set (AI_PROVIDER is 'deepseek')")
        
        if not cls.SPREADSHEET_ID:
            errors.append("SPREADSHEET_ID not set")
        if not Path(cls.SERVICE_ACCOUNT_FILE).exists():
            errors.append(f"Service account file not found: {cls.SERVICE_ACCOUNT_FILE}")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
