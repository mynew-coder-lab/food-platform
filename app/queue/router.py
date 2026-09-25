from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from app.core.database import get_connection
from app.vendors.dependencies import get_current_vendor
from app.queue.schemas import QueueOut
from app.queue import service as queue_service

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_model=list[QueueOut])
def get_my_vendor_queue(vendor: dict = Depends(get_current_vendor), conn: Connection = Depends(get_connection)):
    return queue_service.get_vendor_queue(conn, vendor["id"])


@router.post("/call-next", response_model=QueueOut)
def call_next_in_queue(vendor: dict = Depends(get_current_vendor), conn: Connection = Depends(get_connection)):
    return queue_service.call_next(conn, vendor["id"])


@router.patch("/{queue_entry_id}/serve", response_model=QueueOut)
def serve_queue_entry(
    queue_entry_id: int,
    vendor: dict = Depends(get_current_vendor),
    conn: Connection = Depends(get_connection),
):
    return queue_service.mark_served(conn, queue_entry_id, vendor["id"])
