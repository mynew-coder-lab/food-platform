from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from app.core.database import get_connection
from app.auth.dependencies import get_current_user
from app.transfers.schemas import TransferCreate, TransferOut
from app.transfers import service as transfer_service

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("/orders/{order_id}", response_model=TransferOut, status_code=201)
def list_order_for_resale(
    order_id: int,
    payload: TransferCreate,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    return transfer_service.list_order_for_transfer(conn, order_id, current_user["id"], payload.listed_price)


@router.get("", response_model=list[TransferOut])
def browse_available_transfers(conn: Connection = Depends(get_connection)):
    return transfer_service.browse_transfers(conn)


@router.post("/{transfer_id}/claim", response_model=TransferOut)
def claim_transfer_listing(
    transfer_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    return transfer_service.claim_transfer(conn, transfer_id, current_user["id"])


@router.delete("/{transfer_id}", response_model=TransferOut)
def cancel_transfer_listing(
    transfer_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    return transfer_service.cancel_transfer(conn, transfer_id, current_user["id"])
