# test_sql_changes.py
"""
Test script to verify the changes made to remove vector database dependencies
and add PDF context support.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.initialise_sql_llm import load_database_schema, load_pdf_content, load_sql_examples
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

def test_pdf_loading():
    """Test loading PDF content"""
    print("\nTesting PDF content loading...")
    pdf_content = load_pdf_content()
    
    if pdf_content:
        print(f"✅ PDF content loaded successfully")
        print(f"Content length: {len(pdf_content)} characters")
        print(f"First 200 characters: {pdf_content[:200]}...")
    else:
        print("❌ Failed to load PDF content or PDF file not found")
    
    return pdf_content

def test_sql_examples_loading():
    """Test loading SQL examples"""
    print("\nTesting SQL examples loading...")
    sql_examples = load_sql_examples()
    
    if sql_examples:
        print(f"✅ SQL examples loaded successfully")
        print(f"Content length: {len(sql_examples)} characters")
        lines = sql_examples.count('\n')
        print(f"Number of lines: {lines}")
    else:
        print("❌ Failed to load SQL examples or no examples found")
    
    return sql_examples

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
    
    # Test PDF loading
    pdf_content = test_pdf_loading()
    
    # Test SQL examples loading
    sql_examples = test_sql_examples_loading()
    
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
    
    # Display content summaries
    if pdf_content:
        print(f"\n📄 PDF Content: {len(pdf_content)} characters loaded")
    
    if sql_examples:
        print(f"\n📝 SQL Examples: {len(sql_examples)} characters loaded")

if __name__ == "__main__":
    asyncio.run(main())
