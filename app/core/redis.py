import redis

from app.core.config import settings

# We create a global Redis connection pool.
# Redis is incredibly fast and stores data entirely in RAM. We use it to:
# 1. Cache heavy, frequently accessed endpoints (like the food menu) so we don't spam Postgres.
# 2. Coordinate distributed locks so multiple API workers don't run the same background job twice.
redis_client = redis.from_url(settings.redis_url, decode_responses=True)
