from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from app.auth.dependencies import require_role
from app.auth.models import UserRole
from app.core.database import get_connection
from app.vendors.models import vendors
from app.vendors.schemas import VendorCreate, VendorOut

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendor_profile(
    payload: VendorCreate,
    current_user: dict = Depends(require_role(UserRole.vendor, UserRole.admin)),
    conn: Connection = Depends(get_connection),
):
    existing = conn.execute(select(vendors).where(vendors.c.user_id == current_user["id"])).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor profile already exists")

    result = conn.execute(
        insert(vendors).values(
            user_id=current_user["id"],
            business_name=payload.business_name,
            location=payload.location,
            description=payload.description,
        )
    )
    new_id = result.inserted_primary_key[0]
    return dict(conn.execute(select(vendors).where(vendors.c.id == new_id)).mappings().first())


@router.get("", response_model=list[VendorOut])
def list_vendors(conn: Connection = Depends(get_connection)):
    rows = conn.execute(select(vendors).where(vendors.c.is_active.is_(True))).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: int, conn: Connection = Depends(get_connection)):
    row = conn.execute(select(vendors).where(vendors.c.id == vendor_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return dict(row)
