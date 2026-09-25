from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.orders.models import OrderStatus


class OrderItemCreate(BaseModel):
    food_item_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    vendor_id: int
    items: List[OrderItemCreate]
    pickup_deadline: datetime


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    food_item_id: int
    quantity: int
    price_at_order: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    original_user_id: int
    vendor_id: int
    status: OrderStatus
    total_amount: Decimal
    pickup_deadline: datetime
    is_transferable: bool
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut] = []


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
