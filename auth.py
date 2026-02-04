"""
API Key authentication middleware and dependencies
"""
from fastapi import Header, HTTPException, status
from config import settings


async def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")) -> str:
    """
    Verify API Key from request header
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key
