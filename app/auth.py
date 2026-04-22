import os
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

def verify_auth(request: Request):
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    if not dev_mode:
        auth_user = request.headers.get("x-auth-request-email") or request.headers.get("x-forwarded-user")
        if not auth_user:
            logger.error("Unauthorized API call. Must be routed through OIDC sidecar supplying auth headers.")
            raise HTTPException(status_code=401, detail="Unauthorized")
        logger.info(f"Authorized Request from OIDC User: {auth_user}")
