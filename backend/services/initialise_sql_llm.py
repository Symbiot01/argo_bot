# services/initialise_sql_llm.py

import logging
import json
import asyncio
import os
import sys  # Import sys
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import PyPDF2

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough,RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import config

# Import utility functions
from utility_functions.chat_history import get_chat_history, format_chat_history_for_context
from contextlib import AsyncExitStack

# MCP Client imports
import mcp
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters

class SQLMCPClient:
    """MCP Client for SQL query execution and database operations"""
    
    def __init__(self, server_script_path: str = "mcp_server.py"):
        self.server_script_path = server_script_path
        self.session = None
        self._client_context = None  # To hold the context manager
        self.args = [server_script_path]
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Connect to the MCP server"""
        if self.session:
            logging.warning("Already connected.")
            return True
        try:

                
            server_params = StdioServerParameters(
                command="python",
                args=self.args,
                env=None
            )


            # Start the server
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.writer = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.writer))


            await self.session.initialize()

            logging.info("Connected to MCP SQL server successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to MCP server: {e}")
            logging.exception(e)
            self._client_context = None
            self.session = None
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
        if not self._client_context:
            logging.warning("Not connected.")
            return
        try:
            # Manually exit the context to terminate the server process.
            await self._client_context.__aexit__(None, None, None)
            logging.info("Disconnected from MCP server")
        except Exception as e:
            logging.error(f"Error disconnecting from MCP server: {e}")
        finally:
            # Clear the state
            self._client_context = None
            self.session = None

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

def load_pdf_content(pdf_path: str = "datasets/argo_context.pdf") -> str:
    """Load and extract text content from PDF file"""
    try:
        if not os.path.exists(pdf_path):
            logging.warning(f"PDF file not found: {pdf_path}")
            return ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
            
            logging.info(f"PDF content loaded successfully from {pdf_path}")
            return text_content.strip()
            
    except Exception as e:
        logging.error(f"Error loading PDF content: {e}")
        return ""

def load_sql_examples() -> str:
    """Load SQL examples from files in the examples directory"""
    examples_content = ""
    examples_dir = "datasets/sql_examples"
    
    try:
        if not os.path.exists(examples_dir):
            logging.info(f"SQL examples directory {examples_dir} not found")
            return ""
        
        for filename in os.listdir(examples_dir):
            if filename.endswith('.sql') or filename.endswith('.txt'):
                filepath = os.path.join(examples_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    examples_content += f"\n--- {filename} ---\n{content}\n"
        
        logging.info(f"SQL examples loaded from {examples_dir}")
        return examples_content
        
    except Exception as e:
        logging.error(f"Error loading SQL examples: {e}")
        return ""

def initialize_sql_llm():
    """
    Initializes the Google Generative AI model for SQL query generation.
    
    Returns:
        tuple: (llm_instance, mcp_client)
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
        
        # Initialize MCP client
        mcp_client = SQLMCPClient()
        
        logging.info("SQL LLM and MCP client initialized successfully.")
        return llm, mcp_client
        
    except Exception as e:
        logging.error(f"Failed to initialize SQL AI models: {e}")
        raise

# Legacy function for backward compatibility
def initialize_sql_llm_and_embeddings():
    """
    Legacy wrapper for initialize_sql_llm.
    
    Returns:
        tuple: (llm_instance, None, mcp_client) - embeddings set to None as we no longer use them
    """
    llm, mcp_client = initialize_sql_llm()
    return llm, None, mcp_client

def create_sql_rag_chain(llm, chat_id: Optional[int] = None):
    """
    Creates a RAG chain for SQL query generation that returns JSON responses with either SQL queries or HTML content.
    Uses static schema file, SQL examples, and PDF context instead of vector database.
    
    Args:
        llm: The initialized language model.
        chat_id: Optional chat ID for including conversation history.
    
    Returns:
        A runnable LangChain object for SQL response generation.
    """
    logging.info("Creating SQL RAG chain with static context...")

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
    
    def create_context_with_static_data(inputs):
        """Prepare context with static data instead of vector search"""
        question = inputs["question"]
        
        # Load static data
        schema_data = load_database_schema()
        schema_context = format_schema_info(schema_data)
        
        # Load SQL examples
        sql_examples = load_sql_examples()
        
        # Load PDF content
        pdf_content = load_pdf_content()
        
        # Get chat history if chat_id is provided
        chat_context = ""
        if chat_id:
            chat_history = get_chat_history(chat_id, limit=10)
            chat_context = format_chat_history_for_context(chat_history)
        
        return {
            "question": question,
            "sql_examples": sql_examples,
            "schema_info": schema_context,
            "pdf_content": pdf_content,
            "chat_history": chat_context
        }

    sql_template = """You are an intelligent SQL assistant that analyzes questions and provides appropriate responses.

DATABASE SCHEMA INFORMATION:
{schema_info}

SQL QUERY EXAMPLES:
{sql_examples}

ARGO CONTEXT INFORMATION:
{pdf_content}

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

Use the Argo context information to provide relevant insights and context when answering questions.

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
- Consider the conversation history and Argo context when generating responses
- Ensure JSON is valid and properly escaped

JSON RESPONSE:"""
    
    def format_prompt_with_context(inputs):
        """Format the prompt with schema, SQL examples, PDF content, and chat history"""
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
            sql_examples=inputs["sql_examples"],
            pdf_content=inputs["pdf_content"],
            chat_history_section=chat_history_section,
            question=inputs["question"]
        )
    
    # SQL RAG chain with static data and chat history
    sql_rag_chain = (
        RunnableLambda(create_context_with_static_data)
        | RunnableLambda(format_prompt_with_context)
        | llm
        | StrOutputParser()
    )

    logging.info("SQL RAG chain is ready.")
    return sql_rag_chain

# Legacy function name for backward compatibility
def create_unified_rag_chain(llm, vector_store=None, schema_retriever=None, chat_id: Optional[int] = None):
    """Legacy wrapper for create_sql_rag_chain"""
    return create_sql_rag_chain(llm, chat_id)

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
        
        yield "\n\n Processing response...\n"
        
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