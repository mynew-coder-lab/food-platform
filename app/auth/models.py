import enum

from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Enum, func,
)

from app.core.database import metadata


class UserRole(str, enum.Enum):
    customer = "customer"
    vendor = "vendor"
    admin = "admin"


users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(120), nullable=False),
    Column("email", String(255), nullable=False, unique=True, index=True),
    Column("hashed_password", String(255), nullable=False),
    Column("phone", String(30), nullable=True),
    Column("role", Enum(UserRole), nullable=False, default=UserRole.customer),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
