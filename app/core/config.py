from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/canteen_queue_db"

    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Time-based inventory management (food waste reduction) ---
    # How far ahead of a food item's `available_until` window it gets flagged
    # as a "quick-access" listing so it gets surfaced/sold before it expires.
    quick_access_window_minutes: int = 60
    food_item_expiry_grace_minutes: int = 0

    # --- Order transfer (resale of unclaimed orders) ---
    # How far ahead of the pickup deadline an unclaimed order gets flagged as
    # transferable, so it can be resold before it goes to waste.
    transfer_eligible_window_minutes: int = 30
    # Grace period past the pickup deadline before an unclaimed order is force-expired.
    order_expiry_grace_minutes: int = 15

    # How often the background maintenance job runs.
    scheduler_interval_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
