# routers/sql_router.py

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
from agents.sqlagent_invocation import (
    invoke_sql_agent,
    stream_sql_agent,
    get_agent_schema
)
from utility_functions.sql_llm_functions import (
    get_sql_service,
    execute_sql_query,
    get_query_results
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
    Generate SQL query from natural language and execute it, or return HTML response.
    Returns query results with CSV file path for SQL, or HTML content for informational queries.
    Database 1 connection is available for direct SQL operations if needed.
    """
    try:
        logger.info(f"Processing query through SQL Agent: {request.question}")
        
        result = await invoke_sql_agent(
            question=request.question,
            database_name=request.database_name,
            # chat_id=request.chat_id
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
                    "message": "SQL query generated and executed successfully",
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
        logger.error(f"Error in generate_and_execute_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream-query")
async def stream_query_generation(request: SQLQueryRequest, db: Session = Depends(get_db1)):
    """
    Stream SQL query generation and execution process, or HTML response generation.
    Returns a streaming response with real-time updates.
    Database 1 connection is available for direct SQL operations if needed.
    """
    try:
        logger.info(f"Streaming query processing for: {request.question}")
        
        async def generate():
            try:
                async for chunk in stream_sql_agent(
                    question=request.question,
                    database_name=request.database_name,
                    # chat_id=request.chat_id
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
        logger.error(f"Error in stream_query_generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-raw")
async def execute_raw_sql(request: RawSQLRequest, db: Session = Depends(get_db1)):
    """
    Execute a raw SQL query without LLM generation.
    Returns query results and CSV file path.
    Uses Database 1 connection for SQL execution.
    """
    try:
        logger.info(f"Executing raw SQL: {request.query[:100]}...")
        
        result = await execute_sql_query(
            query=request.query,
            database_name=request.database_name
        )
        
        if "error" not in result:
            return {
                "status": "success",
                "query": request.query,
                "result": result,
                "message": "Raw SQL executed successfully",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"SQL execution failed: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in execute_raw_sql: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schema")
async def get_database_schema(request: DatabaseRequest, db: Session = Depends(get_db1)):
    """
    Get database schema information including tables, columns, and relationships.
    Uses Database 1 connection for schema retrieval.
    """
    try:
        logger.info(f"Getting schema for database: {request.database_name or 'default'}")
        
        schema = await get_agent_schema(database_name=request.database_name)
        
        if "error" not in schema:
            return {
                "status": "success",
                "database_name": request.database_name or "default",
                "schema": schema,
                "message": "Schema retrieved successfully",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get schema: {schema['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in get_database_schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-query")
async def process_agent_query(request: SQLQueryRequest, db: Session = Depends(get_db1)):
    """
    Process query through SQL Agent and return JSON response indicating query type and content.
    Returns structured response with SQL query or HTML content.
    Uses Database 1 connection for SQL operations.
    """
    try:
        logger.info(f"Processing agent query: {request.question}")
        
        result = await invoke_sql_agent(
            question=request.question,
            database_name=request.database_name,
            chat_id=request.chat_id
        )
        
        return {
            "status": "success" if result.get("success", False) else "error",
            "question": result["question"],
            "response_type": result.get("response_type", "error"),
            "data": result,
            "message": "Query processed successfully" if result.get("success", False) else f"Error: {result.get('error', 'Unknown error')}",
            "database_connection": "active"
        }
            
    except Exception as e:
        logger.error(f"Error in process_agent_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tables")
async def list_database_tables(request: DatabaseRequest, db: Session = Depends(get_db1)):
    """
    List all tables in the specified database through the agent.
    Uses Database 1 connection for table listing.
    """
    try:
        logger.info(f"Listing tables for database: {request.database_name or 'default'}")
        
        # Use the schema endpoint to get table information
        schema = await get_agent_schema(database_name=request.database_name)
        
        if "error" not in schema:
            # Extract table names from schema if available
            tables = []
            if isinstance(schema, dict) and "tables" in schema:
                tables = list(schema["tables"].keys()) if isinstance(schema["tables"], dict) else schema["tables"]
            
            return {
                "status": "success",
                "database_name": request.database_name or "default",
                "tables": tables,
                "message": "Tables listed successfully",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to list tables: {schema['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in list_database_tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/table-info")
async def get_table_information(request: TableInfoRequest, db: Session = Depends(get_db1)):
    """
    Get detailed information about a specific table.
    Uses Database 1 connection for table information retrieval.
    """
    try:
        logger.info(f"Getting info for table: {request.table_name}")
        
        service = await get_sql_service()
        table_info = await service.get_table_info(
            table_name=request.table_name,
            database_name=request.database_name
        )
        
        if "error" not in table_info:
            return {
                "status": "success",
                "table_name": request.table_name,
                "database_name": request.database_name or "default",
                "table_info": table_info,
                "message": "Table information retrieved successfully",
                "database_connection": "active"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get table info: {table_info['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in get_table_information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database-status")
async def check_database_status(db: Session = Depends(get_db1)):
    """
    Check the status of Database 1 connection and basic information.
    This endpoint directly uses the Database 1 connection.
    """
    try:
        logger.info("Checking Database 1 status")
        
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
        
        return {
            "status": "success",
            "database_connection": "active",
            "connection_test": "passed" if connection_test else "failed",
            "database_info": db_info,
            "message": "Database 1 is connected and operational",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database 1 connection test failed: {e}")
        return {
            "status": "error",
            "database_connection": "failed",
            "error": str(e),
            "message": "Database 1 connection failed",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/results")
async def get_query_result_files():
    """
    Get list of generated CSV files from query executions.
    """
    try:
        logger.info("Getting list of query result files")
        
        csv_files = get_query_results()
        
        return {
            "status": "success",
            "files": csv_files,
            "count": len(csv_files),
            "message": "Query result files retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in get_query_result_files: {e}")
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
        
        service = await get_sql_service()
        preview_data = service.read_csv_file(filename)
        
        if "error" not in preview_data:
            # Limit the number of rows returned
            if "data" in preview_data and len(preview_data["data"]) > rows:
                preview_data["data"] = preview_data["data"][:rows]
                preview_data["truncated"] = True
            
            return {
                "status": "success",
                "filename": filename,
                "preview": preview_data,
                "message": f"CSV file preview (first {rows} rows)"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to preview file: {preview_data['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in preview_csv_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint for SQL service and agent.
    """
    try:
        # Import the agent to check its status
        from agents.sqlagent_invocation import sql_agent
        
        return {
            "status": "healthy",
            "service": "SQL Agent Service",
            "agent_initialized": sql_agent.is_initialized,
            "timestamp": datetime.now().isoformat(),
            "message": "SQL agent service is running"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "SQL Agent Service", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()

        }