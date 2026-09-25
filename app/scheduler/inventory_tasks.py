from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.engine import Connection

from app.core.config import settings
from app.food_items.models import FoodItemStatus, food_items


def refresh_quick_access_flags(conn: Connection) -> int:
    """Flags active listings nearing their `available_until` window as
    quick-access, surfacing soon-to-expire inventory to reduce food waste."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(minutes=settings.quick_access_window_minutes)

    result = conn.execute(
        update(food_items)
        .where(food_items.c.status == FoodItemStatus.active)
        .where(food_items.c.is_quick_access.is_(False))
        .where(food_items.c.available_until.isnot(None))
        .where(food_items.c.available_until <= horizon)
        .where(food_items.c.available_until > now)
        .values(is_quick_access=True)
    )
    return result.rowcount


def expire_stale_food_items(conn: Connection) -> int:
    """Removes items from active listings once their available_until window
    has fully passed."""
    now = datetime.now(timezone.utc)
    result = conn.execute(
        update(food_items)
        .where(food_items.c.status == FoodItemStatus.active)
        .where(food_items.c.available_until.isnot(None))
        .where(food_items.c.available_until <= now)
        .values(status=FoodItemStatus.expired, is_quick_access=False)
    )
    return result.rowcount
