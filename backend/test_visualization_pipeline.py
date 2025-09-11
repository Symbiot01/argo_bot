# test_visualization_pipeline.py

import asyncio
import json
import logging
from mcp_visualization_client import HTTPVisualizationMCPClient
from agents.visualization_agent_invocation import visualization_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_visualization_server():
    """Test the visualization MCP server"""
    print("=== Testing Visualization MCP Server ===")
    
    client = HTTPVisualizationMCPClient()
    
    # Test health check
    print("\n1. Testing health check...")
    health = await client.health_check()
    print(f"Health check result: {health}")
    
    # Test listing tools
    print("\n2. Testing list tools...")
    tools = await client.list_tools()
    print(f"Available tools: {len(tools.get('tools', []))} tools")
    for tool in tools.get('tools', []):
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Test scatter plot creation
    print("\n3. Testing scatter plot creation...")
    test_data = {
        "x": [1, 2, 3, 4, 5],
        "y": [2, 4, 6, 8, 10],
        "category": ["A", "B", "A", "B", "A"]
    }
    
    scatter_result = await client.create_scatter_plot(
        data=test_data,
        x_column="x",
        y_column="y",
        title="Test Scatter Plot",
        color_column="category"
    )
    print(f"Scatter plot result: {scatter_result}")
    
    # Test line plot creation
    print("\n4. Testing line plot creation...")
    line_result = await client.create_line_plot(
        data=test_data,
        x_column="x",
        y_column="y",
        title="Test Line Plot"
    )
    print(f"Line plot result: {line_result}")
    
    return True

async def test_visualization_agent():
    """Test the visualization agent with mock oceanographic data"""
    print("\n=== Testing Visualization Agent ===")
    
    # Mock oceanographic data
    mock_sql_data = [
        {
            "float_id": 5903916,
            "latitude": 35.5,
            "longitude": -15.2,
            "pressure": 10.0,
            "temperature": 18.5,
            "salinity": 35.1,
            "profile_time": "2023-01-15T10:30:00"
        },
        {
            "float_id": 5903916,
            "latitude": 35.5,
            "longitude": -15.2,
            "pressure": 50.0,
            "temperature": 16.2,
            "salinity": 35.3,
            "profile_time": "2023-01-15T10:30:00"
        },
        {
            "float_id": 5903916,
            "latitude": 35.5,
            "longitude": -15.2,
            "pressure": 100.0,
            "temperature": 14.8,
            "salinity": 35.5,
            "profile_time": "2023-01-15T10:30:00"
        }
    ]
    
    user_query = "Show me the temperature depth profile for float 5903916"
    sql_query = "SELECT pressure, temperature FROM measurements WHERE float_id = 5903916"
    
    try:
        html_response, viz_created = await visualization_agent.process_query_with_visualization(
            user_query=user_query,
            sql_data=mock_sql_data,
            sql_query=sql_query
        )
        
        print(f"Visualization created: {viz_created}")
        print(f"HTML response length: {len(html_response)} characters")
        print(f"HTML response preview: {html_response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error testing visualization agent: {e}")
        return False

async def test_health_checks():
    """Test health checks for all services"""
    print("\n=== Testing Health Checks ===")
    
    try:
        health = await visualization_agent.health_check()
        print(f"Visualization agent health: {health}")
        return True
    except Exception as e:
        print(f"Error in health check: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting Visualization Pipeline Tests")
    print("=" * 50)
    
    try:
        # Test individual components
        server_ok = await test_visualization_server()
        agent_ok = await test_visualization_agent()
        health_ok = await test_health_checks()
        
        print("\n" + "=" * 50)
        print("Test Results Summary:")
        print(f"Visualization Server: {'✓ PASS' if server_ok else '✗ FAIL'}")
        print(f"Visualization Agent: {'✓ PASS' if agent_ok else '✗ FAIL'}")
        print(f"Health Checks: {'✓ PASS' if health_ok else '✗ FAIL'}")
        
        if all([server_ok, agent_ok, health_ok]):
            print("\n🎉 All tests passed! Visualization pipeline is ready.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above.")
            
    except Exception as e:
        print(f"Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
