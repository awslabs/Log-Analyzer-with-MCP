#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import argparse
import json
import sys
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Set up argument parser for the CLI
parser = argparse.ArgumentParser(description="CloudWatch Logs MCP Client")
parser.add_argument(
    "--profile", type=str, help="AWS profile name to use for credentials"
)
parser.add_argument("--region", type=str, help="AWS region name to use for API calls")
subparsers = parser.add_subparsers(dest="command", help="Command to execute")

# List log groups command
list_groups_parser = subparsers.add_parser(
    "list-groups", help="List CloudWatch log groups"
)
list_groups_parser.add_argument("--prefix", help="Filter log groups by name prefix")
list_groups_parser.add_argument(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of log groups to return (default: 50)",
)
list_groups_parser.add_argument(
    "--next-token", help="Token for pagination to get the next set of results"
)
list_groups_parser.add_argument(
    "--use-tool", action="store_true", help="Use the tool interface instead of resource"
)
list_groups_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
list_groups_parser.add_argument("--region", help="AWS region name to use for API calls")

# Get log group details command
group_details_parser = subparsers.add_parser(
    "group-details", help="Get detailed information about a log group"
)
group_details_parser.add_argument("log_group_name", help="The name of the log group")
group_details_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
group_details_parser.add_argument(
    "--region", help="AWS region name to use for API calls"
)

# List log streams command
list_streams_parser = subparsers.add_parser(
    "list-streams", help="List log streams for a specific log group"
)
list_streams_parser.add_argument("log_group_name", help="The name of the log group")
list_streams_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
list_streams_parser.add_argument(
    "--region", help="AWS region name to use for API calls"
)

# Get log events command
get_events_parser = subparsers.add_parser(
    "get-events", help="Get log events from a specific log stream"
)
get_events_parser.add_argument("log_group_name", help="The name of the log group")
get_events_parser.add_argument("log_stream_name", help="The name of the log stream")
get_events_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
get_events_parser.add_argument("--region", help="AWS region name to use for API calls")

# Get log sample command
sample_parser = subparsers.add_parser(
    "sample", help="Get a sample of recent logs from a log group"
)
sample_parser.add_argument("log_group_name", help="The name of the log group")
sample_parser.add_argument(
    "--limit", type=int, default=10, help="Number of logs to sample (default: 10)"
)
sample_parser.add_argument("--profile", help="AWS profile name to use for credentials")
sample_parser.add_argument("--region", help="AWS region name to use for API calls")

# Get recent errors command
errors_parser = subparsers.add_parser(
    "recent-errors", help="Get recent error logs from a log group"
)
errors_parser.add_argument(
    "log_group_name", help="The name of the log group to analyze"
)
errors_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
errors_parser.add_argument("--profile", help="AWS profile name to use for credentials")
errors_parser.add_argument("--region", help="AWS region name to use for API calls")

# Get log metrics command
metrics_parser = subparsers.add_parser(
    "metrics", help="Get log volume metrics for a log group"
)
metrics_parser.add_argument(
    "log_group_name", help="The name of the log group to analyze"
)
metrics_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
metrics_parser.add_argument("--profile", help="AWS profile name to use for credentials")
metrics_parser.add_argument("--region", help="AWS region name to use for API calls")

# Analyze log structure command
structure_parser = subparsers.add_parser(
    "structure", help="Analyze the structure of logs in a log group"
)
structure_parser.add_argument(
    "log_group_name", help="The name of the log group to analyze"
)
structure_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
structure_parser.add_argument("--region", help="AWS region name to use for API calls")

# Get analyze logs prompt command
prompt_parser = subparsers.add_parser(
    "get-prompt", help="Get a prompt for analyzing CloudWatch logs"
)
prompt_parser.add_argument(
    "log_group_name", help="The name of the log group to analyze"
)
prompt_parser.add_argument("--profile", help="AWS profile name to use for credentials")
prompt_parser.add_argument("--region", help="AWS region name to use for API calls")

# Get list groups prompt command
list_prompt_parser = subparsers.add_parser(
    "list-prompt", help="Get a prompt for listing CloudWatch log groups"
)
list_prompt_parser.add_argument(
    "--prefix", help="Optional prefix to filter log groups by name"
)
list_prompt_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
list_prompt_parser.add_argument("--region", help="AWS region name to use for API calls")

# Search logs command
search_parser = subparsers.add_parser(
    "search", help="Search for patterns in CloudWatch logs"
)
search_parser.add_argument("log_group_name", help="The name of the log group to search")
search_parser.add_argument(
    "query", help="The search query (CloudWatch Logs Insights syntax)"
)
search_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
search_parser.add_argument(
    "--start-time", type=str, help="Start time (ISO8601, e.g. 2024-06-01T00:00:00Z)"
)
search_parser.add_argument(
    "--end-time", type=str, help="End time (ISO8601, e.g. 2024-06-01T23:59:59Z)"
)
search_parser.add_argument("--profile", help="AWS profile name to use for credentials")
search_parser.add_argument("--region", help="AWS region name to use for API calls")

# Search multiple log groups command
search_multi_parser = subparsers.add_parser(
    "search-multi", help="Search for patterns across multiple CloudWatch log groups"
)
search_multi_parser.add_argument(
    "log_group_names", nargs="+", help="List of log group names to search"
)
search_multi_parser.add_argument(
    "query", help="The search query (CloudWatch Logs Insights syntax)"
)
search_multi_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
search_multi_parser.add_argument(
    "--start-time", type=str, help="Start time (ISO8601, e.g. 2024-06-01T00:00:00Z)"
)
search_multi_parser.add_argument(
    "--end-time", type=str, help="End time (ISO8601, e.g. 2024-06-01T23:59:59Z)"
)
search_multi_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
search_multi_parser.add_argument(
    "--region", help="AWS region name to use for API calls"
)

# Summarize log activity command
summarize_parser = subparsers.add_parser(
    "summarize", help="Generate a summary of log activity"
)
summarize_parser.add_argument(
    "log_group_name", help="The name of the log group to analyze"
)
summarize_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
summarize_parser.add_argument(
    "--start-time", type=str, help="Start time (ISO8601, e.g. 2024-06-01T00:00:00Z)"
)
summarize_parser.add_argument(
    "--end-time", type=str, help="End time (ISO8601, e.g. 2024-06-01T23:59:59Z)"
)
summarize_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
summarize_parser.add_argument("--region", help="AWS region name to use for API calls")

# Find error patterns command
errors_parser = subparsers.add_parser(
    "find-errors", help="Find common error patterns in logs"
)
errors_parser.add_argument(
    "log_group_name", help="The name of the log group to analyze"
)
errors_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
errors_parser.add_argument(
    "--start-time", type=str, help="Start time (ISO8601, e.g. 2024-06-01T00:00:00Z)"
)
errors_parser.add_argument(
    "--end-time", type=str, help="End time (ISO8601, e.g. 2024-06-01T23:59:59Z)"
)
errors_parser.add_argument("--profile", help="AWS profile name to use for credentials")
errors_parser.add_argument("--region", help="AWS region name to use for API calls")

# Correlate logs command
correlate_parser = subparsers.add_parser(
    "correlate", help="Correlate logs across multiple AWS services"
)
correlate_parser.add_argument(
    "log_group_names", nargs="+", help="List of log group names to search"
)
correlate_parser.add_argument("search_term", help="Term to search for in logs")
correlate_parser.add_argument(
    "--hours", type=int, default=24, help="Number of hours to look back (default: 24)"
)
correlate_parser.add_argument(
    "--start-time", type=str, help="Start time (ISO8601, e.g. 2024-06-01T00:00:00Z)"
)
correlate_parser.add_argument(
    "--end-time", type=str, help="End time (ISO8601, e.g. 2024-06-01T23:59:59Z)"
)
correlate_parser.add_argument(
    "--profile", help="AWS profile name to use for credentials"
)
correlate_parser.add_argument("--region", help="AWS region name to use for API calls")


async def main():
    """Main function to run the CloudWatch Logs MCP client."""
    args = parser.parse_args()

    def add_aws_config_args(tool_args):
        """Add profile and region arguments to tool calls if specified."""
        if args.profile:
            tool_args["profile"] = args.profile
        if args.region:
            tool_args["region"] = args.region
        return tool_args

    # Determine the server path (relative or absolute)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "cw-mcp-server", "server.py")

    # Prepare server arguments
    server_args = [server_path]
    if args.profile:
        server_args.extend(["--profile", args.profile])
    if args.region:
        server_args.extend(["--region", args.region])

    # Create server parameters
    server_params = StdioServerParameters(command="python3", args=server_args, env=None)

    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the client session
            await session.initialize()

            # Check if a command was specified
            if args.command is None:
                parser.print_help()
                return

            try:
                # Execute the requested command
                if args.command == "list-groups":
                    if args.use_tool:
                        # Use the tool interface
                        tool_args = {}
                        if args.prefix:
                            tool_args["prefix"] = args.prefix
                        if args.limit:
                            tool_args["limit"] = args.limit
                        if args.next_token:
                            tool_args["next_token"] = args.next_token
                        tool_args = add_aws_config_args(tool_args)

                        result = await session.call_tool(
                            "list_log_groups", arguments=tool_args
                        )
                        print_json_response(result)
                    else:
                        # Use the resource interface
                        # Build query string for parameters if provided
                        if args.prefix:
                            # If prefix is provided, use the filtered endpoint
                            resource_uri = f"logs://groups/filter/{args.prefix}"
                        else:
                            resource_uri = "logs://groups"

                        content, _ = await session.read_resource(resource_uri)
                        print_json_response(content)

                elif args.command == "group-details":
                    resource_uri = f"logs://groups/{args.log_group_name}"
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "list-streams":
                    resource_uri = f"logs://groups/{args.log_group_name}/streams"
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "get-events":
                    resource_uri = f"logs://groups/{args.log_group_name}/streams/{args.log_stream_name}"
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "sample":
                    resource_uri = (
                        f"logs://groups/{args.log_group_name}/sample?limit={args.limit}"
                    )
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "recent-errors":
                    resource_uri = f"logs://groups/{args.log_group_name}/recent-errors?hours={args.hours}"
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "metrics":
                    resource_uri = f"logs://groups/{args.log_group_name}/metrics?hours={args.hours}"
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "structure":
                    resource_uri = f"logs://groups/{args.log_group_name}/structure"
                    content, _ = await session.read_resource(resource_uri)
                    print_json_response(content)

                elif args.command == "get-prompt":
                    # Get the analyze logs prompt from the server
                    arguments = {"log_group_name": args.log_group_name}
                    arguments = add_aws_config_args(arguments)
                    result = await session.get_prompt(
                        "analyze_cloudwatch_logs",
                        arguments=arguments,
                    )

                    # Extract and print the prompt text
                    prompt_messages = result.messages
                    if prompt_messages and len(prompt_messages) > 0:
                        message = prompt_messages[0]
                        if hasattr(message, "content") and hasattr(
                            message.content, "text"
                        ):
                            print(message.content.text)
                        else:
                            print(
                                json.dumps(
                                    message, default=lambda x: x.__dict__, indent=2
                                )
                            )
                    else:
                        print("No prompt received.")

                elif args.command == "list-prompt":
                    # Get arguments for the prompt
                    arguments = {}
                    if args.prefix:
                        arguments["prefix"] = args.prefix
                    arguments = add_aws_config_args(arguments)

                    # Get the list logs prompt from the server
                    result = await session.get_prompt(
                        "list_cloudwatch_log_groups", arguments=arguments
                    )

                    # Extract and print the prompt text
                    prompt_messages = result.messages
                    if prompt_messages and len(prompt_messages) > 0:
                        message = prompt_messages[0]
                        if hasattr(message, "content") and hasattr(
                            message.content, "text"
                        ):
                            print(message.content.text)
                        else:
                            print(
                                json.dumps(
                                    message, default=lambda x: x.__dict__, indent=2
                                )
                            )
                    else:
                        print("No prompt received.")

                elif args.command == "search":
                    tool_args = {
                        "log_group_name": args.log_group_name,
                        "query": args.query,
                    }
                    if args.start_time:
                        tool_args["start_time"] = args.start_time
                    if args.end_time:
                        tool_args["end_time"] = args.end_time
                    if not (args.start_time or args.end_time):
                        tool_args["hours"] = args.hours
                    tool_args = add_aws_config_args(tool_args)
                    result = await session.call_tool(
                        "search_logs",
                        arguments=tool_args,
                    )
                    print_json_response(result)

                elif args.command == "search-multi":
                    tool_args = {
                        "log_group_names": args.log_group_names,
                        "query": args.query,
                    }
                    if args.start_time:
                        tool_args["start_time"] = args.start_time
                    if args.end_time:
                        tool_args["end_time"] = args.end_time
                    if not (args.start_time or args.end_time):
                        tool_args["hours"] = args.hours
                    tool_args = add_aws_config_args(tool_args)
                    result = await session.call_tool(
                        "search_logs_multi",
                        arguments=tool_args,
                    )
                    print_json_response(result)

                elif args.command == "summarize":
                    tool_args = {
                        "log_group_name": args.log_group_name,
                    }
                    if args.start_time:
                        tool_args["start_time"] = args.start_time
                    if args.end_time:
                        tool_args["end_time"] = args.end_time
                    if not (args.start_time or args.end_time):
                        tool_args["hours"] = args.hours
                    tool_args = add_aws_config_args(tool_args)
                    result = await session.call_tool(
                        "summarize_log_activity",
                        arguments=tool_args,
                    )
                    print_json_response(result)

                elif args.command == "find-errors":
                    tool_args = {
                        "log_group_name": args.log_group_name,
                    }
                    if args.start_time:
                        tool_args["start_time"] = args.start_time
                    if args.end_time:
                        tool_args["end_time"] = args.end_time
                    if not (args.start_time or args.end_time):
                        tool_args["hours"] = args.hours
                    tool_args = add_aws_config_args(tool_args)
                    result = await session.call_tool(
                        "find_error_patterns",
                        arguments=tool_args,
                    )
                    print_json_response(result)

                elif args.command == "correlate":
                    tool_args = {
                        "log_group_names": args.log_group_names,
                        "search_term": args.search_term,
                    }
                    if args.start_time:
                        tool_args["start_time"] = args.start_time
                    if args.end_time:
                        tool_args["end_time"] = args.end_time
                    if not (args.start_time or args.end_time):
                        tool_args["hours"] = args.hours
                    tool_args = add_aws_config_args(tool_args)
                    result = await session.call_tool(
                        "correlate_logs",
                        arguments=tool_args,
                    )
                    print_json_response(result)

            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                sys.exit(1)


def print_json_response(content: str):
    """Print JSON content in a formatted way."""
    try:
        # Parse the JSON content and print it in a pretty format
        parsed = json.loads(content)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        # If it's not valid JSON, print it as is
        print(content)


if __name__ == "__main__":
    asyncio.run(main())
