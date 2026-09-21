"""services/backup_config.py — konstanta Backup & Restore (dipisah agar file tetap ramping).

Berisi: lokasi penyimpanan file backup, format/versi, koleksi terlarang, label ramah
Bahasa Indonesia, dan KUNCI NATURAL per koleksi (dipakai mode restore 'combine' untuk
upsert). TIDAK ada logika I/O di sini.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # /app/backend
BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT", str(ROOT / "backups")))
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

DB_NAME = os.environ.get("DB_NAME", "collector_parfum")

FORMAT = "collector-parfum-backup"
VERSION = 1

# Koleksi yang TIDAK BOLEH ikut backup/restore (keamanan / meta internal).
EXCLUDED = {"sessions", "backups"}

# Label ramah (Bahasa Indonesia) untuk koleksi yang dikenal.
COLLECTION_LABELS = {
    "users": "Pengguna",
    "products": "Produk",
    "categories": "Kategori",
    "occasions": "Occasion",
    "characters": "Karakter",
    "vouchers": "Voucher",
    "voucher_redemptions": "Redemption Voucher",
    "voucher_user_usage": "Pemakaian Voucher/User",
    "orders": "Pesanan",
    "addresses": "Alamat",
    "wishlists": "Wishlist",
    "carts": "Keranjang",
    "reviews": "Ulasan Produk",
    "content": "Konten Situs",
    "store_locations": "Lokasi Toko",
    "store_reviews": "Ulasan Toko",
    "settings": "Pengaturan",
    "shipping_methods": "Metode Kirim",
    "payment_methods": "Metode Bayar",
    "payment_proofs": "Bukti Bayar",
    "analytics_events": "Event Analitik",
    "audit_logs": "Log Audit",
    "media_assets": "Aset Media",
    "counters": "Counter Nomor",
}

# Kunci natural per koleksi (untuk upsert mode 'combine').
KEY_FIELDS = {
    "users": ["id"],
    "products": ["id"],
    "categories": ["slug"],
    "occasions": ["slug"],
    "characters": ["slug"],
    "vouchers": ["code"],
    "voucher_redemptions": ["id"],
    "voucher_user_usage": ["voucher_code", "user_id"],
    "orders": ["code"],
    "addresses": ["id"],
    "wishlists": ["user_id"],
    "carts": ["user_id"],
    "reviews": ["id"],
    "content": ["id"],
    "store_locations": ["id"],
    "store_reviews": ["id"],
    "settings": ["id"],
    "shipping_methods": ["id"],
    "payment_methods": ["id"],
    "payment_proofs": ["id"],
    "analytics_events": ["id"],
    "audit_logs": ["id"],
    "media_assets": ["id"],
    "counters": ["name"],
}

__all__ = ["BACKUP_ROOT", "DB_NAME", "FORMAT", "VERSION", "EXCLUDED",
           "COLLECTION_LABELS", "KEY_FIELDS"]
