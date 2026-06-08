#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta, timezone
import dateutil.parser


def _parse_iso_utc(value: str) -> datetime:
    """Parse an ISO8601 string, treating naive (offset-less) input as UTC.

    ``dateutil.parser.isoparse`` returns a tz-naive ``datetime`` when the input
    has no ``Z`` suffix or explicit offset. Calling ``.timestamp()`` on a naive
    datetime interprets it in the *host* local timezone, which would shift the
    epoch by the server's UTC offset. We pin naive values to UTC so the result
    is independent of where the server runs. Offset-aware values are returned
    unchanged so explicit offsets are always honored.
    """
    parsed = dateutil.parser.isoparse(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def get_time_range(hours: int, start_time: str = None, end_time: str = None):
    """
    Calculate time range timestamps from hours or exact start/end times.

    Args:
        hours: Number of hours to look back (used if start_time is not provided)
        start_time: Optional ISO8601 start time. Naive (offset-less) values are
            interpreted as UTC; explicit offsets are honored.
        end_time: Optional ISO8601 end time. Naive (offset-less) values are
            interpreted as UTC; explicit offsets are honored.

    Returns:
        Tuple of (start_timestamp, end_timestamp) in milliseconds since epoch
    """
    if start_time:
        start_ts = int(_parse_iso_utc(start_time).timestamp() * 1000)
    else:
        start_ts = int(
            (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000
        )

    if end_time:
        end_ts = int(_parse_iso_utc(end_time).timestamp() * 1000)
    else:
        end_ts = int(datetime.now(timezone.utc).timestamp() * 1000)

    return start_ts, end_ts
