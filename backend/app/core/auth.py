"""
Authentication utilities for FastAPI.

Handles JWT token verification using Supabase Auth.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import get_settings


# Security scheme
security = HTTPBearer()

# Supabase client dependency
def get_supabase_client() -> Client:
    """Get Supabase client with service role key."""
    # Get settings
    settings = get_settings()
    # Create and return Supabase client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Verify JWT token and return user.
    
    This ia a FastAPI dependency that:
    1. Extracts Bearer token from Authorization header
    2. Verifies token with Supabase
    3. Returns user object if valid
    4. Raises 401 if invalid
    
    Usage:
        @app.get("/api/protected")
        async def protected_route(user = Depends(get_current_user)):
            return {"user_email": user.email}
    
    Args:
        credentials: HTTP Bearer credentials extracted from header
        supabase: Supabase client for verification
        
    Returns:
        User: Supabase user object
        
    Raises:
        HTTPException: 401 if token invalid or missing"""
    
    # Extract token
    token = credentials.credentials

    # Verify token with Supabase
    try:
        # Try to verify the token with Supabase
        # This makes an API call to Supabase Auth service
        response = supabase.auth.get_user(token)

        # Check if user was returned
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INvalid authentication credentials",
            )

        # Token valid! Return the user object
        return response.user

    # Error handling
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )
