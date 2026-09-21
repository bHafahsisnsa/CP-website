#!/usr/bin/env bash
###############################################################################
# load_context.sh — snapshot kondisi proyek (awal sesi)
# Menampilkan: status service, env keys, jumlah dok per koleksi, ukuran file besar.
###############################################################################
set -uo pipefail
CYAN='\033[96m'; BOLD='\033[1m'; RST='\033[0m'
cd "$(dirname "$0")/.." || exit 1
echo -e "${CYAN}${BOLD}== SERVICES ==${RST}"
sudo supervisorctl status 2>/dev/null || true
echo -e "\n${CYAN}${BOLD}== ENV KEYS (values disembunyikan) ==${RST}"
grep -o '^[A-Z_]*=' backend/.env 2>/dev/null
grep -o '^[A-Z_]*=' frontend/.env 2>/dev/null
echo -e "\n${CYAN}${BOLD}== KOLEKSI (jumlah dok) ==${RST}"
python - <<'PY' 2>/dev/null || true
import os, asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('backend/.env'))
from motor.motor_asyncio import AsyncIOMotorClient
async def main():
    c=AsyncIOMotorClient(os.environ['MONGO_URL']); db=c[os.environ.get('DB_NAME','collector_parfum')]
    for name in sorted(await db.list_collection_names()):
        print(f"  {name}: {await db[name].count_documents({})}")
    c.close()
asyncio.run(main())
PY
echo -e "\n${CYAN}${BOLD}== FILE TERBESAR (backend) ==${RST}"
find backend -name '*.py' -not -path '*/__pycache__/*' | xargs wc -l 2>/dev/null | sort -rn | head -8
echo -e "\n${CYAN}${BOLD}== GATE RECEIPT (bila ada) ==${RST}"
[ -f memory/GATE_RECEIPT.md ] && grep -E 'VERDICT|Waktu' memory/GATE_RECEIPT.md || echo '  (belum ada receipt — jalankan bash scripts/gate.sh)'
