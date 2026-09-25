from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.transactions.models import TransactionType, TransactionStatus


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    user_id: int
    amount: Decimal
    type: TransactionType
    status: TransactionStatus
    created_at: datetime
