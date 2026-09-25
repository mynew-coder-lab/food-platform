from sqlalchemy import (
    Table, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func,
)

from app.core.database import metadata


vendors = Table(
    "vendors", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("business_name", String(150), nullable=False),
    Column("location", String(255), nullable=True),
    Column("description", Text, nullable=True),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
