# agents/sqlagent_invocation.py

import logging
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from services.initialise_sql_llm import (
    initialize_sql_llm_and_embeddings,
    create_sql_rag_chain,
    execute_sql_with_context,
    astream_sql_response
)
from services.initialise_sql_vector_db import initialize_vector_store
import config

class SQLAgent:
    """SQL Agent for handling unified SQL and HTML responses"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.mcp_client = None
        self.vector_store = None
        self.sql_chain = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the SQL agent with all required components"""
        try:
            if self.is_initialized:
                return True
                
            logging.info("Initializing SQL Agent...")
            
            # Initialize LLM, embeddings, and MCP client
            self.llm, self.embeddings, self.mcp_client = initialize_sql_llm_and_embeddings()
            
            # Connect to MCP server
            await self.mcp_client.connect()
            
            # Initialize vector store (without schema retriever)
            self.vector_store = await initialize_vector_store(self.embeddings)
            
            # Create SQL RAG chain without schema retriever
            self.sql_chain = create_sql_rag_chain(self.llm, self.vector_store)
            
            self.is_initialized = True
            logging.info("SQL Agent initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize SQL Agent: {e}")
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
                sql_chain = create_sql_rag_chain(self.llm, self.vector_store, chat_id)
            else:
                sql_chain = self.sql_chain
            
            # Execute SQL query processing
            result = await execute_sql_with_context(
                sql_chain,
                self.mcp_client,
                question,
                database_name,
                chat_id
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error processing query in SQL Agent: {e}")
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
                sql_chain = create_sql_rag_chain(self.llm, self.vector_store, chat_id)
            else:
                sql_chain = self.sql_chain
            
            # Stream SQL response processing
            async for chunk in astream_sql_response(
                sql_chain,
                self.mcp_client,
                question,
                database_name,
                chat_id
            ):
                yield chunk
                
        except Exception as e:
            yield f"Error in SQL Agent streaming: {str(e)}\n"
    
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
            
            return await self.mcp_client.get_database_schema(database_name)
            
        except Exception as e:
            logging.error(f"Error getting database schema: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.mcp_client:
                await self.mcp_client.disconnect()
            logging.info("SQL Agent cleanup completed")
        except Exception as e:
            logging.error(f"Error during SQL Agent cleanup: {e}")

# Global SQL Agent instance
sql_agent = SQLAgent()

async def invoke_sql_agent(question: str, database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to invoke the SQL agent
    
    Args:
        question: User's natural language question
        database_name: Target database name (optional)
        chat_id: Chat ID for conversation context (optional)
        
    Returns:
        Dict containing response data
    """
    return await sql_agent.process_query(question, database_name, chat_id)

async def stream_sql_agent(question: str, database_name: str = None, chat_id: Optional[int] = None):
    """
    Convenience function to stream SQL agent responses
    
    Args:
        question: User's natural language question
        database_name: Target database name (optional)
        chat_id: Chat ID for conversation context (optional)
        
    Yields:
        str: Streaming response chunks
    """
    async for chunk in sql_agent.stream_query(question, database_name, chat_id):
        yield chunk

async def get_agent_schema(database_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to get database schema through the agent
    
    Args:
        database_name: Target database name (optional)
        
    Returns:
        Dict containing schema information
    """
    return await sql_agent.get_database_schema(database_name)
