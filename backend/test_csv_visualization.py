#!/usr/bin/env python3
"""
Test script for CSV-based visualization functionality
"""

import asyncio
import pandas as pd
import os
import json
from services.initialise_visualization_llm import visualization_llm_service

async def test_csv_visualization():
    """Test the enhanced visualization system with CSV files"""
    
    # Create test CSV files with different scenarios
    test_cases = [
        {
            "name": "count_query",
            "data": {"count": [156789]},
            "expected_visualize": False,
            "description": "Single count result"
        },
        {
            "name": "geographic_data", 
            "data": {
                "latitude": [45.1, 45.2, 45.3, 45.4, 45.5],
                "longitude": [-125.1, -125.2, -125.3, -125.4, -125.5],
                "temperature": [15.2, 14.8, 15.1, 14.9, 15.3]
            },
            "expected_visualize": True,
            "description": "Geographic oceanographic data"
        },
        {
            "name": "time_series",
            "data": {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
                "temperature": [15.2, 14.8, 15.1, 14.9, 15.3],
                "salinity": [35.1, 35.2, 35.0, 35.3, 35.1]
            },
            "expected_visualize": True,
            "description": "Time series data"
        },
        {
            "name": "small_metadata",
            "data": {
                "table_name": ["argo_profiles", "argo_floats"],
                "record_count": [1234567, 8901]
            },
            "expected_visualize": False,
            "description": "Small metadata result"
        },
        {
            "name": "aggregated_stats",
            "data": {
                "stat_type": ["mean", "max", "min"],
                "temperature": [15.5, 28.2, 2.1],
                "salinity": [35.1, 37.8, 30.2]
            },
            "expected_visualize": True,
            "description": "Aggregated statistics with multiple rows"
        }
    ]
    
    print("Testing CSV-based visualization decisions...")
    print("=" * 60)
    
    # Create datasets directory if it doesn't exist
    os.makedirs("datasets", exist_ok=True)
    
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        
        # Create CSV file
        df = pd.DataFrame(test_case["data"])
        csv_path = f"datasets/test_{test_case['name']}.csv"
        df.to_csv(csv_path, index=False)
        
        # Test visualization decision
        try:
            decision = await visualization_llm_service.should_create_visualization(
                user_query=f"Test query for {test_case['description']}",
                data=None,  # Force it to load from CSV
                sql_query=f"SELECT * FROM test_{test_case['name']}",
                csv_file_path=csv_path
            )
            
            should_visualize = decision.get("should_visualize", False)
            reasoning = decision.get("reasoning", "No reasoning provided")
            viz_type = decision.get("visualization_type", "None")
            
            print(f"Expected visualization: {test_case['expected_visualize']}")
            print(f"Actual visualization: {should_visualize}")
            print(f"Visualization type: {viz_type}")
            print(f"Reasoning: {reasoning}")
            
            # Check if result matches expectation
            if should_visualize == test_case["expected_visualize"]:
                print("✅ PASS - Decision matches expectation")
            else:
                print("❌ FAIL - Decision doesn't match expectation")
                
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
        
        # Clean up test file
        if os.path.exists(csv_path):
            os.remove(csv_path)
    
    print("\n" + "=" * 60)
    print("CSV visualization testing completed!")

if __name__ == "__main__":
    asyncio.run(test_csv_visualization())
