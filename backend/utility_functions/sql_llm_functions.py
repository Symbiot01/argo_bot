# utility_functions/sql_llm_functions.py

import logging
import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from services.initialise_sql_llm import (
    initialize_sql_llm_and_embeddings,
    create_sql_rag_chain,
    execute_sql_with_context,
    astream_sql_response
)

class SQLLLMService:
    """Service class for SQL LLM operations with MCP client integration"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.mcp_client = None
        self.rag_chain = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all components of the SQL LLM service"""
        try:
            logging.info("Initializing SQL LLM service...")
            
            # Initialize LLM, embeddings, and MCP client
            self.llm, self.embeddings, self.mcp_client = initialize_sql_llm_and_embeddings()
            
            # Connect to MCP server
            connection_success = await self.mcp_client.connect()
            if not connection_success:
                raise Exception("Failed to connect to MCP server")
            
            # Create RAG chain for SQL generation (no vector store needed)
            self.rag_chain = create_sql_rag_chain(self.llm)
            
            self.initialized = True
            logging.info("SQL LLM service initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize SQL LLM service: {e}")
            raise
    
    async def generate_and_execute_sql(self, question: str, database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate SQL query from natural language and execute it
        
        Args:
            question: Natural language question
            database_name: Target database name
            chat_id: Chat ID for conversation context
        
        Returns:
            Dictionary containing query, results, and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create RAG chain with chat context if provided
            if chat_id:
                rag_chain = create_sql_rag_chain(self.llm, chat_id)
            else:
                rag_chain = self.rag_chain
            
            result = await execute_sql_with_context(
                rag_chain,
                self.mcp_client,
                question,
                database_name,
                chat_id
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error in SQL generation and execution: {e}")
            return {
                "question": question,
                "error": str(e),
                "success": False,
                "chat_id": chat_id
            }
    
    async def stream_sql_response(self, question: str, database_name: str = None, chat_id: Optional[int] = None):
        """
        Stream SQL query generation and execution results
        
        Args:
            question: Natural language question
            database_name: Target database name
            chat_id: Chat ID for conversation context
        
        Yields:
            String chunks of the response
        """
        if not self.initialized:
            await self.initialize()
        
        # Create RAG chain with chat context if provided
        if chat_id:
            rag_chain = create_sql_rag_chain(self.llm, chat_id)
        else:
            rag_chain = self.rag_chain
        
        async for chunk in astream_sql_response(
            rag_chain,
            self.mcp_client,
            question,
            database_name,
            chat_id
        ):
            yield chunk
    
    async def get_database_schema(self, database_name: str = None) -> Dict[str, Any]:
        """Get database schema information"""
        if not self.initialized:
            await self.initialize()
        
        try:
            schema = await self.mcp_client.get_database_schema(database_name)
            return schema
        except Exception as e:
            logging.error(f"Error getting database schema: {e}")
            return {"error": str(e)}
    
    async def execute_raw_sql(self, query: str, database_name: str = None) -> Dict[str, Any]:
        """Execute raw SQL query without LLM generation"""
        if not self.initialized:
            await self.initialize()
        
        try:
            result = await self.mcp_client.execute_sql_query(query, database_name)
            return result
        except Exception as e:
            logging.error(f"Error executing raw SQL: {e}")
            return {"error": str(e)}
    
    async def get_table_info(self, table_name: str, database_name: str = None) -> Dict[str, Any]:
        """Get information about a specific table"""
        if not self.initialized:
            await self.initialize()
        
        try:
            if not self.mcp_client.session:
                await self.mcp_client.connect()
            
            result = await self.mcp_client.session.call_tool(
                "get_table_info",
                arguments={
                    "table_name": table_name,
                    "database_name": database_name or "default"
                }
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting table info: {e}")
            return {"error": str(e)}
    
    async def list_tables(self, database_name: str = None) -> Dict[str, Any]:
        """List all tables in the database"""
        if not self.initialized:
            await self.initialize()
        
        try:
            if not self.mcp_client.session:
                await self.mcp_client.connect()
            
            result = await self.mcp_client.session.call_tool(
                "list_tables",
                arguments={
                    "database_name": database_name or "default"
                }
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error listing tables: {e}")
            return {"error": str(e)}
    
    def get_csv_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of generated CSV files"""
        try:
            datasets_dir = "datasets"
            if not os.path.exists(datasets_dir):
                return []
            
            csv_files = []
            files = os.listdir(datasets_dir)
            files.sort(reverse=True)  # Most recent first
            
            for filename in files[:limit]:
                if filename.endswith('.csv'):
                    filepath = os.path.join(datasets_dir, filename)
                    stat = os.stat(filepath)
                    
                    csv_files.append({
                        "filename": filename,
                        "filepath": filepath,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return csv_files
            
        except Exception as e:
            logging.error(f"Error getting CSV files: {e}")
            return []
    
    def read_csv_file(self, filename: str) -> Dict[str, Any]:
        """Read and return contents of a CSV file"""
        try:
            filepath = os.path.join("datasets", filename)
            if not os.path.exists(filepath):
                return {"error": "File not found"}
            
            df = pd.read_csv(filepath)
            
            return {
                "filename": filename,
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "data": df.head(100).to_dict('records'),  # First 100 rows
                "summary": df.describe().to_dict() if df.select_dtypes(include=['number']).shape[1] > 0 else None
            }
            
        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.mcp_client:
                await self.mcp_client.disconnect()
            logging.info("SQL LLM service cleanup completed")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

# Global service instance
_sql_service = None

async def get_sql_service() -> SQLLLMService:
    """Get or create the global SQL LLM service instance"""
    global _sql_service
    if _sql_service is None:
        _sql_service = SQLLLMService()
        await _sql_service.initialize()
    return _sql_service

# Convenience functions for direct use
async def generate_sql_query(question: str, database_name: str = None, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """Generate and execute SQL query from natural language question"""
    service = await get_sql_service()
    return await service.generate_and_execute_sql(question, database_name, chat_id)

async def stream_sql_query(question: str, database_name: str = None, chat_id: Optional[int] = None):
    """Stream SQL query generation and execution"""
    service = await get_sql_service()
    async for chunk in service.stream_sql_response(question, database_name, chat_id):
        yield chunk

async def execute_sql_query(query: str, database_name: str = None) -> Dict[str, Any]:
    """Execute raw SQL query"""
    service = await get_sql_service()
    return await service.execute_raw_sql(query, database_name)

async def get_schema_info(database_name: str = None) -> Dict[str, Any]:
    """Get database schema information"""
    service = await get_sql_service()
    return await service.get_database_schema(database_name)

async def get_tables_list(database_name: str = None) -> Dict[str, Any]:
    """Get list of database tables"""
    service = await get_sql_service()
    return await service.list_tables(database_name)

def get_query_results() -> List[Dict[str, Any]]:
    """Get list of generated query result CSV files"""
    try:
        datasets_dir = "datasets"
        if not os.path.exists(datasets_dir):
            return []
        
        csv_files = []
        for filename in os.listdir(datasets_dir):
            if filename.endswith('.csv') and filename.startswith('query_result_'):
                filepath = os.path.join(datasets_dir, filename)
                stat = os.stat(filepath)
                
                csv_files.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # Sort by creation time, most recent first
        csv_files.sort(key=lambda x: x['created'], reverse=True)
        return csv_files
        
    except Exception as e:
        logging.error(f"Error getting query results: {e}")
        return []
