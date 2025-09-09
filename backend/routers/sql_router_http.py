# routers/sql_router_http.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.db import get_db1
from agents.sqlagent_invocation_http import (
    invoke_http_sql_agent,
    stream_http_sql_agent,
    get_http_agent_schema,
    get_http_agent_tables,
    get_http_agent_table_info,
    execute_http_agent_raw_sql,
    http_agent_health_check
)
from services.initialise_sql_llm_http import (
    get_sql_service_http,
    execute_sql_query_http,
    get_query_results_http
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models
class SQLQueryRequest(BaseModel):
    question: str
    database_name: Optional[str] = None
    chat_id: Optional[int] = None

class RawSQLRequest(BaseModel):
    query: str
    database_name: Optional[str] = None

class DatabaseRequest(BaseModel):
    database_name: Optional[str] = None

class TableInfoRequest(BaseModel):
    table_name: str
    database_name: Optional[str] = None

# API Endpoints

@router.post("/generate-query")
async def generate_and_execute_query(request: SQLQueryRequest, db: Session = Depends(get_db1)):
    """
    Generate SQL query from natural language and execute it using HTTP MCP, or return HTML response.
    Returns query results with CSV file path for SQL, or HTML content for informational queries.
    Database 1 connection is available for direct SQL operations if needed.
    """
    try:
        logger.info(f"Processing query through HTTP SQL Agent: {request.question}")
        
        result = await invoke_http_sql_agent(
            question=request.question,
            database_name=request.database_name,
            chat_id=request.chat_id
        )
        
        if result.get("success", False):
            if result.get("response_type") == "sql":
                # SQL query was executed
                return {
                    "status": "success",
                    "response_type": "sql",
                    "question": result["question"],
                    "sql_query": result["sql_query"],
                    "execution_result": result["execution_result"],
                    "csv_file": result.get("csv_file"),
                    "message": "SQL query generated and executed successfully via HTTP MCP",
                    "mcp_type": "http",
                    "database_connection": "active"
                }
            elif result.get("response_type") == "html":
                # HTML response was generated
                return HTMLResponse(
                    content=result["html_content"],
                    status_code=200
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown response type: {result.get('response_type')}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Query processing failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error in generate_and_execute_query (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream-query")
async def stream_query_generation(request: SQLQueryRequest, db: Session = Depends(get_db1)):
    """
    Stream SQL query generation and execution process using HTTP MCP, or HTML response generation.
    Returns a streaming response with real-time updates.
    Database 1 connection is available for direct SQL operations if needed.
    """
    try:
        logger.info(f"Streaming query processing (HTTP) for: {request.question}")
        
        async def generate():
            try:
                async for chunk in stream_http_sql_agent(
                    question=request.question,
                    database_name=request.database_name,
                    chat_id=request.chat_id
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream_query_generation (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-raw")
async def execute_raw_sql(request: RawSQLRequest, db: Session = Depends(get_db1)):
    """
    Execute a raw SQL query without LLM generation using HTTP MCP.
    Returns query results and CSV file path.
    Uses Database 1 connection for SQL execution.
    """
    try:
        logger.info(f"Executing raw SQL (HTTP): {request.query[:100]}...")
        
        result = await execute_http_agent_raw_sql(
            query=request.query,
            database_name=request.database_name
        )
        
        if "error" not in result:
            return {
                "status": "success",
                "query": request.query,
                "result": result,
                "message": "Raw SQL executed successfully via HTTP MCP",
                "mcp_type": "http",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"SQL execution failed: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in execute_raw_sql (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schema")
async def get_database_schema(request: DatabaseRequest, db: Session = Depends(get_db1)):
    """
    Get database schema information including tables, columns, and relationships using HTTP MCP.
    Uses Database 1 connection for schema retrieval.
    """
    try:
        logger.info(f"Getting schema (HTTP) for database: {request.database_name or 'default'}")
        
        schema = await get_http_agent_schema(database_name=request.database_name)
        
        if "error" not in schema:
            return {
                "status": "success",
                "database_name": request.database_name or "default",
                "schema": schema,
                "message": "Schema retrieved successfully via HTTP MCP",
                "mcp_type": "http",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get schema: {schema['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in get_database_schema (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-query")
async def process_agent_query(request: SQLQueryRequest, db: Session = Depends(get_db1)):
    """
    Process query through HTTP SQL Agent and return JSON response indicating query type and content.
    Returns structured response with SQL query or HTML content.
    Uses Database 1 connection for SQL operations.
    """
    try:
        logger.info(f"Processing agent query (HTTP): {request.question}")
        
        result = await invoke_http_sql_agent(
            question=request.question,
            database_name=request.database_name,
            chat_id=request.chat_id
        )
        
        return {
            "status": "success" if result.get("success", False) else "error",
            "question": result["question"],
            "response_type": result.get("response_type", "error"),
            "data": result,
            "message": "Query processed successfully via HTTP MCP" if result.get("success", False) else f"Error: {result.get('error', 'Unknown error')}",
            "mcp_type": "http",
            "database_connection": "active"
        }
            
    except Exception as e:
        logger.error(f"Error in process_agent_query (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tables")
async def list_database_tables(request: DatabaseRequest, db: Session = Depends(get_db1)):
    """
    List all tables in the specified database through the HTTP agent.
    Uses Database 1 connection for table listing.
    """
    try:
        logger.info(f"Listing tables (HTTP) for database: {request.database_name or 'default'}")
        
        tables_result = await get_http_agent_tables(database_name=request.database_name)
        
        if "error" not in tables_result:
            tables = tables_result.get("tables", [])
            
            return {
                "status": "success",
                "database_name": request.database_name or "default",
                "tables": tables,
                "message": "Tables listed successfully via HTTP MCP",
                "mcp_type": "http",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to list tables: {tables_result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in list_database_tables (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/table-info")
async def get_table_information(request: TableInfoRequest, db: Session = Depends(get_db1)):
    """
    Get detailed information about a specific table using HTTP MCP.
    Uses Database 1 connection for table information retrieval.
    """
    try:
        logger.info(f"Getting info (HTTP) for table: {request.table_name}")
        
        table_info = await get_http_agent_table_info(
            table_name=request.table_name,
            database_name=request.database_name
        )
        
        if "error" not in table_info:
            return {
                "status": "success",
                "table_name": request.table_name,
                "database_name": request.database_name or "default",
                "table_info": table_info,
                "message": "Table information retrieved successfully via HTTP MCP",
                "mcp_type": "http",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get table info: {table_info['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in get_table_information (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database-status")
async def check_database_status(db: Session = Depends(get_db1)):
    """
    Check the status of Database 1 connection and HTTP MCP server.
    This endpoint directly uses the Database 1 connection and checks HTTP MCP health.
    """
    try:
        logger.info("Checking Database 1 status and HTTP MCP health")
        
        # Test the database connection
        result = db.execute(text("SELECT 1 as test_connection"))
        connection_test = result.fetchone()
        
        # Get basic database information
        db_info = {}
        try:
            # Try to get database version (works for PostgreSQL)
            version_result = db.execute(text("SELECT version()"))
            db_info["version"] = version_result.fetchone()[0] if version_result else "Unknown"
        except:
            db_info["version"] = "Could not retrieve version"
        
        try:
            # Get current database name
            db_name_result = db.execute(text("SELECT current_database()"))
            db_info["database_name"] = db_name_result.fetchone()[0] if db_name_result else "Unknown"
        except:
            db_info["database_name"] = "Could not retrieve database name"
        
        # Check HTTP MCP server health
        mcp_health = await http_agent_health_check()
        
        return {
            "status": "success",
            "database_connection": "active",
            "connection_test": "passed" if connection_test else "failed",
            "database_info": db_info,
            "mcp_server_health": mcp_health,
            "mcp_type": "http",
            "message": "Database 1 is connected and HTTP MCP server is operational",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database 1 or HTTP MCP connection test failed: {e}")
        return {
            "status": "error",
            "database_connection": "failed",
            "mcp_type": "http",
            "error": str(e),
            "message": "Database 1 or HTTP MCP connection failed",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/mcp-health")
async def check_mcp_health():
    """
    Check the health of the HTTP MCP server specifically
    """
    try:
        logger.info("Checking HTTP MCP server health")
        
        health_result = await http_agent_health_check()
        
        return {
            "status": "success",
            "mcp_type": "http",
            "health": health_result,
            "message": "HTTP MCP server health check completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"HTTP MCP health check failed: {e}")
        return {
            "status": "error",
            "mcp_type": "http",
            "error": str(e),
            "message": "HTTP MCP server health check failed",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/results")
async def get_query_result_files():
    """
    Get list of generated CSV files from query executions (HTTP version).
    """
    try:
        logger.info("Getting list of query result files (HTTP)")
        
        csv_files = get_query_results_http()
        
        return {
            "status": "success",
            "files": csv_files,
            "count": len(csv_files),
            "mcp_type": "http",
            "message": "Query result files retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in get_query_result_files (HTTP): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{filename}")
async def download_csv_file(filename: str):
    """
    Download a specific CSV file generated from query execution.
    """
    try:
        logger.info(f"Downloading CSV file: {filename}")
        
        filepath = os.path.join("datasets", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="text/csv"
        )
        
    except Exception as e:
        logger.error(f"Error in download_csv_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{filename}/preview")
async def preview_csv_file(filename: str, rows: int = 100):
    """
    Preview contents of a CSV file without downloading.
    """
    try:
        logger.info(f"Previewing CSV file: {filename}")
        
        import pandas as pd
        
        filepath = os.path.join("datasets", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read CSV file
        df = pd.read_csv(filepath)
        
        # Limit rows
        preview_df = df.head(rows)
        
        preview_data = {
            "columns": list(df.columns),
            "data": preview_df.to_dict(orient="records"),
            "total_rows": len(df),
            "preview_rows": len(preview_df),
            "truncated": len(df) > rows
        }
        
        return {
            "status": "success",
            "filename": filename,
            "preview": preview_data,
            "mcp_type": "http",
            "message": f"CSV file preview (first {rows} rows)"
        }
            
    except Exception as e:
        logger.error(f"Error in preview_csv_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint for HTTP SQL service and agent.
    """
    try:
        # Check the HTTP SQL agent
        health_result = await http_agent_health_check()
        
        return {
            "status": "healthy",
            "service": "HTTP SQL Agent Service",
            "mcp_type": "http",
            "agent_health": health_result,
            "timestamp": datetime.now().isoformat(),
            "message": "HTTP SQL agent service is running"
        }
        
    except Exception as e:
        logger.error(f"Health check failed (HTTP): {e}")
        return {
            "status": "unhealthy",
            "service": "HTTP SQL Agent Service",
            "mcp_type": "http", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
