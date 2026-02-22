"""
Database base class for SQLAlchemy models.

All models inherit from Base, which:
- Provides common table metadata
- Enables Alembic autogenerate to detect models
- Centralizes database configuration
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass