# mcp_server.py

import asyncio
import logging
import json
import os
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent,
    CallToolRequest,
  
)

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

class SQLMCPServer:
    """MCP Server for SQL database operations"""
    
    def __init__(self):
        self.server = FastMCP("SQL Database Server")
        self.database_connections = {}
        self.setup_tools()
        self.setup_resources()
    
    def setup_tools(self):
        """Setup MCP tools for SQL operations"""
        
        @self.server.tool()
        async def execute_sql_query(query: str, database_name: str = "default") -> Dict[str, Any]:
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
                
                return result
                
            except Exception as e:
                logger.error(f"Error executing SQL query: {e}")
                return {"error": str(e)}
        
        @self.server.tool()
        async def get_database_schema(database_name: str = "default") -> Dict[str, Any]:
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
        
        @self.server.tool()
        async def list_tables(database_name: str = "default") -> Dict[str, Any]:
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
        
        @self.server.tool()
        async def get_table_info(table_name: str, database_name: str = "default") -> Dict[str, Any]:
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
    
    def setup_resources(self):
        """Setup MCP resources"""
        
        @self.server.resource("database://config")
        async def database_config() -> Resource:
            """Database configuration resource"""
            config_data = {
                "databases": {
                    "database1": {
                        "type": "postgresql",
                        "url": DATABASE_URL,
                        "description": "Main PostgreSQL database for predefined structure and data"
                    },
                    "database2": {
                        "type": "sqlite",
                        "url": USER_DATABASE_URL,
                        "description": "SQLite database for user data, chat, and messages"
                    }
                },
                "default_database": "database1",
                "available_aliases": {
                    "database1": ["default", "postgres", "main"],
                    "database2": ["user_db", "users"]
                }
            }
            
            return Resource(
                uri="database://config",
                name="Database Configuration",
                description="Current database connections and settings",
                mimeType="application/json"
            )
    
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
            if database_name in ["default", "postgres", "database1", "main"]:
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
    
    async def load_database_config(self, database_name: str) -> Dict[str, Any]:
        """Load database configuration from config file or environment"""
        try:
            # Return configuration based on database name
            if database_name in ["default", "postgres", "database1", "main"]:
                return {
                    "type": "postgresql",
                    "url": DATABASE_URL,
                    "name": "PostgreSQL Database (database1)"
                }
            elif database_name in ["user_db", "database2", "users"]:
                return {
                    "type": "sqlite",
                    "url": USER_DATABASE_URL,
                    "name": "SQLite User Database (database2)"
                }
            
            # Try to load from mcp_config.json as fallback
            config_path = "mcp_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if "databases" in config and database_name in config["databases"]:
                        return config["databases"][database_name]
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading database config: {e}")
            return None
    
    async def execute_postgres_query(self, engine, query: str) -> Dict[str, Any]:
        """Execute query on PostgreSQL database"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query))
                
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
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting SQL MCP Server...")
        # Initialize database connections
        await self.initialize_connections()
        await self.server.run()

# Main execution
async def main():
    server = SQLMCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
        # If we get here, there's already a running loop
        # Create a task to run main
        asyncio.create_task(main())
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        asyncio.run(main())
