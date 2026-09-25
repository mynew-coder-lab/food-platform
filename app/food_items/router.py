from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection

from app.core.database import get_connection
from app.core.redis import redis_client
from app.vendors.dependencies import get_current_vendor
from app.food_items.models import FoodItemStatus, food_items
from app.food_items.schemas import FoodItemCreate, FoodItemOut, FoodItemUpdate
import json

CACHE_KEY_MENU = "menu:available_items"

router = APIRouter(prefix="/food-items", tags=["food-items"])


@router.post("", response_model=FoodItemOut, status_code=status.HTTP_201_CREATED)
def create_food_item(
    payload: FoodItemCreate,
    vendor: dict = Depends(get_current_vendor),
    conn: Connection = Depends(get_connection),
):
    result = conn.execute(
        insert(food_items).values(
            vendor_id=vendor["id"],
            name=payload.name,
            description=payload.description,
            price=payload.price,
            original_price=payload.original_price,
            quantity_available=payload.quantity_available,
            available_until=payload.available_until,
        )
    )
    new_id = result.inserted_primary_key[0]
    
    # [REDIS] Invalidate cache because menu changed!
    redis_client.delete(CACHE_KEY_MENU)
    
    return dict(conn.execute(select(food_items).where(food_items.c.id == new_id)).mappings().first())


@router.get("", response_model=list[FoodItemOut])
def list_food_items(
    vendor_id: Optional[int] = None,
    quick_access: Optional[bool] = None,
    conn: Connection = Depends(get_connection),
):
    # [REDIS] Only cache the default menu (no filters)
    if vendor_id is None and quick_access is None:
        cached_menu = redis_client.get(CACHE_KEY_MENU)
        if cached_menu:
            return json.loads(cached_menu)

    query = select(food_items).where(food_items.c.status == FoodItemStatus.active)
    if vendor_id is not None:
        query = query.where(food_items.c.vendor_id == vendor_id)
    if quick_access is not None:
        query = query.where(food_items.c.is_quick_access.is_(quick_access))
    rows = conn.execute(query.order_by(food_items.c.available_until.asc().nulls_last())).mappings().all()
    results = [dict(r) for r in rows]

    # [REDIS] Save to cache for 60 seconds
    if vendor_id is None and quick_access is None:
        def default_serializer(obj):
            if hasattr(obj, 'isoformat'): return obj.isoformat()
            return str(obj)
        redis_client.set(CACHE_KEY_MENU, json.dumps(results, default=default_serializer), ex=60)

    return results


@router.get("/quick-access", response_model=list[FoodItemOut])
def list_quick_access_items(conn: Connection = Depends(get_connection)):
    """Items nearing their available-until window — surfaced to reduce food waste."""
    rows = conn.execute(
        select(food_items)
        .where(food_items.c.status == FoodItemStatus.active)
        .where(food_items.c.is_quick_access.is_(True))
        .order_by(food_items.c.available_until.asc())
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{food_item_id}", response_model=FoodItemOut)
def get_food_item(food_item_id: int, conn: Connection = Depends(get_connection)):
    row = conn.execute(select(food_items).where(food_items.c.id == food_item_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    return dict(row)


@router.patch("/{food_item_id}", response_model=FoodItemOut)
def update_food_item(
    food_item_id: int,
    payload: FoodItemUpdate,
    vendor: dict = Depends(get_current_vendor),
    conn: Connection = Depends(get_connection),
):
    row = conn.execute(select(food_items).where(food_items.c.id == food_item_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    if row["vendor_id"] != vendor["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your food item")

    updates = payload.model_dump(exclude_unset=True)
    if updates:
        conn.execute(update(food_items).where(food_items.c.id == food_item_id).values(**updates))
        # [REDIS] Invalidate cache
        redis_client.delete(CACHE_KEY_MENU)

    return dict(conn.execute(select(food_items).where(food_items.c.id == food_item_id)).mappings().first())


@router.delete("/{food_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_food_item(
    food_item_id: int,
    vendor: dict = Depends(get_current_vendor),
    conn: Connection = Depends(get_connection),
):
    row = conn.execute(select(food_items).where(food_items.c.id == food_item_id)).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
    if row["vendor_id"] != vendor["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your food item")

    conn.execute(update(food_items).where(food_items.c.id == food_item_id).values(status=FoodItemStatus.removed))
    
    # [REDIS] Invalidate cache
    redis_client.delete(CACHE_KEY_MENU)
