# mcp_http_client.py

import asyncio
import logging
import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTTPMCPClient:
    """HTTP-based MCP Client for SQL query execution and database operations"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.health_url = f"{base_url}/mcp/health"
        self.tools_url = f"{base_url}/mcp/tools"
        self.client = None
        self.request_id = 0
        self.connected = False
    
    def _get_next_request_id(self) -> int:
        """Get next request ID for JSON-RPC"""
        self.request_id += 1
        return self.request_id
    
    async def connect(self) -> bool:
        """Connect to the HTTP MCP server"""
        try:
            if self.connected:
                logger.info("Already connected to HTTP MCP server")
                return True
            
            # Create HTTP client
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection with health check
            response = await self.client.get(self.health_url)
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Connected to HTTP MCP server: {health_data}")
                
                # Initialize the server
                init_result = await self._make_jsonrpc_request("initialize", {})
                if init_result and not self._is_error_response(init_result):
                    self.connected = True
                    logger.info("HTTP MCP server initialized successfully")
                    return True
                else:
                    logger.error(f"Failed to initialize HTTP MCP server: {init_result}")
                    return False
            else:
                logger.error(f"HTTP MCP server health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the HTTP MCP server"""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            self.connected = False
            logger.info("Disconnected from HTTP MCP server")
        except Exception as e:
            logger.error(f"Error disconnecting from HTTP MCP server: {e}")
    
    async def _make_jsonrpc_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make a JSON-RPC request to the MCP server"""
        try:
            if not self.client:
                raise Exception("Not connected to HTTP MCP server")
            
            request_data = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": self._get_next_request_id()
            }
            
            logger.debug(f"Making JSON-RPC request: {method} with params: {params}")
            
            response = await self.client.post(
                self.mcp_url,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"HTTP error: {response.status_code}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            
            response_data = response.json()
            
            if "error" in response_data:
                logger.error(f"JSON-RPC error: {response_data['error']}")
                return response_data
            
            return response_data.get("result")
            
        except Exception as e:
            logger.error(f"Error making JSON-RPC request: {e}")
            return {"error": str(e)}
    
    def _is_error_response(self, response: Dict[str, Any]) -> bool:
        """Check if response contains an error"""
        return isinstance(response, dict) and "error" in response
    
    async def execute_sql_query(self, query: str, database_name: str = "default") -> Dict[str, Any]:
        """Execute SQL query through HTTP MCP server"""
        try:
            if not self.connected:
                connect_result = await self.connect()
                if not connect_result:
                    return {"error": "Failed to connect to HTTP MCP server"}
            
            logger.info(f"Executing SQL query via HTTP MCP: {query[:100]}...")
            
            result = await self._make_jsonrpc_request(
                "execute_sql_query",
                {
                    "query": query,
                    "database_name": database_name
                }
            )
            
            if self._is_error_response(result):
                logger.error(f"SQL query execution failed: {result}")
                return result
            
            logger.info("SQL query executed successfully via HTTP MCP")
            return result
            
        except Exception as e:
            logger.error(f"Error executing SQL query via HTTP MCP: {e}")
            return {"error": str(e)}
    
    async def get_database_schema(self, database_name: str = "default") -> Dict[str, Any]:
        """Get database schema information through HTTP MCP server"""
        try:
            if not self.connected:
                connect_result = await self.connect()
                if not connect_result:
                    return {"error": "Failed to connect to HTTP MCP server"}
            
            logger.info(f"Getting database schema via HTTP MCP for: {database_name}")
            
            result = await self._make_jsonrpc_request(
                "get_database_schema",
                {"database_name": database_name}
            )
            
            if self._is_error_response(result):
                logger.error(f"Schema retrieval failed: {result}")
                return result
            
            logger.info("Database schema retrieved successfully via HTTP MCP")
            return result
            
        except Exception as e:
            logger.error(f"Error getting database schema via HTTP MCP: {e}")
            return {"error": str(e)}
    
    async def list_tables(self, database_name: str = "default") -> Dict[str, Any]:
        """List all tables in the specified database through HTTP MCP server"""
        try:
            if not self.connected:
                connect_result = await self.connect()
                if not connect_result:
                    return {"error": "Failed to connect to HTTP MCP server"}
            
            logger.info(f"Listing tables via HTTP MCP for: {database_name}")
            
            result = await self._make_jsonrpc_request(
                "list_tables",
                {"database_name": database_name}
            )
            
            if self._is_error_response(result):
                logger.error(f"Table listing failed: {result}")
                return result
            
            logger.info("Tables listed successfully via HTTP MCP")
            return result
            
        except Exception as e:
            logger.error(f"Error listing tables via HTTP MCP: {e}")
            return {"error": str(e)}
    
    async def get_table_info(self, table_name: str, database_name: str = "default") -> Dict[str, Any]:
        """Get detailed information about a specific table through HTTP MCP server"""
        try:
            if not self.connected:
                connect_result = await self.connect()
                if not connect_result:
                    return {"error": "Failed to connect to HTTP MCP server"}
            
            logger.info(f"Getting table info via HTTP MCP for: {table_name}")
            
            result = await self._make_jsonrpc_request(
                "get_table_info",
                {
                    "table_name": table_name,
                    "database_name": database_name
                }
            )
            
            if self._is_error_response(result):
                logger.error(f"Table info retrieval failed: {result}")
                return result
            
            logger.info("Table info retrieved successfully via HTTP MCP")
            return result
            
        except Exception as e:
            logger.error(f"Error getting table info via HTTP MCP: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the HTTP MCP server"""
        try:
            if not self.client:
                self.client = httpx.AsyncClient(timeout=30.0)
            
            response = await self.client.get(self.health_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Health check failed: HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {"error": str(e)}
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """List all available tools on the HTTP MCP server"""
        try:
            if not self.client:
                self.client = httpx.AsyncClient(timeout=30.0)
            
            response = await self.client.get(self.tools_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Tools listing failed: HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {"error": str(e)}

# Example usage and testing
async def test_http_mcp_client():
    """Test the HTTP MCP client"""
    client = HTTPMCPClient()
    
    try:
        # Test connection
        logger.info("Testing HTTP MCP client connection...")
        connected = await client.connect()
        
        if not connected:
            logger.error("Failed to connect to HTTP MCP server")
            return
        
        # Test health check
        health = await client.health_check()
        logger.info(f"Health check result: {health}")
        
        # Test tools listing
        tools = await client.list_available_tools()
        logger.info(f"Available tools: {tools}")
        
        # Test schema retrieval
        schema = await client.get_database_schema("default")
        logger.info(f"Schema result: {schema}")
        
        # Test table listing
        tables = await client.list_tables("default")
        logger.info(f"Tables result: {tables}")
        
        # Test SQL execution
        sql_result = await client.execute_sql_query("SELECT 1 as test_column", "default")
        logger.info(f"SQL execution result: {sql_result}")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
    finally:
        # Cleanup
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_http_mcp_client())
