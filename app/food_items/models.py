import enum

from sqlalchemy import (
    Table, Column, Integer, String, Text, Boolean, Numeric, DateTime,
    ForeignKey, Enum, func,
)

from app.core.database import metadata


class FoodItemStatus(str, enum.Enum):
    active = "active"
    sold_out = "sold_out"
    expired = "expired"
    removed = "removed"


# Time-based inventory: `available_until` + `is_quick_access` drive the
# automated waste-reduction workflow (see scheduler/inventory_tasks.py).
food_items = Table(
    "food_items", metadata,
    Column("id", Integer, primary_key=True),
    Column("vendor_id", Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(150), nullable=False),
    Column("description", Text, nullable=True),
    Column("price", Numeric(10, 2), nullable=False),
    Column("original_price", Numeric(10, 2), nullable=True),
    Column("quantity_available", Integer, nullable=False, default=0),
    Column("available_until", DateTime(timezone=True), nullable=True),
    Column("is_quick_access", Boolean, nullable=False, default=False),
    Column("status", Enum(FoodItemStatus), nullable=False, default=FoodItemStatus.active),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)
