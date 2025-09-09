# HTTP MCP Server Implementation

This document describes the new HTTP-based MCP (Model Context Protocol) server implementation that replaces the stdio-based communication with JSON-RPC over HTTP.

## Overview

The new implementation provides the same SQL database operations as the original MCP server but uses HTTP/JSON-RPC communication instead of stdio. This eliminates subprocess management issues and provides better reliability and debugging capabilities.

## Architecture Changes

### Original Implementation (stdio-based)
- `mcp_server.py` - stdio-based MCP server using FastMCP
- `services/initialise_sql_llm.py` - Uses `SQLMCPClient` with stdio communication
- `agents/sqlagent_invocation.py` - SQL agent using stdio MCP client

### New Implementation (HTTP-based)
- `mcp_http_server.py` - HTTP-based MCP server using FastAPI and JSON-RPC
- `mcp_http_client.py` - HTTP client for JSON-RPC communication
- `services/initialise_sql_llm_http.py` - HTTP-based SQL LLM services
- `agents/sqlagent_invocation_http.py` - HTTP-based SQL agent
- `routers/sql_router_http.py` - HTTP-based SQL API routes

## Key Components

### 1. HTTP MCP Server (`mcp_http_server.py`)

FastAPI-based server that exposes MCP functionality via HTTP endpoints:

- **Base URL**: `http://127.0.0.1:8001`
- **Main endpoint**: `/mcp` (JSON-RPC)
- **Health check**: `/mcp/health`
- **Tools listing**: `/mcp/tools`

#### Available Tools
- `execute_sql_query` - Execute SQL queries
- `get_database_schema` - Get database schema information
- `list_tables` - List all tables in a database
- `get_table_info` - Get detailed table information

### 2. HTTP MCP Client (`mcp_http_client.py`)

HTTP client that communicates with the MCP server using JSON-RPC 2.0 protocol:

```python
from mcp_http_client import HTTPMCPClient

client = HTTPMCPClient()
await client.connect()
result = await client.execute_sql_query("SELECT * FROM users LIMIT 5")
await client.disconnect()
```

### 3. HTTP SQL Agent (`agents/sqlagent_invocation_http.py`)

Enhanced SQL agent that uses the HTTP MCP client:

```python
from agents.sqlagent_invocation_http import invoke_http_sql_agent

result = await invoke_http_sql_agent("What are the top 5 users by registration date?")
```

## API Endpoints

### HTTP-based SQL Operations

All HTTP-based endpoints are prefixed with `/api/v1/http/`:

- `POST /api/v1/http/generate-query` - Generate and execute SQL from natural language
- `POST /api/v1/http/stream-query` - Stream query processing
- `POST /api/v1/http/execute-raw` - Execute raw SQL queries
- `POST /api/v1/http/schema` - Get database schema
- `POST /api/v1/http/tables` - List database tables
- `POST /api/v1/http/table-info` - Get table information
- `GET /api/v1/http/database-status` - Check database and MCP status
- `GET /api/v1/http/mcp-health` - Check MCP server health
- `GET /api/v1/http/health` - Service health check

### Original stdio-based endpoints remain at `/api/v1/`

## Running the System

### Option 1: Integrated Mode (Recommended)

The HTTP MCP server runs automatically when you start the main FastAPI application:

```bash
cd d:\argo_bot\backend
python main.py
```

This starts:
- Main API server on port 8000
- HTTP MCP server on port 8001

### Option 2: Standalone HTTP MCP Server

Run only the HTTP MCP server:

```bash
python mcp_http_server.py
```

### Option 3: Both Implementations

You can run both stdio and HTTP implementations simultaneously to compare or migrate gradually.

## Testing

### Test the HTTP Implementation

```bash
python test_http_mcp.py
```

This script tests:
- HTTP MCP client connectivity
- SQL agent functionality
- Service initialization
- Comparison with stdio implementation

### Manual Testing

1. Start the servers:
```bash
python main.py
```

2. Test HTTP MCP health:
```bash
curl http://127.0.0.1:8001/mcp/health
```

3. Test JSON-RPC call:
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "execute_sql_query",
    "params": {"query": "SELECT 1 as test", "database_name": "default"},
    "id": 1
  }'
```

4. Test via main API:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/http/generate-query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me a test query"}'
```

## Migration Guide

### For Developers

To switch from stdio to HTTP implementation:

1. **Import changes**:
```python
# Old
from agents.sqlagent_invocation import invoke_sql_agent

# New
from agents.sqlagent_invocation_http import invoke_http_sql_agent
```

2. **Function calls remain the same**:
```python
# Both work identically
result = await invoke_sql_agent(question)
result = await invoke_http_sql_agent(question)
```

3. **Use HTTP endpoints**:
```
# Old
POST /api/v1/generate-query

# New  
POST /api/v1/http/generate-query
```

### For API Users

Simply change the endpoint prefix from `/api/v1/` to `/api/v1/http/` to use the HTTP implementation.

## Benefits of HTTP Implementation

1. **No subprocess management** - Eliminates process spawning issues
2. **Better error handling** - HTTP status codes and structured JSON errors
3. **Easier debugging** - Standard HTTP tools and logging
4. **Scalability** - HTTP servers can handle multiple concurrent requests
5. **Health monitoring** - Built-in health check endpoints
6. **Standard protocol** - Uses JSON-RPC 2.0 standard
7. **Network flexibility** - Can be deployed on different hosts if needed

## Configuration

### Environment Variables

Same as original implementation:
- `GOOGLE_API_KEY` - Google AI API key
- `DATABASE_URL` - PostgreSQL database URL
- `USER_DATABASE_URL` - SQLite database URL

### HTTP MCP Server Configuration

Default configuration in `mcp_http_server.py`:
- Host: `127.0.0.1`
- Port: `8001`
- Timeout: `30 seconds`

To customize:
```python
await start_http_mcp_server(host="0.0.0.0", port=8002)
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
```
Error: [Errno 10048] Only one usage of each socket address
```
Solution: Change the port or stop the conflicting service.

2. **Connection refused**:
```
Error: Connection refused to http://127.0.0.1:8001
```
Solution: Ensure the HTTP MCP server is running.

3. **Database connection errors**:
Check database URLs in `config.py` and ensure databases are accessible.

### Debugging

1. **Enable debug logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check HTTP MCP server logs**:
The server logs all requests and responses.

3. **Use health check endpoints**:
- `/mcp/health` - Basic server health
- `/api/v1/http/mcp-health` - Detailed MCP health
- `/api/v1/http/database-status` - Database connectivity

## Performance Considerations

- HTTP overhead is minimal for typical use cases
- Connection pooling is handled by httpx client
- JSON-RPC batching can be implemented if needed
- Database connections are reused within the server

## Security Notes

- Server runs on localhost by default
- No authentication implemented (same as stdio version)
- Consider adding authentication for production use
- Firewall rules may be needed if running on different hosts

## Future Enhancements

Possible improvements for the HTTP implementation:

1. **Authentication** - Add API key or token-based auth
2. **Caching** - Cache schema and metadata
3. **Batch operations** - Support JSON-RPC batch requests
4. **WebSocket support** - For real-time streaming
5. **Load balancing** - Multiple server instances
6. **Metrics** - Prometheus/monitoring integration

## Files Changed/Added

### New Files
- `mcp_http_server.py` - HTTP MCP server
- `mcp_http_client.py` - HTTP MCP client
- `services/initialise_sql_llm_http.py` - HTTP-based LLM services
- `agents/sqlagent_invocation_http.py` - HTTP-based SQL agent
- `routers/sql_router_http.py` - HTTP-based API routes
- `test_http_mcp.py` - Test suite

### Modified Files
- `main.py` - Added HTTP MCP server startup and HTTP routes
- Added this README

### Original Files (Unchanged)
- `mcp_server.py` - Original stdio MCP server
- `services/initialise_sql_llm.py` - Original LLM services
- `agents/sqlagent_invocation.py` - Original SQL agent
- `routers/sql_router.py` - Original SQL routes

This allows for side-by-side comparison and gradual migration.
