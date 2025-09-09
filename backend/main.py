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

# Global variable for MCP server thread
mcp_server_thread = None
mcp_server_running = False

def run_mcp_server():
    """
    Function to run MCP server in a separate thread
    """
    global mcp_server_running
    try:
        mcp_server_running = True
        logger.info("MCP server thread starting...")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Import and run your MCP server logic here
        from start_mcp_server import main as start_mcp
        loop.run_until_complete(start_mcp())
        
    except Exception as e:
        logger.error(f"MCP server thread error: {e}")
        mcp_server_running = False
    finally:
        # Clean up the event loop
        if 'loop' in locals():
            loop.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager with threading approach
    """
    global mcp_server_thread, mcp_server_running
    
    # Startup
    logger.info("Starting MCP server in separate thread...")
    mcp_server_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_server_thread.start()
    
    # Give MCP server time to start
    time.sleep(3)
    
    if mcp_server_running:
        logger.info("MCP server thread started successfully")
    else:
        logger.error("MCP server thread failed to start")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    mcp_server_running = False

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

app.include_router(userrouter.router, prefix="/api/v1", tags=["users"])
app.include_router(chatrouter.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(sql_router, prefix="/api/v1", tags=["SQL Operations"])

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
    Overall health check including MCP server status
    """
    global mcp_server_thread, mcp_server_running
    
    mcp_status = "running" if mcp_server_running and mcp_server_thread and mcp_server_thread.is_alive() else "stopped"
    
    return {
        "status": "healthy",
        "api": "running",
        "mcp_server": mcp_status,
        "message": "Argobot Backend API is operational"
    }


# Example of a route with database dependency
@app.get("/documents")
def get_documents(db: Session = Depends(get_db2)):
    # You need to create the Document model first for this to work
    # documents = db.query(models.Document).all()
    # return documents
    return {"message": "This is where you would list documents from the database."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_level="info")