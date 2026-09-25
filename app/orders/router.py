from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from app.core.database import get_connection
from app.auth.dependencies import get_current_user
from app.vendors.dependencies import get_current_vendor
from app.orders.schemas import OrderCreate, OrderOut, OrderStatusUpdate
from app.orders import service as order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    return order_service.create_order(conn, current_user["id"], payload)


@router.get("", response_model=list[OrderOut])
def list_my_orders(current_user: dict = Depends(get_current_user), conn: Connection = Depends(get_connection)):
    return order_service.list_orders_for_user(conn, current_user["id"])


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, current_user: dict = Depends(get_current_user), conn: Connection = Depends(get_connection)):
    return order_service.get_order_for_user(conn, order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    vendor: dict = Depends(get_current_vendor),
    conn: Connection = Depends(get_connection),
):
    return order_service.update_order_status(conn, order_id, vendor["id"], payload.status)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, current_user: dict = Depends(get_current_user), conn: Connection = Depends(get_connection)):
    return order_service.cancel_order(conn, order_id, current_user["id"])
