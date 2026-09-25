from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.engine import Connection

from app.core.database import get_connection
from app.auth.dependencies import get_current_user
from app.transactions.models import transactions
from app.transactions.schemas import TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def list_my_transactions(current_user: dict = Depends(get_current_user), conn: Connection = Depends(get_connection)):
    rows = conn.execute(
        select(transactions)
        .where(transactions.c.user_id == current_user["id"])
        .order_by(transactions.c.created_at.desc())
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    row = conn.execute(select(transactions).where(transactions.c.id == transaction_id)).mappings().first()
    if row is None or row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return dict(row)
