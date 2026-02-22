"""
Authentication test endpoints.

These endpoints test JWT verification.
"""

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user

# Create router for authentication endpoints
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Endpoints
@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    """
    Get current user info from JWT token.
    
    This endpoint verifies the JWT token and returns user details.
    
    Args:
        user: User object injected by get_current_user dependency
        
    Returns:
        dict: User information (id, email, created_at)
        
    Requires:
        Authorization: Bearer <token> header
    """
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at,
    }

@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    """
    Example protected route.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        user: User object injected by get_current_user dependency
        
    Returns:
        dict: Welcome message with user info
    """

    return {
        "message": f"Hello {user.email}! This is a protected route.",
        "user_id": str(user.id),
    }