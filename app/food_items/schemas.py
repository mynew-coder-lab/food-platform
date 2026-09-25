from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.food_items.models import FoodItemStatus


class FoodItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    quantity_available: int = Field(ge=0)
    available_until: Optional[datetime] = None


class FoodItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    quantity_available: Optional[int] = Field(default=None, ge=0)
    available_until: Optional[datetime] = None
    status: Optional[FoodItemStatus] = None


class FoodItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vendor_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    quantity_available: int
    available_until: Optional[datetime] = None
    is_quick_access: bool
    status: FoodItemStatus
    created_at: datetime
    updated_at: datetime
