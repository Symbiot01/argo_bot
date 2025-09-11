# agents/sqlagent_invocation_http.py

import logging
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from services.initialise_sql_llm_http import (
    initialize_sql_llm_and_embeddings_http,
    create_sql_rag_chain_http,
    execute_sql_with_context_http,
    astream_sql_response_http
)
import config

class HTTPSQLAgent:
    """HTTP-based SQL Agent for handling unified SQL and HTML responses"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.http_mcp_client = None
        self.sql_chain = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the HTTP SQL agent with all required components"""
        try:
            if self.is_initialized:
                return True
                
            logging.info("Initializing HTTP SQL Agent...")
            
            # Initialize LLM, embeddings, and HTTP MCP client
            self.llm, self.embeddings, self.http_mcp_client = initialize_sql_llm_and_embeddings_http()
            
            # Connect to HTTP MCP server
            connected = await self.http_mcp_client.connect()
            if not connected:
                raise Exception("Failed to connect to HTTP MCP server")
            
            # Create SQL RAG chain (no vector store needed)
            self.sql_chain = create_sql_rag_chain_http(self.llm)
            
            self.is_initialized = True
            logging.info("HTTP SQL Agent initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize HTTP SQL Agent: {e}")
            raise
    
    async def process_query(self, question: str, database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a query and return appropriate response (SQL execution or HTML)
        
        Args:
            question: User's natural language question
            database_name: Target database name (optional)
            chat_id: Chat ID for conversation context (optional)
            
        Returns:
            Dict containing response data
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Create SQL chain with chat context if provided
            if chat_id:
                sql_chain = create_sql_rag_chain_http(self.llm, chat_id)
            else:
                sql_chain = self.sql_chain
            
            # Execute SQL query processing
            result = await execute_sql_with_context_http(
                sql_chain,
                self.http_mcp_client,
                question,
                database_name,
                chat_id
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error processing query in HTTP SQL Agent: {e}")
            logging.exception(e)
            return {
                "question": question,
                "error": str(e),
                "success": False,
                "response_type": "error",
                "chat_id": chat_id
            }
    
    async def stream_query(self, question: str, database_name: str = None, chat_id: Optional[int] = None):
        """
        Stream the query processing with real-time updates
        
        Args:
            question: User's natural language question
            database_name: Target database name (optional)
            chat_id: Chat ID for conversation context (optional)
            
        Yields:
            str: Streaming response chunks
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Create SQL chain with chat context if provided
            if chat_id:
                sql_chain = create_sql_rag_chain_http(self.llm, chat_id)
            else:
                sql_chain = self.sql_chain
            
            # Stream SQL response processing
            async for chunk in astream_sql_response_http(
                sql_chain,
                self.http_mcp_client,
                question,
                database_name,
                chat_id
            ):
                yield chunk
                
        except Exception as e:
            yield f"Error in HTTP SQL Agent streaming: {str(e)}\n"
    
    async def get_database_schema(self, database_name: str = None) -> Dict[str, Any]:
        """
        Get database schema information
        
        Args:
            database_name: Target database name (optional)
            
        Returns:
            Dict containing schema information
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            return await self.http_mcp_client.get_database_schema(database_name)
            
        except Exception as e:
            logging.error(f"Error getting database schema: {e}")
            return {"error": str(e)}
    
    async def list_tables(self, database_name: str = None) -> Dict[str, Any]:
        """
        List all tables in the specified database
        
        Args:
            database_name: Target database name (optional)
            
        Returns:
            Dict containing list of tables
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            return await self.http_mcp_client.list_tables(database_name)
            
        except Exception as e:
            logging.error(f"Error listing tables: {e}")
            return {"error": str(e)}
    
    async def get_table_info(self, table_name: str, database_name: str = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific table
        
        Args:
            table_name: Name of the table
            database_name: Target database name (optional)
            
        Returns:
            Dict containing table information
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            return await self.http_mcp_client.get_table_info(table_name, database_name)
            
        except Exception as e:
            logging.error(f"Error getting table info: {e}")
            return {"error": str(e)}
    
    async def execute_raw_sql(self, query: str, database_name: str = None) -> Dict[str, Any]:
        """
        Execute a raw SQL query without LLM processing
        
        Args:
            query: SQL query to execute
            database_name: Target database name (optional)
            
        Returns:
            Dict containing query results
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            return await self.http_mcp_client.execute_sql_query(query, database_name)
            
        except Exception as e:
            logging.error(f"Error executing raw SQL: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the HTTP MCP connection
        
        Returns:
            Dict containing health status
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            health_result = await self.http_mcp_client.health_check()
            
            return {
                "agent_status": "healthy" if self.is_initialized else "not_initialized",
                "mcp_server_status": health_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error in health check: {e}")
            return {
                "agent_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_user_query(self, user_input: str, chat_id: Optional[str] = None, 
                                argo_context: Optional[str] = "") -> Dict[str, Any]:
        """
        Process user query and return formatted response for combined pipeline
        
        Args:
            user_input: User's natural language question
            chat_id: Chat ID for conversation context (optional)
            argo_context: Argo domain context (optional)
            
        Returns:
            Dict containing formatted response for combined pipeline
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Convert chat_id to int if provided
            chat_id_int = None
            if chat_id:
                try:
                    chat_id_int = int(chat_id)
                except (ValueError, TypeError):
                    logging.warning(f"Invalid chat_id format: {chat_id}")
            
            # Process the query
            result = await self.process_query(
                question=user_input,
                database_name=None,  # Use default database
                chat_id=chat_id_int
            )

            # print(f"SQL Agent Result: {json.dumps(result, indent=2)}")
            
            # Format response for combined pipeline
            if result.get("success", False):
                if result.get("response_type") == "sql":

                    print(f"SQL Query: {result.get('sql_query')}")
                    # SQL query was executed
                    return {
                        "success": True,
                        "response": "SQL query executed successfully",
                        "sql_query": result.get("sql_query"),
                        "data": result.get("execution_result", {}).get("data", []),
                        "csv_file": result.get("csv_file"),
                        "response_type": "sql"
                    }
                elif result.get("response_type") == "html":
                    # HTML response was generated
                    return {
                        "success": True,
                        "response": result.get("html_content", ""),
                        "response_type": "html"
                    }
                else:
                    # Other response type
                    return {
                        "success": True,
                        "response": str(result.get("response", "")),
                        "response_type": "text"
                    }
            else:
                # Error occurred
                return {
                    "success": False,
                    "response": result.get("error", "An error occurred"),
                    "error_message": result.get("error"),
                    "response_type": "error"
                }
                
        except Exception as e:
            logging.error(f"Error in process_user_query: {e}")
            return {
                "success": False,
                "response": f"An error occurred: {str(e)}",
                "error_message": str(e),
                "response_type": "error"
            }

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.http_mcp_client:
                await self.http_mcp_client.disconnect()
            logging.info("HTTP SQL Agent cleanup completed")
        except Exception as e:
            logging.error(f"Error during HTTP SQL Agent cleanup: {e}")

# Global HTTP SQL Agent instance
http_sql_agent = HTTPSQLAgent()

async def invoke_http_sql_agent(question: str, database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to invoke the HTTP SQL agent
    
    Args:
        question: User's natural language question
        database_name: Target database name (optional)
        chat_id: Chat ID for conversation context (optional)
        
    Returns:
        Dict containing response data
    """
    return await http_sql_agent.process_query(question, database_name, chat_id)

async def stream_http_sql_agent(question: str, database_name: str = None, chat_id: Optional[int] = None):
    """
    Convenience function to stream HTTP SQL agent responses
    
    Args:
        question: User's natural language question
        database_name: Target database name (optional)
        chat_id: Chat ID for conversation context (optional)
        
    Yields:
        str: Streaming response chunks
    """
    async for chunk in http_sql_agent.stream_query(question, database_name, chat_id):
        yield chunk

async def get_http_agent_schema(database_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to get database schema through the HTTP agent
    
    Args:
        database_name: Target database name (optional)
        
    Returns:
        Dict containing schema information
    """
    return await http_sql_agent.get_database_schema(database_name)

async def get_http_agent_tables(database_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to list tables through the HTTP agent
    
    Args:
        database_name: Target database name (optional)
        
    Returns:
        Dict containing list of tables
    """
    return await http_sql_agent.list_tables(database_name)

async def get_http_agent_table_info(table_name: str, database_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to get table info through the HTTP agent
    
    Args:
        table_name: Name of the table
        database_name: Target database name (optional)
        
    Returns:
        Dict containing table information
    """
    return await http_sql_agent.get_table_info(table_name, database_name)

async def execute_http_agent_raw_sql(query: str, database_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to execute raw SQL through the HTTP agent
    
    Args:
        query: SQL query to execute
        database_name: Target database name (optional)
        
    Returns:
        Dict containing query results
    """
    return await http_sql_agent.execute_raw_sql(query, database_name)

async def http_agent_health_check() -> Dict[str, Any]:
    """
    Convenience function to check HTTP agent health
    
    Returns:
        Dict containing health status
    """
    return await http_sql_agent.health_check()

# For backward compatibility - these functions can be used to replace the old stdio-based ones
async def invoke_sql_agent_http(question: str, database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """Alias for invoke_http_sql_agent for backward compatibility"""
    return await invoke_http_sql_agent(question, database_name, chat_id)

async def stream_sql_agent_http(question: str, database_name: str = None, chat_id: Optional[int] = None):
    """Alias for stream_http_sql_agent for backward compatibility"""
    async for chunk in stream_http_sql_agent(question, database_name, chat_id):
        yield chunk

async def get_agent_schema_http(database_name: str = None) -> Dict[str, Any]:
    """Alias for get_http_agent_schema for backward compatibility"""
    return await get_http_agent_schema(database_name)
