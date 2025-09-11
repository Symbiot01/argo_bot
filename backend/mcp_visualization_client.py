# mcp_visualization_client.py

import httpx
import logging
import json
from typing import Dict, Any, Optional
from pandas import DataFrame

logger = logging.getLogger(__name__)

class HTTPVisualizationMCPClient:
    """HTTP client for the Visualization MCP server"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8002"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.health_url = f"{base_url}/mcp/health"
        self.tools_url = f"{base_url}/mcp/tools"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the MCP server is healthy"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.health_url)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Health check failed with status {response.status_code}"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"error": str(e)}
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available visualization tools"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.tools_url)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to list tools with status {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return {"error": str(e)}
    
    async def call_tool(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a JSON-RPC call to the MCP server"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for visualization
                response = await client.post(
                    self.mcp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "error" in result:
                        return {"error": result["error"]}
                    return result.get("result", {})
                else:
                    return {"error": f"HTTP error {response.status_code}: {response.text}"}
                    
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling tool {method}: {e}")
            logger.exception(e)
            return {"error": str(e)}
    
    async def create_scatter_plot(self, data: str, x_column: str, y_column: str,
                                title: str = "Scatter Plot", color_column: str = None) -> Dict[str, Any]:
        """Create a scatter plot"""
        params = {
            "data": data,
            "x_column": x_column,
            "y_column": y_column,
            "title": title
        }
        if color_column:
            params["color_column"] = color_column
        
        return await self.call_tool("create_scatter_plot", params)
    
    async def create_line_plot(self, data: str, x_column: str, y_column: str,
                             title: str = "Line Plot", group_column: str = None) -> Dict[str, Any]:
        """Create a line plot"""
        params = {
            "data": data,
            "x_column": x_column,
            "y_column": y_column,
            "title": title
        }
        if group_column:
            params["group_column"] = group_column
        
        return await self.call_tool("create_line_plot", params)
    
    async def create_heatmap(self, data: str, title: str = "Heatmap",
                           correlation: bool = False) -> Dict[str, Any]:
        """Create a heatmap"""
        params = {
            "data": data,
            "title": title,
            "correlation": correlation
        }
        return await self.call_tool("create_heatmap", params)
    
    async def create_depth_profile(self, data: str, depth_column: str,
                                 value_column: str, title: str = "Depth Profile") -> Dict[str, Any]:
        """Create a depth profile plot"""
        params = {
            "data": data,
            "depth_column": depth_column,
            "value_column": value_column,
            "title": title
        }
        return await self.call_tool("create_depth_profile", params)
    
    async def create_geographic_plot(self, data: str, lat_column: str, lon_column: str,
                                   title: str = "Geographic Plot", color_column: str = None) -> Dict[str, Any]:
        """Create a geographic scatter plot"""
        params = {
            "data": data,
            "lat_column": lat_column,
            "lon_column": lon_column,
            "title": title
        }
        if color_column:
            params["color_column"] = color_column
        
        return await self.call_tool("create_geographic_plot", params)
    
    async def create_histogram(self, data: str, column: str, title: str = "Histogram",
                             bins: int = 30) -> Dict[str, Any]:
        """Create a histogram"""
        params = {
            "data": data,
            "column": column,
            "title": title,
            "bins": bins
        }
        return await self.call_tool("create_histogram", params)
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP server"""
        return await self.call_tool("initialize", {})
