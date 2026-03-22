"""POST /prompt Lambda stub (Phase 1 infrastructure placeholder)."""

from __future__ import annotations

import json  # JSON encode API Gateway responses
from typing import Any, Dict  # API Gateway proxy typing


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Return a healthy JSON response for the prompt endpoint.

    Args:
        event: API Gateway proxy request event.
        context: Lambda runtime context object.

    Returns:
        API Gateway proxy response dictionary with statusCode and JSON body.
    """
    _ = event  # Reserved for future SEO prompt inputs
    _ = context  # Reserved for future logging and tracing
    body = {"status": "ok", "handler": "prompt"}  # Minimal stub payload
    return {"statusCode": 200, "body": json.dumps(body)}  # Proxy integration response
