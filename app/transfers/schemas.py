from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.transfers.models import TransferStatus


class TransferCreate(BaseModel):
    listed_price: Decimal


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    from_user_id: int
    to_user_id: Optional[int] = None
    listed_price: Decimal
    status: TransferStatus
    listed_at: datetime
    claimed_at: Optional[datetime] = None
