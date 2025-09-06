# /services/initialise_sql_vector_db.py

import time
import logging
import os
import asyncio
import json
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config

class SQLQueryProcessor:
    """Process SQL examples for vector storage (without schema)"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_sql_examples_from_files(self, examples_dir: str = "datasets/sql_examples") -> List[Document]:
        """Load SQL examples from files in the examples directory"""
        documents = []
        
        try:
            if not os.path.exists(examples_dir):
                logging.info(f"SQL examples directory {examples_dir} not found")
                return documents
            
            for filename in os.listdir(examples_dir):
                if filename.endswith('.sql') or filename.endswith('.txt'):
                    filepath = os.path.join(examples_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "type": "sql_example",
                            "filename": filename,
                            "source": "sql_examples"
                        }
                    )
                    documents.append(doc)
            
            logging.info(f"Loaded {len(documents)} SQL example files")
            return documents
            
        except Exception as e:
            logging.error(f"Error loading SQL examples: {e}")
            return []

def load_database_schema() -> Dict[str, Any]:
    """Load database schema from static JSON file"""
    try:
        schema_file = "datasets/database_schema.json"
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            logging.info("Database schema loaded from file")
            return schema_data
        else:
            logging.warning("Database schema file not found")
            return {}
    except Exception as e:
        logging.error(f"Error loading database schema: {e}")
        return {}

def initialize_sql_pinecone():
    """
    Initializes connection to Pinecone for SQL schema knowledge base.
    
    Returns:
        pinecone.Index: The Pinecone index object.
    """
    try:
        # Get API key from environment
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        pc = Pinecone(api_key=api_key)
        index_name = os.getenv("PINECONE_SQL_INDEX_NAME", "sql-knowledge-base")

        if index_name not in [index["name"] for index in pc.list_indexes()]:
            logging.info(f"Creating new Pinecone index for SQL: {index_name}...")
            pc.create_index(
                name=index_name,
                dimension=config.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            while not pc.describe_index(index_name).status["ready"]:
                logging.info("Waiting for SQL index to be ready...")
                time.sleep(5)
            logging.info("SQL index created successfully.")
        else:
            logging.info(f"SQL Index '{index_name}' already exists.")

        return pc.Index(index_name)
        
    except Exception as e:
        logging.error(f"Failed to initialize SQL Pinecone: {e}")
        raise

def get_sql_vector_store(index, embeddings):
    """
    Initializes the PineconeVectorStore for SQL query examples.
    """
    return PineconeVectorStore(index=index, embedding=embeddings)

async def initialize_vector_store(embeddings):
    """
    Initialize the vector store for SQL query examples only.
    
    Args:
        embeddings: The embeddings model
        
    Returns:
        vector_store: The initialized vector store
    """
    try:
        # Initialize Pinecone
        index = initialize_sql_pinecone()
        
        # Get vector store
        vector_store = get_sql_vector_store(index, embeddings)
        
        logging.info("Vector store initialized successfully")
        return vector_store
        
    except Exception as e:
        logging.error(f"Failed to initialize vector store: {e}")
        raise

async def setup_sql_knowledge_base(index, embeddings):
    """
    Sets up the SQL knowledge base with query examples only (no schema).
    """
    try:
        # Check if knowledge base is already populated
        if index.describe_index_stats()['total_vector_count'] > 0:
            logging.info("SQL knowledge base already populated. Skipping setup.")
            return get_sql_vector_store(index, embeddings)
        
        processor = SQLQueryProcessor()
        all_documents = []
        
        # Load SQL examples from files
        example_docs = processor.load_sql_examples_from_files()
        all_documents.extend(example_docs)
        
        # Add some default SQL patterns and best practices
        default_patterns = create_default_sql_patterns()
        all_documents.extend(default_patterns)
        
        if all_documents:
            logging.info(f"Adding {len(all_documents)} documents to SQL knowledge base...")
            vector_store = get_sql_vector_store(index, embeddings)
            
            # Split documents if they're too large
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP
            )
            
            split_docs = []
            for doc in all_documents:
                splits = text_splitter.split_documents([doc])
                split_docs.extend(splits)
            
            # Add to vector store
            vector_store.add_documents(documents=split_docs)
            logging.info("SQL knowledge base setup complete.")
            return vector_store
        else:
            logging.warning("No documents found for SQL knowledge base")
            return get_sql_vector_store(index, embeddings)
            
    except Exception as e:
        logging.error(f"Error setting up SQL knowledge base: {e}")
        # Return empty vector store
        return get_sql_vector_store(index, embeddings)

def create_default_sql_patterns() -> List[Document]:
    """Create default SQL patterns and best practices documents"""
    patterns = [
        {
            "content": """
SQL BEST PRACTICES:

1. Always use proper JOIN syntax instead of comma-separated tables
2. Use WHERE clauses to filter data efficiently
3. Use appropriate indexes for better performance
4. Use LIMIT when testing queries
5. Use aliases for better readability
6. Always specify column names in INSERT statements
7. Use transactions for data modification operations
8. Avoid SELECT * in production queries
9. Use parameterized queries to prevent SQL injection
10. Use appropriate data types for columns
""",
            "metadata": {
                "type": "best_practices", 
                "source": "default_patterns"
            }
        },
        {
            "content": """
COMMON SQL PATTERNS:

1. Basic SELECT with WHERE:
   SELECT column1, column2 FROM table_name WHERE condition;

2. JOIN operations:
   SELECT t1.col1, t2.col2 
   FROM table1 t1 
   JOIN table2 t2 ON t1.id = t2.table1_id;

3. Aggregation with GROUP BY:
   SELECT category, COUNT(*), AVG(price) 
   FROM products 
   GROUP BY category 
   HAVING COUNT(*) > 10;

4. Subqueries:
   SELECT * FROM table1 
   WHERE id IN (SELECT table1_id FROM table2 WHERE condition);

5. Window functions:
   SELECT name, salary, 
   RANK() OVER (ORDER BY salary DESC) as rank 
   FROM employees;
""",
            "metadata": {
                "type": "common_patterns", 
                "source": "default_patterns"
            }
        }
    ]
    
    documents = []
    for pattern in patterns:
        doc = Document(
            page_content=pattern["content"],
            metadata=pattern["metadata"]
        )
        documents.append(doc)
    
    return documents