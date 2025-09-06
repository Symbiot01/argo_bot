# /services/initialise_sql_vector_db.py

import time
import logging
import os
import asyncio
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config

class SQLSchemaProcessor:
    """Process database schema and SQL examples for vector storage"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def create_schema_documents(self, schema_info: Dict[str, Any]) -> List[Document]:
        """Convert database schema information to LangChain documents"""
        documents = []
        
        try:
            # Process table schemas
            if "tables" in schema_info:
                for table_name, table_info in schema_info["tables"].items():
                    # Create document for table structure
                    table_content = f"""
TABLE: {table_name}
DESCRIPTION: {table_info.get('description', 'Database table')}

COLUMNS:
"""
                    if "columns" in table_info:
                        for col_name, col_info in table_info["columns"].items():
                            table_content += f"- {col_name}: {col_info.get('type', 'unknown')} "
                            if col_info.get('nullable', True):
                                table_content += "(nullable) "
                            if col_info.get('primary_key', False):
                                table_content += "(PRIMARY KEY) "
                            if col_info.get('foreign_key'):
                                table_content += f"(FK -> {col_info['foreign_key']}) "
                            table_content += f"- {col_info.get('description', '')}\n"
                    
                    # Add relationships
                    if "relationships" in table_info:
                        table_content += "\nRELATIONSHIPS:\n"
                        for rel in table_info["relationships"]:
                            table_content += f"- {rel}\n"
                    
                    # Add indexes
                    if "indexes" in table_info:
                        table_content += "\nINDEXES:\n"
                        for idx in table_info["indexes"]:
                            table_content += f"- {idx}\n"
                    
                    doc = Document(
                        page_content=table_content,
                        metadata={
                            "type": "table_schema",
                            "table_name": table_name,
                            "source": "database_schema"
                        }
                    )
                    documents.append(doc)
            
            # Process SQL query examples
            if "query_examples" in schema_info:
                for example in schema_info["query_examples"]:
                    example_content = f"""
SQL QUERY EXAMPLE:
DESCRIPTION: {example.get('description', 'SQL query example')}
QUERY TYPE: {example.get('type', 'SELECT')}

QUERY:
{example.get('query', '')}

EXPLANATION:
{example.get('explanation', '')}

TABLES USED: {', '.join(example.get('tables', []))}
"""
                    doc = Document(
                        page_content=example_content,
                        metadata={
                            "type": "query_example",
                            "query_type": example.get('type', 'SELECT'),
                            "tables": example.get('tables', []),
                            "source": "query_examples"
                        }
                    )
                    documents.append(doc)
            
            logging.info(f"Created {len(documents)} schema documents")
            return documents
            
        except Exception as e:
            logging.error(f"Error creating schema documents: {e}")
            return []
    
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
                            "type": "sql_file",
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
    Initializes the PineconeVectorStore for SQL schema retrieval.
    """
    return PineconeVectorStore(index=index, embedding=embeddings)

async def setup_sql_knowledge_base(index, embeddings, mcp_client):
    """
    Sets up the SQL knowledge base with database schema and query examples.
    """
    try:
        # Check if knowledge base is already populated
        if index.describe_index_stats()['total_vector_count'] > 0:
            logging.info("SQL knowledge base already populated. Skipping setup.")
            return get_sql_vector_store(index, embeddings)
        
        processor = SQLSchemaProcessor()
        all_documents = []
        
        # Get database schema from MCP client
        logging.info("Fetching database schema from MCP server...")
        schema_info = await mcp_client.get_database_schema()
        
        if schema_info and "error" not in schema_info:
            schema_docs = processor.create_schema_documents(schema_info)
            all_documents.extend(schema_docs)
        
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
            "metadata": {"type": "best_practices", "source": "default_patterns"}
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
            "metadata": {"type": "common_patterns", "source": "default_patterns"}
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