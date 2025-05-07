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


class CloudWatchLogsCorrelationTools:
    """Tools for correlating logs across multiple CloudWatch Log groups."""

    def __init__(self):
        """Initialize the CloudWatch Logs client."""
        # Initialize boto3 CloudWatch Logs client using default credential chain
        self.logs_client = boto3.client("logs")

    @handle_exceptions
    async def correlate_logs(
        self,
        log_group_names: List[str],
        search_term: str,
        hours: int = 24,
        start_time: str = None,
        end_time: str = None,
    ) -> str:
        """
        Correlate logs across multiple AWS services using a common search term.

        Args:
            log_group_names: List of log group names to search
            search_term: Term to search for in logs (request ID, transaction ID, etc.)
            hours: Number of hours to look back
            start_time: Start time in ISO8601 format
            end_time: End time in ISO8601 format

        Returns:
            JSON string with correlated events
        """
        start_ts, end_ts = get_time_range(hours, start_time, end_time)

        # Validate inputs
        if not log_group_names:
            return json.dumps(
                {"status": "Error", "error": "No log groups specified"}, indent=2
            )

        if not search_term:
            return json.dumps(
                {"status": "Error", "error": "No search term specified"}, indent=2
            )

        # Results dictionary
        results = {
            "timeRange": {
                "start": datetime.fromtimestamp(start_ts / 1000).isoformat(),
                "end": datetime.fromtimestamp(end_ts / 1000).isoformat(),
                "hours": hours,
            },
            "searchTerm": search_term,
            "logGroups": {},
            "correlatedEvents": [],
        }

        # Get relevant logs from each group
        for log_group_name in log_group_names:
            # Use CloudWatch Logs Insights query
            query = f"""
            filter @message like "{search_term}"
            | sort @timestamp asc
            | limit 100
            """

            # Start the query
            start_query_response = self.logs_client.start_query(
                logGroupName=log_group_name,
                startTime=start_ts,
                endTime=end_ts,
                queryString=query,
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
                        response = {"status": "Timeout", "results": []}
                        break

            # Process results for this log group
            log_group_events = []

            for result in response.get("results", []):
                event = {"logGroup": log_group_name, "timestamp": None, "message": None}

                for field in result:
                    if field["field"] == "@timestamp":
                        event["timestamp"] = field["value"]
                    elif field["field"] == "@message":
                        event["message"] = field["value"]
                    elif field["field"] == "@logStream":
                        event["logStream"] = field["value"]

                if event["timestamp"] and event["message"]:
                    log_group_events.append(event)
                    results["correlatedEvents"].append(event)

            # Store events for this log group
            results["logGroups"][log_group_name] = {
                "eventCount": len(log_group_events),
                "events": log_group_events,
            }

        # Sort all correlated events by timestamp
        results["correlatedEvents"] = sorted(
            results["correlatedEvents"], key=lambda x: x.get("timestamp", "")
        )

        return json.dumps(results, indent=2)
