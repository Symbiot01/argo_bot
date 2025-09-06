# simple_test.py
"""
Simple test to verify schema file loading without dependencies
"""

import json
import os

def test_schema_file():
    """Test loading schema from static file"""
    print("Testing schema file loading...")
    
    schema_file = "datasets/database_schema.json"
    
    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        return None
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        print(f"✅ Schema loaded successfully")
        print(f"Database: {schema_data.get('database_name', 'Unknown')}")
        
        if "tables" in schema_data:
            print(f"Tables found: {len(schema_data['tables'])}")
            for table_name, table_info in schema_data["tables"].items():
                columns = list(table_info.get("columns", {}).keys())
                print(f"  - {table_name}: {len(columns)} columns")
        
        return schema_data
        
    except Exception as e:
        print(f"❌ Error loading schema: {e}")
        return None

def main():
    """Run the test"""
    print("🧪 Testing schema file...")
    print("=" * 50)
    
    schema = test_schema_file()
    
    print("\n" + "=" * 50)
    if schema:
        print("✅ Schema test passed!")
    else:
        print("❌ Schema test failed!")

if __name__ == "__main__":
    main()
