"""
TLS Proxy Service - FastAPI Application
A proxy service that uses async-tls-client with chrome_133 profile to bypass Cloudflare protection
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uuid

from config import settings
from models import (
    ProxyRequest,
    ProxyResponse,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionCookiesResponse,
    HealthResponse,
    ErrorResponse
)
from auth import verify_api_key
from proxy_client import proxy_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting TLS Proxy Service...")
    await proxy_manager.start()
    logger.info(f"Service started on port {settings.port}")
    logger.info(f"Using TLS profile: {settings.client_identifier}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TLS Proxy Service...")
    await proxy_manager.stop()
    logger.info("Service stopped")


app = FastAPI(
    title="TLS Proxy Service",
    description="A proxy service using async-tls-client with chrome_133 profile for Cloudflare bypass",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs"""
    return {
        "message": "TLS Proxy Service",
        "docs": "/docs",
        "health": "/health"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check service health and get statistics
    
    Returns service status and session statistics
    """
    return HealthResponse(
        status="healthy",
        active_sessions=proxy_manager.get_active_sessions_count(),
        max_sessions=settings.max_sessions
    )


@app.post(
    "/proxy/request",
    response_model=ProxyResponse,
    tags=["Proxy"],
    summary="Make a proxied request",
    responses={
        200: {"description": "Request successful"},
        401: {"description": "Unauthorized - Invalid API Key"},
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)
async def proxy_request(
    request: ProxyRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Make a proxied request through TLS client
    
    This endpoint forwards your request to the target URL using async-tls-client
    with chrome_133 profile, which helps bypass Cloudflare protection.
    
    **Session Management:**
    - If `session_id` is provided, cookies and state will persist across requests
    - If `session_id` is omitted, each request is independent
    
    **Example:**
    ```json
    {
        "method": "GET",
        "url": "https://api.example.com/data",
        "headers": {"User-Agent": "Custom Agent"},
        "session_id": "my-session-1"
    }
    ```
    """
    try:
        (status_code, headers, body, elapsed_ms, session_id,
         redirect_count, redirect_chain, final_url) = await proxy_manager.make_request(
            method=request.method.value,
            url=request.url,
            headers=request.headers,
            body=request.body,
            session_id=request.session_id,
            proxy=request.proxy
        )
        
        return ProxyResponse(
            status_code=status_code,
            headers=headers,
            body=body,
            session_id=session_id,
            elapsed_ms=round(elapsed_ms, 2),
            redirect_count=redirect_count,
            redirect_chain=redirect_chain,
            final_url=final_url
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Proxy request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request failed: {str(e)}"
        )


@app.post(
    "/proxy/session/create",
    response_model=SessionCreateResponse,
    tags=["Session Management"],
    summary="Create a new session",
    responses={
        200: {"description": "Session created successfully"},
        401: {"description": "Unauthorized - Invalid API Key"},
        400: {"description": "Maximum sessions reached"}
    }
)
async def create_session(
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new session with a unique session ID
    
    Sessions maintain cookies and state across multiple requests.
    The session ID is automatically generated and returned.
    
    **Returns:**
    A unique session_id that can be used in subsequent /proxy/request calls
    """
    try:
        session_id = str(uuid.uuid4())
        await proxy_manager.get_or_create_session(session_id)
        
        return SessionCreateResponse(
            session_id=session_id,
            message="Session created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@app.delete(
    "/proxy/session/{session_id}",
    response_model=SessionDeleteResponse,
    tags=["Session Management"],
    summary="Delete a session",
    responses={
        200: {"description": "Session deleted successfully"},
        401: {"description": "Unauthorized - Invalid API Key"},
        404: {"description": "Session not found"}
    }
)
async def delete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete an existing session
    
    This will close the TLS client connection and remove all cookies
    associated with the session.
    
    **Parameters:**
    - `session_id`: The session ID to delete
    """
    success = await proxy_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    
    return SessionDeleteResponse(
        session_id=session_id,
        message="Session deleted successfully"
    )


@app.get(
    "/proxy/session/{session_id}/cookies",
    response_model=SessionCookiesResponse,
    tags=["Session Management"],
    summary="Get session cookies",
    responses={
        200: {"description": "Cookies retrieved successfully"},
        401: {"description": "Unauthorized - Invalid API Key"},
        404: {"description": "Session not found"}
    }
)
async def get_session_cookies(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get all cookies stored in a session
    
    This endpoint allows you to inspect cookies that have been
    collected during requests made with this session.
    
    **Parameters:**
    - `session_id`: The session ID to get cookies from
    """
    cookies = await proxy_manager.get_session_cookies(session_id)
    
    if cookies is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    
    return SessionCookiesResponse(
        session_id=session_id,
        cookies=cookies
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc)
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
