# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import functools
import json
import traceback
from typing import Callable


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in tool methods.
    Ensures that all tool methods return a standardized error response
    rather than raising exceptions that would cause the client to fail.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_response = {
                "status": "Error",
                "error": str(e),
                "error_type": e.__class__.__name__,
                "details": error_traceback.split("\n")[-2] if error_traceback else None,
            }
            return json.dumps(error_response, indent=2)

    return wrapper
