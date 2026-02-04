"""
TLS Client wrapper with session management
"""
from async_tls_client import AsyncSession
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import asyncio
import time
import logging
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)


class SessionInfo:
    """Information about a session"""
    
    def __init__(self, client: AsyncSession, session_id: str):
        self.client = client
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.request_count = 0
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used = datetime.now()
        self.request_count += 1
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if session is expired"""
        return datetime.now() - self.last_used > timedelta(seconds=ttl_seconds)


class ProxyClientManager:
    """
    Manager for TLS client sessions with cookie persistence
    Uses chrome_133 profile for maximum Cloudflare bypass capability
    """
    
    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the session cleanup background task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            logger.info("Session cleanup task started")
    
    async def stop(self):
        """Stop the session cleanup background task and close all sessions"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        # Close all active sessions
        async with self._lock:
            for session_info in self.sessions.values():
                try:
                    await session_info.client.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"Error closing session {session_info.session_id}: {e}")
            self.sessions.clear()
        
        logger.info("All sessions closed")
    
    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._remove_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _remove_expired_sessions(self):
        """Remove expired sessions"""
        async with self._lock:
            expired_sessions = [
                session_id for session_id, session_info in self.sessions.items()
                if session_info.is_expired(settings.session_ttl)
            ]
            
            for session_id in expired_sessions:
                try:
                    session_info = self.sessions.pop(session_id)
                    await session_info.client.__aexit__(None, None, None)
                    logger.info(f"Removed expired session: {session_id}")
                except Exception as e:
                    logger.error(f"Error removing expired session {session_id}: {e}")
    
    async def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[AsyncSession, Optional[str]]:
        """
        Get existing session or create a new one
        
        Args:
            session_id: Optional session ID. If None, creates a temporary session.
            
        Returns:
            Tuple of (AsyncSession, session_id or None)
        """
        if session_id is None:
            # Create temporary session (not stored)
            client = await self._create_client()
            return client, None
        
        async with self._lock:
            # Check if session exists
            if session_id in self.sessions:
                session_info = self.sessions[session_id]
                session_info.update_last_used()
                return session_info.client, session_id
            
            # Check max sessions limit
            if len(self.sessions) >= settings.max_sessions:
                raise ValueError(f"Maximum number of sessions ({settings.max_sessions}) reached")
            
            # Create new session
            client = await self._create_client()
            self.sessions[session_id] = SessionInfo(client, session_id)
            logger.info(f"Created new session: {session_id}")
            
            return client, session_id
    
    def _get_default_headers(self) -> Dict[str, str]:
        """
        Chrome 133 için standart browser header'ları
        
        Returns:
            Standart header dictionary
        """
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
    
    def _prepare_headers(self, url: str, user_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        URL'e göre dinamik Origin ve Referer ile header'ları hazırla
        
        Args:
            url: Target URL
            user_headers: Kullanıcı tarafından sağlanan header'lar
            
        Returns:
            Hazırlanmış header dictionary
        """
        # URL'den origin çıkar
        parsed_url = urlparse(url)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Standart header'ları başlat
        headers = self._get_default_headers()
        
        # Origin ve Referer'ı dinamik ayarla
        headers["Origin"] = origin
        headers["Referer"] = f"{origin}/"
        
        # Kullanıcı header'larını ekle (override yapabilir)
        if user_headers:
            headers.update(user_headers)
        
        return headers
    
    async def _create_client(self) -> AsyncSession:
        """
        Create a new AsyncSession with chrome_133 profile
        
        Returns:
            Configured AsyncSession instance
        """
        client = AsyncSession(
            client_identifier=settings.client_identifier,  # chrome_133
            random_tls_extension_order=settings.random_tls_extension_order,
        )
        # Enter the async context manager
        await client.__aenter__()
        return client
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if session was deleted, False if not found
        """
        async with self._lock:
            if session_id not in self.sessions:
                return False
            
            session_info = self.sessions.pop(session_id)
            try:
                await session_info.client.__aexit__(None, None, None)
                logger.info(f"Deleted session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting session {session_id}: {e}")
                return False
    
    async def get_session_cookies(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Get cookies from a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary of cookies or None if session not found
        """
        async with self._lock:
            if session_id not in self.sessions:
                return None
            
            session_info = self.sessions[session_id]
            # Extract cookies from the client
            # The async_tls_client stores cookies internally
            # We need to access them through the cookie jar
            try:
                cookies = {}
                if hasattr(session_info.client, 'cookies') and session_info.client.cookies:
                    for cookie in session_info.client.cookies:
                        cookies[cookie.name] = cookie.value
                return cookies
            except Exception as e:
                logger.error(f"Error getting cookies for session {session_id}: {e}")
                return {}
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    async def _follow_redirects(
        self,
        client: AsyncSession,
        method: str,
        url: str,
        kwargs: Dict,
        user_headers: Optional[Dict[str, str]],
        max_redirects: int = 5
    ) -> tuple[Any, list[str], int, str]:
        """
        Follow HTTP redirects up to max_redirects
        
        Args:
            client: AsyncSession client
            method: HTTP method
            url: Starting URL
            kwargs: Request kwargs
            user_headers: User-provided headers (for header preparation)
            max_redirects: Maximum number of redirects to follow
            
        Returns:
            Tuple of (final_response, redirect_chain, redirect_count, final_url)
        """
        redirect_chain = []
        redirect_count = 0
        current_url = url
        current_method = method
        
        while redirect_count <= max_redirects:
            # Update headers for current URL (dynamic Origin/Referer)
            kwargs['headers'] = self._prepare_headers(current_url, user_headers)
            
            # Make the request
            response = await getattr(client, current_method.lower())(current_url, **kwargs)
            
            # Check if redirect
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location') or response.headers.get('location')
                
                if not location:
                    # No Location header, return current response
                    break
                
                # Add current URL to chain
                redirect_chain.append(current_url)
                redirect_count += 1
                
                # Check max redirects
                if redirect_count > max_redirects:
                    raise ValueError(f"Too many redirects (max: {max_redirects})")
                
                # Handle relative URLs
                if not location.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    location = urljoin(current_url, location)
                
                logger.info(f"Redirect {redirect_count}: {current_url} -> {location} (status: {response.status_code})")
                
                # Update URL for next iteration
                current_url = location
                
                # For 303, change method to GET and remove body
                if response.status_code == 303 and current_method.upper() != 'GET':
                    logger.info(f"303 redirect: changing method from {current_method} to GET")
                    current_method = 'GET'
                    kwargs.pop('json', None)
                    kwargs.pop('data', None)
            else:
                # Not a redirect, return response
                break
        
        # Get final URL (some clients expose response.url)
        final_url = current_url
        
        return response, redirect_chain, redirect_count, final_url
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        session_id: Optional[str] = None,
        proxy: Optional[str] = None
    ) -> tuple[int, Dict[str, str | list[str]], Any, float, Optional[str], int, Optional[list[str]], str]:
        """
        Make a request through the TLS client
        
        Args:
            method: HTTP method
            url: Target URL
            headers: Optional request headers (user headers will override defaults)
            body: Optional request body
            session_id: Optional session ID for cookie persistence
            proxy: Optional proxy URL (http://user:pass@host:port or socks5://host:port)
            
        Returns:
            Tuple of (status_code, headers, body, elapsed_ms, session_id, redirect_count, redirect_chain, final_url)
        """
        client, actual_session_id = await self.get_or_create_session(session_id)
        
        start_time = time.time()
        
        try:
            # Prepare request parameters
            kwargs = {}
            
            # Handle body based on method
            if body is not None and method.upper() in ['POST', 'PUT', 'PATCH']:
                if isinstance(body, dict):
                    kwargs['json'] = body
                else:
                    kwargs['data'] = body
            
            # Add proxy if provided
            if proxy:
                kwargs['proxy'] = proxy
            
            # Follow redirects (headers will be prepared inside _follow_redirects)
            response, redirect_chain, redirect_count, final_url = await self._follow_redirects(
                client=client,
                method=method,
                url=url,
                kwargs=kwargs,
                user_headers=headers,
                max_redirects=5
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Parse response body
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text
            
            # Process response headers
            # Some headers like Set-Cookie can have multiple values
            response_headers = {}
            for key, value in response.headers.items():
                # If header has multiple values, keep as list
                # Otherwise convert to string
                if isinstance(value, list):
                    response_headers[key] = value
                else:
                    response_headers[key] = str(value)
            
            return (
                response.status_code,
                response_headers,
                response_body,
                elapsed_ms,
                actual_session_id,
                redirect_count,
                redirect_chain if redirect_chain else None,
                final_url
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # If it was a temporary session (no session_id), clean it up
            if session_id is None and actual_session_id is None:
                try:
                    await client.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"Error closing temporary client: {e}")


# Global proxy client manager instance
proxy_manager = ProxyClientManager()
