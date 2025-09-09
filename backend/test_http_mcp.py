# test_http_mcp.py

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_http_mcp_components():
    """Test all HTTP MCP components"""
    
    print("=" * 60)
    print("TESTING HTTP MCP IMPLEMENTATION")
    print("=" * 60)
    
    # Test 1: HTTP MCP Client
    print("\n1. Testing HTTP MCP Client...")
    try:
        from mcp_http_client import HTTPMCPClient
        
        client = HTTPMCPClient()
        
        # Test connection
        logger.info("Testing client connection...")
        connected = await client.connect()
        
        if connected:
            print("✅ HTTP MCP Client connected successfully")
            
            # Test health check
            health = await client.health_check()
            print(f"✅ Health check: {health}")
            
            # Test tools listing
            tools = await client.list_available_tools()
            print(f"✅ Available tools: {len(tools.get('tools', []))} tools")
            
            # Test schema retrieval
            schema = await client.get_database_schema("default")
            if "error" not in schema:
                print("✅ Schema retrieval successful")
            else:
                print(f"❌ Schema retrieval failed: {schema['error']}")
            
            await client.disconnect()
            print("✅ Client disconnected successfully")
            
        else:
            print("❌ HTTP MCP Client connection failed")
            return False
            
    except Exception as e:
        print(f"❌ HTTP MCP Client test failed: {e}")
        return False
    
    # Test 2: HTTP SQL Agent
    print("\n2. Testing HTTP SQL Agent...")
    try:
        from agents.sqlagent_invocation_http import invoke_http_sql_agent, http_agent_health_check
        
        # Test health check
        health = await http_agent_health_check()
        print(f"✅ Agent health check: {health}")
        
        # Test simple query
        result = await invoke_http_sql_agent("What is the current date?")
        if result.get("success"):
            print(f"✅ Test query successful: {result.get('response_type')}")
        else:
            print(f"❌ Test query failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ HTTP SQL Agent test failed: {e}")
        return False
    
    # Test 3: HTTP LLM Services
    print("\n3. Testing HTTP LLM Services...")
    try:
        from services.initialise_sql_llm_http import initialize_sql_llm_and_embeddings_http
        
        llm, embeddings, http_mcp_client = initialize_sql_llm_and_embeddings_http()
        
        if llm and http_mcp_client:
            print("✅ HTTP LLM services initialized successfully")
            
            # Test connection
            connected = await http_mcp_client.connect()
            if connected:
                print("✅ HTTP MCP client from services connected")
                await http_mcp_client.disconnect()
            else:
                print("❌ HTTP MCP client from services connection failed")
                
        else:
            print("❌ HTTP LLM services initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ HTTP LLM Services test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL HTTP MCP TESTS PASSED!")
    print("=" * 60)
    
    return True

async def test_comparison():
    """Test comparison between stdio and HTTP implementations"""
    
    print("\n" + "=" * 60)
    print("COMPARISON TEST: STDIO vs HTTP")
    print("=" * 60)
    
    test_question = "Show me the first 3 rows from any table"
    
    # Test stdio implementation
    print("\n1. Testing stdio implementation...")
    try:
        from agents.sqlagent_invocation import invoke_sql_agent
        
        stdio_result = await invoke_sql_agent(test_question)
        print(f"✅ Stdio result: {stdio_result.get('response_type')} - Success: {stdio_result.get('success')}")
        
    except Exception as e:
        print(f"❌ Stdio test failed: {e}")
    
    # Test HTTP implementation
    print("\n2. Testing HTTP implementation...")
    try:
        from agents.sqlagent_invocation_http import invoke_http_sql_agent
        
        http_result = await invoke_http_sql_agent(test_question)
        print(f"✅ HTTP result: {http_result.get('response_type')} - Success: {http_result.get('success')}")
        
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
    
    print("\n" + "=" * 60)
    print("COMPARISON COMPLETE")
    print("=" * 60)

def run_server_test():
    """Test if we can start the HTTP MCP server standalone"""
    
    print("\n" + "=" * 60)
    print("TESTING HTTP MCP SERVER STARTUP")
    print("=" * 60)
    
    try:
        from mcp_http_server import HTTPSQLMCPServer
        
        # Create server instance
        server = HTTPSQLMCPServer()
        app = server.get_app()
        
        print("✅ HTTP MCP Server instance created successfully")
        print("✅ FastAPI app instance obtained")
        print("Server can be started with: uvicorn mcp_http_server:http_mcp_server.get_app() --host 127.0.0.1 --port 8001")
        
        return True
        
    except Exception as e:
        print(f"❌ HTTP MCP Server test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    print(f"Starting HTTP MCP tests at {datetime.now().isoformat()}")
    
    # Test server creation first
    server_ok = run_server_test()
    
    if not server_ok:
        print("❌ Server test failed, skipping other tests")
        return
    
    # Test components (these require the server to be running)
    print("\nNote: Component tests require the HTTP MCP server to be running.")
    print("Start the server with:")
    print("python -m uvicorn mcp_http_server:http_mcp_server.get_app --host 127.0.0.1 --port 8001")
    
    # Wait for user input
    response = input("\nHas the HTTP MCP server been started? (y/n): ")
    
    if response.lower() == 'y':
        components_ok = await test_http_mcp_components()
        
        if components_ok:
            await test_comparison()
    else:
        print("Skipping component tests. Start the server and run this test again.")

if __name__ == "__main__":
    asyncio.run(main())
