#!/usr/bin/env python3
"""fa_mutation.py — FORENSIC META-GATE: buktikan guardrail BENAR-BENAR bisa GAGAL.

Mutation testing untuk GATE (bukan kode aplikasi): suntik cacat yang DIKETAHUI, jalankan gate
yang seharusnya menangkap, pastikan gate exit!=0 (mendeteksi), lalu PULIHKAN. Bila gate tetap
hijau saat ada cacat → gate itu no-op (BAHAYA) → exit 1.

Mutan:
  MUT-1 voucher.value=0 di DB → verify_data_integrity.py HARUS FAIL (INV-9).
  MUT-2 file service pakai `db.items` (alias terlarang) → verify_contract.py HARUS FAIL (RC-1).
  MUT-3 field numerik tanpa bound di schemas → verify_numeric_bounds.py HARUS FAIL (INV-NUM-01).
Semua mutan dibersihkan di akhir (idempotent).
Usage: cd /app && python forensic/fa_mutation.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
from pymongo import MongoClient

G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
DB = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "collector_parfum")]
escaped = []


def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / script), *args],
                          capture_output=True, text=True, cwd=str(ROOT)).returncode


def check(mut_id, desc, gate_rc_when_mutated):
    if gate_rc_when_mutated != 0:
        print(f"  {G}[CAUGHT]{X} {mut_id}: {desc} → gate FAIL (baik).")
    else:
        escaped.append(f"{mut_id}: {desc} — gate TETAP HIJAU (no-op!).")
        print(f"  {R}[ESCAPED]{X} {mut_id}: {desc} → gate tidak menangkap!")


def main():
    print(f"\n{B}FA_MUTATION — meta-gate (guardrail harus bisa GAGAL){X}")

    # MUT-1: voucher.value=0
    DB.vouchers.insert_one({"id": "vcr_mut", "code": "MUTBAD", "type": "percent", "value": 0, "active": True})
    rc = run("scripts/verify_data_integrity.py")
    DB.vouchers.delete_one({"id": "vcr_mut"})
    check("MUT-1", "voucher.value=0 (INV-9)", rc)

    # MUT-2: alias terlarang db.items
    tmp = ROOT / "backend" / "services" / "_mut_drift.py"
    tmp.write_text("from db import get_db\nasync def x():\n    db=get_db()\n    return await db.items.find({}).to_list(10)\n")
    rc = run("scripts/verify_contract.py", "--all")
    tmp.unlink(missing_ok=True)
    check("MUT-2", "db.items alias (RC-1)", rc)

    # MUT-3: field numerik tanpa bound
    schemas = ROOT / "backend" / "schemas.py"
    orig = schemas.read_text()
    mutated = orig + "\n\nclass _MutBad(BaseModel):\n    model_config = _cfg\n    price_bad: int = 0\n"
    schemas.write_text(mutated)
    rc = run("scripts/guardrails/verify_numeric_bounds.py")
    schemas.write_text(orig)
    check("MUT-3", "field int tanpa ge=/gt= (INV-NUM-01)", rc)

    print(f"\n  {R}ESCAPED {len(escaped)}{X}")
    if escaped:
        print(f"  {R}{B}ADA GATE NO-OP — perkuat gate!{X}\n")
        return 1
    print(f"  {G}{B}Semua mutan tertangkap — guardrail terbukti efektif.{X}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as ex:
        # pastikan tak ada mutan tertinggal
        DB.vouchers.delete_one({"id": "vcr_mut"})
        (ROOT / "backend" / "services" / "_mut_drift.py").unlink(missing_ok=True)
        print(f"{Y}fa_mutation error: {ex}{X}")
        sys.exit(1)
