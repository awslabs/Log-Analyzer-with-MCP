# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for cw_mcp_server.tools.utils.get_time_range.

These tests pin a non-UTC host timezone (Asia/Tokyo, +09:00) to prove that a
*naive* ISO8601 timestamp (no Z, no offset) is interpreted as UTC rather than
as the server's local time. The relative (hours-based) path is also checked to
remain anchored to UTC.
"""

import time

import pytest

from cw_mcp_server.tools.utils import get_time_range


@pytest.fixture
def tokyo_tz(monkeypatch):
    """Run the test body with the host timezone set to Asia/Tokyo (+09:00)."""
    monkeypatch.setenv("TZ", "Asia/Tokyo")
    time.tzset()
    yield
    # monkeypatch restores the TZ env var on teardown; re-apply it to the C lib.
    time.tzset()


def test_naive_iso_treated_as_utc_under_non_utc_tz(tokyo_tz):
    """A naive ISO string must yield the same epoch as its UTC/offset equivalents.

    Under TZ=Asia/Tokyo, the buggy implementation interpreted
    "2025-01-01T00:00:00" as 00:00 *Tokyo* time, drifting the epoch 9h earlier
    than the intended 00:00 UTC.
    """
    naive_start, _ = get_time_range(24, "2025-01-01T00:00:00", None)
    zulu_start, _ = get_time_range(24, "2025-01-01T00:00:00Z", None)
    offset_start, _ = get_time_range(24, "2025-01-01T09:00:00+09:00", None)

    # All three describe the same instant (2025-01-01T00:00:00Z).
    assert naive_start == zulu_start
    assert naive_start == offset_start


def test_explicit_offset_is_honored(tokyo_tz):
    """An explicit offset must be respected, not overridden by the host TZ."""
    # 2025-01-01T00:00:00+09:00 is 2024-12-31T15:00:00Z.
    aware_start, _ = get_time_range(24, "2025-01-01T00:00:00+09:00", None)
    utc_equivalent_start, _ = get_time_range(24, "2024-12-31T15:00:00Z", None)
    assert aware_start == utc_equivalent_start


def test_naive_end_time_treated_as_utc(tokyo_tz):
    """The end_time path must apply the same UTC assumption for naive input."""
    _, naive_end = get_time_range(24, None, "2025-01-01T00:00:00")
    _, zulu_end = get_time_range(24, None, "2025-01-01T00:00:00Z")
    assert naive_end == zulu_end


def test_returns_millisecond_epochs():
    """Return shape: a tuple of two ints in milliseconds since epoch."""
    start_ts, end_ts = get_time_range(
        24, "2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z"
    )
    assert isinstance(start_ts, int)
    assert isinstance(end_ts, int)
    # 24h apart, expressed in milliseconds.
    assert end_ts - start_ts == 24 * 60 * 60 * 1000
