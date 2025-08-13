# config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Configuration management for DocuReview Pro"""
    
    # Application Settings
    APP_NAME = "DocuReview Pro"
    APP_VERSION = "1.0.0"
    DEFAULT_PORT = 8555
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server Configuration
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", DEFAULT_PORT))
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///docureview_pro.db")
    DB_PATH = os.getenv("DB_PATH", "docureview_pro.db")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://prave-mcngte2t-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2025-01-01-preview")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-nano")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1-nano")
    
    # Embedding Configuration
    SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    # Vector Search Configuration
    FAISS_INDEX_TYPE = os.getenv("FAISS_INDEX_TYPE", "IndexFlatIP")
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    ALLOWED_EXTENSIONS = ["txt", "pdf",]
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    
    # Performance Configuration
    MAX_INGESTION_TIME_SECONDS = int(os.getenv("MAX_INGESTION_TIME_SECONDS", "30"))
    MAX_RETRIEVAL_TIME_MS = int(os.getenv("MAX_RETRIEVAL_TIME_MS", "500"))
    
    # UI Configuration
    THEME_PRIMARY_COLOR = os.getenv("THEME_PRIMARY_COLOR", "#1f77b4")
    THEME_BACKGROUND_COLOR = os.getenv("THEME_BACKGROUND_COLOR", "#ffffff")
    THEME_SECONDARY_COLOR = os.getenv("THEME_SECONDARY_COLOR", "#ff7f0e")
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            ("AZURE_OPENAI_ENDPOINT", cls.AZURE_OPENAI_ENDPOINT),
            ("AZURE_OPENAI_API_KEY", cls.AZURE_OPENAI_API_KEY),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_database_path(cls):
        """Get absolute database path"""
        return Path(cls.DB_PATH).absolute()
    
    @classmethod
    def ensure_upload_folder(cls):
        """Ensure upload folder exists"""
        Path(cls.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
        return Path(cls.UPLOAD_FOLDER).absolute()

# Initialize configuration
config = Config()