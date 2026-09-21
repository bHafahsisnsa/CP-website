"""routers/auth.py — autentikasi (fondasi infra).

Kontrak:
  POST /api/auth/register {name,email,password,phone?} -> {token, user}
  POST /api/auth/login    {email,password}             -> {token, user}
  GET  /api/auth/me                                    -> user (Bearer sess_)

Hash password = bcrypt (core_utils). Token sesi = 'sess_...' disimpan di koleksi `sessions`.
Router TIPIS: validasi + I/O DB; helper di core_utils/services.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from core_utils import (hash_password, needs_rehash, new_id, new_token, now_iso,
                        safe_doc, verify_password)
from db import get_db
from dependencies import get_current_user
from schemas import AuthResponse, LoginRequest, RegisterRequest
from services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_DAYS = 30


async def _issue_session(db, user_id: str) -> str:
    token = new_token()
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
    await db.sessions.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": now_iso(),
        "expires_at": expires,
    })
    return token


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest):
    db = get_db()
    email = payload.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    user = {
        "id": new_id("usr"),
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": "customer",
        "phone": payload.phone,
        "status": "active",
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    token = await _issue_session(db, user["id"])
    await log_action(user["id"], "register", "users", user["id"])
    return {"token": token, "user": safe_doc(user)}


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    db = get_db()
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah")
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Akun nonaktif")
    # Migrasi transparan hash legacy -> bcrypt saat login berhasil.
    if needs_rehash(user.get("password_hash", "")):
        await db.users.update_one({"id": user["id"]},
                                  {"$set": {"password_hash": hash_password(payload.password)}})
    token = await _issue_session(db, user["id"])
    await log_action(user["id"], "login", "users", user["id"])
    return {"token": token, "user": safe_doc(user)}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
