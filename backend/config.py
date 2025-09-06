# /config.py

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- API Keys and Environment ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DOCUMENT_DIRECTORY = os.getenv("DOCUMENT_DIRECTORY", "documents")
VALID_API_KEY = os.getenv('VALID_API_KEY', 'your-default-api-key')

# Validate required API keys
if not GOOGLE_API_KEY:
    logging.warning("GOOGLE_API_KEY not set in environment variables.")
if not PINECONE_API_KEY:
    logging.warning("PINECONE_API_KEY not set in environment variables.")

# Set Google API key in the environment for LangChain modules
if GOOGLE_API_KEY:
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

# --- Vector Database Configuration ---
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "argobot-knowledge-base")
PINECONE_SQL_INDEX_NAME = os.getenv("PINECONE_SQL_INDEX_NAME", "sql-knowledge-base")

# --- Model Configuration ---
EMBEDDING_MODEL = "models/text-embedding-004"
LLM_MODEL = "gemini-2.0-flash-lite" # More standard model name
EMBEDDING_DIMENSION = 768      # For 'text-embedding-004'

# --- Text Splitter Configuration ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# --- Retriever Configuration ---
RETRIEVER_SEARCH_TYPE = "mmr" 
RETRIEVER_SEARCH_KWARGS = {"k": 4,"fetch_k": 6, "lambda_mult": 0.8 }

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres_buoy:buoy_sih123@localhost:5432/database")
USER_DATABASE_URL = os.getenv("USER_DATABASE_URL", "sqlite:///./user_data.db")

# --- JWT Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CHAT_TOKEN_EXPIRE_DAYS = 1

# --- MCP Configuration ---
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))
MCP_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "30"))

# --- SQL LLM Configuration ---
SQL_MAX_RESULTS = int(os.getenv("SQL_MAX_RESULTS", "1000"))
SQL_QUERY_TIMEOUT = int(os.getenv("SQL_QUERY_TIMEOUT", "30"))
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "datasets")

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "argobot.log")

logging.info("Configuration loaded successfully.")