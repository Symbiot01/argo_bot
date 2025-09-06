# SQL LLM with MCP Integration

This implementation provides a sophisticated SQL query generation system using Large Language Models (LLM) integrated with Model Context Protocol (MCP) for database operations.

## Architecture Overview

The system consists of three main components:

1. **SQL LLM Chain** - Generates SQL queries from natural language using RAG (Retrieval Augmented Generation)
2. **Vector Database** - Stores database schema and SQL examples for knowledge retrieval
3. **MCP Client/Server** - Handles actual database operations and query execution

## Features

### 🔍 Natural Language to SQL
- Convert natural language questions to SQL queries
- Context-aware query generation using database schema
- Support for complex queries with JOINs, aggregations, and subqueries

### 🗃️ Database Schema Integration
- Automatic schema extraction and vectorization
- Table relationships and constraint awareness
- Column type and constraint information

### 📊 Query Execution & Results
- Execute generated SQL queries safely
- Export results to CSV files in `datasets/` folder
- Real-time streaming of query generation process

### 🔌 MCP Integration
- Model Context Protocol for secure database operations
- Support for PostgreSQL and SQLite databases
- Isolated execution environment

## File Structure

```
backend/
├── services/
│   ├── initialise_sql_llm.py      # LLM and MCP client initialization
│   └── initialise_sql_vector_db.py # Vector database setup
├── routers/
│   └── sql_router.py              # FastAPI endpoints for SQL operations
├── utility_functions/
│   └── sql_llm_functions.py       # Core SQL LLM service functions
├── mcp_server.py                  # MCP server for database operations
├── mcp_config.json               # MCP server configuration
├── start_mcp_server.py           # MCP server startup script
└── datasets/
    ├── sql_examples/             # SQL query examples for training
    └── query_result_*.csv        # Generated query results
```

## Setup Instructions

### 1. Environment Variables

Create a `.env` file with the following variables:

```env
# Google AI API Key for LLM
GOOGLE_API_KEY=your_google_api_key

# Pinecone for Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_SQL_INDEX_NAME=sql-knowledge-base

# Database Connections
DATABASE_URL=postgresql://postgres_buoy:buoy_sih123@localhost:5432/database
USER_DATABASE_URL=sqlite:///./user_data.db
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the MCP Server

```bash
python start_mcp_server.py
```

### 4. Start the Main API Server

```bash
uvicorn main:app --reload
```

## API Endpoints

### Generate SQL Query
```http
POST /api/v1/sql/generate-query
Content-Type: application/json

{
    "question": "Show me all users who have posted in the last 30 days",
    "database_name": "default"
}
```

### Stream Query Generation
```http
POST /api/v1/sql/stream-query
Content-Type: application/json

{
    "question": "What are the top 10 most active users?",
    "database_name": "default"
}
```

### Execute Raw SQL
```http
POST /api/v1/sql/execute-raw
Content-Type: application/json

{
    "query": "SELECT COUNT(*) FROM users WHERE status = 'active'",
    "database_name": "default"
}
```

### Get Database Schema
```http
POST /api/v1/sql/schema
Content-Type: application/json

{
    "database_name": "default"
}
```

### List Tables
```http
POST /api/v1/sql/tables
Content-Type: application/json

{
    "database_name": "default"
}
```

### Get Query Results
```http
GET /api/v1/sql/results
```

### Download CSV File
```http
GET /api/v1/sql/results/query_result_20250101_120000.csv
```

## Usage Examples

### 1. Basic Query Generation

```python
from utility_functions.sql_llm_functions import generate_sql_query

# Generate and execute SQL from natural language
result = await generate_sql_query(
    "Show me all users who registered in the last month"
)

print(f"Generated SQL: {result['sql_query']}")
print(f"Results saved to: {result['csv_file']}")
```

### 2. Streaming Query Generation

```python
from utility_functions.sql_llm_functions import stream_sql_query

# Stream the query generation process
async for chunk in stream_sql_query("What are the most popular products?"):
    print(chunk, end="")
```

### 3. Schema Exploration

```python
from utility_functions.sql_llm_functions import get_schema_info

# Get database schema
schema = await get_schema_info("default")
print(f"Tables: {list(schema['tables'].keys())}")
```

## MCP Server Configuration

The MCP server is configured through `mcp_config.json`:

```json
{
  "databases": {
    "default": {
      "type": "postgresql",
      "url": "postgresql://user:pass@host:port/db"
    },
    "sqlite": {
      "type": "sqlite", 
      "url": "sqlite:///./data.db"
    }
  },
  "tools": [
    "execute_sql_query",
    "get_database_schema", 
    "list_tables",
    "get_table_info"
  ]
}
```

## Vector Database Setup

The system automatically:

1. **Extracts Database Schema** - Tables, columns, relationships, indexes
2. **Loads SQL Examples** - From `datasets/sql_examples/` directory
3. **Creates Embeddings** - Using Google's text-embedding-004 model
4. **Stores in Pinecone** - For fast similarity search during query generation

## SQL Query Examples

The system includes comprehensive SQL examples in `datasets/sql_examples/`:

- **common_queries.sql** - Basic SELECT, JOIN, aggregation patterns
- **postgresql_specific.sql** - PostgreSQL-specific features (JSON, arrays, CTEs)

## Error Handling

The system includes robust error handling:

- **SQL Syntax Errors** - Detected and reported with suggestions
- **Database Connection Issues** - Automatic retry and fallback mechanisms
- **Query Timeout** - Configurable timeouts for long-running queries
- **Permission Errors** - Proper error messages for access issues

## Security Considerations

1. **SQL Injection Prevention** - All queries are parameterized
2. **Read-Only Operations** - Default configuration allows only SELECT queries
3. **Query Validation** - Queries are validated before execution
4. **Database Isolation** - MCP server provides isolation between operations

## Monitoring and Logging

All operations are logged with appropriate levels:

- **INFO** - Successful operations
- **WARNING** - Non-critical issues
- **ERROR** - Failed operations with details

Logs are written to both console and `mcp_server.log` file.

## Performance Optimization

1. **Vector Database Caching** - Schema information is cached in Pinecone
2. **Connection Pooling** - Database connections are reused
3. **Query Result Streaming** - Large results are streamed to avoid memory issues
4. **Async Operations** - All database operations are asynchronous

## Troubleshooting

### Common Issues

1. **MCP Server Not Starting**
   ```bash
   # Check if port is available
   netstat -an | grep :8000
   
   # Check logs
   tail -f mcp_server.log
   ```

2. **Database Connection Failed**
   ```bash
   # Test connection manually
   psql postgresql://user:pass@host:port/db
   ```

3. **Vector Database Issues**
   ```bash
   # Check Pinecone API key
   python -c "import pinecone; print('API key valid')"
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Multi-Database Support** - Query across multiple databases
2. **Query Optimization** - Automatic query performance optimization
3. **Data Visualization** - Automatic chart generation from query results
4. **Natural Language Explanations** - Explain query results in natural language
5. **Query History** - Store and search previous queries
6. **Collaborative Features** - Share queries and results with team members

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.