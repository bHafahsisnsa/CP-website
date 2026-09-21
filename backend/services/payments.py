"""services/payments.py — bukti bayar (Epic E6). Owner submit, admin verify/reject.

SSOT uang = services.orders.record_payment (menaikkan paid_amount → turunkan payment_status;
maju ke `paid` via transition_order bila lunas). Verifikasi IDEMPOTEN per-bukti (INV-P1):
hanya bukti berstatus `pending` yang diproses (guard atomik). Terminal ditolak (INV-P2).
COD tak butuh bukti transfer.
"""
from core_utils import new_id, now_iso, safe_doc
from services import orders as orders_svc
from services.audit import log_action

LIST_MAX = 500


async def _owned_order(db, code, user):
    """Ambil order milik user (owner-or-404, IDOR-safe RC-E10). Guest order (user_id None) via code."""
    doc = await db.orders.find_one({"code": code})
    if not doc:
        return None, "notfound"
    uid = (user or {}).get("id")
    if doc.get("user_id") and doc.get("user_id") != uid:
        return None, "notfound"  # bukan pemilik → 404 (jangan bocorkan keberadaan)
    return doc, None


async def submit_proof(db, user, code, data):
    order, err = await _owned_order(db, code, user)
    if err or not order:
        return None, "notfound"
    if order.get("status") in orders_svc.TERMINAL:
        return None, "terminal"
    if (order.get("payment") or {}).get("group") == "cod":
        return None, "cod"
    proof = {
        "id": new_id("pay"),
        "order_code": code,
        "user_id": (user or {}).get("id"),
        "amount": int(data["amount"]),
        "ref": (data.get("ref") or None),
        "image_url": (data.get("image_url") or None),
        "status": "pending",
        "note": None,
        "verified_by": None,
        "created_at": now_iso(),
        "verified_at": None,
    }
    await db.payment_proofs.insert_one(proof)
    await log_action((user or {}).get("id", "guest"), "submit", "payment_proofs", proof["id"], {"order": code})
    return safe_doc(proof), None


async def list_proofs_for_order(db, code):
    docs = await db.payment_proofs.find({"order_code": code}).sort([("created_at", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def list_proofs(db, status=None):
    filt = {}
    if status in ("pending", "verified", "rejected"):
        filt["status"] = status
    docs = await db.payment_proofs.find(filt).sort([("created_at", -1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def verify_proof(db, admin_id, proof_id, approve, note=None):
    proof = await db.payment_proofs.find_one({"id": proof_id})
    if not proof:
        return None, "notfound"
    order = await db.orders.find_one({"code": proof["order_code"]})
    if not order:
        return None, "notfound"
    if order.get("status") in orders_svc.TERMINAL:
        return None, "terminal"  # INV-P2 / RC-E8
    # Idempoten: hanya bukti `pending` yang diproses (guard atomik anti double-count / INV-P1).
    new_status = "verified" if approve else "rejected"
    res = await db.payment_proofs.update_one(
        {"id": proof_id, "status": "pending"},
        {"$set": {"status": new_status, "verified_by": admin_id,
                  "verified_at": now_iso(), "note": (note or None)}},
    )
    if res.modified_count != 1:
        return None, "processed"
    await log_action(admin_id, ("verify" if approve else "reject"),
                     "payment_proofs", proof_id, {"order": proof["order_code"]})
    if approve:
        try:
            return await orders_svc.record_payment(db, order, proof["amount"], source="proof"), None
        except orders_svc.InvalidTransition:
            # order menjadi terminal di tengah jalan — kembalikan bukti ke pending.
            await db.payment_proofs.update_one(
                {"id": proof_id},
                {"$set": {"status": "pending", "verified_by": None, "verified_at": None}})
            return None, "terminal"
    return safe_doc(await db.orders.find_one({"code": proof["order_code"]})), None
