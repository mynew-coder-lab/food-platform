from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Connection

from app.queue.models import QueueStatus, queue_entries


def assign_queue_number(conn: Connection, vendor_id: int, order_id: int) -> int:
    """Assigns the next sequential queue number for a vendor. Numbers increase
    monotonically per vendor and are not reset between days."""
    max_number = conn.execute(
        select(func.max(queue_entries.c.queue_number)).where(queue_entries.c.vendor_id == vendor_id)
    ).scalar()
    next_number = (max_number or 0) + 1

    conn.execute(
        insert(queue_entries).values(
            vendor_id=vendor_id,
            order_id=order_id,
            queue_number=next_number,
            status=QueueStatus.waiting,
        )
    )
    return next_number


def get_vendor_queue(conn: Connection, vendor_id: int) -> list[dict]:
    rows = conn.execute(
        select(queue_entries)
        .where(queue_entries.c.vendor_id == vendor_id)
        .where(queue_entries.c.status.in_([QueueStatus.waiting, QueueStatus.called]))
        .order_by(queue_entries.c.queue_number.asc())
    ).mappings().all()
    return [dict(r) for r in rows]


def call_next(conn: Connection, vendor_id: int) -> dict:
    row = conn.execute(
        select(queue_entries)
        .where(queue_entries.c.vendor_id == vendor_id)
        .where(queue_entries.c.status == QueueStatus.waiting)
        .order_by(queue_entries.c.queue_number.asc())
        .with_for_update()
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No one waiting in queue")

    conn.execute(
        update(queue_entries)
        .where(queue_entries.c.id == row["id"])
        .values(status=QueueStatus.called, called_at=datetime.now(timezone.utc))
    )
    return dict(conn.execute(select(queue_entries).where(queue_entries.c.id == row["id"])).mappings().first())


def mark_served(conn: Connection, queue_entry_id: int, vendor_id: int) -> dict:
    row = conn.execute(select(queue_entries).where(queue_entries.c.id == queue_entry_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue entry not found")
    if row["vendor_id"] != vendor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your queue")

    conn.execute(
        update(queue_entries)
        .where(queue_entries.c.id == queue_entry_id)
        .values(status=QueueStatus.served, served_at=datetime.now(timezone.utc))
    )
    return dict(conn.execute(select(queue_entries).where(queue_entries.c.id == queue_entry_id)).mappings().first())
