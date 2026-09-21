#!/usr/bin/env bash
# run_forensics.sh — jalankan SELURUH probe forensik (audit adversarial + meta-gate).
# Butuh backend RUNNING + seed. Usage: bash scripts/run_forensics.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
run(){ echo; echo "########## $1 ##########"; python "forensic/$1" ${3:-} 2>&1 | tail -"${2:-25}"; }
reseed(){ python scripts/seed_data.py >/dev/null 2>&1; }

reseed
run fa_static.py 20
run fa_nplus1.py 15
run fa_dark_sweep.py 15
run fa_mutation.py 15
run fa_5xx.py 20
run fa_fuzz.py 20
run fa_session.py 15
run fa_idor.py 20
run fa_idor_matrix.py 15
run fa_write_idor.py 10
run fa_race.py 15
reseed
echo; echo "########## GATE INTEGRITY (post) ##########"
python scripts/verify_data_integrity.py 2>&1 | grep -E "PASS [0-9]+|FAIL [0-9]+|INTEGRITY" | tail -2
