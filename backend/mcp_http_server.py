# mcp_http_server.py

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Import database configuration from local config
from config import DATABASE_URL, USER_DATABASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTTPSQLMCPServer:
    """HTTP-based MCP Server for SQL database operations using JSON-RPC"""
    
    def __init__(self):
        self.app = FastAPI(title="MCP SQL Server", description="HTTP MCP Server for SQL operations")
        self.database_connections = {}
        self.setup_routes()
        self.setup_error_handlers()
    
    def setup_error_handlers(self):
        """Setup error handlers for the FastAPI app"""
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(exc)
                    }
                }
            )
    
    def setup_routes(self):
        """Setup HTTP routes for MCP operations"""
        
        @self.app.post("/mcp")
        async def handle_jsonrpc(request: Request):
            """Handle JSON-RPC requests for MCP operations"""
            try:
                body = await request.json()
                return await self.process_jsonrpc_request(body)
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                )
        
        @self.app.get("/mcp/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server": "MCP SQL Server",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """List available MCP tools"""
            return {
                "tools": [
                    {
                        "name": "execute_sql_query",
                        "description": "Execute SQL query on specified database and return results",
                        "parameters": {
                            "query": {"type": "string", "description": "SQL query to execute"},
                            "database_name": {"type": "string", "description": "Name of the database to query", "default": "default"}
                        }
                    },
                    {
                        "name": "get_database_schema",
                        "description": "Get database schema information including tables, columns, and relationships",
                        "parameters": {
                            "database_name": {"type": "string", "description": "Name of the database", "default": "default"}
                        }
                    },
                    {
                        "name": "list_tables",
                        "description": "List all tables in the specified database",
                        "parameters": {
                            "database_name": {"type": "string", "description": "Name of the database", "default": "default"}
                        }
                    },
                    {
                        "name": "get_table_info",
                        "description": "Get detailed information about a specific table",
                        "parameters": {
                            "table_name": {"type": "string", "description": "Name of the table"},
                            "database_name": {"type": "string", "description": "Name of the database", "default": "default"}
                        }
                    }
                ]
            }
    
    async def process_jsonrpc_request(self, request_data: Dict[str, Any]) -> JSONResponse:
        """Process JSON-RPC request and return appropriate response"""
        try:
            # Validate JSON-RPC format
            if request_data.get("jsonrpc") != "2.0":
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_data.get("id"),
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request"
                        }
                    }
                )
            
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            # Route to appropriate method
            if method == "execute_sql_query":
                result = await self.execute_sql_query(**params)
            elif method == "get_database_schema":
                result = await self.get_database_schema(**params)
            elif method == "list_tables":
                result = await self.list_tables(**params)
            elif method == "get_table_info":
                result = await self.get_table_info(**params)
            elif method == "initialize":
                result = await self.initialize()
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": "Method not found"
                        }
                    }
                )
            
            # Check if result contains an error
            if isinstance(result, dict) and "error" in result:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": result["error"]
                        }
                    }
                )
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing JSON-RPC request: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_data.get("id"),
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
            )
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP server and database connections"""
        try:
            await self.initialize_connections()
            logger.info("MCP SQL Server initialized successfully")
            return {
                "status": "initialized",
                "message": "MCP SQL Server ready",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error initializing MCP server: {e}")
            return {"error": str(e)}
    
    async def initialize_connections(self):
        """Initialize database connections at startup"""
        try:
            # Initialize PostgreSQL connection (database1)
            await self.get_database_connection("database1")
            # Initialize SQLite connection (database2)
            await self.get_database_connection("database2")
            logger.info("Database connections initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database connections: {e}")
    
    async def get_database_connection(self, database_name: str):
        """Get or create database connection"""
        try:
            if database_name in self.database_connections:
                return self.database_connections[database_name]
            
            # Map database names to actual database URLs
            if database_name in ["default", "postgres", "sih_data", "main"]:
                # Use the main PostgreSQL database (database1)
                engine = create_engine(DATABASE_URL)
                self.database_connections[database_name] = engine
                logger.info(f"Connected to PostgreSQL database: {database_name}")
                return engine
            elif database_name in ["user_db", "database2", "users"]:
                # Use the user SQLite database (database2)
                engine = create_engine(USER_DATABASE_URL)
                self.database_connections[database_name] = engine
                logger.info(f"Connected to SQLite database: {database_name}")
                return engine
            else:
                logger.error(f"Unknown database name: {database_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating database connection: {e}")
            return None
    
    async def execute_sql_query(self, query: str, database_name: str = "default") -> Dict[str, Any]:
        """
        Execute SQL query on specified database and return results.
        
        Args:
            query: SQL query to execute
            database_name: Name of the database to query
        
        Returns:
            Dictionary containing query results, row count, and metadata
        """
        try:
            logger.info(f"Executing SQL query on database '{database_name}': {query}")
            
            # Get database connection
            connection = await self.get_database_connection(database_name)
            if not connection:
                return {"error": f"Failed to connect to database '{database_name}'"}
            
            # Execute query based on database type
            if database_name in ["default", "postgres", "database1", "main"]:
                # PostgreSQL database
                result = await self.execute_postgres_query(connection, query)
            elif database_name in ["user_db", "database2", "users"]:
                # SQLite database
                result = await self.execute_generic_query(connection, query)
            else:
                # Try to detect database type from connection string
                if "postgresql" in str(connection.url).lower():
                    result = await self.execute_postgres_query(connection, query)
                else:
                    result = await self.execute_generic_query(connection, query)
            
            # Save results to CSV
            if result.get("data") and len(result["data"]) > 0:
                csv_path = await self.save_results_to_csv(result["data"], query)
                result["csv_file"] = csv_path

            del result['data']

            print(f"SQL Query Execution Result: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return {"error": str(e)}
    
    async def get_database_schema(self, database_name: str = "default") -> Dict[str, Any]:
        """
        Get database schema information including tables, columns, and relationships.
        
        Args:
            database_name: Name of the database
        
        Returns:
            Dictionary containing complete database schema
        """
        try:
            logger.info(f"Getting schema for database '{database_name}'")
            
            connection = await self.get_database_connection(database_name)
            if not connection:
                return {"error": f"Failed to connect to database '{database_name}'"}
            
            schema = await self.extract_database_schema(connection, database_name)
            return schema
            
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return {"error": str(e)}
    
    async def list_tables(self, database_name: str = "default") -> Dict[str, Any]:
        """
        List all tables in the specified database.
        
        Args:
            database_name: Name of the database
        
        Returns:
            Dictionary containing list of tables
        """
        try:
            connection = await self.get_database_connection(database_name)
            if not connection:
                return {"error": f"Failed to connect to database '{database_name}'"}
            
            tables = await self.get_table_list(connection, database_name)
            return {"tables": tables}
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return {"error": str(e)}
    
    async def get_table_info(self, table_name: str, database_name: str = "default") -> Dict[str, Any]:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table
            database_name: Name of the database
        
        Returns:
            Dictionary containing table structure and metadata
        """
        try:
            connection = await self.get_database_connection(database_name)
            if not connection:
                return {"error": f"Failed to connect to database '{database_name}'"}
            
            table_info = await self.get_table_details(connection, table_name, database_name)
            return table_info
            
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {"error": str(e)}
    
    async def execute_postgres_query(self, engine, query: str) -> Dict[str, Any]:
        """Execute query on PostgreSQL database"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query))

                print(f"Raw SQLAlchemy Result: {result}")
                
                if result.returns_rows:
                    # Fetch all results
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Convert to list of dictionaries
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    return {
                        "data": data,
                        "row_count": len(data),
                        "columns": list(columns),
                        "query": query,
                        "success": True
                    }
                else:
                    # For non-SELECT queries (INSERT, UPDATE, DELETE)
                    return {
                        "message": "Query executed successfully",
                        "rows_affected": result.rowcount,
                        "query": query,
                        "success": True
                    }
                    
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error: {e}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e), "success": False}
    
    async def execute_generic_query(self, engine, query: str) -> Dict[str, Any]:
        """Execute query on generic database"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query))
                
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    return {
                        "data": data,
                        "row_count": len(data),
                        "columns": list(columns),
                        "query": query,
                        "success": True
                    }
                else:
                    return {
                        "message": "Query executed successfully",
                        "rows_affected": result.rowcount,
                        "query": query,
                        "success": True
                    }
                    
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e), "success": False}
    
    async def extract_database_schema(self, engine, database_name: str) -> Dict[str, Any]:
        """Extract complete database schema"""
        try:
            inspector = inspect(engine)
            schema = {
                "database_name": database_name,
                "tables": {},
                "query_examples": []
            }
            
            # Get all tables
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                table_info = {
                    "description": f"Table {table_name}",
                    "columns": {},
                    "indexes": [],
                    "foreign_keys": [],
                    "primary_keys": []
                }
                
                # Get columns
                columns = inspector.get_columns(table_name)
                for column in columns:
                    table_info["columns"][column["name"]] = {
                        "type": str(column["type"]),
                        "nullable": column["nullable"],
                        "default": column.get("default"),
                        "primary_key": column.get("primary_key", False)
                    }
                
                # Get foreign keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                for fk in foreign_keys:
                    table_info["foreign_keys"].append({
                        "columns": fk["constrained_columns"],
                        "refers_to": f"{fk['referred_table']}.{fk['referred_columns']}"
                    })
                
                # Get indexes
                indexes = inspector.get_indexes(table_name)
                for idx in indexes:
                    table_info["indexes"].append({
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx["unique"]
                    })
                
                # Get primary key
                pk = inspector.get_pk_constraint(table_name)
                if pk and pk["constrained_columns"]:
                    table_info["primary_keys"] = pk["constrained_columns"]
                
                schema["tables"][table_name] = table_info
            
            return schema
            
        except Exception as e:
            logger.error(f"Error extracting schema: {e}")
            return {"error": str(e)}
    
    async def get_table_list(self, engine, database_name: str) -> List[str]:
        """Get list of all tables"""
        try:
            inspector = inspect(engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    async def get_table_details(self, engine, table_name: str, database_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        try:
            inspector = inspect(engine)
            
            table_info = {
                "table_name": table_name,
                "database": database_name,
                "columns": {},
                "sample_data": []
            }
            
            # Get column information
            columns = inspector.get_columns(table_name)
            for column in columns:
                table_info["columns"][column["name"]] = {
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "default": column.get("default")
                }
            
            # Get sample data (first 5 rows)
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                rows = result.fetchall()
                columns = result.keys()
                
                for row in rows:
                    table_info["sample_data"].append(dict(zip(columns, row)))
            
            return table_info
            
        except Exception as e:
            logger.error(f"Error getting table details: {e}")
            return {"error": str(e)}
    
    async def save_results_to_csv(self, data: List[Dict], query: str) -> str:
        """Save query results to CSV file"""
        try:
            # Create datasets directory if it doesn't exist
            os.makedirs("datasets", exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_result_{timestamp}.csv"
            filepath = os.path.join("datasets", filename)
            
            # Convert to DataFrame and save
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)
            
            logger.info(f"Query results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results to CSV: {e}")
            return None
    
    def get_app(self) -> FastAPI:
        """Return the FastAPI app instance"""
        return self.app

# Global server instance
http_mcp_server = HTTPSQLMCPServer()

async def start_http_mcp_server(host: str = "127.0.0.1", port: int = 8001):
    """Start the HTTP MCP server"""
    logger.info(f"Starting HTTP MCP Server on {host}:{port}")
    config = uvicorn.Config(http_mcp_server.get_app(), host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_http_mcp_server())
