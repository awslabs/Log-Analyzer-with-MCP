#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import boto3
import json
from datetime import datetime, timedelta

from . import handle_exceptions


class CloudWatchLogsAnalysisTools:
    """Tools for analyzing CloudWatch Logs data."""

    def __init__(self):
        """Initialize the CloudWatch Logs client."""
        # Initialize boto3 CloudWatch Logs client using default credential chain
        self.logs_client = boto3.client("logs")

    @handle_exceptions
    async def summarize_log_activity(self, log_group_name: str, hours: int = 24) -> str:
        """
        Generate a summary of log activity over a specified time period.

        Args:
            log_group_name: The log group to analyze
            hours: Number of hours to look back

        Returns:
            JSON string with activity summary
        """
        # Calculate time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)

        # Use CloudWatch Logs Insights to get a summary
        query = """
        stats count(*) as logEvents,
              count_distinct(stream) as streams
        | sort @timestamp desc
        | limit 1000
        """

        # Start the query
        start_query_response = self.logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query,
        )

        query_id = start_query_response["queryId"]

        # Poll for query results
        response = None
        while response is None or response["status"] == "Running":
            await asyncio.sleep(1)  # Wait before checking again
            response = self.logs_client.get_query_results(queryId=query_id)

        # Get the hourly distribution
        hourly_query = """
        stats count(*) as count by bin(1h)
        | sort @timestamp desc
        | limit 24
        """

        # Start the hourly query
        hourly_query_response = self.logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=hourly_query,
        )

        hourly_query_id = hourly_query_response["queryId"]

        # Poll for hourly query results
        hourly_response = None
        while hourly_response is None or hourly_response["status"] == "Running":
            await asyncio.sleep(1)  # Wait before checking again
            hourly_response = self.logs_client.get_query_results(
                queryId=hourly_query_id
            )

        # Process the main summary results
        summary = {
            "timeRange": {
                "start": datetime.fromtimestamp(start_time / 1000).isoformat(),
                "end": datetime.fromtimestamp(end_time / 1000).isoformat(),
                "hours": hours,
            },
            "logEvents": 0,
            "uniqueStreams": 0,
            "hourlyDistribution": [],
        }

        # Extract the main stats
        for result in response.get("results", []):
            for field in result:
                if field["field"] == "logEvents":
                    summary["logEvents"] = int(field["value"])
                elif field["field"] == "streams":
                    summary["uniqueStreams"] = int(field["value"])

        # Extract the hourly distribution
        for result in hourly_response.get("results", []):
            hour_data = {}
            for field in result:
                if field["field"] == "bin(1h)":
                    hour_data["hour"] = field["value"]
                elif field["field"] == "count":
                    hour_data["count"] = int(field["value"])

            if hour_data:
                summary["hourlyDistribution"].append(hour_data)

        return json.dumps(summary, indent=2)

    @handle_exceptions
    async def find_error_patterns(self, log_group_name: str, hours: int = 24) -> str:
        """
        Find common error patterns in logs.

        Args:
            log_group_name: The log group to analyze
            hours: Number of hours to look back

        Returns:
            JSON string with error patterns
        """
        # Calculate time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)

        # Query for error logs
        error_query = """
        filter @message like /(?i)(error|exception|fail|traceback)/
        | stats count(*) as errorCount by @message
        | sort errorCount desc
        | limit 20
        """

        # Start the query
        start_query_response = self.logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=error_query,
        )

        query_id = start_query_response["queryId"]

        # Poll for query results
        response = None
        while response is None or response["status"] == "Running":
            await asyncio.sleep(1)  # Wait before checking again
            response = self.logs_client.get_query_results(queryId=query_id)

        # Process the results
        error_patterns = {
            "timeRange": {
                "start": datetime.fromtimestamp(start_time / 1000).isoformat(),
                "end": datetime.fromtimestamp(end_time / 1000).isoformat(),
                "hours": hours,
            },
            "errorPatterns": [],
        }

        for result in response.get("results", []):
            pattern = {}
            for field in result:
                if field["field"] == "@message":
                    pattern["message"] = field["value"]
                elif field["field"] == "errorCount":
                    pattern["count"] = int(field["value"])

            if pattern:
                error_patterns["errorPatterns"].append(pattern)

        return json.dumps(error_patterns, indent=2)
