from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, metadata
from app.auth.router import auth_router, users_router
from app.vendors.router import router as vendors_router
from app.food_items.router import router as food_items_router
from app.orders.router import router as orders_router
from app.transfers.router import router as transfers_router
from app.queue.router import router as queue_router
from app.transactions.router import router as transactions_router
from app.scheduler.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    metadata.create_all(engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Food Ordering & Queue Management Platform",
    description=(
        "Backend API for order processing, queue handling, transaction management, "
        "order transfer/resale of unclaimed orders, and time-based quick-access "
        "inventory listings for food waste reduction."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(vendors_router)
app.include_router(food_items_router)
app.include_router(orders_router)
app.include_router(transfers_router)
app.include_router(queue_router)
app.include_router(transactions_router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
