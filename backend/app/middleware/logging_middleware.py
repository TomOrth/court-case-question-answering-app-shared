"""
HTTP Request Logging Middleware

Captures all HTTP requests/responses and logs to database.
- Non-blocking: DB writes happen in background
- Captures: Full request/response bodies, headers, user info
- Filters: OPTIONS requests are skipped
"""

import asyncio
import time
import traceback
import json
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.http_logs import HTTPRequestLog
from app.db.session import AsyncSessionLocal


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests to database.
    
    How it works:
    1. Request comes in → capture details
    2. Pass request to route handler
    3. Response comes back → capture details
    4. Save to database (async, non-blocking)
    5. Return response to client
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Main middleware logic.
        
        Args:
            request: Incoming HTTP request
            call_next: Function to call next middleware/route handler
            
        Returns:
            Response from the route handler
        """
        
        # ============================================
        # FILTER: Skip OPTIONS requests
        # ============================================
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # ============================================
        # STEP 1: Capture request details
        # ============================================
        start_time = time.time()
        
        # Basic request info
        method = request.method
        path = request.url.path
        full_url = str(request.url)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Query parameters (e.g., ?session_id=xxx)
        query_params = dict(request.query_params) if request.query_params else None
        
        # NOTE: Path parameters are NOT available here (before route matching)
        # We will capture them AFTER the request is processed
        
        # Request headers (convert to dict)
        request_headers = dict(request.headers)
        
        # Request body (read and cache for route handler)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                # If body isn't JSON or can't be decoded, store as string
                request_body = {"_raw": body_bytes.decode("utf-8", errors="ignore")}
        
        # ============================================
        # STEP 2: Extract user info (if authenticated)
        # ============================================
        user_id = None
        user_email = None
        
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            # Extract user from token
            user_info = await self._get_user_from_token(token)
            if user_info:
                user_id = user_info.get("user_id")
                user_email = user_info.get("user_email")
        
        # ============================================
        # STEP 3: Call route handler (process request)
        # ============================================
        error_type = None
        error_message = None
        error_traceback_str = None
        
        try:
            # Call the actual route handler
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            # If route handler throws an exception, capture it
            status_code = 500
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback_str = traceback.format_exc()
            
            # Re-raise the exception so FastAPI's error handlers can process it
            raise
        
        # ============================================
        # STEP 4: Capture response details
        # ============================================
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        # Capture path params (now available after route matching)
        path_params = dict(request.path_params) if request.path_params else None
        
        # Response headers
        response_headers = dict(response.headers)
        
        # Response body (only if JSON)
        response_body = None
        content_type = response.headers.get("content-type", "")
        
        if content_type.startswith("application/json"):
            # We need to consume the body iterator to read the content
            # Then create a NEW response so the client still gets the data
            try:
                # Read all chunks from the response iterator
                body_chunks = []
                async for chunk in response.body_iterator:
                    body_chunks.append(chunk)
                
                # Combine chunks
                body_bytes = b"".join(body_chunks)
                
                # Decode and parse JSON
                if body_bytes:
                    response_body = json.loads(body_bytes.decode("utf-8"))
                    
                # Re-create the response for the client
                # We use Response (not JSONResponse) because we have row bytes
                response = Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception as e:
                print(f"⚠️ Failed to capture response body: {e}")
                # Don't crash, just proceed without body log
                pass
        
        # ============================================
        # STEP 5: Save to database (NON-BLOCKING)
        # ============================================
        # Create background task to save log
        asyncio.create_task(
            self._save_log_to_db(
                method=method,
                path=path,
                full_url=full_url,
                client_ip=client_ip,
                user_agent=user_agent,
                user_id=user_id,
                user_email=user_email,
                query_params=query_params,
                path_params=path_params,
                request_headers=request_headers,
                request_body=request_body,
                status_code=status_code,
                response_headers=response_headers,
                response_body=response_body,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=error_message,
                error_traceback=error_traceback_str,
            )
        )
        
        # ============================================
        # STEP 6: Return response immediately
        # ============================================
        return response
    
    async def _get_user_from_token(self, token: str) -> Optional[dict]:
        """
        Extract user info from JWT token.
        
        Args:
            token: JWT token from Authorization header
            
        Returns:
            Dict with user_id and user_email, or None if invalid
        """
        try:
            from app.core.auth import get_supabase_client
            
            supabase = get_supabase_client()
            response = supabase.auth.get_user(token)
            
            if response.user:
                return {
                    "user_id": response.user.id,
                    "user_email": response.user.email,
                }
        except Exception:
            # If token verification fails, just return None
            # Don't want to break the request because of logging
            pass
        
        return None
    
    async def _save_log_to_db(
        self,
        method: str,
        path: str,
        full_url: str,
        client_ip: Optional[str],
        user_agent: Optional[str],
        user_id: Optional[str],
        user_email: Optional[str],
        query_params: Optional[dict],
        path_params: Optional[dict],
        request_headers: dict,
        request_body: Optional[dict],
        status_code: int,
        response_headers: dict,
        response_body: Optional[dict],
        duration_ms: int,
        error_type: Optional[str],
        error_message: Optional[str],
        error_traceback: Optional[str],
    ) -> None:
        """
        Save log entry to database (runs in background).
        
        This function runs AFTER the response is sent to client,
        so any errors here won't affect the user's request.
        """
        try:
            async with AsyncSessionLocal() as db:
                log_entry = HTTPRequestLog(
                    method=method,
                    path=path,
                    full_url=full_url,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    user_id=user_id,
                    user_email=user_email,
                    query_params=query_params,
                    path_params=path_params,
                    request_headers=request_headers,
                    request_body=request_body,
                    status_code=status_code,
                    response_headers=response_headers,
                    response_body=response_body,
                    duration_ms=duration_ms,
                    error_type=error_type,
                    error_message=error_message,
                    error_traceback=error_traceback,
                )
                
                db.add(log_entry)
                await db.commit()
                
        except Exception as e:
            # If logging fails, print to console but don't crash
            print(f"❌ Failed to save HTTP log: {e}")