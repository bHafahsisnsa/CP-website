#!/usr/bin/env python3
"""verify_contract.py — Collection Contract Verifier (Collector Parfum).

Memastikan kode (routers/services/seed) memakai nama koleksi MongoDB KANONIK
sesuai docs/03_DATA_MODEL.md — mencegah RC-1 (Collection Name Drift) SEBELUM runtime.
Mendeteksi dua bentuk: db.<name> DAN db["<name>"].

Usage:
  cd /app && python scripts/verify_contract.py --all
  python scripts/verify_contract.py --list-canonical
  python scripts/verify_contract.py --find products
Exit 0 = bersih. 1 = ada koleksi terlarang (drift).
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
SCAN_DIRS = [BACKEND / "routers", BACKEND / "services", ROOT / "scripts"]
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"

# Sinkron dengan docs/03_DATA_MODEL.md
CANONICAL_COLLECTIONS = {
    "users", "sessions", "products", "categories", "vouchers", "carts",
    "orders", "addresses", "shipping_methods", "payment_methods",
    "reviews", "wishlists", "counters", "settings", "audit_logs",
    "voucher_redemptions", "media_assets", "payment_proofs", "analytics_events", "content",
    "content_revisions", "import_sessions",
}

DANGEROUS_ALIASES = {
    "product": "products", "items": "products", "item": "products",
    "catalog": "products", "parfum": "products", "parfums": "products",
    "perfume": "products", "perfumes": "products", "skus": "products", "sku": "products",
    "category": "categories", "kategori": "categories",
    "voucher": "vouchers", "promo": "vouchers", "promos": "vouchers",
    "discount": "vouchers", "discounts": "vouchers", "coupon": "vouchers", "coupons": "vouchers",
    "cart": "carts", "basket": "carts", "baskets": "carts",
    "order": "orders", "pesanan": "orders", "transaction": "orders", "transactions": "orders", "checkout": "orders",
    "address": "addresses", "alamat": "addresses",
    "shipping": "shipping_methods", "courier": "shipping_methods", "couriers": "shipping_methods",
    "kurir": "shipping_methods", "ongkir": "shipping_methods", "shipment": "shipping_methods",
    "payment": "payment_methods", "payments": "payment_methods", "pembayaran": "payment_methods",
    "review": "reviews", "testimonial": "reviews", "testimonials": "reviews", "ulasan": "reviews",
    "wishlist": "wishlists", "favorite": "wishlists", "favorites": "wishlists", "favorit": "wishlists",
    "session": "sessions",
    "user": "users", "customer": "users", "customers": "users", "pelanggan": "users", "staff": "users",
    "config": "settings", "setting": "settings", "configuration": "settings",
    "counter": "counters", "sequence": "counters", "sequences": "counters",
    "audit": "audit_logs", "audit_log": "audit_logs", "logs": "audit_logs",
}

NON_COLLECTION = {"get_db", "command", "ping", "list_collection_names", "client",
                  "name", "drop", "create_collection", "with_options", "list_collections"}


def extract_collections(filepath):
    pattern = re.compile(r'''db(?:\.([a-z][a-z0-9_]*)|\[\s*['\"]([a-z][a-z0-9_]*)['\"]\s*\])''')
    cols = {}
    try:
        for i, line in enumerate(filepath.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for m in pattern.finditer(line):
                col = m.group(1) or m.group(2)
                if col and col not in NON_COLLECTION:
                    cols.setdefault(col, []).append(i)
    except Exception as e:
        print(f"  ERROR membaca {filepath}: {e}")
    return cols


def classify(col):
    if col in CANONICAL_COLLECTIONS:
        return "KANONIK"
    if col in DANGEROUS_ALIASES:
        return "TERLARANG"
    return "TIDAK_DIKENAL"


def scan_all():
    print(f"\n{C}{B}{'='*64}{X}\n{B}  CONTRACT SCAN: routers + services + scripts{X}\n{C}{B}{'='*64}{X}")
    files = []
    for d in SCAN_DIRS:
        if d.exists():
            files += list(d.rglob("*.py"))
    dangerous, unknown = [], []
    for f in sorted(files):
        if "__pycache__" in str(f):
            continue
        for col, lines in extract_collections(f).items():
            k = classify(col)
            if k == "TERLARANG":
                dangerous.append((f.name, col, DANGEROUS_ALIASES[col], lines[:3]))
            elif k == "TIDAK_DIKENAL" and not col.startswith("_") and len(col) > 3:
                unknown.append((f.name, col, lines[:3]))
    if dangerous:
        print(f"\n{R}{B}[DRIFT] Koleksi TERLARANG (RC-1):{X}")
        for fn, col, correct, lines in dangerous:
            print(f"  {R}{fn}: '{col}' → seharusnya '{correct}' (baris {lines}){X}")
    else:
        print(f"\n{G}[OK] Tidak ada koleksi terlarang.{X}")
    if unknown:
        print(f"\n{Y}[INFO] Koleksi tidak dikenal (daftarkan di 03_DATA_MODEL bila domain baru):{X}")
        for fn, col, lines in unknown[:40]:
            print(f"  {Y}{fn}: '{col}' (baris {lines}){X}")
    print(f"\n{B}{'='*64}{X}")
    if dangerous:
        print(f"  {R}{B}CONTRACT VIOLATION — perbaiki nama koleksi.{X}\n")
        return 1
    print(f"  {G}{B}CONTRACT OK.{X}\n")
    return 0


def find_collection(name):
    pat = re.compile(rf'''db(?:\.{re.escape(name)}\b|\[\s*['\"]{re.escape(name)}['\"]\s*\])''')
    found = []
    if BACKEND.exists():
        for py in sorted(BACKEND.rglob("*.py")):
            if "__pycache__" in str(py):
                continue
            for i, line in enumerate(py.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if pat.search(line):
                    found.append((str(py.relative_to(ROOT)), i, line.strip()[:100]))
    for fp, ln, txt in found:
        print(f"  {fp}:{ln}  {txt}")
    if not found:
        print("  (tidak ditemukan)")
    if name in DANGEROUS_ALIASES:
        print(f"  {R}PERINGATAN: '{name}' TERLARANG! Gunakan '{DANGEROUS_ALIASES[name]}'.{X}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--find")
    ap.add_argument("--list-canonical", action="store_true")
    args = ap.parse_args()
    if args.list_canonical:
        print("\nKoleksi Kanonik:")
        for c in sorted(CANONICAL_COLLECTIONS):
            print(f"  - {c}")
        return 0
    if args.find:
        return find_collection(args.find)
    return scan_all()


if __name__ == "__main__":
    sys.exit(main())
