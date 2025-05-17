#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import argparse
from typing import List

from mcp.server.fastmcp import FastMCP
from resources.cloudwatch_logs_resource import CloudWatchLogsResource
from tools.search_tools import CloudWatchLogsSearchTools
from tools.analysis_tools import CloudWatchLogsAnalysisTools
from tools.correlation_tools import CloudWatchLogsCorrelationTools

# Parse command line arguments
parser = argparse.ArgumentParser(description='CloudWatch Logs Analyzer MCP Server')
parser.add_argument('--profile', type=str, help='AWS profile name to use for credentials')
args, unknown = parser.parse_known_args()

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Create the MCP server for CloudWatch logs
mcp = FastMCP("CloudWatch Logs Analyzer")

# Initialize our resource and tools classes with the specified AWS profile
cw_resource = CloudWatchLogsResource(profile_name=args.profile)
search_tools = CloudWatchLogsSearchTools(profile_name=args.profile)
analysis_tools = CloudWatchLogsAnalysisTools(profile_name=args.profile)
correlation_tools = CloudWatchLogsCorrelationTools(profile_name=args.profile)

# ==============================
# Resource Handlers
# ==============================


@mcp.resource("logs://groups")
def get_log_groups() -> str:
    """Get a list of all CloudWatch Log Groups"""
    # Use default values for parameters
    prefix = None
    limit = 50
    next_token = None

    return cw_resource.get_log_groups(prefix, limit, next_token)


@mcp.resource("logs://groups/filter/{prefix}")
def get_filtered_log_groups(prefix: str) -> str:
    """
    Get a filtered list of CloudWatch Log Groups by prefix

    Args:
        prefix: The prefix to filter log groups by
    """
    # Default values for other parameters
    limit = 50
    next_token = None

    return cw_resource.get_log_groups(prefix, limit, next_token)


@mcp.resource("logs://groups/{log_group_name}")
def get_log_group_details(log_group_name: str) -> str:
    """Get detailed information about a specific log group"""
    return cw_resource.get_log_group_details(log_group_name)


@mcp.resource("logs://groups/{log_group_name}/streams")
def get_log_streams(log_group_name: str) -> str:
    """
    Get a list of log streams for a specific log group

    Args:
        log_group_name: The name of the log group
    """
    # Use default limit value
    limit = 20
    return cw_resource.get_log_streams(log_group_name, limit)


@mcp.resource("logs://groups/{log_group_name}/streams/{log_stream_name}")
def get_log_events(log_group_name: str, log_stream_name: str) -> str:
    """
    Get log events from a specific log stream

    Args:
        log_group_name: The name of the log group
        log_stream_name: The name of the log stream
    """
    # Use default limit value
    limit = 100
    return cw_resource.get_log_events(log_group_name, log_stream_name, limit)


@mcp.resource("logs://groups/{log_group_name}/sample")
def get_log_sample(log_group_name: str) -> str:
    """
    Get a sample of recent logs from a log group

    Args:
        log_group_name: The name of the log group
    """
    # Use default limit value
    limit = 10
    return cw_resource.get_log_sample(log_group_name, limit)


@mcp.resource("logs://groups/{log_group_name}/recent-errors")
def get_recent_errors(log_group_name: str) -> str:
    """
    Get recent error logs from a log group

    Args:
        log_group_name: The name of the log group
    """
    # Use default hours value
    hours = 24
    return cw_resource.get_recent_errors(log_group_name, hours)


@mcp.resource("logs://groups/{log_group_name}/metrics")
def get_log_metrics(log_group_name: str) -> str:
    """
    Get log volume metrics for a log group

    Args:
        log_group_name: The name of the log group
    """
    # Use default hours value
    hours = 24
    return cw_resource.get_log_metrics(log_group_name, hours)


@mcp.resource("logs://groups/{log_group_name}/structure")
def analyze_log_structure(log_group_name: str) -> str:
    """Analyze and provide information about the structure of logs"""
    return cw_resource.analyze_log_structure(log_group_name)


# ==============================
# Prompts
# ==============================


@mcp.prompt()
def list_cloudwatch_log_groups(prefix: str = None, profile: str = None) -> str:
    """
    Prompt for listing and exploring CloudWatch log groups.

    Args:
        profile: AWS profile name to use for credentials
        prefix: Optional prefix to filter log groups by name
    """
    prefix_text = f" starting with '{prefix}'" if prefix else ""
    profile_text = f" and using profile '{profile}'" if profile else ""
    return f"""I'll help you explore the CloudWatch log groups{prefix_text}{profile_text} in your AWS environment    

First, I'll list the available log groups. For each log group, I can help you:

1. Examine its structure and format
2. Check for recent errors or patterns
3. View metrics like volume and activity
4. Sample recent logs to understand the content
5. Search for specific patterns or events

Let me know which log group you'd like to explore further, or if you'd like to refine the search with a different prefix.
"""


@mcp.prompt()
def analyze_cloudwatch_logs(log_group_name: str, profile: str = None) -> str:
    """
    Prompt for analyzing CloudWatch logs to help identify issues, patterns, and insights.

    Args:
        profile: AWS profile name to use for credentials
        log_group_name: The name of the log group to analyze
    """
    profile_text = f" using profile '{profile}'" if profile else ""
    return f"""Please analyze the following CloudWatch logs from the {log_group_name} log group{profile_text}.

First, I'll get you some information about the log group:
1. Get the basic log group structure to understand the format of logs
2. Check for any recent errors
3. Examine the log volume metrics
4. Analyze a sample of recent logs

Based on this information, please:
- Identify any recurring errors or exceptions
- Look for unusual patterns or anomalies
- Suggest possible root causes for any issues found
- Recommend actions to resolve or mitigate problems
- Provide insights on performance or resource utilization

Feel free to ask for additional context if needed, such as:
- Correlation with logs from other services
- More specific time ranges for analysis
- Queries for specific error messages or events
"""


# ==============================
# Tool Handlers
# ==============================


@mcp.tool()
async def list_log_groups(
    prefix: str = None, profile: str = None, limit: int = 50, next_token: str = None
) -> str:
    """
    List available CloudWatch log groups with optional filtering by prefix.

    Args:
        profile: AWS profile name to use for credentials
        prefix: Optional prefix to filter log groups by name
        limit: Maximum number of log groups to return (default: 50)
        next_token: Token for pagination to get the next set of results

    Returns:
        JSON string with log groups information
    """
    cw_resource = CloudWatchLogsResource(profile_name=profile or args.profile)
    return cw_resource.get_log_groups(prefix, limit, next_token)


@mcp.tool()
async def search_logs(
    log_group_name: str,
    query: str,
    hours: int = 24,
    start_time: str = None,
    end_time: str = None,
    profile: str = None
) -> str:
    """
    Search logs using CloudWatch Logs Insights query.
    Args:
        log_group_name: The log group to search
        query: CloudWatch Logs Insights query syntax
        hours: Number of hours to look back
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time
    Returns:
        JSON string with search results
    """
    search_tools = CloudWatchLogsSearchTools(profile_name=profile or args.profile)
    return await search_tools.search_logs(
        log_group_name, query, hours, start_time, end_time
    )


@mcp.tool()
async def search_logs_multi(
    log_group_names: List[str],
    query: str,
    hours: int = 24,
    start_time: str = None,
    end_time: str = None,
    profile: str = None
) -> str:
    """
    Search logs across multiple log groups using CloudWatch Logs Insights.
    Args:
        log_group_names: List of log groups to search
        query: CloudWatch Logs Insights query in Logs Insights syntax
        hours: Number of hours to look back (default: 24)
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time
    Returns:
        JSON string with search results
    """
    search_tools = CloudWatchLogsSearchTools(profile_name=profile or args.profile)
    return await search_tools.search_logs_multi(
        log_group_names, query, hours, start_time, end_time
    )


@mcp.tool()
async def filter_log_events(
    log_group_name: str,
    filter_pattern: str,
    hours: int = 24,
    start_time: str = None,
    end_time: str = None,
    profile: str = None
) -> str:
    """
    Filter log events by pattern across all streams in a log group.
    Args:
        log_group_name: The log group to filter
        filter_pattern: The pattern to search for (CloudWatch Logs filter syntax)
        hours: Number of hours to look back
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time
    Returns:
        JSON string with filtered events
    """
    search_tools = CloudWatchLogsSearchTools(profile_name=profile or args.profile)
    return await search_tools.filter_log_events(
        log_group_name, filter_pattern, hours, start_time, end_time
    )


@mcp.tool()
async def summarize_log_activity(
    log_group_name: str, hours: int = 24, start_time: str = None, end_time: str = None, profile: str = None
) -> str:
    """
    Generate a summary of log activity over a specified time period.
    Args:
        log_group_name: The log group to analyze
        hours: Number of hours to look back
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time
    Returns:
        JSON string with activity summary
    """
    analysis_tools = CloudWatchLogsAnalysisTools(profile_name=profile or args.profile)
    return await analysis_tools.summarize_log_activity(
        log_group_name, hours, start_time, end_time
    )


@mcp.tool()
async def find_error_patterns(
    log_group_name: str, hours: int = 24, start_time: str = None, end_time: str = None, profile: str = None
) -> str:
    """
    Find common error patterns in logs.
    Args:
        log_group_name: The log group to analyze
        hours: Number of hours to look back
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time
    Returns:
        JSON string with error patterns
    """
    analysis_tools = CloudWatchLogsAnalysisTools(profile_name=profile or args.profile)
    return await analysis_tools.find_error_patterns(
        log_group_name, hours, start_time, end_time
    )


@mcp.tool()
async def correlate_logs(
    log_group_names: List[str],
    search_term: str,
    hours: int = 24,
    start_time: str = None,
    end_time: str = None,
    profile: str = None,
) -> str:
    """
    Correlate logs across multiple AWS services using a common search term.
    Args:
        log_group_names: List of log group names to search
        search_term: Term to search for in logs (request ID, transaction ID, etc.)
        hours: Number of hours to look back
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time
    Returns:
        JSON string with correlated events
    """
    correlation_tools = CloudWatchLogsCorrelationTools(profile_name=profile or args.profile)
    return await correlation_tools.correlate_logs(
        log_group_names, search_term, hours, start_time, end_time
    )


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
