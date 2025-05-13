#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import boto3
import json
import time
from datetime import datetime
from typing import List

from . import handle_exceptions
from .utils import get_time_range


class CloudWatchLogsSearchTools:
    """Tools for searching and querying CloudWatch Logs."""

    def __init__(self, profile_name=None):
        """Initialize the CloudWatch Logs client.
        
        Args:
            profile_name: Optional AWS profile name to use for credentials
        """
        # Initialize boto3 CloudWatch Logs client using specified profile or default credential chain
        self.profile_name = profile_name
        session = boto3.Session(profile_name=profile_name)
        self.logs_client = session.client("logs")

    @handle_exceptions
    async def search_logs(
        self,
        log_group_name: str,
        query: str,
        hours: int = 24,
        start_time: str = None,
        end_time: str = None,
    ) -> str:
        """
        Search logs using CloudWatch Logs Insights query.

        Args:
            log_group_name: The log group to search
            query: CloudWatch Logs Insights query syntax
            hours: Number of hours to look back
            start_time: Start time in ISO8601 format
            end_time: End time in ISO8601 format

        Returns:
            JSON string with search results
        """
        return await self.search_logs_multi(
            [log_group_name], query, hours, start_time, end_time
        )

    @handle_exceptions
    async def search_logs_multi(
        self,
        log_group_names: List[str],
        query: str,
        hours: int = 24,
        start_time: str = None,
        end_time: str = None,
    ) -> str:
        """
        Search logs across multiple log groups using CloudWatch Logs Insights query.

        Args:
            log_group_names: List of log groups to search
            query: CloudWatch Logs Insights query syntax
            hours: Number of hours to look back
            start_time: Start time in ISO8601 format
            end_time: End time in ISO8601 format

        Returns:
            JSON string with search results
        """
        start_ts, end_ts = get_time_range(hours, start_time, end_time)
        # Start the query
        start_query_response = self.logs_client.start_query(
            logGroupNames=log_group_names,
            startTime=start_ts,
            endTime=end_ts,
            queryString=query,
            limit=100,
        )
        query_id = start_query_response["queryId"]

        # Poll for query results
        response = None
        while response is None or response["status"] == "Running":
            await asyncio.sleep(1)  # Wait before checking again
            response = self.logs_client.get_query_results(queryId=query_id)

            # Avoid long-running queries
            if response["status"] == "Running":
                # Check if we've been running too long (30 seconds)
                if time.time() * 1000 - end_ts > 30000:
                    return json.dumps(
                        {
                            "status": "Timeout",
                            "error": "Search query failed to complete within time limit",
                        },
                        indent=2,
                    )

        # Process and format the results
        formatted_results = {
            "status": response["status"],
            "statistics": response.get("statistics", {}),
            "searchedLogGroups": log_group_names,
            "results": [],
        }

        for result in response.get("results", []):
            result_dict = {}
            for field in result:
                result_dict[field["field"]] = field["value"]
            formatted_results["results"].append(result_dict)

        return json.dumps(formatted_results, indent=2)

    @handle_exceptions
    async def filter_log_events(
        self,
        log_group_name: str,
        filter_pattern: str,
        hours: int = 24,
        start_time: str = None,
        end_time: str = None,
    ) -> str:
        """
        Filter log events by pattern across all streams in a log group.

        Args:
            log_group_name: The log group to filter
            filter_pattern: The pattern to search for (CloudWatch Logs filter syntax)
            hours: Number of hours to look back
            start_time: Start time in ISO8601 format
            end_time: End time in ISO8601 format

        Returns:
            JSON string with filtered events
        """
        start_ts, end_ts = get_time_range(hours, start_time, end_time)
        response = self.logs_client.filter_log_events(
            logGroupName=log_group_name,
            filterPattern=filter_pattern,
            startTime=start_ts,
            endTime=end_ts,
            limit=100,
        )

        events = response.get("events", [])
        formatted_events = []

        for event in events:
            formatted_events.append(
                {
                    "timestamp": datetime.fromtimestamp(
                        event.get("timestamp", 0) / 1000
                    ).isoformat(),
                    "message": event.get("message"),
                    "logStreamName": event.get("logStreamName"),
                }
            )

        return json.dumps(formatted_events, indent=2)
