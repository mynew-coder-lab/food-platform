from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VendorCreate(BaseModel):
    business_name: str
    location: Optional[str] = None
    description: Optional[str] = None


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    business_name: str
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
