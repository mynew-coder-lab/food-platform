import enum

from sqlalchemy import (
    Table, Column, Integer, DateTime, ForeignKey, Enum, func,
)

from app.core.database import metadata


class QueueStatus(str, enum.Enum):
    waiting = "waiting"
    called = "called"
    served = "served"
    no_show = "no_show"


queue_entries = Table(
    "queue_entries", metadata,
    Column("id", Integer, primary_key=True),
    Column("vendor_id", Integer, ForeignKey("vendors.id"), nullable=False),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("queue_number", Integer, nullable=False),
    Column("status", Enum(QueueStatus), nullable=False, default=QueueStatus.waiting),
    Column("joined_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("called_at", DateTime(timezone=True), nullable=True),
    Column("served_at", DateTime(timezone=True), nullable=True),
)
