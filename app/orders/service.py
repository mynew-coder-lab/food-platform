from fastapi import HTTPException, status
from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection

from app.food_items.models import food_items
from app.orders.models import OrderStatus, order_items, orders
from app.queue.models import QueueStatus, queue_entries
from app.transactions.models import TransactionStatus, TransactionType, transactions
from app.orders.schemas import OrderCreate
from app.queue.service import assign_queue_number


def _order_with_items(conn: Connection, order_id: int) -> dict:
    order_row = conn.execute(select(orders).where(orders.c.id == order_id)).mappings().first()
    if order_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    items = conn.execute(select(order_items).where(order_items.c.order_id == order_id)).mappings().all()
    result = dict(order_row)
    result["items"] = [dict(i) for i in items]
    return result


def create_order(conn: Connection, user_id: int, payload: OrderCreate) -> dict:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must contain at least one item")

    total = 0
    line_items = []

    for item in payload.items:
        food_row = conn.execute(
            select(food_items).where(food_items.c.id == item.food_item_id).with_for_update()
        ).mappings().first()
        if food_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Food item {item.food_item_id} not found")
        if food_row["vendor_id"] != payload.vendor_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All items must belong to the same vendor")
        if food_row["quantity_available"] < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {food_row['name']}")

        price = food_row["price"]
        total += price * item.quantity
        line_items.append({"food_item_id": item.food_item_id, "quantity": item.quantity, "price_at_order": price})

        conn.execute(
            update(food_items)
            .where(food_items.c.id == item.food_item_id)
            .values(quantity_available=food_row["quantity_available"] - item.quantity)
        )

    result = conn.execute(
        insert(orders).values(
            user_id=user_id,
            original_user_id=user_id,
            vendor_id=payload.vendor_id,
            status=OrderStatus.confirmed,
            total_amount=total,
            pickup_deadline=payload.pickup_deadline,
        )
    )
    order_id = result.inserted_primary_key[0]

    for line in line_items:
        conn.execute(insert(order_items).values(order_id=order_id, **line))

    conn.execute(
        insert(transactions).values(
            order_id=order_id,
            user_id=user_id,
            amount=total,
            type=TransactionType.payment,
            status=TransactionStatus.completed,
        )
    )

    assign_queue_number(conn, vendor_id=payload.vendor_id, order_id=order_id)

    return _order_with_items(conn, order_id)


def get_order_for_user(conn: Connection, order_id: int, current_user: dict) -> dict:
    order = _order_with_items(conn, order_id)
    if order["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    return order


def list_orders_for_user(conn: Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        select(orders).where(orders.c.user_id == user_id).order_by(orders.c.created_at.desc())
    ).mappings().all()

    results = []
    for row in rows:
        order = dict(row)
        items = conn.execute(select(order_items).where(order_items.c.order_id == row["id"])).mappings().all()
        order["items"] = [dict(i) for i in items]
        results.append(order)
    return results


def update_order_status(conn: Connection, order_id: int, vendor_id: int, new_status: OrderStatus) -> dict:
    order_row = conn.execute(select(orders).where(orders.c.id == order_id)).mappings().first()
    if order_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order_row["vendor_id"] != vendor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")

    conn.execute(update(orders).where(orders.c.id == order_id).values(status=new_status))

    if new_status == OrderStatus.completed:
        conn.execute(
            update(queue_entries)
            .where(queue_entries.c.order_id == order_id)
            .values(status=QueueStatus.served)
        )
    elif new_status == OrderStatus.cancelled:
        _restock_and_refund(conn, order_id)

    return _order_with_items(conn, order_id)


def cancel_order(conn: Connection, order_id: int, user_id: int) -> dict:
    order_row = conn.execute(select(orders).where(orders.c.id == order_id)).mappings().first()
    if order_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order_row["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    if order_row["status"] in (OrderStatus.completed, OrderStatus.cancelled, OrderStatus.expired):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order can no longer be cancelled")

    conn.execute(update(orders).where(orders.c.id == order_id).values(status=OrderStatus.cancelled))
    _restock_and_refund(conn, order_id)
    conn.execute(update(queue_entries).where(queue_entries.c.order_id == order_id).values(status=QueueStatus.no_show))

    return _order_with_items(conn, order_id)


def _restock_and_refund(conn: Connection, order_id: int) -> None:
    order_row = conn.execute(select(orders).where(orders.c.id == order_id)).mappings().first()
    items = conn.execute(select(order_items).where(order_items.c.order_id == order_id)).mappings().all()

    for item in items:
        conn.execute(
            update(food_items)
            .where(food_items.c.id == item["food_item_id"])
            .values(quantity_available=food_items.c.quantity_available + item["quantity"])
        )

    conn.execute(
        insert(transactions).values(
            order_id=order_id,
            user_id=order_row["user_id"],
            amount=order_row["total_amount"],
            type=TransactionType.refund,
            status=TransactionStatus.completed,
        )
    )
