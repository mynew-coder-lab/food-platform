import enum

from sqlalchemy import (
    Table, Column, Integer, Numeric, DateTime, Boolean, ForeignKey, Enum, func,
)

from app.core.database import metadata


class OrderStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    confirmed = "confirmed"
    preparing = "preparing"
    ready_for_pickup = "ready_for_pickup"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"


# `is_transferable` is flipped on automatically as pickup_deadline nears (see
# scheduler/order_lifecycle_tasks.py) so unclaimed orders surface for resale.
orders = Table(
    "orders", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("original_user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("vendor_id", Integer, ForeignKey("vendors.id"), nullable=False),
    Column("status", Enum(OrderStatus), nullable=False, default=OrderStatus.pending_payment),
    Column("total_amount", Numeric(10, 2), nullable=False),
    Column("pickup_deadline", DateTime(timezone=True), nullable=False),
    Column("is_transferable", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

order_items = Table(
    "order_items", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
    Column("food_item_id", Integer, ForeignKey("food_items.id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("price_at_order", Numeric(10, 2), nullable=False),
)
