# test_sql_changes.py
"""
Test script to verify the changes made to remove schema retriever
and add chat history support.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.initialise_sql_vector_db import load_database_schema
from utility_functions.chat_history import get_chat_history, format_chat_history_for_context

async def test_schema_loading():
    """Test loading schema from static file"""
    print("Testing schema loading...")
    schema = load_database_schema()
    
    if schema:
        print(f"✅ Schema loaded successfully")
        print(f"Database: {schema.get('database_name', 'Unknown')}")
        print(f"Tables: {list(schema.get('tables', {}).keys())}")
    else:
        print("❌ Failed to load schema")
    
    return schema

def test_chat_history():
    """Test chat history functions"""
    print("\nTesting chat history functions...")
    
    # Test with a non-existent chat ID (should return empty list)
    chat_history = get_chat_history(999999, limit=5)
    print(f"Chat history for non-existent chat: {len(chat_history)} messages")
    
    # Test formatting
    formatted = format_chat_history_for_context(chat_history)
    print(f"Formatted history length: {len(formatted)} characters")
    
    return chat_history

async def main():
    """Run all tests"""
    print("🧪 Testing SQL system changes...")
    print("=" * 50)
    
    # Test schema loading
    schema = await test_schema_loading()
    
    # Test chat history
    chat_history = test_chat_history()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    
    # Display schema structure if loaded
    if schema and "tables" in schema:
        print(f"\n📊 Schema Summary:")
        for table_name, table_info in schema["tables"].items():
            columns = list(table_info.get("columns", {}).keys())
            print(f"  {table_name}: {len(columns)} columns")

if __name__ == "__main__":
    asyncio.run(main())
