import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.db import Base1, engine1, get_db1, Base2, engine2, get_db2
from models import User, Chat, Message
import uvicorn
import logging
import os
import asyncio

Base2.metadata.create_all(bind=engine2)
# Base1.metadata.create_all(bind=engine1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global variable for HTTP MCP server task
http_mcp_server_task = None

async def run_http_mcp_server():
    """
    Function to run HTTP MCP server as an asyncio task.
    """
    try:
        logger.info("HTTP MCP server task starting...")
        from mcp_http_server import start_http_mcp_server
        
        # Start the HTTP MCP server on port 8001
        await start_http_mcp_server(host="127.0.0.1", port=8001)
        
    except Exception as e:
        logger.error(f"HTTP MCP server task crashed: {e}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager using asyncio tasks for HTTP MCP server.
    """
    global http_mcp_server_task
    
    # Startup
    logger.info("Starting HTTP MCP server as asyncio task...")
    http_mcp_server_task = asyncio.create_task(run_http_mcp_server())
    
    # Give it a moment to start
    await asyncio.sleep(2)
    
    if not http_mcp_server_task.done():
        logger.info("HTTP MCP server task has started and is running on port 8001.")
    else:
        logger.error("HTTP MCP server task failed to start or crashed immediately.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HTTP MCP server task...")
    if http_mcp_server_task and not http_mcp_server_task.done():
        http_mcp_server_task.cancel()
        try:
            await http_mcp_server_task
        except asyncio.CancelledError:
            logger.info("HTTP MCP server task cancelled successfully.")

# Initialize FastAPI app
app = FastAPI(
    title="Argobot Backend API",
    description="APIs and RAG logic for ARGO Bot with integrated MCP server",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import userrouter, chatrouter
from routers.sql_router import router as sql_router
from routers.sql_router_http import router as sql_router_http

app.include_router(userrouter.router, prefix="/api/v1", tags=["users"])
app.include_router(chatrouter.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(sql_router, prefix="/api/v1", tags=["SQL Operations (stdio)"])
app.include_router(sql_router_http, prefix="/api/v1/http", tags=["SQL Operations (HTTP)"])

@app.get("/")
async def root():
    return {
        "message": "Argobot API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "status_endpoint": "/api/v1/status"
    }

@app.get("/health")
async def health_check():
    """
    Overall health check including HTTP MCP server status
    """
    global http_mcp_server_task
    
    mcp_status = "running" if http_mcp_server_task and not http_mcp_server_task.done() else "stopped"
    
    # Also check HTTP MCP server health directly
    mcp_health = "unknown"
    try:
        from mcp_http_client import HTTPMCPClient
        client = HTTPMCPClient()
        health_result = await client.health_check()
        if "error" not in health_result:
            mcp_health = "healthy"
        else:
            mcp_health = "unhealthy"
    except Exception as e:
        mcp_health = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "api": "running",
        "mcp_server_task": mcp_status,
        "mcp_server_health": mcp_health,
        "mcp_server_url": "http://127.0.0.1:8001/mcp",
        "message": "Argobot Backend API is operational with HTTP MCP server"
    }

# Example of a route with database dependency
@app.get("/documents")
def get_documents(db: Session = Depends(get_db2)):
    return {"message": "This is where you would list documents from the database."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_level="info")