from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.engine import Connection

from app.core.config import settings
from app.orders.models import OrderStatus, orders
from app.transfers.models import TransferStatus, order_transfers

_ACTIVE_ORDER_STATUSES = (OrderStatus.confirmed, OrderStatus.preparing, OrderStatus.ready_for_pickup)


def flag_orders_nearing_deadline(conn: Connection) -> int:
    """Marks unclaimed orders as transferable once they enter the
    pre-deadline window, surfacing them for resale before they'd go to waste."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(minutes=settings.transfer_eligible_window_minutes)

    result = conn.execute(
        update(orders)
        .where(orders.c.status.in_(_ACTIVE_ORDER_STATUSES))
        .where(orders.c.is_transferable.is_(False))
        .where(orders.c.pickup_deadline <= horizon)
        .where(orders.c.pickup_deadline > now)
        .values(is_transferable=True)
    )
    return result.rowcount


def expire_unclaimed_orders(conn: Connection) -> int:
    """Force-expires orders that were never picked up past their grace
    period, and closes out any transfer listings still open on them."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=settings.order_expiry_grace_minutes)

    stale_order_ids = conn.execute(
        select(orders.c.id)
        .where(orders.c.status.in_(_ACTIVE_ORDER_STATUSES))
        .where(orders.c.pickup_deadline <= cutoff)
    ).scalars().all()

    if not stale_order_ids:
        return 0

    conn.execute(
        update(orders).where(orders.c.id.in_(stale_order_ids)).values(status=OrderStatus.expired, is_transferable=False)
    )
    conn.execute(
        update(order_transfers)
        .where(order_transfers.c.order_id.in_(stale_order_ids))
        .where(order_transfers.c.status == TransferStatus.listed)
        .values(status=TransferStatus.expired)
    )
    return len(stale_order_ids)
