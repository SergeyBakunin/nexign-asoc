from fastapi import Header, HTTPException, status
from app.config import settings


async def verify_token(x_api_token: str | None = Header(default=None)):
    if x_api_token != settings.api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing x-api-token")
