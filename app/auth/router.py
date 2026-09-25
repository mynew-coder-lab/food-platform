from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from app.auth.security import create_access_token, hash_password, verify_password
from app.core.database import get_connection
from app.auth.models import users
from app.auth.schemas import Token, UserCreate, UserOut
from app.auth.dependencies import get_current_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


# -------------------- Auth --------------------

@auth_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, conn: Connection = Depends(get_connection)):
    existing = conn.execute(select(users).where(users.c.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    result = conn.execute(
        insert(users).values(
            name=payload.name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            phone=payload.phone,
            role=payload.role,
        )
    )
    new_id = result.inserted_primary_key[0]
    return dict(conn.execute(select(users).where(users.c.id == new_id)).mappings().first())


@auth_router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), conn: Connection = Depends(get_connection)):
    # OAuth2PasswordRequestForm uses `username`; callers should pass their email there.
    row = conn.execute(select(users).where(users.c.email == form_data.username)).mappings().first()
    if row is None or not verify_password(form_data.password, row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    return Token(access_token=create_access_token(subject=str(row["id"])))


# -------------------- Users --------------------

@users_router.get("/me", response_model=UserOut)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user
