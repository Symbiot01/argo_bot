# routers/sql_router.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import asyncio
from datetime import datetime

from utility_functions.sql_llm_functions import (
    get_sql_service,
    generate_sql_query,
    stream_sql_query,
    execute_sql_query,
    get_schema_info,
    get_tables_list,
    get_query_results
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/sql", tags=["SQL Operations"])

# Pydantic models
class SQLQueryRequest(BaseModel):
    question: str
    database_name: Optional[str] = None

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
async def generate_and_execute_query(request: SQLQueryRequest):
    """
    Generate SQL query from natural language and execute it.
    Returns query, results, and CSV file path.
    """
    try:
        logger.info(f"Generating SQL query for: {request.question}")
        
        result = await generate_sql_query(
            question=request.question,
            database_name=request.database_name
        )
        
        if result.get("success", False):
            return {
                "status": "success",
                "question": result["question"],
                "sql_query": result["sql_query"],
                "execution_result": result["execution_result"],
                "csv_file": result.get("csv_file"),
                "message": "Query generated and executed successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Query execution failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error in generate_and_execute_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream-query")
async def stream_query_generation(request: SQLQueryRequest):
    """
    Stream SQL query generation and execution process.
    Returns a streaming response with real-time updates.
    """
    try:
        logger.info(f"Streaming SQL query for: {request.question}")
        
        async def generate():
            try:
                async for chunk in stream_sql_query(
                    question=request.question,
                    database_name=request.database_name
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
async def execute_raw_sql(request: RawSQLRequest):
    """
    Execute a raw SQL query without LLM generation.
    Returns query results and CSV file path.
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
                "message": "Raw SQL executed successfully"
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
async def get_database_schema(request: DatabaseRequest):
    """
    Get database schema information including tables, columns, and relationships.
    """
    try:
        logger.info(f"Getting schema for database: {request.database_name or 'default'}")
        
        schema = await get_schema_info(database_name=request.database_name)
        
        if "error" not in schema:
            return {
                "status": "success",
                "database_name": request.database_name or "default",
                "schema": schema,
                "message": "Schema retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get schema: {schema['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in get_database_schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tables")
async def list_database_tables(request: DatabaseRequest):
    """
    List all tables in the specified database.
    """
    try:
        logger.info(f"Listing tables for database: {request.database_name or 'default'}")
        
        tables = await get_tables_list(database_name=request.database_name)
        
        if "error" not in tables:
            return {
                "status": "success",
                "database_name": request.database_name or "default",
                "tables": tables,
                "message": "Tables listed successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to list tables: {tables['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in list_database_tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/table-info")
async def get_table_information(request: TableInfoRequest):
    """
    Get detailed information about a specific table.
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
                "message": "Table information retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get table info: {table_info['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error in get_table_information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    Health check endpoint for SQL service.
    """
    try:
        service = await get_sql_service()
        
        return {
            "status": "healthy",
            "service": "SQL LLM Service",
            "initialized": service.initialized,
            "timestamp": datetime.now().isoformat(),
            "message": "SQL service is running"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "SQL LLM Service", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Error handlers
@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception in SQL router: {exc}")
    raise HTTPException(status_code=500, detail="Internal server error")
