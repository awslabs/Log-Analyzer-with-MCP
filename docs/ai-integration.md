# AI Integration Guide

## 🖥️ Claude Desktop Integration

You can add the configuration for the MCP server in Claude for Desktop for AI-assisted log analysis.

To get Claude for Desktop and how to add an MCP server, access [this link](https://modelcontextprotocol.io/quickstart/user). Add this to your respective json file:

```json
{
  "mcpServers": {
    "cw-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Log-Analyzer-with-MCP/src/cw-mcp-server",
        "run",
        "server.py"
      ]
    }
  },
}
```

## 🤖 Amazon Q CLI Integration

Amazon Q CLI acts as an MCP Client. To connect to MCP Servers and access the tools they surface, you need to create a configuration file called `mcp.json` in your Amazon Q configuration directory.

Your directory structure should look like this:

```bash
~/.aws
└── amazonq
    ├── mcp.json
    ├── profiles
    ├── cache
    ├── history
    └── prompts
```

If `mcp.json` is empty, edit it to add this to your MCP Server configuration file:

```json
{
  "mcpServers": {
    "cw-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Log-Analyzer-with-MCP/src/cw-mcp-server",
        "run",
        "server.py"
      ]
    }
  }
}
```

### Testing the configuration
Every time you start Amazon Q CLI, it will attempt to load any configured MCP Servers. You should see output indicating that the MCP Server has been discovered and initialized.

![image](https://github.com/user-attachments/assets/9acc1632-5a9a-4465-9fdc-a8464640f6a6)

If you're running into issues, check out the [troubleshooting guide](./troubleshooting.md) or open a GitHub Issue. 

## 🔍 AI Assistant Capabilities

With the enhanced tool support, AI assistants can now:

1. **Discover Log Groups**:
   - "Show me all my CloudWatch log groups"
   - "List log groups that start with /aws/lambda"
   - "Show me the next page of log groups"

2. **Understand Log Structure**:
   - "Analyze the structure of my API Gateway logs"
   - "What fields are common in these JSON logs?"
   - "Show me a sample of recent logs from this group"

3. **Diagnose Issues**:
   - "Find all errors in my Lambda logs from the past 24 hours"
   - "What's the most common error pattern in this log group?"
   - "Show me logs around the time this service crashed"

4. **Perform Analysis**:
   - "Compare log volumes between these three services"
   - "Find correlations between errors in my database and API logs"
   - "Analyze the trend of timeouts in my Lambda function"

>If you want to use different aws profile, just mention the profile name with your prompt - `"Show me all my CloudWatch log groups using <profile_name> profile"`

## 💬 AI Prompt Templates

The server provides specialized prompts that AI assistants can use:

1. **List and Explore Log Groups Prompt**:
   ```
   I'll help you explore the CloudWatch log groups in your AWS environment.
   First, I'll list the available log groups...
   ```

2. **Log Analysis Prompt**:
   ```
   Please analyze the following CloudWatch logs from the {log_group_name} log group.
   First, I'll get you some information about the log group...

   ```
3. **Profile Override**:
   ```
   I'll help you list CloudWatch log groups using the <profile_name> profile. Let me do that for you:
   ```
