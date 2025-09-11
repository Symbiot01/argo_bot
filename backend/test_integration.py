#!/usr/bin/env python3
"""
Test script to verify the integration between SQL LLM and Visualization LLM
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sql_to_visualization_integration():
    """Test the complete integration flow"""
    try:
        # Import the HTTP SQL agent
        from agents.sqlagent_invocation_http import http_sql_agent
        
        # Import the visualization agent
        from agents.visualization_agent_invocation import visualization_agent
        
        logger.info("Testing SQL to Visualization Integration")
        
        # Test query that should generate SQL and potentially visualization
        test_query = "Show me temperature and salinity data from the last 10 Argo float measurements"
        
        logger.info(f"Processing test query: {test_query}")
        
        # Step 1: Process with SQL agent
        sql_response = await http_sql_agent.process_user_query(
            user_input=test_query,
            chat_id=None,
            argo_context="Testing integration between SQL and visualization systems"
        )
        
        logger.info(f"SQL Response: {json.dumps(sql_response, indent=2, default=str)}")
        
        # Check if SQL was successful and returned data
        if sql_response.get("success") and sql_response.get("data"):
            logger.info("SQL query was successful, proceeding with visualization analysis")
            
            # Step 2: Test visualization decision
            data = sql_response.get("data", [])
            sql_query = sql_response.get("sql_query", "")
            document_link = sql_response.get("document_link")
            
            logger.info(f"Document link: {document_link}")
            logger.info(f"Data rows: {len(data)}")
            
            # Test visualization agent
            html_response, visualization_created = await visualization_agent.process_query_with_visualization(
                user_query=test_query,
                sql_data=data,
                sql_query=sql_query,
                chat_id=None,
                argo_context="Testing integration",
                document_link=document_link
            )
            
            logger.info(f"Visualization created: {visualization_created}")
            logger.info(f"HTML response length: {len(html_response)} characters")
            
            # Save the HTML response for inspection
            with open("test_integration_output.html", "w", encoding="utf-8") as f:
                f.write(html_response)
            
            logger.info("HTML response saved to test_integration_output.html")
            
            return {
                "success": True,
                "sql_successful": True,
                "data_count": len(data),
                "visualization_created": visualization_created,
                "document_link": document_link,
                "html_length": len(html_response)
            }
        
        else:
            logger.warning("SQL query did not return data or failed")
            return {
                "success": False,
                "sql_successful": False,
                "error": sql_response.get("error_message", "Unknown error")
            }
    
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def test_visualization_decision_only():
    """Test just the visualization decision logic"""
    try:
        from services.initialise_visualization_llm import visualization_llm_service
        
        # Mock data for testing
        mock_data = [
            {"temperature": 15.2, "salinity": 35.1, "latitude": 45.2, "longitude": -125.3, "depth": 10},
            {"temperature": 14.8, "salinity": 35.0, "latitude": 45.3, "longitude": -125.2, "depth": 20},
            {"temperature": 14.5, "salinity": 34.9, "latitude": 45.1, "longitude": -125.4, "depth": 30},
            {"temperature": 14.0, "salinity": 34.8, "latitude": 45.4, "longitude": -125.1, "depth": 40},
            {"temperature": 13.5, "salinity": 34.7, "latitude": 45.0, "longitude": -125.5, "depth": 50}
        ]
        
        test_query = "Show me temperature and salinity data with geographic coordinates"
        sql_query = "SELECT temperature, salinity, latitude, longitude, depth FROM argo_data LIMIT 5"
        
        logger.info("Testing visualization decision logic")
        
        decision = await visualization_llm_service.should_create_visualization(
            user_query=test_query,
            data=mock_data,
            sql_query=sql_query
        )
        
        logger.info(f"Visualization decision: {json.dumps(decision, indent=2)}")
        
        return decision
        
    except Exception as e:
        logger.error(f"Visualization decision test failed: {e}")
        return {"error": str(e)}

async def main():
    """Main test function"""
    logger.info("Starting integration tests")
    
    # Test 1: Visualization decision only
    logger.info("\n=== Test 1: Visualization Decision ===")
    viz_decision = await test_visualization_decision_only()
    
    # Test 2: Full integration (commented out to avoid database dependency)
    # logger.info("\n=== Test 2: Full Integration ===")
    # integration_result = await test_sql_to_visualization_integration()
    
    logger.info("\n=== Test Results ===")
    logger.info(f"Visualization Decision Test: {viz_decision}")
    # logger.info(f"Integration Test: {integration_result}")

if __name__ == "__main__":
    asyncio.run(main())
