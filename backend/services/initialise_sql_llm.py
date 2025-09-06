# services/initialise_sql_llm.py

import logging
import json
import asyncio
import os
from typing import AsyncGenerator, Dict, Any
from datetime import datetime
import pandas as pd

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import config

# MCP Client imports
import mcp
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

class SQLMCPClient:
    """MCP Client for SQL query execution and database operations"""
    
    def __init__(self, server_script_path: str = "mcp_server.py"):
        self.server_script_path = server_script_path
        self.session = None
        self.client = None
        
    async def connect(self):
        """Connect to the MCP server"""
        try:
            # Start the MCP server process
            server_params = mcp.ClientParameters(
                name="sql-client",
                version="1.0.0"
            )
            
            # Create stdio client connection
            self.client = stdio_client(
                command=["python", self.server_script_path],
                env=None
            )
            
            # Start session
            self.session = await self.client.__aenter__()
            await self.session.initialize()
            
            logging.info("Connected to MCP SQL server successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def execute_sql_query(self, query: str, database_name: str = None) -> Dict[str, Any]:
        """Execute SQL query through MCP server and save results as CSV"""
        try:
            if not self.session:
                await self.connect()
            
            # Call the SQL execution tool through MCP
            result = await self.session.call_tool(
                "execute_sql_query",
                arguments={
                    "query": query,
                    "database_name": database_name or "default"
                }
            )
            
            # Save results to CSV file in datasets folder
            if result and "data" in result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"query_result_{timestamp}.csv"
                filepath = os.path.join("datasets", filename)
                
                # Ensure datasets directory exists
                os.makedirs("datasets", exist_ok=True)
                
                # Convert to DataFrame and save as CSV
                df = pd.DataFrame(result["data"])
                df.to_csv(filepath, index=False)
                
                result["csv_file"] = filepath
                logging.info(f"Query results saved to {filepath}")
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to execute SQL query: {e}")
            return {"error": str(e)}
    
    async def get_database_schema(self, database_name: str = None) -> Dict[str, Any]:
        """Get database schema information through MCP server"""
        try:
            if not self.session:
                await self.connect()
            
            result = await self.session.call_tool(
                "get_database_schema",
                arguments={
                    "database_name": database_name or "default"
                }
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to get database schema: {e}")
            return {"error": str(e)}
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        try:
            if self.client:
                await self.client.__aexit__(None, None, None)
            logging.info("Disconnected from MCP server")
        except Exception as e:
            logging.error(f"Error disconnecting from MCP server: {e}")

def initialize_sql_llm_and_embeddings():
    """
    Initializes the Google Generative AI models for SQL query generation.
    
    Returns:
        tuple: (llm_instance, embeddings_model_instance, mcp_client)
    """
    try:
        # Configure Google API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
            
        genai.configure(api_key=api_key)
        
        # Initialize LLM with specific configuration for SQL generation
        llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL, 
            temperature=0,  # Low temperature for consistent SQL generation
            max_tokens=2048
        )
        
        embeddings_model = GoogleGenerativeAIEmbeddings(model=config.EMBEDDING_MODEL)
        
        # Initialize MCP client
        mcp_client = SQLMCPClient()
        
        logging.info("SQL LLM, Embedding models, and MCP client initialized successfully.")
        return llm, embeddings_model, mcp_client
        
    except Exception as e:
        logging.error(f"Failed to initialize SQL AI models: {e}")
        raise

def create_sql_rag_chain(llm, vector_store, mcp_client):
    """
    Creates a RAG chain specifically for SQL query generation.
    This chain uses database schema knowledge from vector store and MCP client for execution.
    
    Args:
        llm: The initialized language model.
        vector_store: Vector store containing database schema and query examples.
        mcp_client: MCP client for database operations.
    
    Returns:
        A runnable LangChain object for SQL query generation.
    """
    logging.info("Creating SQL RAG chain...")

    # Retriever for database schema and SQL examples
    schema_retriever = vector_store.as_retriever(
        search_type=config.RETRIEVER_SEARCH_TYPE,
        search_kwargs=config.RETRIEVER_SEARCH_KWARGS
    )

    sql_template = """You are an expert SQL query generator with deep knowledge of database schemas and SQL best practices.

INSTRUCTIONS:
1. Generate ONLY valid SQL queries based on the provided database schema
2. Use the schema information to understand table structures, relationships, and constraints
3. Follow SQL best practices and optimize for performance
4. Return ONLY the SQL query without explanations unless specifically requested
5. Use appropriate JOINs, WHERE clauses, and aggregations as needed
6. Ensure proper syntax for PostgreSQL database

DATABASE SCHEMA CONTEXT:
{schema_context}

SQL QUERY EXAMPLES (for reference):
{example_context}

USER QUESTION: {question}

REQUIREMENTS:
- Generate syntactically correct PostgreSQL SQL
- Use proper table and column names from the schema
- Include appropriate WHERE, JOIN, ORDER BY, GROUP BY clauses as needed
- Optimize for readability and performance
- Handle edge cases and data types correctly

SQL QUERY:"""
    
    prompt = PromptTemplate.from_template(sql_template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # SQL RAG chain with schema-aware query generation
    sql_rag_chain = (
        {
            "schema_context": itemgetter("question") | schema_retriever | format_docs,
            "example_context": lambda x: format_docs(x.get('examples', [])),
            "question": itemgetter("question")
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    logging.info("SQL RAG chain is ready.")
    return sql_rag_chain

async def execute_sql_with_context(rag_chain, mcp_client, question: str, 
                                 database_name: str = None) -> Dict[str, Any]:
    """
    Execute SQL query generation and execution pipeline.
    
    Args:
        rag_chain: The SQL RAG chain
        mcp_client: MCP client for database operations
        question: User's natural language question
        database_name: Target database name
    
    Returns:
        Dict containing SQL query, results, and CSV file path
    """
    try:
        # Generate SQL query using RAG chain
        logging.info(f"Generating SQL query for: {question}")
        
        chain_input = {"question": question}
        sql_query = await rag_chain.ainvoke(chain_input)
        
        # Clean up the SQL query (remove any markdown formatting)
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        logging.info(f"Generated SQL query: {sql_query}")
        
        # Execute query through MCP client
        result = await mcp_client.execute_sql_query(sql_query, database_name)
        
        response = {
            "question": question,
            "sql_query": sql_query,
            "execution_result": result,
            "success": "error" not in result
        }
        
        if "csv_file" in result:
            response["csv_file"] = result["csv_file"]
            logging.info(f"Query executed successfully. Results saved to: {result['csv_file']}")
        
        return response
        
    except Exception as e:
        logging.error(f"Error in SQL execution pipeline: {e}")
        return {
            "question": question,
            "error": str(e),
            "success": False
        }

async def astream_sql_response(rag_chain, mcp_client, question: str, 
                              database_name: str = None) -> AsyncGenerator[str, None]:
    """
    Stream SQL query generation and execution results.
    
    Args:
        rag_chain: The SQL RAG chain
        mcp_client: MCP client for database operations
        question: User's natural language question
        database_name: Target database name
    
    Yields:
        str: Chunks of the response including SQL query and results
    """
    try:
        yield f"🔍 Analyzing question: {question}\n\n"
        
        # Generate SQL query
        yield "⚡ Generating SQL query...\n"
        chain_input = {"question": question}
        
        sql_query = ""
        async for chunk in rag_chain.astream(chain_input):
            sql_query += chunk
            yield chunk
        
        yield "\n\n📊 Executing query...\n"
        
        # Clean and execute SQL
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Execute through MCP client
        result = await mcp_client.execute_sql_query(sql_query, database_name)
        
        if "error" in result:
            yield f"❌ Error executing query: {result['error']}\n"
        else:
            yield f"✅ Query executed successfully!\n"
            if "csv_file" in result:
                yield f"📁 Results saved to: {result['csv_file']}\n"
            if "row_count" in result:
                yield f"📈 Rows returned: {result['row_count']}\n"
        
    except Exception as e:
        yield f"❌ Error in SQL pipeline: {str(e)}\n"
