#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta
import dateutil.parser


def get_time_range(hours: int, start_time: str = None, end_time: str = None):
    """
    Calculate time range timestamps from hours or exact start/end times.

    Args:
        hours: Number of hours to look back (used if start_time is not provided)
        start_time: Optional ISO8601 start time
        end_time: Optional ISO8601 end time

    Returns:
        Tuple of (start_timestamp, end_timestamp) in milliseconds since epoch
    """
    if start_time:
        start_ts = int(dateutil.parser.isoparse(start_time).timestamp() * 1000)
    else:
        start_ts = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)

    if end_time:
        end_ts = int(dateutil.parser.isoparse(end_time).timestamp() * 1000)
    else:
        end_ts = int(datetime.now().timestamp() * 1000)

    return start_ts, end_ts
