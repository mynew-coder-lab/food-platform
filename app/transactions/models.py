import enum

from sqlalchemy import (
    Table, Column, Integer, Numeric, DateTime, ForeignKey, Enum, func,
)

from app.core.database import metadata


class TransactionType(str, enum.Enum):
    payment = "payment"
    refund = "refund"
    transfer_payment = "transfer_payment"
    transfer_payout = "transfer_payout"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


transactions = Table(
    "transactions", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("amount", Numeric(10, 2), nullable=False),
    Column("type", Enum(TransactionType), nullable=False),
    Column("status", Enum(TransactionStatus), nullable=False, default=TransactionStatus.pending),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
