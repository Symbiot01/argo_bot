# CSV-Based Visualization System

## Overview

The visualization system has been enhanced to intelligently handle CSV files returned by the SQL agent instead of requiring all data to be loaded into memory. This approach improves performance and scalability while making smarter decisions about when visualization is beneficial.

## Key Changes

### 1. Enhanced Visualization LLM Service (`services/initialise_visualization_llm.py`)

**New Features:**
- **CSV Data Loading**: `_load_csv_data()` method loads data from CSV files with intelligent sampling for large datasets
- **CSV Analysis**: `_analyze_csv_for_visualization()` performs quick analysis to determine visualization worthiness
- **Smart Sampling**: Large datasets (>10,000 rows) are intelligently sampled to maintain performance
- **Enhanced Decision Logic**: More sophisticated criteria for when visualization is beneficial

**Key Decision Criteria:**
- ❌ **Skip visualization for:**
  - Single value results (count queries)
  - Small datasets (<5 rows) with limited numeric data
  - Purely text/metadata results
  - Simple aggregated results with 1-2 data points

- ✅ **Recommend visualization for:**
  - Geographic data (lat/lon coordinates)
  - Time series data (temporal patterns)
  - Depth profiles (oceanographic measurements)
  - Multi-dimensional datasets (>5 rows with numeric columns)
  - Statistical distributions
  - Correlation analysis

### 2. Updated Visualization Agent (`agents/visualization_agent_invocation.py`)

**Enhancements:**
- **Flexible Data Handling**: Can work with data in memory OR load from CSV files
- **Performance Optimization**: Intelligent sampling for large CSV files
- **Error Resilience**: Graceful handling when CSV files are not accessible

### 3. Improved Combined Pipeline (`routers/combined_pipeline_router.py`)

**Updates:**
- **CSV File Path Handling**: Properly passes CSV file paths to visualization pipeline
- **Flexible Data Sources**: Works whether SQL agent returns data in memory or CSV files
- **Fallback Mechanisms**: Continues processing even if visualization fails

## Usage Examples

### Example 1: Count Query (No Visualization)
```sql
SELECT COUNT(*) FROM argo_profiles WHERE date > '2024-01-01'
```
**Result:** Single value (e.g., 156789)
**Decision:** ❌ No visualization - single count value doesn't benefit from visualization

### Example 2: Geographic Data (Visualization Recommended)
```sql
SELECT latitude, longitude, temperature 
FROM argo_profiles 
WHERE date BETWEEN '2024-01-01' AND '2024-01-07'
LIMIT 100
```
**Result:** Multiple rows with lat/lon coordinates
**Decision:** ✅ Create geographic visualization - spatial data benefits greatly from mapping

### Example 3: Time Series (Visualization Recommended)
```sql
SELECT date, AVG(temperature) as avg_temp 
FROM argo_profiles 
WHERE float_id = 12345 
GROUP BY date 
ORDER BY date
```
**Result:** Temporal data with trends
**Decision:** ✅ Create line plot - time series data shows patterns better visually

### Example 4: Small Metadata Result (No Visualization)
```sql
SELECT table_name, COUNT(*) 
FROM information_schema.tables 
WHERE table_schema = 'argo'
```
**Result:** 2-3 rows of table names and counts
**Decision:** ❌ No visualization - simple metadata doesn't need visual representation

## Performance Optimizations

### 1. Intelligent Sampling
- **Large datasets (>10,000 rows)**: Random sampling preserves statistical properties
- **Very large datasets (>30,000 rows)**: Stratified sampling when possible
- **Moderate datasets**: Evenly spaced sampling to preserve patterns

### 2. Lazy Loading
- Data is only loaded from CSV when needed for visualization
- HTML responses can be generated without loading full datasets
- Memory usage is optimized for large query results

### 3. Quick Analysis
- CSV files are analyzed using pandas metadata operations
- Fast determination of data characteristics (row count, column types, etc.)
- Early exit for obviously non-visual data

## Configuration

### Environment Variables
```bash
# Maximum rows to load for visualization (default: 10000)
MAX_VISUALIZATION_ROWS=10000

# CSV output directory (default: datasets)
CSV_OUTPUT_DIR=datasets
```

### Thresholds
- **Minimum rows for visualization**: 5 (configurable)
- **Maximum sample size**: 10,000 rows
- **Geographic data**: Always visualized regardless of size
- **Time series**: Visualized if >3 data points

## Testing

Run the test script to verify CSV visualization decisions:

```bash
python test_csv_visualization.py
```

This tests various scenarios including:
- Count queries
- Geographic data
- Time series
- Metadata results
- Aggregated statistics

## Benefits

1. **Performance**: No need to load large datasets into memory for simple queries
2. **Scalability**: Can handle massive query results through CSV files
3. **Intelligence**: Makes smarter decisions about when visualization adds value
4. **Flexibility**: Works with both in-memory data and CSV files
5. **Resource Efficiency**: Reduces memory usage and API payload sizes

## Integration Points

### SQL Agent → Visualization Pipeline
```python
# SQL agent returns CSV file path
response = {
    "csv_file": "datasets/query_result_20240911_123456.csv",
    "document_link": "datasets/query_result_20240911_123456.csv",
    "response_type": "sql"
}

# Visualization pipeline processes CSV
html_response, viz_created = await visualization_agent.process_query_with_visualization(
    user_query="Show temperature trends",
    sql_data=None,  # Data will be loaded from CSV
    document_link=response["csv_file"]
)
```

### API Response
```json
{
    "response": "<html>...</html>",
    "response_type": "html",
    "visualization_created": true,
    "data_summary": {
        "total_rows": 1500,
        "columns": ["date", "temperature", "latitude", "longitude"],
        "sample_count": 5
    }
}
```

This enhanced system provides a more efficient, intelligent, and scalable approach to handling visualization decisions for oceanographic data analysis.
