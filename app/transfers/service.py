from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection

from app.orders.models import OrderStatus, orders
from app.transactions.models import TransactionStatus, TransactionType, transactions
from app.transfers.models import TransferStatus, order_transfers
from app.core.utils import ensure_utc

# Orders in these states haven't been picked up yet and are eligible for resale.
_ACTIVE_ORDER_STATUSES = (OrderStatus.confirmed, OrderStatus.preparing, OrderStatus.ready_for_pickup)


def list_order_for_transfer(conn: Connection, order_id: int, user_id: int, listed_price) -> dict:
    order_row = conn.execute(select(orders).where(orders.c.id == order_id)).mappings().first()
    if order_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order_row["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    if order_row["status"] not in _ACTIVE_ORDER_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not eligible for transfer")
    if ensure_utc(order_row["pickup_deadline"]) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup deadline has already passed")

    existing = conn.execute(
        select(order_transfers)
        .where(order_transfers.c.order_id == order_id)
        .where(order_transfers.c.status == TransferStatus.listed)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already listed for transfer")

    result = conn.execute(
        insert(order_transfers).values(
            order_id=order_id,
            from_user_id=user_id,
            listed_price=listed_price,
            status=TransferStatus.listed,
        )
    )
    transfer_id = result.inserted_primary_key[0]
    return dict(conn.execute(select(order_transfers).where(order_transfers.c.id == transfer_id)).mappings().first())


def browse_transfers(conn: Connection) -> list[dict]:
    rows = conn.execute(
        select(order_transfers)
        .where(order_transfers.c.status == TransferStatus.listed)
        .order_by(order_transfers.c.listed_at.asc())
    ).mappings().all()
    return [dict(r) for r in rows]


def claim_transfer(conn: Connection, transfer_id: int, buyer_id: int) -> dict:
    transfer_row = conn.execute(
        select(order_transfers).where(order_transfers.c.id == transfer_id).with_for_update()
    ).mappings().first()
    if transfer_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer listing not found")
    if transfer_row["status"] != TransferStatus.listed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This listing is no longer available")
    if transfer_row["from_user_id"] == buyer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot claim your own listing")

    order_row = conn.execute(select(orders).where(orders.c.id == transfer_row["order_id"])).mappings().first()
    if ensure_utc(order_row["pickup_deadline"]) <= datetime.now(timezone.utc) or order_row["status"] not in _ACTIVE_ORDER_STATUSES:
        conn.execute(update(order_transfers).where(order_transfers.c.id == transfer_id).values(status=TransferStatus.expired))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is no longer eligible for transfer")

    conn.execute(
        update(order_transfers)
        .where(order_transfers.c.id == transfer_id)
        .values(status=TransferStatus.claimed, to_user_id=buyer_id, claimed_at=datetime.now(timezone.utc))
    )
    # Ownership of the order (and its place in the queue) passes to the buyer.
    conn.execute(update(orders).where(orders.c.id == order_row["id"]).values(user_id=buyer_id))

    conn.execute(
        insert(transactions).values(
            order_id=order_row["id"], user_id=buyer_id, amount=transfer_row["listed_price"],
            type=TransactionType.transfer_payment, status=TransactionStatus.completed,
        )
    )
    conn.execute(
        insert(transactions).values(
            order_id=order_row["id"], user_id=transfer_row["from_user_id"], amount=transfer_row["listed_price"],
            type=TransactionType.transfer_payout, status=TransactionStatus.completed,
        )
    )

    return dict(conn.execute(select(order_transfers).where(order_transfers.c.id == transfer_id)).mappings().first())


def cancel_transfer(conn: Connection, transfer_id: int, user_id: int) -> dict:
    row = conn.execute(select(order_transfers).where(order_transfers.c.id == transfer_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer listing not found")
    if row["from_user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing")
    if row["status"] != TransferStatus.listed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active listings can be cancelled")

    conn.execute(update(order_transfers).where(order_transfers.c.id == transfer_id).values(status=TransferStatus.cancelled))
    return dict(conn.execute(select(order_transfers).where(order_transfers.c.id == transfer_id)).mappings().first())
