from datetime import datetime, timezone


def ensure_utc(dt: datetime) -> datetime:
    """Normalizes a datetime to be timezone-aware in UTC.

    Some drivers/DBs return naive datetimes for timezone-aware columns
    (e.g. SQLite), and clients may submit naive timestamps. Comparing a
    naive and an aware datetime raises a TypeError, so every value read
    back for a deadline/expiry comparison is passed through this first.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
