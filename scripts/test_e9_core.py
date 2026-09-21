#!/usr/bin/env python3
"""test_e9_core.py — POC CORE E9 (Storefront CMS). PROVE-BEFORE-BUILD.

  T1 GET /api/content publik -> merge default+DB, semua section lengkap.
  T2 GET /api/admin/content/schema -> list section (>=18) dgn fields terdefinisi.
  T3 PUT /api/admin/content/{key} sebagai admin -> data ter-update, publik ikut berubah.
  T4 PUT /api/admin/content/{key} tanpa admin -> 401/403 (RBAC RC-E10).
  T5 PUT section tak dikenal -> 404.
  T6 INV-C1: setiap key section punya dokumen (via GET admin).
  T7 INV-C2: field diluar skema di-drop (anti-injection).

Self-cleaning (kembalikan section ke default). Usage: cd /app && python scripts/test_e9_core.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
try:
    import httpx
except ImportError:
    os.system("pip install httpx -q")
    import httpx

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
ADMIN = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
CUSTOMER = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}
G, R, Y, B, X = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"
passed = failed = 0


def ok(msg):
    global passed
    passed += 1
    print(f"  {G}[OK]{X} {msg}")


def bad(msg):
    global failed
    failed += 1
    print(f"  {R}[FAIL]{X} {msg}")


def login(c, cred):
    r = c.post(f"{API}/api/auth/login", json=cred)
    r.raise_for_status()
    return r.json()["token"]


def main():
    print(f"\n{B}{'='*60}{X}\n  TEST E9 CORE — Storefront CMS\n{B}{'='*60}{X}")
    with httpx.Client(timeout=10.0) as c:
        # T1 — publik content
        r = c.get(f"{API}/api/content")
        if r.status_code == 200 and isinstance(r.json(), dict) and len(r.json()) >= 10:
            ok(f"T1 GET /api/content -> 200 ({len(r.json())} section)")
        else:
            bad(f"T1 publik content gagal: {r.status_code}")
            return

        # Login admin
        try:
            adm_tok = login(c, ADMIN)
            ok("login admin sukses")
        except Exception as e:
            bad(f"login admin gagal: {e}")
            return
        H = {"Authorization": f"Bearer {adm_tok}"}

        # T2 — schema
        r = c.get(f"{API}/api/admin/content/schema", headers=H)
        schema = r.json() if r.status_code == 200 else []
        if r.status_code == 200 and isinstance(schema, list) and len(schema) >= 18:
            ok(f"T2 schema -> {len(schema)} section")
        else:
            bad(f"T2 schema gagal: {r.status_code} len={len(schema) if isinstance(schema, list) else 'n/a'}")

        # T3 — update announcement
        original = c.get(f"{API}/api/content").json().get("announcement", {})
        new_items = ["TEST E9 T3 — banner update", "Kedua"]
        r = c.put(f"{API}/api/admin/content/announcement",
                  headers=H, json={"data": {"items": new_items}})
        if r.status_code == 200:
            pub = c.get(f"{API}/api/content").json().get("announcement", {})
            if pub.get("items") == new_items:
                ok("T3 update announcement -> publik ikut update")
            else:
                bad(f"T3 publik tidak ikut update: {pub}")
        else:
            bad(f"T3 PUT gagal: {r.status_code} {r.text[:120]}")

        # T5 — section tak dikenal (sebelum kembalikan defaults, tak berdampak)
        r = c.put(f"{API}/api/admin/content/section_tidak_ada",
                  headers=H, json={"data": {"x": 1}})
        if r.status_code == 404:
            ok("T5 section tak dikenal -> 404")
        else:
            bad(f"T5 harusnya 404, dapat {r.status_code}")

        # T7 — INV-C2 injection field bukan skema
        r = c.put(f"{API}/api/admin/content/announcement",
                  headers=H, json={"data": {"items": new_items, "__evil__": "x"}})
        if r.status_code == 200 and "__evil__" not in r.json().get("data", {}):
            ok("T7 INV-C2 field liar di-drop (anti-injection)")
        else:
            bad(f"T7 field liar bocor: {r.json() if r.status_code==200 else r.status_code}")

        # T6 — INV-C1: setiap key di schema muncul di admin content
        r_admin = c.get(f"{API}/api/admin/content", headers=H)
        admin_data = r_admin.json() if r_admin.status_code == 200 else {}
        missing = [s["key"] for s in schema if s["key"] not in admin_data]
        if not missing:
            ok(f"T6 INV-C1: semua {len(schema)} section punya dokumen")
        else:
            bad(f"T6 section tanpa dokumen: {missing}")

        # T8 — Revision history: PUT tercatat sbg revisi
        c.put(f"{API}/api/admin/content/announcement",
              headers=H, json={"data": {"items": ["Rev-A"]}})
        c.put(f"{API}/api/admin/content/announcement",
              headers=H, json={"data": {"items": ["Rev-B"]}})
        r = c.get(f"{API}/api/admin/content/announcement/revisions", headers=H)
        revs = r.json().get("revisions", []) if r.status_code == 200 else []
        if len(revs) >= 2:
            ok(f"T8 revisions: {len(revs)} tersimpan")
        else:
            bad(f"T8 revisions kurang: {len(revs)}")

        # T9 — Revert ke revision_id
        if revs:
            rid = revs[-1]["id"]
            r = c.post(f"{API}/api/admin/content/announcement/revert",
                       headers=H, json={"revision_id": rid})
            if r.status_code == 200 and r.json().get("mode") == "revision":
                ok("T9 revert ke revision_id sukses")
            else:
                bad(f"T9 revert gagal: {r.status_code}")

        # T10 — Revert ke default pabrik
        r = c.post(f"{API}/api/admin/content/announcement/revert",
                   headers=H, json={"to_default": True})
        if r.status_code == 200 and r.json().get("mode") == "default":
            ok("T10 revert to_default sukses")
        else:
            bad(f"T10 revert default gagal: {r.status_code}")

        # T11 — Media upload (admin only)
        # PNG 1x1 valid
        png_bytes = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000d49444154789c626000000000050001a5f645400000000049454e44ae426082"
        )
        files = {"file": ("test.png", png_bytes, "image/png")}
        r = c.post(f"{API}/api/admin/uploads", headers=H, files=files)
        if r.status_code == 200 and r.json().get("url", "").startswith("/api/media/"):
            ok(f"T11 upload PNG -> {r.json()['url']}")
            # verify file dapat diakses
            url = r.json()["url"]
            rf = c.get(f"{API}{url}")
            if rf.status_code == 200 and len(rf.content) > 0:
                ok("T11b file terlayani via /api/media/")
            else:
                bad(f"T11b GET file gagal: {rf.status_code}")
        else:
            bad(f"T11 upload gagal: {r.status_code} {r.text[:120]}")

        # T12 — Upload MIME tidak diizinkan
        r = c.post(f"{API}/api/admin/uploads", headers=H,
                   files={"file": ("evil.exe", b"MZ", "application/octet-stream")})
        if r.status_code == 400:
            ok("T12 MIME terlarang -> 400")
        else:
            bad(f"T12 harusnya 400, dapat {r.status_code}")

        # T13 — Upload tanpa token -> 401/403
        r = c.post(f"{API}/api/admin/uploads",
                   files={"file": ("test.png", png_bytes, "image/png")})
        if r.status_code in (401, 403):
            ok(f"T13 upload tanpa token -> {r.status_code}")
        else:
            bad(f"T13 harusnya 401/403, dapat {r.status_code}")

        # T4 — RBAC: tanpa token
        r = c.put(f"{API}/api/admin/content/announcement",
                  json={"data": {"items": ["x"]}})
        if r.status_code in (401, 403):
            ok(f"T4 tanpa token -> {r.status_code}")
        else:
            bad(f"T4 harusnya 401/403, dapat {r.status_code}")

        # T4b — RBAC: customer token
        try:
            cust_tok = login(c, CUSTOMER)
            r = c.put(f"{API}/api/admin/content/announcement",
                      headers={"Authorization": f"Bearer {cust_tok}"},
                      json={"data": {"items": ["x"]}})
            if r.status_code in (401, 403):
                ok(f"T4 customer -> {r.status_code}")
            else:
                bad(f"T4 customer harusnya 401/403, dapat {r.status_code}")
        except Exception as e:
            print(f"  {Y}[skip]{X} T4b (login customer gagal): {e}")

        # cleanup — kembalikan announcement ke original
        if original:
            c.put(f"{API}/api/admin/content/announcement",
                  headers=H, json={"data": original})

    print(f"\n{B}{'='*60}{X}\n  passed={passed}  failed={failed}\n{B}{'='*60}{X}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
