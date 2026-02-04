"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal
from enum import Enum


class HTTPMethod(str, Enum):
    """Supported HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ProxyRequest(BaseModel):
    """Request model for proxy endpoint"""
    method: HTTPMethod = Field(
        description="HTTP method for the request"
    )
    url: str = Field(
        description="Target URL to send the request to",
        examples=["https://api.example.com/endpoint"]
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional headers to include in the request"
    )
    body: Optional[Dict[str, Any] | str] = Field(
        default=None,
        description="Optional request body (JSON object or string)"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for cookie persistence",
        examples=["my-session-123"]
    )
    proxy: Optional[str] = Field(
        default=None,
        description="Optional proxy URL (http://user:pass@host:port or socks5://host:port)",
        examples=["http://user:pass@proxy.example.com:8080", "socks5://127.0.0.1:1080"]
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL starts with http:// or https://"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate session_id format"""
        if v is not None and len(v) == 0:
            raise ValueError('session_id cannot be empty string')
        return v


class ProxyResponse(BaseModel):
    """Response model for proxy endpoint"""
    status_code: int = Field(
        description="HTTP status code from the target server"
    )
    headers: Dict[str, str | list[str]] = Field(
        description="Response headers from the target server (some headers like Set-Cookie can have multiple values)"
    )
    body: Any = Field(
        description="Response body from the target server"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID used for this request"
    )
    elapsed_ms: float = Field(
        description="Request duration in milliseconds"
    )
    redirect_count: int = Field(
        default=0,
        description="Number of redirects followed"
    )
    redirect_chain: Optional[list[str]] = Field(
        default=None,
        description="List of URLs in redirect chain (if any redirects occurred)"
    )
    final_url: str = Field(
        description="Final URL after following redirects"
    )


class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    session_id: str = Field(
        description="Newly created session ID"
    )
    message: str = Field(
        default="Session created successfully"
    )


class SessionDeleteResponse(BaseModel):
    """Response model for session deletion"""
    session_id: str = Field(
        description="Deleted session ID"
    )
    message: str = Field(
        default="Session deleted successfully"
    )


class SessionCookiesResponse(BaseModel):
    """Response model for session cookies"""
    session_id: str = Field(
        description="Session ID"
    )
    cookies: Dict[str, str] = Field(
        description="Cookies stored in the session"
    )


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: Literal["healthy"] = "healthy"
    active_sessions: int = Field(
        description="Number of currently active sessions"
    )
    max_sessions: int = Field(
        description="Maximum allowed sessions"
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(
        description="Error message"
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
