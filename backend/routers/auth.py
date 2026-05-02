import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from database import get_user_by_email, get_user_by_username, create_user
from auth_utils import hash_password, verify_password, create_access_token

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _public_user(user: dict) -> dict:
    return {"id": user["id"], "username": user["username"], "email": user["email"]}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    if len(body.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters.")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    if get_user_by_email(body.email):
        raise HTTPException(400, "Email already registered.")
    if get_user_by_username(body.username):
        raise HTTPException(400, "Username already taken.")

    user = {
        "id": str(uuid.uuid4()),
        "username": body.username,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "wins": 0,
        "losses": 0,
        "gamesPlayed": 0,
    }
    create_user(user)

    token = create_access_token({"sub": user["id"], "username": user["username"], "email": user["email"]})
    return {"token": token, "user": _public_user(user)}


@router.post("/login")
def login(body: LoginRequest):
    user = get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": user["id"], "username": user["username"], "email": user["email"]})
    return {"token": token, "user": _public_user(user)}
