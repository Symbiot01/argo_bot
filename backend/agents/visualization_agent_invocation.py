# agents/visualization_agent_invocation.py

import logging
import json
import pandas as pd
import os
from typing import Dict, Any, List, Optional, Tuple
from mcp_visualization_client import HTTPVisualizationMCPClient
from services.initialise_visualization_llm import visualization_llm_service
from pandas import DataFrame
# from utility_functions.chat_history import get_recent_chat_history

logger = logging.getLogger(__name__)

class VisualizationAgent:
    """Agent for handling visualization pipeline with SQL and visualization LLM integration"""
    
    def __init__(self):
        self.visualization_client = HTTPVisualizationMCPClient()
        self.llm_service = visualization_llm_service
    
    async def process_query_with_visualization(self, user_query: str, sql_data: Optional[List[Dict[str, Any]]] = None, 
                                             sql_query: str = "", chat_id: Optional[str] = None,
                                             argo_context: str = "", document_link: Optional[str] = None) -> Tuple[str, bool]:
        """
        Process a query with potential visualization
        
        Args:
            user_query: Original user question
            sql_data: Data returned from SQL query (optional if CSV file is provided)
            sql_query: The SQL query that was executed
            chat_id: Chat ID for history context
            argo_context: Argo domain context
            document_link: Path to the CSV file containing the SQL results
            
        Returns:
            Tuple of (HTML response, whether visualization was created)
        """
        try:
            logger.info(f"Processing query with visualization pipeline: {user_query[:100]}...")
            
            # Load data from CSV file if not provided in memory
            actual_data = sql_data
            if not actual_data and document_link:
                logger.info(f"Loading data from CSV file: {document_link}")
                actual_data = await self._load_csv_data(document_link)
            
            # Get chat history context
            chat_history = ""
            # if chat_id:
            #     try:
            #         chat_history = await get_recent_chat_history(chat_id, limit=5)
            #     except Exception as e:
            #         logger.warning(f"Could not retrieve chat history: {e}")
            
            # Step 1: Decide if visualization is needed
            visualization_decision = await self.llm_service.should_create_visualization(
                user_query=user_query,
                data=actual_data,
                sql_query=sql_query,
                csv_file_path=document_link
            )
            
            visualization_info = None
            visualization_created = False
            
            # Step 2: Create visualization if recommended
            if visualization_decision.get("should_visualize", False):
                logger.info(f"Creating visualization: {visualization_decision.get('visualization_type')}")
                
                # Ensure we have data for visualization
                viz_data = pd.DataFrame(actual_data) if actual_data else None
                    
                
                if actual_data:
                    visualization_info = await self._create_visualization(
                        data=viz_data,
                        document_link=document_link,
                        viz_decision=visualization_decision,
                        user_query=user_query
                    )
                    
                    if visualization_info and not visualization_info.get("error"):
                        visualization_created = True
                        logger.info(f"Visualization created successfully: {visualization_info.get('s3_url')}")
                    else:
                        logger.warning(f"Visualization creation failed: {visualization_info}")
                else:
                    logger.warning("No data available for visualization creation")
            else:
                logger.info(f"No visualization needed: {visualization_decision.get('reasoning')}")
            
            # Step 3: Generate comprehensive HTML response
            html_response = await self.llm_service.generate_html_response(
                user_query=user_query,
                sql_query=sql_query,
                data=actual_data,  # Use actual_data which might be loaded from CSV
                visualization_info=visualization_info,
                chat_history=chat_history,
                document_link=document_link
            )
            
            return html_response, visualization_created
            
        except Exception as e:
            logger.error(f"Error in visualization pipeline: {e}")
            logger.exception(e)
            error_html = f"""
<div style="color: red; padding: 20px; border: 1px solid red; border-radius: 4px;">
    <h3>Error in Visualization Pipeline</h3>
    <p>An error occurred while processing your request: {str(e)}</p>
</div>
"""
            return error_html, False
    
    async def _load_csv_data(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """
        Load data from CSV file and return as list of dictionaries
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            List of dictionaries representing the data
        """
        try:
            if not os.path.exists(csv_file_path):
                logger.error(f"CSV file not found: {csv_file_path}")
                return []
            
            df = pd.read_csv(csv_file_path)
            
            # Limit data size for visualization (take a reasonable sample)
            if len(df) > 10000:
                logger.info(f"Large dataset detected ({len(df)} rows), sampling 10000 rows for visualization")
                df = df.sample(n=10000, random_state=42)
            
            # Convert DataFrame to list of dictionaries
            data = df.to_dict('records')
            
            logger.info(f"Loaded {len(data)} rows from CSV file: {csv_file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_file_path}: {e}")
            return []
    
    async def _create_visualization(self, data: DataFrame, viz_decision: Dict[str, Any], document_link: str,
                                  user_query: str) -> Optional[Dict[str, Any]]:
        """Create the specified visualization"""
        try:
            viz_type = viz_decision.get("visualization_type")
            params = viz_decision.get("parameters")
            
            # Convert list of dicts to dict of lists for the visualization server
            viz_data = data
            
            if viz_type == "scatter":
                return await self.visualization_client.create_scatter_plot(
                    data=document_link,
                    x_column=params.get("x_column"),
                    y_column=params.get("y_column"),
                    title=params.get("title", "Scatter Plot"),
                    color_column=params.get("color_column")
                )
            
            elif viz_type == "line":
                return await self.visualization_client.create_line_plot(
                    data=document_link,
                    x_column=params.get("x_column"),
                    y_column=params.get("y_column"),
                    title=params.get("title", "Line Plot"),
                    group_column=params.get("group_column")
                )
            
            elif viz_type == "heatmap":
                return await self.visualization_client.create_heatmap(
                    data=document_link,
                    title=params.get("title", "Heatmap"),
                    correlation=params.get("correlation", False)
                )
            
            elif viz_type == "depth_profile":
                return await self.visualization_client.create_depth_profile(
                    data=document_link,
                    depth_column=params.get("depth_column", "pressure"),
                    value_column=params.get("value_column"),
                    title=params.get("title", "Depth Profile")
                )
            
            elif viz_type == "geographic":
                return await self.visualization_client.create_geographic_plot(
                    data=document_link,
                    lat_column=params.get("lat_column", "latitude"),
                    lon_column=params.get("lon_column", "longitude"),
                    title=params.get("title", "Geographic Plot"),
                    color_column=params.get("color_column")
                )
            
            elif viz_type == "histogram":
                return await self.visualization_client.create_histogram(
                    data=document_link,
                    column=params.get("column"),
                    title=params.get("title", "Histogram"),
                    bins=params.get("bins", 30)
                )
            
            else:
                logger.warning(f"Unknown visualization type: {viz_type}")
                return {"error": f"Unknown visualization type: {viz_type}"}
                
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return {"error": str(e)}
    
    def _convert_data_format(self, data: List[Dict[str, Any]]) -> Dict[str, List]:
        """Convert list of dictionaries to dictionary of lists for visualization"""
        try:
            if not data:
                return {}
            
            # Get all unique keys
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            
            # Convert to dict of lists
            result = {}
            for key in all_keys:
                result[key] = [row.get(key) for row in data]
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting data format: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of visualization services"""
        try:
            viz_health = await self.visualization_client.health_check()
            return {
                "status": "healthy",
                "visualization_server": viz_health,
                "llm_service": "initialized" if self.llm_service.llm else "not initialized"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global instance
visualization_agent = VisualizationAgent()
