"""
HTTP Request Logging Model

Stores every HTTP request/response for debugging and monitoring.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class HTTPRequestLog(Base):
    """
    Logs all HTTP requests to the FastAPI backend.
    
    Used for debugging, monitoring, and tracing API usage.
    Query examples in Supabase:
    - All 500 errors: WHERE status_code >= 500
    - Slow requests: WHERE duration_ms > 1000
    - By user: WHERE user_id = '...'
    - By endpoint: WHERE path LIKE '/api/chat%'
    """
    __tablename__ = 'http_request_logs'
    
    # Primary Key
    log_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Timestamp (indexed for time-range queries)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # HTTP Request Info
    method = Column(
        String(10),
        nullable=False,
        comment="GET, POST, PUT, DELETE, PATCH, OPTIONS"
    )
    
    path = Column(
        Text,
        nullable=False,
        comment="URL path: /api/chat/sessions"
    )
    
    full_url = Column(
        Text,
        nullable=False,
        comment="Complete URL with query params"
    )
    
    # Client Info
    client_ip = Column(
        String(50),
        comment="Client IP address"
    )
    
    user_agent = Column(
        Text,
        comment="Browser/client user agent string"
    )
    
    # User Info (if authenticated)
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Supabase user ID if authenticated"
    )
    
    user_email = Column(
        String(255),
        nullable=True,
        comment="User email if authenticated"
    )
    
    # Request Details
    query_params = Column(
        JSONB,
        comment="URL query parameters as JSON"
    )
    
    path_params = Column(
        JSONB,
        comment="Path parameters (e.g., {session_id: '...'})"
    )
    
    request_headers = Column(
        JSONB,
        comment="HTTP request headers"
    )
    
    request_body = Column(
        JSONB,
        comment="Full request body for POST/PUT/PATCH"
    )
    
    # Response Details
    status_code = Column(
        Integer,
        nullable=False,
        comment="HTTP status code: 200, 404, 500, etc."
    )
    
    response_body = Column(
        JSONB,
        comment="Full response body (if JSON)"
    )
    
    response_headers = Column(
        JSONB,
        comment="HTTP response headers"
    )
    
    # Performance
    duration_ms = Column(
        Integer,
        comment="Request processing time in milliseconds"
    )
    
    # Error Info (if request failed)
    error_type = Column(
        String(255),
        comment="Exception class name if error occurred"
    )
    
    error_message = Column(
        Text,
        comment="Error message if request failed"
    )
    
    error_traceback = Column(
        Text,
        comment="Full stack trace for debugging"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_http_logs_timestamp', 'timestamp'),
        Index('idx_http_logs_status', 'status_code'),
        Index('idx_http_logs_user', 'user_id'),
        Index('idx_http_logs_path', 'path'),
        Index('idx_http_logs_method_path', 'method', 'path'),
        # Partial index for errors only (saves space)
        Index(
            'idx_http_logs_errors',
            'timestamp',
            postgresql_where="status_code >= 400"
        ),
    )