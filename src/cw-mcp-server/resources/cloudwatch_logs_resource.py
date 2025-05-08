#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List
import re
from collections import Counter


class CloudWatchLogsResource:
    """Resource class for handling CloudWatch Logs resources."""

    def __init__(self, profile_name=None):
        """Initialize the CloudWatch Logs resource client.
        
        Args:
            profile_name: Optional AWS profile name to use for credentials
        """
        # Initialize boto3 CloudWatch Logs client using specified profile or default credential chain
        session = boto3.Session(profile_name=profile_name)
        self.logs_client = session.client("logs")

    def get_log_groups(
        self, prefix: str = None, limit: int = 50, next_token: str = None
    ) -> str:
        """
        Get a list of CloudWatch Log Groups with optional filtering and pagination.

        Args:
            prefix: Optional prefix to filter log groups by name
            limit: Maximum number of log groups to return (default: 50)
            next_token: Token for pagination to get the next set of results

        Returns:
            JSON string with log groups information
        """
        kwargs = {"limit": limit}
        if prefix:
            kwargs["logGroupNamePrefix"] = prefix
        if next_token:
            kwargs["nextToken"] = next_token

        response = self.logs_client.describe_log_groups(**kwargs)
        log_groups = response.get("logGroups", [])

        # Format the log groups information
        formatted_groups = []
        for group in log_groups:
            formatted_groups.append(
                {
                    "name": group.get("logGroupName"),
                    "arn": group.get("arn"),
                    "storedBytes": group.get("storedBytes"),
                    "creationTime": datetime.fromtimestamp(
                        group.get("creationTime", 0) / 1000
                    ).isoformat(),
                }
            )

        # Include the nextToken if available
        result = {"logGroups": formatted_groups}

        if "nextToken" in response:
            result["nextToken"] = response["nextToken"]

        return json.dumps(result, indent=2)

    def get_log_group_details(self, log_group_name: str) -> str:
        """Get detailed information about a specific log group."""
        try:
            response = self.logs_client.describe_log_groups(
                logGroupNamePrefix=log_group_name, limit=1
            )
            log_groups = response.get("logGroups", [])

            if not log_groups:
                return json.dumps(
                    {"error": f"Log group '{log_group_name}' not found"}, indent=2
                )

            log_group = log_groups[0]

            # Get retention policy
            retention = "Never Expire"
            if "retentionInDays" in log_group:
                retention = f"{log_group['retentionInDays']} days"

            # Get metrics for the log group
            session = boto3.Session(profile_name=getattr(self, 'profile_name', None))
            cloudwatch = session.client("cloudwatch")
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)

            metrics_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Logs",
                MetricName="IncomingBytes",
                Dimensions=[
                    {"Name": "LogGroupName", "Value": log_group_name},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=["Sum"],
            )

            # Format the detailed information
            details = {
                "name": log_group.get("logGroupName"),
                "arn": log_group.get("arn"),
                "storedBytes": log_group.get("storedBytes"),
                "creationTime": datetime.fromtimestamp(
                    log_group.get("creationTime", 0) / 1000
                ).isoformat(),
                "retentionPolicy": retention,
                "metricFilterCount": log_group.get("metricFilterCount", 0),
                "kmsKeyId": log_group.get("kmsKeyId", "Not encrypted with KMS"),
                "dailyIncomingBytes": [
                    {"timestamp": point["Timestamp"].isoformat(), "bytes": point["Sum"]}
                    for point in metrics_response.get("Datapoints", [])
                ],
            }

            return json.dumps(details, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def get_log_streams(self, log_group_name: str, limit: int = 20) -> str:
        """
        Get a list of log streams for a specific log group.

        Args:
            log_group_name: The name of the log group
            limit: Maximum number of streams to return (default: 20)
        """
        try:
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy="LastEventTime",
                descending=True,
                limit=limit,
            )

            log_streams = response.get("logStreams", [])
            formatted_streams = []

            for stream in log_streams:
                last_event_time = stream.get("lastEventTimestamp", 0)
                first_event_time = stream.get("firstEventTimestamp", 0)

                formatted_streams.append(
                    {
                        "name": stream.get("logStreamName"),
                        "firstEventTime": datetime.fromtimestamp(
                            first_event_time / 1000
                        ).isoformat()
                        if first_event_time
                        else None,
                        "lastEventTime": datetime.fromtimestamp(
                            last_event_time / 1000
                        ).isoformat()
                        if last_event_time
                        else None,
                        "storedBytes": stream.get("storedBytes"),
                    }
                )

            return json.dumps(formatted_streams, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def get_log_events(
        self, log_group_name: str, log_stream_name: str, limit: int = 100
    ) -> str:
        """
        Get log events from a specific log stream.

        Args:
            log_group_name: The name of the log group
            log_stream_name: The name of the log stream
            limit: Maximum number of events to return (default: 100)
        """
        try:
            response = self.logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                limit=limit,
                startFromHead=False,
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
                        "ingestionTime": datetime.fromtimestamp(
                            event.get("ingestionTime", 0) / 1000
                        ).isoformat(),
                    }
                )

            return json.dumps(formatted_events, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def get_log_sample(self, log_group_name: str, limit: int = 10) -> str:
        """Get a sample of recent logs from a log group."""
        try:
            # First get the most recent stream
            stream_response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy="LastEventTime",
                descending=True,
                limit=1,
            )

            log_streams = stream_response.get("logStreams", [])
            if not log_streams:
                return json.dumps(
                    {"error": f"No streams found in log group '{log_group_name}'"},
                    indent=2,
                )

            # Get events from the most recent stream
            log_stream_name = log_streams[0].get("logStreamName")
            response = self.logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                limit=limit,
                startFromHead=False,
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
                        "streamName": log_stream_name,
                    }
                )

            return json.dumps(
                {
                    "description": f"Sample of {len(formatted_events)} recent logs from '{log_group_name}'",
                    "logStream": log_stream_name,
                    "events": formatted_events,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def get_recent_errors(self, log_group_name: str, hours: int = 24) -> str:
        """Get recent error logs from a log group."""
        try:
            # Calculate start time
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int(
                (datetime.now() - timedelta(hours=hours)).timestamp() * 1000
            )

            # Use filter_log_events to search for errors across all streams
            # Common error patterns to search for
            error_patterns = [
                "ERROR",
                "Error",
                "error",
                "exception",
                "Exception",
                "EXCEPTION",
                "fail",
                "Fail",
                "FAIL",
            ]

            filter_pattern = " ".join([f'"{pattern}"' for pattern in error_patterns])
            response = self.logs_client.filter_log_events(
                logGroupName=log_group_name,
                filterPattern=f"{filter_pattern}",
                startTime=start_time,
                endTime=end_time,
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

            return json.dumps(
                {
                    "description": f"Recent errors from '{log_group_name}' in the last {hours} hours",
                    "totalErrors": len(formatted_events),
                    "events": formatted_events,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def get_log_metrics(self, log_group_name: str, hours: int = 24) -> str:
        """Get log volume metrics for a log group."""
        try:
            # Create CloudWatch client
            session = boto3.Session(profile_name=getattr(self, 'profile_name', None))
            cloudwatch = session.client("cloudwatch")

            # Calculate start and end times
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Get incoming bytes
            incoming_bytes = cloudwatch.get_metric_statistics(
                Namespace="AWS/Logs",
                MetricName="IncomingBytes",
                Dimensions=[
                    {"Name": "LogGroupName", "Value": log_group_name},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=["Sum"],
            )

            # Get incoming log events
            incoming_events = cloudwatch.get_metric_statistics(
                Namespace="AWS/Logs",
                MetricName="IncomingLogEvents",
                Dimensions=[
                    {"Name": "LogGroupName", "Value": log_group_name},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=["Sum"],
            )

            # Format metrics data
            bytes_datapoints = incoming_bytes.get("Datapoints", [])
            events_datapoints = incoming_events.get("Datapoints", [])

            bytes_datapoints.sort(key=lambda x: x["Timestamp"])
            events_datapoints.sort(key=lambda x: x["Timestamp"])

            bytes_data = [
                {"timestamp": point["Timestamp"].isoformat(), "bytes": point["Sum"]}
                for point in bytes_datapoints
            ]

            events_data = [
                {"timestamp": point["Timestamp"].isoformat(), "events": point["Sum"]}
                for point in events_datapoints
            ]

            # Calculate totals
            total_bytes = sum(point["Sum"] for point in bytes_datapoints)
            total_events = sum(point["Sum"] for point in events_datapoints)

            return json.dumps(
                {
                    "description": f"Log metrics for '{log_group_name}' over the last {hours} hours",
                    "totalBytes": total_bytes,
                    "totalEvents": total_events,
                    "bytesByHour": bytes_data,
                    "eventsByHour": events_data,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def analyze_log_structure(self, log_group_name: str) -> str:
        """Analyze and provide information about the structure of logs."""
        try:
            # Get a sample of logs to analyze
            sample_data = json.loads(self.get_log_sample(log_group_name, 50))

            if "error" in sample_data:
                return json.dumps(sample_data, indent=2)

            events = sample_data.get("events", [])

            if not events:
                return json.dumps(
                    {"error": "No log events found for analysis"}, indent=2
                )

            # Analyze the structure
            structure_info = {
                "description": f"Log structure analysis for '{log_group_name}'",
                "sampleSize": len(events),
                "format": self._detect_log_format(events),
                "commonPatterns": self._extract_common_patterns(events),
                "fieldAnalysis": self._analyze_fields(events),
            }

            return json.dumps(structure_info, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def _detect_log_format(self, events: List[Dict]) -> str:
        """Detect the format of logs (JSON, plaintext, etc.)."""
        json_count = 0
        key_value_count = 0
        xml_count = 0

        for event in events:
            message = event.get("message", "")

            # Check for JSON format
            if message.strip().startswith("{") and message.strip().endswith("}"):
                try:
                    json.loads(message)
                    json_count += 1
                    continue
                except json.JSONDecodeError:
                    pass

            # Check for XML format
            if message.strip().startswith("<") and message.strip().endswith(">"):
                xml_count += 1
                continue

            # Check for key-value pairs
            if re.search(r"\w+=[\'\"][^\'\"]*[\'\"]|\w+=\S+", message):
                key_value_count += 1

        total = len(events)

        if json_count > total * 0.7:
            return "JSON"
        elif xml_count > total * 0.7:
            return "XML"
        elif key_value_count > total * 0.7:
            return "Key-Value Pairs"
        else:
            return "Plaintext/Unstructured"

    def _extract_common_patterns(self, events: List[Dict]) -> Dict:
        """Extract common patterns from log messages."""
        # Look for common log patterns
        level_pattern = re.compile(
            r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b"
        )
        timestamp_patterns = [
            re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),  # ISO format
            re.compile(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            ),  # Common datetime format
            re.compile(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"),  # MM/DD/YYYY format
        ]

        # Count occurrences
        levels = Counter()
        has_timestamp = 0

        for event in events:
            message = event.get("message", "")

            # Check log levels
            level_match = level_pattern.search(message)
            if level_match:
                levels[level_match.group(0)] += 1

            # Check timestamps in message content (not event timestamp)
            for pattern in timestamp_patterns:
                if pattern.search(message):
                    has_timestamp += 1
                    break

        return {
            "logLevels": dict(levels),
            "containsTimestamp": has_timestamp,
            "timestampPercentage": round((has_timestamp / len(events)) * 100, 2)
            if events
            else 0,
        }

    def _analyze_fields(self, events: List[Dict]) -> Dict:
        """Analyze fields in structured log messages."""
        format_type = self._detect_log_format(events)

        if format_type == "JSON":
            # Try to extract fields from JSON logs
            fields_count = Counter()

            for event in events:
                message = event.get("message", "")
                try:
                    json_data = json.loads(message)
                    for key in json_data.keys():
                        fields_count[key] += 1
                except json.JSONDecodeError:
                    continue

            # Get the most common fields
            common_fields = [
                {
                    "field": field,
                    "occurrences": count,
                    "percentage": round((count / len(events)) * 100, 2),
                }
                for field, count in fields_count.most_common(10)
            ]

            return {"commonFields": common_fields, "uniqueFields": len(fields_count)}

        elif format_type == "Key-Value Pairs":
            # Try to extract key-value pairs
            key_pattern = re.compile(r"(\w+)=[\'\"]?([^\'\"\s]*)[\'\"]?")
            fields_count = Counter()

            for event in events:
                message = event.get("message", "")
                matches = key_pattern.findall(message)
                for key, _ in matches:
                    fields_count[key] += 1

            # Get the most common fields
            common_fields = [
                {
                    "field": field,
                    "occurrences": count,
                    "percentage": round((count / len(events)) * 100, 2),
                }
                for field, count in fields_count.most_common(10)
            ]

            return {"commonFields": common_fields, "uniqueFields": len(fields_count)}

        else:
            return {
                "analysis": f"Field analysis not applicable for {format_type} format"
            }
