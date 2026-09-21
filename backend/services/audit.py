"""services/audit.py — jejak audit ringan (append-only).

Mencatat aksi penting (login, create/update/delete entitas) ke koleksi `audit_logs`.
Dipakai lintas router; jaga tetap ringkas & defensif (jangan pernah melempar ke caller).
"""
from core_utils import new_id, now_iso
from db import get_db


async def log_action(actor_id: str, action: str, entity: str,
                     entity_id: str = "", meta: dict | None = None) -> None:
    """Tulis satu baris audit. Best-effort: kegagalan audit tidak boleh menggagalkan request."""
    try:
        db = get_db()
        await db.audit_logs.insert_one({
            "id": new_id("aud"),
            "actor_id": actor_id or "system",
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "meta": meta or {},
            "created_at": now_iso(),
        })
    except Exception:
        # Sengaja diam: audit adalah efek samping, bukan jalur kritis.
        pass
