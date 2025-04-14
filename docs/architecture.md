# 🏗️ Architecture Details

The following diagram illustrates the high-level architecture of the MCP CloudWatch Log Analyzer:

![Architecture Diagram](../docs/assets/Log-Analyzer-with-MCP-arch.png)

The architecture consists of three main components:

## 💻 Client Side
- AWS Credentials are configured on the client machine
- The local computer runs the MCP client applications
- MCP Server runs locally and manages the communication

## ☁️ AWS Cloud
- CloudWatch service provides the log data and search capabilities

## 🔄 Data Flow
- AWS Credentials flow from configuration to the client
- The client communicates with CloudWatch through the MCP Server
- The MCP Server mediates all interactions with AWS services

The project follows the Model Context Protocol architecture:

## 📚 Resources
Expose CloudWatch log groups, streams, and events as addressable URIs
- `logs://groups` - List all log groups
- `logs://groups/{log_group_name}/streams` - List streams for a specific group
- `logs://groups/{log_group_name}/streams/{log_stream_name}` - Get events from a stream

## 🧰 Tools
Provide functionality for log analysis, search, and correlation
- `list_log_groups` - List and filter available log groups
- `search_logs` - Search logs with CloudWatch Insights queries
- `summarize_log_activity` - Generate time-based activity summaries
- `find_error_patterns` - Identify common error patterns
- `correlate_logs` - Find related events across multiple log groups

## 💬 Prompts
Guide AI assistants through common workflows
- `list_cloudwatch_log_groups` - Help explore available log groups
- `analyze_cloudwatch_logs` - Guide log analysis process

## 🖥️ Server
Handles MCP protocol communication and AWS API integration
- Manages API access to CloudWatch Logs
- Handles asynchronous CloudWatch Logs Insights queries
- Provides structured data responses

## 📱 Client
Command-line interface for interacting with the server
- Parses commands and arguments
- Connects to the server via stdio
- Formats JSON responses for human readability 