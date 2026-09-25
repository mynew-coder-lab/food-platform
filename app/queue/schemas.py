from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.queue.models import QueueStatus


class QueueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vendor_id: int
    order_id: int
    queue_number: int
    status: QueueStatus
    joined_at: datetime
    called_at: Optional[datetime] = None
    served_at: Optional[datetime] = None
