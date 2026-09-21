#!/usr/bin/env python3
"""HTTP E2E — Import wizard endpoints (analyze -> validate -> commit -> verify -> export).

Menembak backend lokal (localhost:8001) memakai token admin. Membersihkan produk QA di akhir.
"""
import io
import sys
import requests

BASE = "http://localhost:8001/api"
ADMIN = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
SAMPLES = "/app/tests/import_samples"

PASS, FAIL = 0, 0


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  \033[92m✓\033[0m {name}")
    else:
        FAIL += 1
        print(f"  \033[91m✗\033[0m {name} — {detail}")


def login():
    r = requests.post(f"{BASE}/auth/login", json=ADMIN, timeout=30)
    r.raise_for_status()
    return r.json()["token"]


def run_file(h, fname, expect_products, mode="add-only"):
    print(f"\n[FILE] {fname}")
    with open(f"{SAMPLES}/{fname}", "rb") as f:
        data = f.read()
    mime = "text/csv" if fname.endswith(".csv") else \
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    # analyze
    r = requests.post(f"{BASE}/admin/products/io/analyze", headers=h,
                      files={"file": (fname, io.BytesIO(data), mime)}, timeout=60)
    ok(f"{fname}: analyze 200", r.status_code == 200, f"{r.status_code}:{r.text[:200]}")
    if r.status_code != 200:
        return
    a = r.json()
    rows, mapping = a["rows"], a["suggested_mapping"]
    ok(f"{fname}: ada rows", len(rows) > 0, f"n={len(rows)}")
    # validate
    r = requests.post(f"{BASE}/admin/products/io/validate", headers=h,
                      json={"rows": rows, "mapping": mapping}, timeout=60)
    ok(f"{fname}: validate 200", r.status_code == 200, r.text[:200])
    v = r.json()
    ok(f"{fname}: 0 baris error", v["summary"]["error"] == 0,
       str([rp["errors"] for rp in v["reports"] if rp["status"] == "error"]))
    ok(f"{fname}: produk={expect_products}", v["summary"]["products"] == expect_products,
       f'got={v["summary"]["products"]}')
    # commit
    r = requests.post(f"{BASE}/admin/products/io/commit", headers=h,
                      json={"rows": rows, "mapping": mapping, "mode": mode}, timeout=120)
    ok(f"{fname}: commit 200", r.status_code == 200, r.text[:200])
    c = r.json()
    ok(f"{fname}: created+updated>0", (c["created"] + c["updated"]) > 0, str(c))
    ok(f"{fname}: 0 failed", c["failed"] == 0, str(c.get("errors")))
    return c


def main():
    print("=" * 62)
    print("  HTTP E2E — Import Wizard (N-Dimensi)")
    print("=" * 62)
    token = login()
    h = {"Authorization": f"Bearer {token}"}

    run_file(h, "sample_2d.csv", 1)
    run_file(h, "sample_3d.csv", 1)
    run_file(h, "sample_4d.csv", 1)
    run_file(h, "sample_legacy.csv", 1)

    # Verify products exist with options/variants
    print("\n[VERIFY] produk QA di katalog admin")
    r = requests.get(f"{BASE}/admin/products?q=QA", headers=h, timeout=30)
    prods = r.json()
    qa = [p for p in prods if p.get("name", "").startswith("QA ")]
    ok(">=4 produk QA terbuat", len(qa) >= 4, f"n={len(qa)}: {[p['name'] for p in qa]}")
    # Check 3D product has 3 options
    oud = next((p for p in qa if p["name"] == "QA Oud Signature"), None)
    if oud:
        det = requests.get(f"{BASE}/admin/products/{oud['id']}", headers=h, timeout=30).json()
        ok("QA Oud Signature = 3 dimensi", len(det.get("options", [])) == 3,
           [o["name"] for o in det.get("options", [])])
        ok("QA Oud Signature = 4 varian", len(det.get("variants", [])) == 4,
           f'n={len(det.get("variants", []))}')
    amber = next((p for p in qa if p["name"] == "QA Amber Deluxe"), None)
    if amber:
        det = requests.get(f"{BASE}/admin/products/{amber['id']}", headers=h, timeout=30).json()
        ok("QA Amber Deluxe = 4 dimensi", len(det.get("options", [])) == 4,
           [o["name"] for o in det.get("options", [])])

    # Export roundtrip
    print("\n[EXPORT] unduh & cek header")
    r = requests.get(f"{BASE}/admin/products/io/export?format=csv", headers=h, timeout=60)
    ok("export 200", r.status_code == 200, str(r.status_code))
    header = r.text.splitlines()[0].lstrip("\ufeff")
    ok("export header punya option4_value", "option4_value" in header, header[:120])

    # Cleanup QA products (archive then hard-remove from DB not exposed; archive is fine)
    print("\n[CLEANUP] arsipkan produk QA")
    for p in qa:
        requests.delete(f"{BASE}/admin/products/{p['id']}", headers=h, timeout=30)
    print(f"  diarsipkan: {len(qa)} produk QA")

    print("\n" + "=" * 62)
    print(f"  HASIL: {PASS} PASS / {FAIL} FAIL")
    print("=" * 62)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
