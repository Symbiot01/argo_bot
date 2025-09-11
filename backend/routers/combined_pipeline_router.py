# routers/combined_pipeline_router.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
from sqlalchemy.orm import Session

# Import database dependencies
from database.db import get_db1, get_db2

# Import existing SQL agent
from agents.sqlagent_invocation_http import http_sql_agent

# Import visualization agent
from agents.visualization_agent_invocation import visualization_agent

# Import utility functions
# from utility_functions.chat_history import store_message, get_recent_chat_history

logger = logging.getLogger(__name__)

router = APIRouter()

class CombinedPipelineRequest(BaseModel):
    user_input: str
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    include_visualization: bool = True
    argo_context: Optional[str] = ""

class CombinedPipelineResponse(BaseModel):
    response: str
    response_type: str  # "text", "html", "error"
    sql_query: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None
    visualization_created: bool = False
    visualization_url: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

@router.post("/combined-pipeline", response_model=CombinedPipelineResponse)
async def process_combined_pipeline(
    request: CombinedPipelineRequest,
    db1: Session = Depends(get_db1),
    db2: Session = Depends(get_db2)
):
    """
    Combined pipeline that processes user queries through SQL LLM and optionally creates visualizations
    
    Flow:
    1. Process query with SQL LLM
    2. If SQL query is generated, execute it
    3. Determine if visualization is needed
    4. Create visualization if recommended
    5. Generate comprehensive HTML response
    """
    try:
        logger.info(f"Processing combined pipeline request: {request.user_input[:100]}...")
        
        # Step 1: Process with SQL LLM
        sql_response = await http_sql_agent.process_user_query(
            user_input=request.user_input,
            chat_id=request.chat_id,
            argo_context=request.argo_context
        )

        # print(f"SQL Response: {json.dumps(sql_response, indent=2)}")
        
        if not sql_response.get("success", False):
            # SQL processing failed, return error
            logger.error(f"SQL processing failed: {sql_response.get('error_message')}")
            return CombinedPipelineResponse(
                response=sql_response.get("response", "An error occurred processing your query."),
                response_type="error",
                success=False,
                error_message=sql_response.get("error_message"),
                visualization_created=False
            )
        

        
        # Step 2: Check if SQL query was generated and data returned
        sql_query = sql_response.get("sql_query")
        response_type = sql_response.get("response_type")
        data = sql_response.get("data", [])
        document_link = sql_response.get("document_link")  # CSV file path from SQL response
        csv_file = sql_response.get("csv_file")  # Alternative CSV file path

        print(f"response_type: {response_type}")
        
        if response_type!="sql":
            # No SQL query or data, return the SQL LLM response as-is
            logger.info("No SQL query generated or no data returned, returning text response")
            
            # # Store the message in chat history
            # if request.chat_id and request.user_id:
            #     try:
            #         await store_message(
            #             request.chat_id, 
            #             request.user_id, 
            #             request.user_input,
            #             sql_response.get("response", ""),
            #             db2
            #         )
            #     except Exception as e:
            #         logger.warning(f"Failed to store message: {e}")
            
            return CombinedPipelineResponse(
                response=sql_response.get("response", ""),
                response_type="text",
                sql_query=sql_query,
                success=True,
                visualization_created=False
            )
        
        # Step 3: Process with visualization pipeline if requested
        html_response = sql_response.get("response", "")
        visualization_created = False
        visualization_url = None
        
        if request.include_visualization and response_type=="sql":
            try:
                logger.info("Processing with visualization pipeline...")
                
                # Use document_link or csv_file path - prioritize document_link
                csv_file_path = document_link or csv_file
                
                html_response, visualization_created = await visualization_agent.process_query_with_visualization(
                    user_query=request.user_input,
                    sql_data=data,  # May be empty if data is in CSV file
                    sql_query=sql_query,
                    chat_id=request.chat_id,
                    argo_context=request.argo_context,
                    document_link=csv_file_path  # Pass CSV file path
                )
                
                # Extract visualization URL if available
                if visualization_created and "img src=" in html_response:
                    import re
                    url_match = re.search(r'img src="([^"]+)"', html_response)
                    if url_match:
                        visualization_url = url_match.group(1)
                        
            except Exception as e:
                logger.error(f"Visualization pipeline failed: {e}")
                # Continue with SQL response if visualization fails
                html_response = sql_response.get("response", "")
                visualization_created = False
        
        # Step 4: Prepare data summary
        data_summary = None
        if data:
            data_summary = {
                "total_rows": len(data),
                "columns": list(data[0].keys()) if data else [],
                "sample_count": min(5, len(data))
            }
        
        # # Step 5: Store message in chat history
        # if request.chat_id and request.user_id:
        #     try:
        #         await store_message(
        #             request.chat_id, 
        #             request.user_id, 
        #             request.user_input,
        #             html_response if request.include_visualization else sql_response.get("response", ""),
        #             db2
        #         )
        #     except Exception as e:
        #         logger.warning(f"Failed to store message: {e}")
        
        # Step 6: Return comprehensive response
        response_type = "html" if request.include_visualization and visualization_created else "text"
        
        return CombinedPipelineResponse(
            response=html_response,
            response_type=response_type,
            sql_query=sql_query,
            data_summary=data_summary,
            visualization_created=visualization_created,
            visualization_url=visualization_url,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error in combined pipeline: {e}")
        return CombinedPipelineResponse(
            response=f"An unexpected error occurred: {str(e)}",
            response_type="error",
            success=False,
            error_message=str(e),
            visualization_created=False
        )

@router.get("/health")
async def health_check():
    """Health check for the combined pipeline"""
    try:
        # Check SQL agent health
        sql_health = await http_sql_agent.health_check()
        
        # Check visualization agent health
        viz_health = await visualization_agent.health_check()
        
        return {
            "status": "healthy",
            "sql_agent": sql_health,
            "visualization_agent": viz_health,
            "pipeline": "operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/sql-only")
async def process_sql_only(
    request: CombinedPipelineRequest,
    db1: Session = Depends(get_db1),
    db2: Session = Depends(get_db2)
):
    """Process query with SQL LLM only (no visualization)"""
    try:
        sql_response = await http_sql_agent.process_user_query(
            user_input=request.user_input,
            chat_id=request.chat_id,
            argo_context=request.argo_context
        )
        
        # # Store message in chat history
        # if request.chat_id and request.user_id:
        #     try:
        #         await store_message(
        #             request.chat_id, 
        #             request.user_id, 
        #             request.user_input,
        #             sql_response.get("response", ""),
        #             db2
        #         )
        #     except Exception as e:
        #         logger.warning(f"Failed to store message: {e}")
        
        return CombinedPipelineResponse(
            response=sql_response.get("response", ""),
            response_type="text",
            sql_query=sql_response.get("sql_query"),
            success=sql_response.get("success", False),
            error_message=sql_response.get("error_message"),
            visualization_created=False
        )
        
    except Exception as e:
        logger.error(f"Error in SQL-only pipeline: {e}")
        return CombinedPipelineResponse(
            response=f"An error occurred: {str(e)}",
            response_type="error",
            success=False,
            error_message=str(e),
            visualization_created=False
        )

@router.post("/visualization-test")
async def test_visualization(
    data: Dict[str, Any],
    viz_type: str = "scatter",
    title: str = "Test Visualization"
):
    """Test endpoint for visualization functionality"""
    try:
        # Create a simple test visualization
        if viz_type == "scatter":
            result = await visualization_agent.visualization_client.create_scatter_plot(
                data=data,
                x_column=list(data.keys())[0] if data else "x",
                y_column=list(data.keys())[1] if len(data.keys()) > 1 else "y",
                title=title
            )
        else:
            result = {"error": f"Unsupported visualization type: {viz_type}"}
        
        return {
            "success": not ("error" in result),
            "result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
