# Detailed Usage Guide

## 🌐 Integrated with MCP clients (Claude for Desktop, Cursor, Windsurf, etc.) - recommended way for usage

AI assistants can leverage this MCP server. To understand more check out the [AI Integration Guide](./ai-integration.md)

## 🖥️ Standalone Server directly

The MCP server exposes CloudWatch logs data and analysis tools to AI assistants and MCP clients:

```bash
python src/cw-mcp-server/server.py
```

The server runs in the foreground by default. To run it in the background, you can use:

```bash
python src/cw-mcp-server/server.py &
```

## 📟 CLI Client (one off usage)

The project includes a command-line client for interacting with the MCP server:

```bash
# List available log groups
python src/client.py list-groups

# List log groups with a prefix filter
python src/client.py list-groups --prefix "/aws/lambda"

# Use the tool interface instead of resource
python src/client.py list-groups --use-tool

# Get a prompt for exploring log groups
python src/client.py list-prompt

# List log streams in a specific log group
python src/client.py list-streams "/aws/lambda/my-function"

# Get log events from a specific stream
python src/client.py get-events "/aws/lambda/my-function" "2023/06/01/[$LATEST]abcdef123456"

# Get a sample of recent logs
python src/client.py sample "/aws/lambda/my-function"

# Get recent errors
python src/client.py recent-errors "/aws/lambda/my-function"

# Get log structure analysis
python src/client.py structure "/aws/lambda/my-function"

# Search logs for a specific pattern
python src/client.py search "/aws/lambda/my-function" "filter @message like 'error'"

# Generate a summary of log activity
python src/client.py summarize "/aws/lambda/my-function" --hours 48

# Find common error patterns
python src/client.py find-errors "/aws/lambda/my-function"

# Correlate logs across multiple services
python src/client.py correlate "/aws/lambda/service1" "/aws/lambda/service2" "OrderId: 12345"
```

## 🧩 Example Workflows

### Finding and analyzing errors in a Lambda function using the standalone server directly

```bash
# 1. List your log groups to find the Lambda function
python src/client.py list-groups --prefix "/aws/lambda"

# 2. Generate a summary to see when errors occurred
python src/client.py summarize "/aws/lambda/my-function" --hours 24

# 3. Find the most common error patterns
python src/client.py find-errors "/aws/lambda/my-function"

# 4. Search for details about a specific error
python src/client.py search "/aws/lambda/my-function" "filter @message like 'ConnectionError'"
```

### Correlating requests across microservices using the standalone server directly

```bash
# Track a request ID across multiple services
python src/client.py correlate \
  "/aws/lambda/api-gateway" \
  "/aws/lambda/auth-service" \
  "/aws/lambda/payment-processor" \
  "req-abc123"
```

## 🔗 Resource URIs

The MCP server exposes CloudWatch Logs data through the following resource URIs:

| Resource URI | Description |
|--------------|-------------|
| `logs://groups` | List all log groups |
| `logs://groups/filter/{prefix}` | List log groups filtered by prefix |
| `logs://groups/{log_group_name}` | Get details about a specific log group |
| `logs://groups/{log_group_name}/streams` | List streams for a log group |
| `logs://groups/{log_group_name}/streams/{log_stream_name}` | Get events from a specific log stream |
| `logs://groups/{log_group_name}/sample` | Get a sample of recent logs |
| `logs://groups/{log_group_name}/recent-errors` | Get recent errors from a log group |
| `logs://groups/{log_group_name}/metrics` | Get log metrics (volume, frequency) |
| `logs://groups/{log_group_name}/structure` | Analyze log format and structure |

## 🧰 Tool Handlers

The server provides the following tool handlers for AI assistants:

| Tool | Description |
|------|-------------|
| `list_log_groups` | List available CloudWatch log groups with filtering options |
| `search_logs` | Execute CloudWatch Logs Insights queries |
| `filter_log_events` | Filter logs by pattern across all streams |
| `summarize_log_activity` | Generate time-based activity summaries |
| `find_error_patterns` | Identify common error patterns |
| `correlate_logs` | Find related events across multiple log groups | 