# Visualization MCP Server and Pipeline Documentation

## Overview

This document describes the new visualization system added to the Argo Bot backend, which extends the existing SQL MCP server with comprehensive data visualization capabilities.

## Architecture

The visualization system consists of several modular components:

### 1. Visualization MCP Server (`mcp_visualization_server.py`)
- **Port**: 8002
- **Protocol**: HTTP JSON-RPC
- **Purpose**: Handles visualization creation and AWS S3 storage
- **Functions**:
  - `create_scatter_plot`: Geographic plots, correlation analysis
  - `create_line_plot`: Time series, depth profiles
  - `create_heatmap`: Correlation matrices, spatial data
  - `create_depth_profile`: Ocean depth vs measurement profiles
  - `create_geographic_plot`: Float location mapping
  - `create_histogram`: Data distribution analysis

### 2. Visualization LLM Service (`services/initialise_visualization_llm.py`)
- **Model**: Google Gemini 1.5 Pro
- **Purpose**: Intelligent visualization decision making and HTML response generation
- **Functions**:
  - Analyzes query results to determine if visualization is beneficial
  - Selects appropriate visualization type based on data characteristics
  - Generates comprehensive HTML responses with embedded visualizations

### 3. Visualization Agent (`agents/visualization_agent_invocation.py`)
- **Purpose**: Orchestrates the complete visualization pipeline
- **Workflow**:
  1. Receives SQL query results from SQL LLM
  2. Determines if visualization is needed using LLM
  3. Creates appropriate visualizations via MCP server
  4. Generates comprehensive HTML response

### 4. Combined Pipeline Router (`routers/combined_pipeline_router.py`)
- **Endpoints**:
  - `POST /api/v1/pipeline/combined-pipeline`: Full SQL + Visualization pipeline
  - `POST /api/v1/pipeline/sql-only`: SQL processing only
  - `POST /api/v1/pipeline/visualization-test`: Test visualization creation
  - `GET /api/v1/pipeline/health`: Health check for entire pipeline

## Data Flow

```
User Query → SQL LLM → SQL Execution → Visualization Decision → Visualization Creation → HTML Response
     ↓             ↓             ↓              ↓                    ↓                ↓
   Natural      SQL Query    Data Result   LLM Analysis      MCP Server         Comprehensive
   Language                                                   + S3 Upload         HTML + Image
```

## Configuration

### Environment Variables
```bash
# AWS S3 Configuration (optional - falls back to local storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Google AI Configuration (required)
GOOGLE_API_KEY=your_gemini_api_key
```

### S3 Bucket Setup
- **Bucket Name**: `argo-bot-visualizations` (configurable in code)
- **Folder Structure**: `visualizations/`
- **File Format**: PNG images with timestamps
- **Permissions**: Public read access for image display

## API Usage

### Combined Pipeline Request
```json
{
    "user_input": "Show me temperature vs depth for float 5903916",
    "chat_id": "optional_chat_id",
    "user_id": "optional_user_id", 
    "include_visualization": true,
    "argo_context": "Additional context about Argo floats"
}
```

### Response Format
```json
{
    "response": "<html>Comprehensive analysis with embedded visualization</html>",
    "response_type": "html",
    "sql_query": "SELECT pressure, temperature FROM measurements WHERE float_id = 5903916",
    "data_summary": {
        "total_rows": 150,
        "columns": ["pressure", "temperature"],
        "sample_count": 5
    },
    "visualization_created": true,
    "visualization_url": "https://s3-bucket-url/visualization.png",
    "success": true
}
```

## Visualization Types and Use Cases

### 1. Scatter Plot
- **Use Cases**: Geographic plotting, correlation analysis
- **Example**: Float locations, temperature vs salinity relationships
- **Columns**: x_column, y_column, optional color_column

### 2. Line Plot  
- **Use Cases**: Time series analysis, trend visualization
- **Example**: Temperature changes over time, multiple float trajectories
- **Columns**: x_column, y_column, optional group_column

### 3. Depth Profile
- **Use Cases**: Ocean vertical profiles
- **Example**: Temperature/salinity vs depth/pressure
- **Columns**: depth_column (pressure), value_column (measurement)

### 4. Geographic Plot
- **Use Cases**: Spatial distribution of floats
- **Example**: Float deployment locations with color-coded properties
- **Columns**: lat_column, lon_column, optional color_column

### 5. Heatmap
- **Use Cases**: Correlation analysis, spatial data matrices
- **Example**: Inter-variable correlations, depth-time temperature grids
- **Options**: correlation=true for correlation matrices

### 6. Histogram
- **Use Cases**: Data distribution analysis
- **Example**: Distribution of temperature measurements, salinity ranges
- **Columns**: column, optional bins parameter

## Intelligent Visualization Decision

The system uses an LLM to automatically determine when visualizations are beneficial:

### Recommended Scenarios:
- Geographic/spatial queries (latitude/longitude data)
- Time series data with temporal patterns
- Depth profile queries (pressure/depth relationships)
- Statistical distribution questions
- Correlation analysis requests
- Multi-variable comparisons

### Not Recommended:
- Simple count queries
- Single value results
- Text-only metadata
- Very small datasets (< 5 rows)

## Error Handling and Fallbacks

### S3 Upload Failure
- Automatically falls back to local file storage
- Returns local file paths when S3 is unavailable
- Continues operation without visualization if all storage fails

### Visualization Creation Failure
- Returns SQL LLM response without visualization
- Logs errors for debugging
- Maintains system availability

### LLM Service Failure
- Falls back to rule-based visualization decisions
- Continues with basic HTML formatting
- Preserves core functionality

## Testing

### Manual Testing
```bash
# Run the test script
python test_visualization_pipeline.py
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/pipeline/health

# Test combined pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/combined-pipeline \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show me temperature data for float 5903916", "include_visualization": true}'
```

## Performance Considerations

### Image Generation
- Uses matplotlib with optimized DPI (300) for quality
- Automatic plot cleanup to prevent memory leaks
- Configurable timeouts for visualization creation

### S3 Upload
- Asynchronous uploads to prevent blocking
- Automatic retry logic for failed uploads
- Optimized image formats (PNG with compression)

### LLM Calls
- Low temperature (0.1) for consistent decisions
- Prompt optimization to reduce token usage
- Caching strategies for repeated queries

## Monitoring and Logging

### Health Checks
- Individual service health monitoring
- End-to-end pipeline verification
- AWS S3 connectivity status

### Logging Levels
- INFO: Normal operation events
- WARNING: Fallback activations, non-critical errors
- ERROR: Service failures, critical issues

### Metrics to Monitor
- Visualization creation success rate
- S3 upload success rate
- LLM response times
- Overall pipeline latency

## Future Enhancements

### Planned Features
1. **Interactive Visualizations**: Plotly integration for interactive plots
2. **Custom Styling**: User-configurable visualization themes
3. **Batch Processing**: Multiple visualization creation in single request
4. **Caching**: Visualization result caching for repeated queries
5. **Analytics**: Usage analytics and optimization insights

### Scalability Improvements
1. **Worker Queues**: Background processing for visualization creation
2. **CDN Integration**: CloudFront distribution for faster image delivery
3. **Multi-region**: Geographic distribution of visualization services
4. **Load Balancing**: Multiple visualization server instances

## Troubleshooting

### Common Issues

1. **S3 Upload Failures**
   - Check AWS credentials and permissions
   - Verify bucket existence and access policies
   - Monitor AWS service status

2. **Visualization Quality Issues**
   - Adjust DPI settings in visualization server
   - Check data quality and completeness
   - Verify column mappings in requests

3. **LLM Decision Errors**
   - Review prompt templates for edge cases
   - Check API key validity and rate limits
   - Monitor token usage and costs

4. **Performance Issues**
   - Monitor memory usage during plot generation
   - Check network latency to S3
   - Optimize data transfer sizes

### Debug Mode
Enable detailed logging by setting log level to DEBUG in the initialization modules.
