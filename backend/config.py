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

if not GOOGLE_API_KEY or not PINECONE_API_KEY:
    logging.error("API keys for Google or Pinecone are not set in the environment variables.")
    raise ValueError("Missing API keys. Please set GOOGLE_API_KEY and PINECONE_API_KEY in your .env file.")

# Set Google API key in the environment for LangChain modules
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

# --- Model and VectorDB Configuration ---
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres_buoy:buoy_sih123@host:port/database")
USER_DATABASE_URL = os.getenv("USER_DATABASE_URL", "sqlite:///./user_data.db")

logging.info("Configuration loaded successfully.")