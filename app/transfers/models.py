import enum

from sqlalchemy import (
    Table, Column, Integer, Numeric, DateTime, ForeignKey, Enum, func,
)

from app.core.database import metadata


class TransferStatus(str, enum.Enum):
    listed = "listed"
    claimed = "claimed"
    cancelled = "cancelled"
    expired = "expired"


# Order-transfer / resale listings. Only one 'listed' row per order is
# enforced in service logic (see transfers/service.py).
order_transfers = Table(
    "order_transfers", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
    Column("from_user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("to_user_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("listed_price", Numeric(10, 2), nullable=False),
    Column("status", Enum(TransferStatus), nullable=False, default=TransferStatus.listed),
    Column("listed_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("claimed_at", DateTime(timezone=True), nullable=True),
)
