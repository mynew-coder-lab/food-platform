from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.engine import Connection

from app.auth.dependencies import require_role
from app.auth.models import UserRole
from app.core.database import get_connection
from app.vendors.models import vendors


def get_current_vendor(
    current_user: dict = Depends(require_role(UserRole.vendor, UserRole.admin)),
    conn: Connection = Depends(get_connection),
) -> dict:
    """Resolves the vendor profile owned by the authenticated user."""
    row = conn.execute(select(vendors).where(vendors.c.user_id == current_user["id"])).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found for this user")
    return dict(row)
