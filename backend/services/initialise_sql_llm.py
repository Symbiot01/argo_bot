# services/initialise_sql_llm.py

import logging
import json
import asyncio
import os
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import pandas as pd

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import config

# Import utility functions
from services.initialise_sql_vector_db import load_database_schema
from utility_functions.chat_history import get_chat_history, format_chat_history_for_context

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

def create_sql_rag_chain(llm, vector_store, chat_id: Optional[int] = None):
    """
    Creates a RAG chain for SQL query generation that returns JSON responses with either SQL queries or HTML content.
    Uses static schema file and includes chat history context.
    
    Args:
        llm: The initialized language model.
        vector_store: Vector store containing SQL query examples.
        chat_id: Optional chat ID for including conversation history.
    
    Returns:
        A runnable LangChain object for SQL response generation.
    """
    logging.info("Creating SQL RAG chain with static schema...")

    # Query examples retriever
    query_retriever = vector_store.as_retriever(
        search_type=config.RETRIEVER_SEARCH_TYPE,
        search_kwargs=config.RETRIEVER_SEARCH_KWARGS
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    def format_schema_info(schema_data: Dict[str, Any]) -> str:
        """Format schema data into readable string"""
        if not schema_data:
            return "No database schema information available."
        
        schema_text = f"DATABASE: {schema_data.get('database_name', 'Unknown')}\n"
        schema_text += f"DESCRIPTION: {schema_data.get('description', 'No description')}\n\n"
        
        if "tables" in schema_data:
            schema_text += "TABLES:\n"
            for table_name, table_info in schema_data["tables"].items():
                schema_text += f"\nTable: {table_name}\n"
                schema_text += f"Description: {table_info.get('description', 'No description')}\n"
                schema_text += "Columns:\n"
                
                if "columns" in table_info:
                    for col_name, col_info in table_info["columns"].items():
                        col_line = f"  - {col_name}: {col_info.get('type', 'unknown')}"
                        if col_info.get('primary_key', False):
                            col_line += " (PRIMARY KEY)"
                        if col_info.get('foreign_key'):
                            col_line += f" (FK -> {col_info['foreign_key']})"
                        if not col_info.get('nullable', True):
                            col_line += " (NOT NULL)"
                        col_line += f" - {col_info.get('description', '')}\n"
                        schema_text += col_line
                
                if "relationships" in table_info:
                    schema_text += "Relationships:\n"
                    for rel in table_info["relationships"]:
                        schema_text += f"  - {rel}\n"
        
        return schema_text
    
    def create_context_with_chat_history(inputs):
        """Retrieve query examples and prepare context with chat history"""
        question = inputs["question"]
        
        # Get relevant query examples
        query_examples = query_retriever.get_relevant_documents(question)
        examples_context = format_docs(query_examples)
        
        # Load static schema
        schema_data = load_database_schema()
        schema_context = format_schema_info(schema_data)
        
        # Get chat history if chat_id is provided
        chat_context = ""
        if chat_id:
            chat_history = get_chat_history(chat_id, limit=10)
            chat_context = format_chat_history_for_context(chat_history)
        
        return {
            "question": question,
            "query_examples": examples_context,
            "schema_info": schema_context,
            "chat_history": chat_context
        }

    sql_template = """You are an intelligent SQL assistant that analyzes questions and provides appropriate responses.

DATABASE SCHEMA INFORMATION:
{schema_info}

RELEVANT SQL QUERY EXAMPLES:
{query_examples}

{chat_history_section}

USER QUESTION: {question}

INSTRUCTIONS:
Analyze the question and determine if it requires database query execution or informational response.

For DATA QUERIES (requiring database access):
- Questions asking for specific data, reports, analytics, calculations
- Questions requiring filtering, searching, or aggregating data
- Questions about finding, comparing, or analyzing records

For INFORMATIONAL QUERIES (general help/explanations):
- Questions about concepts, definitions, or how things work
- General help or guidance requests
- Non-data related questions

RESPONSE FORMAT:
Return a valid JSON object with this exact structure:

For SQL queries:
{{
    "sql": "yes",
    "query": "SELECT * FROM table_name WHERE condition;"
}}

For HTML responses:
{{
    "sql": "no",
    "query": "<html><body><h1>Title</h1><p>Informative content...</p></body></html>"
}}

REQUIREMENTS:
- Return ONLY the JSON object, no additional text
- For SQL: Generate syntactically correct PostgreSQL queries using the schema information
- For HTML: Create well-formatted HTML with proper tags (h1, h2, p, ul, li, strong, etc.)
- Use the schema information to ensure correct table and column names
- Consider the conversation history when generating responses
- Ensure JSON is valid and properly escaped

JSON RESPONSE:"""
    
    def format_prompt_with_context(inputs):
        """Format the prompt with schema and chat history"""
        chat_history_section = ""
        if inputs.get("chat_history") and inputs["chat_history"] != "No previous conversation history available.":
            chat_history_section = f"""
CONVERSATION CONTEXT:
{inputs["chat_history"]}
"""
        else:
            chat_history_section = ""
        
        return sql_template.format(
            schema_info=inputs["schema_info"],
            query_examples=inputs["query_examples"],
            chat_history_section=chat_history_section,
            question=inputs["question"]
        )
    
    # SQL RAG chain with static schema and chat history
    sql_rag_chain = (
        create_context_with_chat_history
        | format_prompt_with_context
        | llm
        | StrOutputParser()
    )

    logging.info("SQL RAG chain is ready.")
    return sql_rag_chain

# Legacy function name for backward compatibility
def create_unified_rag_chain(llm, vector_store, schema_retriever=None, chat_id: Optional[int] = None):
    """Legacy wrapper for create_sql_rag_chain"""
    return create_sql_rag_chain(llm, vector_store, chat_id)

async def execute_sql_with_context(sql_chain, mcp_client, question: str, 
                                 database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Execute SQL query processing pipeline that handles both SQL and HTML responses.
    
    Args:
        sql_chain: The SQL RAG chain
        mcp_client: MCP client for database operations
        question: User's natural language question
        database_name: Target database name
        chat_id: Optional chat ID for context
    
    Returns:
        Dict containing the response, execution results, and CSV file path if applicable
    """
    try:
        # Generate response using SQL chain
        logging.info(f"Processing question: {question}")
        
        chain_input = {"question": question}
        response_text = await sql_chain.ainvoke(chain_input)
        
        # Clean up the response (remove any markdown formatting)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        logging.info(f"Generated response: {response_text}")
        
        # Parse JSON response
        try:
            json_response = json.loads(response_text)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {e}")
            return {
                "question": question,
                "error": f"Invalid JSON response: {str(e)}",
                "success": False,
                "response_type": "error"
            }
        
        # Check if SQL execution is required
        if json_response.get("sql", "").lower() == "yes":
            # SQL query needs to be executed
            sql_query = json_response.get("query", "")
            
            if not sql_query:
                return {
                    "question": question,
                    "error": "No SQL query provided in response",
                    "success": False,
                    "response_type": "error"
                }
            
            logging.info(f"Executing SQL query: {sql_query}")
            
            # Execute query through MCP client
            result = await mcp_client.execute_sql_query(sql_query, database_name)
            
            response = {
                "question": question,
                "response_type": "sql",
                "sql_query": sql_query,
                "execution_result": result,
                "success": "error" not in result,
                "chat_id": chat_id
            }
            
            if "csv_file" in result:
                response["csv_file"] = result["csv_file"]
                logging.info(f"Query executed successfully. Results saved to: {result['csv_file']}")
            
            return response
            
        else:
            # HTML response - no database execution needed
            html_content = json_response.get("query", "")
            
            logging.info("Generated HTML response (no database execution required)")
            
            return {
                "question": question,
                "response_type": "html",
                "html_content": html_content,
                "success": True,
                "chat_id": chat_id
            }
        
    except Exception as e:
        logging.error(f"Error in SQL query pipeline: {e}")
        return {
            "question": question,
            "error": str(e),
            "success": False,
            "response_type": "error",
            "chat_id": chat_id
        }

# Legacy function name for backward compatibility
async def execute_unified_query(unified_chain, mcp_client, question: str, 
                               database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """Legacy wrapper for execute_sql_with_context"""
    return await execute_sql_with_context(unified_chain, mcp_client, question, database_name, chat_id)

async def astream_unified_response(unified_chain, mcp_client, question: str, 
                                  database_name: str = None) -> AsyncGenerator[str, None]:
    """
    Stream unified response generation that handles both SQL and HTML responses.
    
    Args:
        unified_chain: The unified RAG chain
        mcp_client: MCP client for database operations
        question: User's natural language question
        database_name: Target database name
    
    Yields:
        str: Chunks of the response including JSON output and execution results if SQL
    """
    try:
        yield f"🔍 Analyzing question: {question}\n\n"
        
        # Generate response using unified chain
        yield "⚡ Generating response...\n"
        chain_input = {"question": question}
        
        response_text = ""
        async for chunk in unified_chain.astream(chain_input):
            response_text += chunk
            yield chunk
        
        yield "\n\n� Processing response...\n"
        
        # Clean up the response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        try:
            json_response = json.loads(response_text)
        except json.JSONDecodeError as e:
            yield f"❌ Error parsing JSON response: {str(e)}\n"
            return
        
        # Check if SQL execution is required
        if json_response.get("sql", "").lower() == "yes":
            sql_query = json_response.get("query", "")
            
            if not sql_query:
                yield "❌ Error: No SQL query provided in response\n"
                return
            
            yield f"📊 Executing SQL query...\n"
            
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
        else:
            # HTML response - no database execution needed
            yield "Generated HTML response (no database execution required)\n"
            yield "Response completed!\n"
        
    except Exception as e:
        yield f"Error in unified pipeline: {str(e)}\n"

async def astream_sql_response(sql_chain, mcp_client, question: str, 
                              database_name: str = None, chat_id: Optional[int] = None) -> AsyncGenerator[str, None]:
    """
    Stream SQL response generation that handles both SQL and HTML responses.
    
    Args:
        sql_chain: The SQL RAG chain
        mcp_client: MCP client for database operations
        question: User's natural language question
        database_name: Target database name
        chat_id: Optional chat ID for context
    
    Yields:
        str: Chunks of the response including JSON output and execution results if SQL
    """
    try:
        yield f"Analyzing question: {question}\n\n"
        
        # Generate response using SQL chain
        yield "Generating response...\n"
        chain_input = {"question": question}
        
        response_text = ""
        async for chunk in sql_chain.astream(chain_input):
            response_text += chunk
            yield chunk
        
        yield "\n\nProcessing response...\n"
        
        # Clean up the response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        try:
            json_response = json.loads(response_text)
        except json.JSONDecodeError as e:
            yield f"Error parsing JSON response: {str(e)}\n"
            return
        
        # Check if SQL execution is required
        if json_response.get("sql", "").lower() == "yes":
            sql_query = json_response.get("query", "")
            
            if not sql_query:
                yield "Error: No SQL query provided in response\n"
                return
            
            yield f"Executing SQL query...\n"
            
            # Execute through MCP client
            result = await mcp_client.execute_sql_query(sql_query, database_name)
            
            if "error" in result:
                yield f"Error executing query: {result['error']}\n"
            else:
                yield f"Query executed successfully!\n"
                if "csv_file" in result:
                    yield f"Results saved to: {result['csv_file']}\n"
                if "row_count" in result:
                    yield f"Rows returned: {result['row_count']}\n"
        else:
            # HTML response - no database execution needed
            yield "Generated HTML response (no database execution required)\n"
            yield "Response completed!\n"
        
    except Exception as e:
        yield f"Error in SQL pipeline: {str(e)}\n"
