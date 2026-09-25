import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import engine
from app.scheduler import inventory_tasks, order_lifecycle_tasks

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler()


def _run_maintenance_cycle() -> None:
    """Single periodic pass that drives both automated workflows:
    1) time-based inventory management (quick-access flags / expiry), and
    2) order-transfer window flagging / unclaimed-order expiry."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            quick_access_count = inventory_tasks.refresh_quick_access_flags(conn)
            expired_items_count = inventory_tasks.expire_stale_food_items(conn)
            transferable_count = order_lifecycle_tasks.flag_orders_nearing_deadline(conn)
            expired_orders_count = order_lifecycle_tasks.expire_unclaimed_orders(conn)
            trans.commit()
            logger.info(
                "Maintenance cycle: %s items flagged quick-access, %s items expired, "
                "%s orders flagged transferable, %s orders expired",
                quick_access_count, expired_items_count, transferable_count, expired_orders_count,
            )
        except Exception:
            trans.rollback()
            logger.exception("Maintenance cycle failed")


def start_scheduler() -> None:
    scheduler.add_job(
        _run_maintenance_cycle,
        "interval",
        seconds=settings.scheduler_interval_seconds,
        id="inventory_and_order_maintenance",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
