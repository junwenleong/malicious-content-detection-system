import hmac
import hashlib
import time
import json
import logging
from fastapi import Request, HTTPException
from src.config import settings

logger = logging.getLogger(__name__)

async def verify_signature(request: Request) -> None:
    """
    Verifies HMAC-SHA256 signature of the request body.
    Requires 'X-Signature' header with format: 'timestamp:signature'.
    
    This dependency only runs if settings.hmac_enabled is True.
    """
    if not settings.hmac_enabled:
        return

    signature_header = request.headers.get("X-Signature")
    if not signature_header:
        logger.warning(
            json.dumps({
                "event": "hmac_missing_header",
                "client_ip": request.client.host if request.client else "unknown",
                "correlation_id": getattr(request.state, "correlation_id", None)
            })
        )
        raise HTTPException(status_code=401, detail="Missing X-Signature header")

    try:
        parts = signature_header.split(":")
        if len(parts) != 2:
             raise ValueError("Invalid format")
        timestamp_str, received_sig = parts
        timestamp = int(timestamp_str)
    except ValueError:
        logger.warning(
            json.dumps({
                "event": "hmac_invalid_format",
                "client_ip": request.client.host if request.client else "unknown",
                "correlation_id": getattr(request.state, "correlation_id", None)
            })
        )
        raise HTTPException(status_code=401, detail="Invalid X-Signature format (timestamp:signature)")

    # 1. Replay Protection (5 minutes)
    current_time = int(time.time())
    if abs(current_time - timestamp) > 300:
        logger.warning(
            json.dumps({
                "event": "hmac_expired",
                "client_ip": request.client.host if request.client else "unknown",
                "correlation_id": getattr(request.state, "correlation_id", None),
                "timestamp_diff": abs(current_time - timestamp)
            })
        )
        raise HTTPException(status_code=401, detail="Request signature expired")

    # 2. Verify Signature
    if not settings.hmac_secret:
         logger.error("HMAC secret missing in configuration")
         raise HTTPException(status_code=500, detail="Server configuration error: HMAC secret missing")

    body = await request.body()
    # Payload: timestamp + body
    payload = f"{timestamp}".encode() + body
    
    expected_sig = hmac.new(
        settings.hmac_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, received_sig):
        logger.warning(
            json.dumps({
                "event": "hmac_invalid_signature",
                "client_ip": request.client.host if request.client else "unknown",
                "correlation_id": getattr(request.state, "correlation_id", None)
            })
        )
        raise HTTPException(status_code=403, detail="Invalid signature")
