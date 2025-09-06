# start_mcp_server.py

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from mcp_server import SQLMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_server.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Start the MCP SQL server"""
    try:
        logger.info("Starting MCP SQL Server...")
        
        # Create server instance
        server = SQLMCPServer()
        
        # Run the server
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Set environment variables if needed
    os.environ.setdefault("PYTHONPATH", str(current_dir))
    
    # Run the server
    asyncio.run(main())