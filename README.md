# Food Ordering & Queue Management Platform — Backend

FastAPI backend for a food ordering and queue management platform. Built with
**FastAPI**, **PostgreSQL**, **SQLAlchemy Core** (no ORM — raw `Table`/`select`/`insert`
constructs), and **Psycopg2**.

## Features

- **Order processing** — cart-style order creation with stock validation, atomic
  stock decrement, total calculation, and transaction records.
- **Queue management** — sequential per-vendor queue numbers assigned automatically
  on order confirmation; vendor endpoints to call the next customer and mark orders served.
- **Order transfer / resale** — users can list an unclaimed, not-yet-picked-up order
  for resale before its pickup deadline; another user can browse and claim it, which
  reassigns order ownership (and queue position) and records the payment/payout.
- **Time-based inventory management (waste reduction)** — a background job
  periodically flags food items nearing their `available_until` window as
  "quick-access" listings, and expires items once that window passes.
- **Automated order lifecycle** — the same background job flags unclaimed orders as
  transferable as they approach their pickup deadline, and force-expires orders that
  are never picked up past a grace period (closing out any open transfer listing).
- **Transaction management** — every payment, refund, transfer payment, and transfer
  payout is recorded and queryable per user.
- **JWT auth** with `customer` / `vendor` / `admin` roles.

## Project layout

```
app/
  main.py                     FastAPI app, router registration, scheduler lifecycle
  config.py                   Environment-driven settings (pydantic-settings)
  database.py                 SQLAlchemy engine, MetaData, per-request connection
  models.py                   SQLAlchemy Core Table definitions + enums
  schemas.py                  Pydantic request/response models
  auth.py                     Password hashing + JWT helpers
  dependencies.py             get_current_user / role guards / vendor resolution
  utils.py                    Timezone-safe datetime helper
  routers/
    auth.py                   POST /auth/register, /auth/login
    users.py                  GET /users/me
    vendors.py                Vendor profile CRUD
    food_items.py             Food item CRUD + /food-items/quick-access
    orders.py                 Order creation, listing, status updates, cancellation
    transfers.py              List / browse / claim / cancel order-transfer listings
    queue.py                  Vendor queue view, call-next, mark-served
    transactions.py           Transaction history
  services/
    order_service.py          Order business logic (stock, totals, refunds)
    transfer_service.py       Order resale business logic
    queue_service.py          Queue numbering and progression
    inventory_service.py      Quick-access flagging / food item expiry
    order_lifecycle_service.py  Transfer-window flagging / order expiry
    scheduler.py               APScheduler wiring for the two workflows above
requirements.txt
.env.example
```

## Setup

1. **Create a PostgreSQL database** and note its connection string.

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** — copy `.env.example` to `.env` and fill in
   `DATABASE_URL` and a real `SECRET_KEY`:
   ```bash
   cp .env.example .env
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Tables are created automatically on startup via `metadata.create_all()`. For a
   production deployment, swap this for a proper migration tool (e.g. Alembic) —
   it isn't included here to keep the scope to what was asked for.

5. **Interactive API docs** are available at `http://localhost:8000/docs` once running.

## Configuration reference (`.env`)

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Postgres connection string (`postgresql+psycopg2://...`) | — |
| `SECRET_KEY` | JWT signing secret | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime | 60 |
| `QUICK_ACCESS_WINDOW_MINUTES` | How far ahead of `available_until` an item gets flagged quick-access | 60 |
| `TRANSFER_ELIGIBLE_WINDOW_MINUTES` | How far ahead of `pickup_deadline` an order is auto-flagged transferable | 30 |
| `ORDER_EXPIRY_GRACE_MINUTES` | Grace period past `pickup_deadline` before an unclaimed order is force-expired | 15 |
| `SCHEDULER_INTERVAL_SECONDS` | How often the background maintenance job runs | 60 |

## API overview

All endpoints are prefixed as shown; JSON in/out unless noted. Authenticated routes
expect `Authorization: Bearer <token>`.

**Auth**
- `POST /auth/register` — create an account (`role`: `customer` | `vendor` | `admin`)
- `POST /auth/login` — OAuth2 password form (`username` = email); returns a JWT

**Users**
- `GET /users/me`

**Vendors**
- `POST /vendors` — create the caller's vendor profile (vendor/admin role required)
- `GET /vendors`, `GET /vendors/{vendor_id}`

**Food items**
- `POST /food-items` — vendor-only
- `GET /food-items?vendor_id=&quick_access=` — public listing with optional filters
- `GET /food-items/quick-access` — items nearing expiry, surfaced for waste reduction
- `GET /food-items/{id}`, `PATCH /food-items/{id}`, `DELETE /food-items/{id}` — vendor-owner only

**Orders**
- `POST /orders` — `{vendor_id, items: [{food_item_id, quantity}], pickup_deadline}`
- `GET /orders` — caller's own orders
- `GET /orders/{id}`
- `PATCH /orders/{id}/status` — vendor-only status transition
- `POST /orders/{id}/cancel` — owner cancels (restocks items, issues a refund transaction)

**Transfers (resale)**
- `POST /transfers/orders/{order_id}` — `{listed_price}`, order owner only
- `GET /transfers` — browse active listings
- `POST /transfers/{transfer_id}/claim` — buy a listed order; reassigns ownership
- `DELETE /transfers/{transfer_id}` — seller cancels their own listing

**Queue** (vendor-only)
- `GET /queue` — current waiting/called entries for the caller's vendor
- `POST /queue/call-next`
- `PATCH /queue/{queue_entry_id}/serve`

**Transactions**
- `GET /transactions`, `GET /transactions/{id}` — caller's own transaction history

**Health**
- `GET /health`

## Notes on the automated workflows

Both waste-reduction/resale automations run from a single periodic job
(`services/scheduler.py`, via APScheduler) rather than per-request checks, so they
apply uniformly across the whole catalog/order book instead of relying on lazy,
request-time evaluation. The window sizes are configurable via `.env` above so you
can tune how early items/orders get surfaced.

## Testing performed

Before delivery this was smoke-tested end-to-end against a live database (register →
login → vendor profile → food item creation → order placement with stock/total
validation → transfer listing → claim by a second user → ownership/queue/transaction
verification → scheduler-driven quick-access flagging after its interval elapsed).
All flows passed.
