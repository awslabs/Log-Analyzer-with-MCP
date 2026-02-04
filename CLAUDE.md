# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Log-Analyzer-with-MCP is an MCP (Model Context Protocol) server that provides AI assistants access to AWS CloudWatch Logs for searching, analysis, and cross-service correlation.

## Commands

### Installation & Setup
```bash
uv sync                      # Install dependencies
source .venv/bin/activate    # Activate virtual environment
```

### Running the Server
```bash
# Via uvx (recommended for users)
uvx --from git+https://github.com/awslabs/Log-Analyzer-with-MCP cw-mcp-server [--profile PROFILE] [--region REGION] [--stateless]

# Local development
python -m cw_mcp_server.server [--profile PROFILE] [--region REGION] [--stateless]
```

### Linting & Formatting
```bash
pre-commit run --all-files   # Run ruff linting and formatting
```

### CLI Client (for testing)
```bash
python src/client.py list-groups [--prefix PREFIX]
python src/client.py search LOG_GROUP "query" [--hours N]
python src/client.py summarize LOG_GROUP [--hours N]
python src/client.py find-errors LOG_GROUP
python src/client.py correlate LOG_GROUP1 LOG_GROUP2 "search_term"
```

## Architecture

### Core Components

```
src/
├── client.py                    # Standalone CLI client for testing
└── cw_mcp_server/
    ├── server.py                # Main MCP server entry point
    ├── resources/
    │   └── cloudwatch_logs_resource.py  # CloudWatch data as MCP resources
    └── tools/
        ├── __init__.py          # @handle_exceptions decorator
        ├── utils.py             # Time range parsing utilities
        ├── search_tools.py      # Log search/query tools
        ├── analysis_tools.py    # Log analysis tools
        └── correlation_tools.py # Cross-service correlation
```

### Data Flow
```
AI Assistant / CLI Client → MCP Server (server.py) → Tool Classes → boto3 CloudWatch Logs Client → AWS
```

### Key Patterns

1. **AWS Config Decorator**: `@with_aws_config()` wraps tools to handle AWS profile/region override per-call
2. **Exception Handling**: `@handle_exceptions` in `tools/__init__.py` returns JSON errors instead of raising exceptions
3. **Async Operations**: All tool methods are async for CloudWatch Insights query polling
4. **Resource URIs**: MCP resources exposed via URIs like `logs://groups/{name}`, `logs://groups/{name}/streams`
5. **Time Range Flexibility**: Tools accept either `hours` offset or `start_time`/`end_time` ISO8601 timestamps

### MCP Server Structure

- **Entry Point**: `cw_mcp_server.server:main()`
- **Server Instance**: `FastMCP("CloudWatch Logs Analyzer", stateless_http=args.stateless)`
- **Decorators Used**: `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`

### Tool Classes

| Class | File | Purpose |
|-------|------|---------|
| `CloudWatchLogsResource` | `resources/cloudwatch_logs_resource.py` | Exposes log groups, streams, samples as resources |
| `CloudWatchLogsSearchTools` | `tools/search_tools.py` | `search_logs()`, `search_logs_multi()`, `filter_log_events()` |
| `CloudWatchLogsAnalysisTools` | `tools/analysis_tools.py` | `summarize_log_activity()`, `find_error_patterns()` |
| `CloudWatchLogsCorrelationTools` | `tools/correlation_tools.py` | `correlate_logs()` for cross-group analysis |

### Stateless Mode

The `--stateless` flag enables stateless HTTP mode for Amazon Bedrock AgentCore integration.

## Tech Stack

- **Python**: 3.12+
- **Package Manager**: uv
- **AWS SDK**: boto3
- **MCP Library**: mcp[cli] with FastMCP
- **Linting**: ruff (via pre-commit)

## Code Style

- **License header**: All Python files require Apache-2.0 header
- **Docstrings**: Google-style with Args/Returns
- **Returns**: All tools return `json.dumps(..., indent=2)`
- **Error handling**: Use `@handle_exceptions` decorator or return JSON errors
- **AWS params**: Always support `profile` and `region` parameters
- **Linting**: See `.pre-commit-config.yaml` for pinned ruff version

## Debugging

```bash
# MCP Inspector for interactive testing
npx @modelcontextprotocol/inspector python -m cw_mcp_server.server

# Enable debug logging
export MCP_LOG_LEVEL=debug
python -m cw_mcp_server.server

# Verify AWS credentials
aws sts get-caller-identity --profile PROFILE
```

## Dependency Management

```bash
uv add <package>             # Add dependency
uv add --dev <package>       # Add dev dependency
uv remove <package>          # Remove dependency
uv sync                      # Sync environment
```

## Git Conventions

- **Branch naming**: `feat/`, `fix/`, `docs/`, `refactor/`
- **Commit format**: `<type>: <description>` (e.g., `feat: add time range filtering`)

## Testing

```bash
# Manual testing via CLI
python src/client.py list-groups --prefix /aws/lambda
python src/client.py search "/aws/lambda/my-function" "ERROR"

# MCP Inspector
npx @modelcontextprotocol/inspector python -m cw_mcp_server.server
```

## Common Pitfalls

1. Don't raise exceptions in tools - return JSON errors
2. Decorator order: `@mcp.tool()` before `@with_aws_config()`
3. Tool function bodies are `pass` - logic lives in tool classes
4. Support both `hours` offset and ISO8601 `start_time`/`end_time` for time ranges
