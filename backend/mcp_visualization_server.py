# mcp_visualization_server.py

import asyncio
import logging
import json
import os
import io
import base64
import boto3
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors 
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
from botocore.exceptions import ClientError, NoCredentialsError
from pandas import DataFrame

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import logging
from itertools import cycle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTTPVisualizationMCPServer:
    """HTTP-based MCP Server for Data Visualization operations using JSON-RPC"""
    
    def __init__(self):
        self.app = FastAPI(title="MCP Visualization Server", description="HTTP MCP Server for Data Visualization")
        self.s3_client = None
        self.bucket_name = "argo-bot-visualizations"  # Configure as needed
        self.setup_aws_client()
        self.setup_routes()
        self.setup_error_handlers()
    
    def setup_aws_client(self):
        """Setup AWS S3 client"""
        try:
            # Try to initialize S3 client with default credentials
            self.s3_client = boto3.client('s3')
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            logger.info("AWS S3 client initialized successfully")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS S3 client not available: {e}")
            self.s3_client = None
    
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
                "server": "MCP Visualization Server",
                "s3_available": self.s3_client is not None,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """List available MCP tools"""
            return {
                "tools": [
                    {
                        "name": "create_scatter_plot",
                        "description": "Create a scatter plot from oceanographic data and save to S3",
                        "parameters": {
                            "data": {"type": "string", "description": "document link"},
                            "x_column": {"type": "string", "description": "Column name for x-axis"},
                            "y_column": {"type": "string", "description": "Column name for y-axis"},
                            "title": {"type": "string", "description": "Plot title", "default": "Scatter Plot"},
                            "color_column": {"type": "string", "description": "Column for color mapping", "default": None}
                        }
                    },
                    {
                        "name": "create_line_plot",
                        "description": "Create a line plot for time series or depth profiles",
                        "parameters": {
                            "data": {"type": "string", "description": "document link"},
                            "x_column": {"type": "string", "description": "Column name for x-axis"},
                            "y_column": {"type": "string", "description": "Column name for y-axis"},
                            "title": {"type": "string", "description": "Plot title", "default": "Line Plot"},
                            "group_column": {"type": "string", "description": "Column for grouping lines", "default": None}
                        }
                    },
                    {
                        "name": "create_heatmap",
                        "description": "Create a heatmap visualization for correlation or spatial data",
                        "parameters": {
                            "data": {"type": "string", "description": "document link"},
                            "title": {"type": "string", "description": "Plot title", "default": "Heatmap"},
                            "correlation": {"type": "boolean", "description": "Create correlation heatmap", "default": False}
                        }
                    },
                    {
                        "name": "create_depth_profile",
                        "description": "Create ocean depth profile visualization",
                        "parameters": {
                            "data": {"type": "string", "description": "document link"},
                            "depth_column": {"type": "string", "description": "Column name for depth/pressure"},
                            "value_column": {"type": "string", "description": "Column name for measurement values"},
                            "title": {"type": "string", "description": "Plot title", "default": "Depth Profile"}
                        }
                    },
                    {
                        "name": "create_geographic_plot",
                        "description": "Create geographic scatter plot of float locations",
                        "parameters": {
                            "data": {"type": "string", "description": "document link"},
                            "lat_column": {"type": "string", "description": "Column name for latitude"},
                            "lon_column": {"type": "string", "description": "Column name for longitude"},
                            "title": {"type": "string", "description": "Plot title", "default": "Geographic Plot"},
                            "color_column": {"type": "string", "description": "Column for color mapping", "default": None}
                        }
                    },
                    {
                        "name": "create_histogram",
                        "description": "Create histogram for data distribution analysis",
                        "parameters": {
                            "data": {"type": "string", "description": "document link"},
                            "column": {"type": "string", "description": "Column name for histogram"},
                            "title": {"type": "string", "description": "Plot title", "default": "Histogram"},
                            "bins": {"type": "integer", "description": "Number of bins", "default": 30}
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
            if method == "create_scatter_plot":
                result = await self.create_scatter_plot(**params)
            elif method == "create_line_plot":
                result = await self.create_line_plot(**params)
            elif method == "create_heatmap":
                result = await self.create_heatmap(**params)
            elif method == "create_depth_profile":
                result = await self.create_depth_profile(**params)
            elif method == "create_geographic_plot":
                result = await self.create_geographic_plot(**params)
            elif method == "create_histogram":
                result = await self.create_histogram(**params)
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
        """Initialize the MCP server"""
        try:
            logger.info("MCP Visualization Server initialized successfully")
            return {
                "status": "initialized",
                "message": "MCP Visualization Server ready",
                "s3_available": self.s3_client is not None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error initializing MCP server: {e}")
            return {"error": str(e)}
    
    async def create_scatter_plot(self, data: str, x_column: str, y_column: str, 
                                title: str = "Scatter Plot", color_column: str = None) -> Dict[str, Any]:
        """Create a scatter plot and upload to S3"""
        try:

            df = pd.read_csv(data)
          
            
            plt.figure(figsize=(10, 8))
            
            if color_column and color_column in df.columns:
                scatter = plt.scatter(df[x_column], df[y_column], c=df[color_column], 
                                   cmap='viridis', alpha=0.6)
                plt.colorbar(scatter, label=color_column)
            else:
                plt.scatter(df[x_column], df[y_column], alpha=0.6)
            
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.title(title)
            plt.grid(True, alpha=0.3)
            
            # Upload to S3 and return URL
            s3_url = await self.save_plot_to_s3(title.replace(" ", "_").lower() + "_scatter")
            
            return {
                "success": True,
                "plot_type": "scatter_plot",
                "title": title,
                "s3_url": s3_url,
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error(f"Error creating scatter plot: {e}")
            return {"error": str(e)}
    
    async def create_line_plot(self, data: str, x_column: str, y_column: str,
                             title: str = "Line Plot", group_column: str = None) -> Dict[str, Any]:
        """Create a line plot and upload to S3"""
        """
        Creates a styled line plot with automatic time-based aggregation and uploads it to S3.
        """
        # --- 🎨 Hardcoded Light Mode Color Palette ---
        BG_COLOR = '#ffffff'
        PRIMARY_TEXT = '#1e293b'
        SECONDARY_TEXT = '#475569'
        GRID_COLOR = '#cbd5e1'
        # A professional color cycle for grouped lines
        COLOR_CYCLE = ['#0ea5e9', '#22c55e', '#f97316', '#8b5cf6', '#ef4444', '#14b8a6']

        try:
            df = pd.read_csv(data)
            
            # 1. Convert x-column to datetime and sort
            df[x_column] = pd.to_datetime(df[x_column])
            df = df.sort_values(by=x_column)

            # 2. Determine aggregation level based on the date range
            date_range = df[x_column].max() - df[x_column].min()
            
            if date_range < pd.Timedelta(days=31):
                agg_period = 'D'
                agg_level_label = 'Daily'
                date_format = '%b %d'
            elif date_range < pd.Timedelta(days=61):
                agg_period = 'W'
                agg_level_label = 'Weekly'
                date_format = '%b %d'
            else:
                agg_period = 'M'
                agg_level_label = 'Monthly'
                date_format = '%b %Y'

            # 3. Aggregate data by the determined time period
            time_period_col = df[x_column].dt.to_period(agg_period)
            
            grouping_keys = [time_period_col]
            if group_column and group_column in df.columns:
                grouping_keys.append(group_column)

            agg_df = df.groupby(grouping_keys)[y_column].mean().reset_index()
            agg_df[x_column] = agg_df[x_column].dt.to_timestamp() # Convert period back to timestamp for plotting

            # 4. Setup the plot with professional styling
            fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG_COLOR)
            ax.set_facecolor(BG_COLOR)
            
            # Style spines and ticks
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_color(GRID_COLOR)
            ax.tick_params(axis='both', colors=SECONDARY_TEXT)

            # 5. Plot the aggregated data
            if group_column and group_column in df.columns:
                colors = cycle(COLOR_CYCLE)
                for group, group_data in agg_df.groupby(group_column):
                    ax.plot(group_data[x_column], group_data[y_column], 
                            label=str(group), color=next(colors), linewidth=2.5)
                
                legend = ax.legend(title=group_column, frameon=False)
                plt.setp(legend.get_title(), color=SECONDARY_TEXT)
                plt.setp(legend.get_texts(), color=SECONDARY_TEXT)
            else:
                ax.plot(agg_df[x_column], agg_df[y_column], color=COLOR_CYCLE[0], linewidth=2.5)

            # 6. Format labels, title, and grid
            ax.set_xlabel(x_column, color=SECONDARY_TEXT, fontsize=12)
            ax.set_ylabel(y_column, color=SECONDARY_TEXT, fontsize=12)
            ax.set_title(f"{title} ({agg_level_label} Average)", color=PRIMARY_TEXT, fontsize=18, weight='bold')
            ax.grid(True, axis='y', color=GRID_COLOR, linestyle='--', alpha=0.7)
            
            # Format date labels on the x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

            plt.tight_layout()
            
            # 7. Save the plot and return the result
            s3_url = await self.save_plot_to_s3(title.replace(" ", "_").lower() + "_line_plot")
            
            return {
                "success": True,
                "plot_type": "line_plot",
                "title": title,
                "s3_url": s3_url,
                "data_points": len(df),
                "aggregation_level": agg_level_label.lower()
            }
            
        except Exception as e:
            logger.error(f"Error creating line plot: {e}", exc_info=True)
            plt.close('all')
            return {"error": str(e)}
    
    async def create_heatmap(self, data: str, title: str = "Heatmap", 
                           correlation: bool = False) -> Dict[str, Any]:
        """Create a heatmap and upload to S3"""
        try:
            df = pd.read_csv(data)
            
            plt.figure(figsize=(10, 8))
            
            if correlation:
                # Create correlation heatmap
                numeric_df = df.select_dtypes(include=[np.number])
                corr_matrix = numeric_df.corr()
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                           square=True, linewidths=0.5)
            else:
                # Create regular heatmap
                numeric_df = df.select_dtypes(include=[np.number])
                sns.heatmap(numeric_df.iloc[:50, :], cmap='viridis')  # Limit to first 50 rows
            
            plt.title(title)
            plt.tight_layout()
            
            s3_url = await self.save_plot_to_s3(title.replace(" ", "_").lower() + "_heatmap")
            
            return {
                "success": True,
                "plot_type": "heatmap",
                "title": title,
                "s3_url": s3_url,
                "correlation": correlation
            }
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return {"error": str(e)}
    
    async def create_depth_profile(self, data: str, depth_column: str, 
                                 value_column: str, title: str = "Depth Profile") -> Dict[str, Any]:
        """Create an ocean depth profile plot and upload to S3"""
        try:
            df = pd.read_csv(data)
            
            plt.figure(figsize=(8, 12))
            
            # Ocean profiles typically show depth increasing downward
            plt.plot(df[value_column], df[depth_column])
            plt.gca().invert_yaxis()  # Invert y-axis so depth increases downward
            
            plt.xlabel(value_column)
            plt.ylabel(f"{depth_column} (increasing depth)")
            plt.title(title)
            plt.grid(True, alpha=0.3)
            
            s3_url = await self.save_plot_to_s3(title.replace(" ", "_").lower() + "_depth_profile")
            
            return {
                "success": True,
                "plot_type": "depth_profile",
                "title": title,
                "s3_url": s3_url,
                "max_depth": df[depth_column].max()
            }
            
        except Exception as e:
            logger.error(f"Error creating depth profile: {e}")
            return {"error": str(e)}
    
    async def create_geographic_plot(self, data: str, lat_column: str, lon_column: str,
                                   title: str = "Geographic Plot", color_column: str = None) -> Dict[str, Any]:
        """Create a geographic scatter plot and upload to S3"""
        """Create a geographic map plot using Cartopy and upload it to S3."""
        BG_COLOR = '#ffffff'
        OCEAN_COLOR = '#e0f2fe'
        LAND_COLOR = '#f0f9ff'
        COASTLINE_COLOR = '#0ea5e9'
        PRIMARY_TEXT = '#1e293b'
        SECONDARY_TEXT = '#475569'
        SCATTER_EDGE = '#ffffff'

        # --- 🌈 Custom Colormap for Temperature Visualization ---
        CMAP_COLORS = ['#3b82f6', '#facc15', '#ef4444'] # Blue -> Yellow -> Red

        try:
            df = pd.read_csv(data)

            # 1. Create a square figure with the light background color
            fig = plt.figure(figsize=(15, 15), facecolor=BG_COLOR)
            projection = ccrs.PlateCarree()
            ax = plt.axes(projection=projection, facecolor=BG_COLOR)

            # 2. Add styled geographic features for the light theme
            ax.add_feature(cfeature.OCEAN, zorder=0, facecolor=OCEAN_COLOR, edgecolor='none')
            ax.add_feature(cfeature.LAND, zorder=0, facecolor=LAND_COLOR, edgecolor='none')
            ax.coastlines(resolution='10m', color=COASTLINE_COLOR, linewidth=0.8, zorder=2)

            # 3. Calculate a square bounding box to ensure a balanced plot
            lon_min, lon_max = df[lon_column].min(), df[lon_column].max()
            lat_min, lat_max = df[lat_column].min(), df[lat_column].max()

            # Find the center of the data
            center_lon = (lon_max + lon_min) / 2
            center_lat = (lat_max + lat_min) / 2

            # Determine the largest range (width or height) and add a 30% buffer
            lon_range = lon_max - lon_min
            lat_range = lat_max - lat_min
            max_range = max(lon_range, lat_range) * 1.30

            # Create new square extents centered on the data
            half_range = max_range / 2
            extent = [
                center_lon - half_range, center_lon + half_range,
                center_lat - half_range, center_lat + half_range
            ]
            ax.set_extent(extent, crs=projection)

            # 4. Define base styling for scatter points
            plot_kwargs = {
                'alpha': 0.85, 's': 45, 'transform': projection,
                'edgecolor': SCATTER_EDGE, 'linewidth': 0.5, 'zorder': 3
            }

            # 5. Plot data points with the custom temperature color map
            if color_column and color_column in df.columns:
                custom_cmap = mcolors.LinearSegmentedColormap.from_list("temp_map", CMAP_COLORS)
                scatter = ax.scatter(df[lon_column], df[lat_column], c=df[color_column],
                                     cmap=custom_cmap, **plot_kwargs)
                cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.03, orientation='horizontal')
                cbar.ax.xaxis.set_tick_params(color=SECONDARY_TEXT, labelcolor=SECONDARY_TEXT)
                cbar.outline.set_edgecolor(SECONDARY_TEXT)
                cbar.set_label(color_column, color=PRIMARY_TEXT, fontsize=12, labelpad=10)
            else:
                ax.scatter(df[lon_column], df[lat_column], color=CMAP_COLORS[0], **plot_kwargs)

            # 6. Add and style gridlines
            gl = ax.gridlines(draw_labels=True, linewidth=1, color=SECONDARY_TEXT, alpha=0.3, linestyle='--')
            gl.top_labels = gl.right_labels = False
            gl.xlabel_style = {'color': SECONDARY_TEXT, 'size': 10}
            gl.ylabel_style = {'color': SECONDARY_TEXT, 'size': 10}

            # 7. Add styled title
            ax.set_title(title, fontsize=20, color=PRIMARY_TEXT, pad=20, weight='bold')

            # 8. Save the plot and return the result
            filename = title.replace(" ", "_").lower() + "_geographic_plot.png"
            s3_url = await self.save_plot_to_s3(filename)
            plt.close(fig)

            return {
                "success": True,
                "plot_type": "cartopy_geographic_plot",
                "title": title,
                "s3_url": s3_url,
                "data_points": len(df)
            }

        except Exception as e:
            logger.error(f"Error creating geographic plot: {e}", exc_info=True)
            plt.close('all')
            return {"error": str(e)}

    
    async def create_histogram(self, data: str, column: str, title: str = "Histogram", 
                             bins: int = 30) -> Dict[str, Any]:
        """Create a histogram and upload to S3"""
        try:
   
            df = pd.read_csv(data)
            plt.figure(figsize=(10, 6))
            
            plt.hist(df[column].dropna(), bins=bins, alpha=0.7, edgecolor='black')
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.title(title)
            plt.grid(True, alpha=0.3)
            
            s3_url = await self.save_plot_to_s3(title.replace(" ", "_").lower() + "_histogram")
            
            return {
                "success": True,
                "plot_type": "histogram",
                "title": title,
                "s3_url": s3_url,
                "data_points": len(df[column].dropna())
            }
            
        except Exception as e:
            logger.error(f"Error creating histogram: {e}")
            return {"error": str(e)}
    
    async def save_plot_to_s3(self, base_filename: str) -> str:
        """Save the current matplotlib plot to S3 and return URL"""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_filename}_{timestamp}.png"
            
            # Save plot to bytes buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()  # Close the plot to free memory
            
            if self.s3_client:
                # Upload to S3
                try:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=f"visualizations/{filename}",
                        Body=img_buffer.getvalue(),
                        ContentType='image/png'
                    )
                    
                    # Generate public URL (adjust based on your S3 configuration)
                    s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/visualizations/{filename}"
                    logger.info(f"Plot uploaded to S3: {s3_url}")
                    return s3_url
                    
                except ClientError as e:
                    logger.error(f"Error uploading to S3: {e}")
                    # Fallback: save locally
                    return await self.save_plot_locally(filename, img_buffer.getvalue())
            else:
                # Fallback: save locally
                return await self.save_plot_locally(filename, img_buffer.getvalue())
                
        except Exception as e:
            logger.error(f"Error saving plot: {e}")
            return f"Error saving plot: {str(e)}"
    
    async def save_plot_locally(self, filename: str, image_data: bytes) -> str:
        """Save plot locally as fallback when S3 is not available"""
        try:
            # Create local directory
            local_dir = "datasets/visualizations"
            os.makedirs(local_dir, exist_ok=True)
            
            # Save file locally
            local_path = os.path.join(local_dir, filename)

            print (f"Saving plot locally at: {local_path}")
            with open(local_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Plot saved locally: {local_path}")
            return f"file://{os.path.abspath(local_path)}"
            
        except Exception as e:
            logger.error(f"Error saving plot locally: {e}")
            return f"Error saving plot locally: {str(e)}"
    
    def get_app(self) -> FastAPI:
        """Return the FastAPI app instance"""
        return self.app

# Global server instance
http_visualization_server = HTTPVisualizationMCPServer()

async def start_http_visualization_server(host: str = "127.0.0.1", port: int = 8002):
    """Start the HTTP Visualization MCP server"""
    logger.info(f"Starting HTTP Visualization MCP Server on {host}:{port}")
    config = uvicorn.Config(http_visualization_server.get_app(), host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_http_visualization_server())
