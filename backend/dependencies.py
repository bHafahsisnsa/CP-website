"""dependencies.py — auth & RBAC dependencies untuk FastAPI.

- get_current_user   : validasi Bearer sess_ token via koleksi `sessions`.
- get_optional_user  : sama, tapi kembalikan None bila tanpa/invalid token (storefront + guest).
- require_role(*r)    : batasi endpoint ke peran tertentu.
- require_section(s)  : batasi berdasarkan matrix permissions_config.
"""
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException

from core_utils import safe_doc
from db import get_db
from permissions_config import can_access


def _is_expired(expires_at) -> bool:
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(str(expires_at))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp < datetime.now(timezone.utc)
    except Exception:
        return False


async def _resolve_user(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    db = get_db()
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None
    if _is_expired(session.get("expires_at")):
        await db.sessions.delete_one({"token": token})
        return None
    user = await db.users.find_one({"id": session.get("user_id")})
    if not user or user.get("status") != "active":
        return None
    return safe_doc(user)


async def get_current_user(authorization: str = Header(default=None)):
    user = await _resolve_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau kedaluwarsa")
    return user


async def get_optional_user(authorization: str = Header(default=None)):
    return await _resolve_user(authorization)


def require_role(*roles):
    async def _dep(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Akses ditolak untuk peran ini")
        return user
    return _dep


def require_section(section: str):
    async def _dep(user=Depends(get_current_user)):
        if not can_access(user.get("role"), section):
            raise HTTPException(status_code=403, detail="Akses ditolak untuk modul ini")
        return user
    return _dep
