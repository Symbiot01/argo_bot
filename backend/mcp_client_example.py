# mcp_client_example.py

import asyncio
import logging
from utility_functions.sql_llm_functions import (
    get_sql_service,
    generate_sql_query,
    stream_sql_query,
    get_schema_info,
    get_tables_list
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Example usage of the SQL LLM system with MCP integration"""
    
    print("🚀 SQL LLM with MCP Integration Example")
    print("=" * 50)
    
    try:
        # Example 1: Get database schema
        print("\n📋 1. Getting Database Schema...")
        schema = await get_schema_info()
        if "error" not in schema:
            tables = list(schema.get("tables", {}).keys())
            print(f"   Found {len(tables)} tables: {tables[:5]}...")  # Show first 5
        else:
            print(f"   Error: {schema['error']}")
        
        # Example 2: List all tables
        print("\n📊 2. Listing Database Tables...")
        tables_result = await get_tables_list()
        if "error" not in tables_result:
            tables = tables_result.get("tables", [])
            print(f"   Tables: {tables}")
        else:
            print(f"   Error: {tables_result['error']}")
        
        # Example 3: Generate and execute SQL query
        print("\n🔍 3. Generating SQL Query from Natural Language...")
        question = "Show me all users who are active"
        result = await generate_sql_query(question)
        
        if result.get("success", False):
            print(f"   Question: {result['question']}")
            print(f"   Generated SQL: {result['sql_query']}")
            print(f"   Execution Status: {'Success' if result['success'] else 'Failed'}")
            if "csv_file" in result:
                print(f"   Results saved to: {result['csv_file']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Example 4: Stream query generation (more interactive)
        print("\n📡 4. Streaming SQL Query Generation...")
        question = "What are the top 10 most recent posts?"
        print(f"   Question: {question}")
        print("   Response:")
        
        async for chunk in stream_sql_query(question):
            print(chunk, end="", flush=True)
        print("\n")
        
        # Example 5: Complex query
        print("\n🧠 5. Complex Query Example...")
        complex_question = "Show me users with their post count, ordered by most active"
        result = await generate_sql_query(complex_question)
        
        if result.get("success", False):
            print(f"   Generated SQL: {result['sql_query']}")
            if "csv_file" in result:
                print(f"   Results saved to: {result['csv_file']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Example 6: Get SQL service health
        print("\n🏥 6. Checking SQL Service Health...")
        service = await get_sql_service()
        print(f"   Service initialized: {service.initialized}")
        print(f"   MCP client connected: {service.mcp_client is not None}")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n❌ Example failed: {e}")
    
    finally:
        # Cleanup
        try:
            service = await get_sql_service()
            await service.cleanup()
            print("🧹 Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def interactive_demo():
    """Interactive demo for testing SQL queries"""
    
    print("\n🎮 Interactive SQL LLM Demo")
    print("=" * 30)
    print("Enter natural language questions to generate SQL queries.")
    print("Type 'quit' to exit, 'schema' to see database schema, 'tables' to list tables.")
    
    try:
        while True:
            question = input("\n💬 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            elif question.lower() == 'schema':
                print("📋 Getting database schema...")
                schema = await get_schema_info()
                if "error" not in schema:
                    for table_name, table_info in schema.get("tables", {}).items():
                        print(f"   Table: {table_name}")
                        columns = table_info.get("columns", {})
                        for col_name, col_info in list(columns.items())[:3]:  # Show first 3 columns
                            print(f"     - {col_name}: {col_info.get('type', 'unknown')}")
                        if len(columns) > 3:
                            print(f"     ... and {len(columns) - 3} more columns")
                else:
                    print(f"   Error: {schema['error']}")
            
            elif question.lower() == 'tables':
                print("📊 Listing tables...")
                tables_result = await get_tables_list()
                if "error" not in tables_result:
                    tables = tables_result.get("tables", [])
                    for table in tables:
                        print(f"   - {table}")
                else:
                    print(f"   Error: {tables_result['error']}")
            
            elif question:
                print("🔍 Generating SQL query...")
                result = await generate_sql_query(question)
                
                if result.get("success", False):
                    print(f"   SQL: {result['sql_query']}")
                    if "csv_file" in result:
                        print(f"   📁 Results: {result['csv_file']}")
                else:
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    finally:
        try:
            service = await get_sql_service()
            await service.cleanup()
        except:
            pass

if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Run basic examples")
    print("2. Interactive demo")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(interactive_demo())
    else:
        asyncio.run(main())
