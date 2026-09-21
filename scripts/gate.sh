#!/usr/bin/env bash
###############################################################################
# gate.sh — ORKESTRATOR GATE TUNGGAL (Collector Parfum) — SUITE LENGKAP
# Menjalankan SEMUA gate (statik + runtime + forensik + meta-gate) lalu menulis
# memory/GATE_RECEIPT.md. "Selesai" hanya sah bila receipt HIJAU.
# Gate STATIK selalu jalan. Gate RUNTIME (butuh backend+auth) di-SKIP rapi bila
# backend belum siap (bukan gagal). Kelas ancaman: lihat docs/09_THREAT_MODEL.md.
# Usage: bash scripts/gate.sh
###############################################################################
set -uo pipefail
CYAN='\033[96m'; GREEN='\033[92m'; RED='\033[91m'; YEL='\033[93m'; BOLD='\033[1m'; RST='\033[0m'
cd "$(dirname "$0")/.." || exit 1
RECEIPT="memory/GATE_RECEIPT.md"
TS="$(date '+%Y-%m-%d %H:%M:%S')"
declare -a NAMES RESULTS
OVERALL=0

run_gate () {
  local label="$1"; shift
  echo -e "\n${CYAN}${BOLD}▶ ${label}${RST}"
  bash -c "$*"
  local rc=$?
  if [ $rc -eq 0 ]; then
    echo -e "  ${GREEN}✓ ${label} PASS${RST}"; NAMES+=("$label"); RESULTS+=("PASS")
  else
    echo -e "  ${RED}✗ ${label} FAIL (rc=$rc)${RST}"; NAMES+=("$label"); RESULTS+=("FAIL"); OVERALL=1
  fi
}
skip_gate () { echo -e "\n${YEL}▶ $1 — SKIP ($2)${RST}"; NAMES+=("$1"); RESULTS+=("SKIP"); }

echo -e "${CYAN}${BOLD}\n=============================================================="
echo "  GATE ORCHESTRATOR (Collector Parfum) — SUITE LENGKAP  —  $TS"
echo -e "==============================================================${RST}"

# --- Deteksi backend & kesiapan auth ---
BACKEND_UP=0; AUTH_READY=0
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/ 2>/dev/null | grep -qE "^[2-4]"; then
  BACKEND_UP=1; echo -e "${GREEN}  Backend RUNNING${RST}"
  AC=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" -d '{}' 2>/dev/null)
  if [ "$AC" != "404" ] && [ "$AC" != "000" ]; then AUTH_READY=1; echo -e "${GREEN}  Auth siap (HTTP $AC) — gate runtime dijalankan${RST}";
  else echo -e "${YEL}  Auth belum ada (HTTP $AC) — gate runtime di-SKIP.${RST}"; fi
else echo -e "${YEL}  Backend down — gate runtime di-SKIP.${RST}"; fi

# ============ STATIK / DATA (selalu) ============
run_gate "seed_reset (seed + contract + api_contract + integrity)" "bash scripts/seed_reset.sh"
run_gate "verify_schema (id-prefix + enum + FK)" "python scripts/verify_schema.py"
run_gate "guardrails/verify_numeric_bounds (RC-E12 negative-value)" "python scripts/guardrails/verify_numeric_bounds.py"
run_gate "guardrails/verify_rbac_guards (RC-E10 RBAC statik)" "python scripts/guardrails/verify_rbac_guards.py"
run_gate "guardrails/verify_auth_resilience (INV-AUTH-01 sesi tahan jaringan)" "python scripts/guardrails/verify_auth_resilience.py"
run_gate "guardrails/verify_stock_locks (RC-E3 oversell statik)" "python scripts/guardrails/verify_stock_locks.py"
run_gate "verify_cross_entity (RC-E9 lintas-koleksi)" "python scripts/verify_cross_entity.py"
run_gate "verify_architecture (performa/tech-debt)" "python scripts/verify_architecture.py"
run_gate "check_nav_map (RC-E13 dead-menu/orphan FE)" "python scripts/check_nav_map.py"
run_gate "ux_audit --strict (baseline UX)" "python scripts/ux_audit.py --strict"
run_gate "validate_compliance (file/naming/env/prefix)" "python scripts/validate_compliance.py"
run_gate "verify_delivery (anti under-deliver + orphan)" "python scripts/verify_delivery.py"
run_gate "verify_roadmap_docs (Epic blueprints E1..E8 structure)" "python scripts/verify_roadmap_docs.py"
run_gate "forensic:fa_static (analisis statik backend)" "python forensic/fa_static.py"
run_gate "forensic:fa_nplus1 (deteksi N+1)" "python forensic/fa_nplus1.py"
run_gate "forensic:fa_dark_sweep (endpoint gelap)" "python forensic/fa_dark_sweep.py"
run_gate "forensic:fa_mutation (META: guardrail harus bisa GAGAL)" "python forensic/fa_mutation.py"

# ============ RUNTIME (butuh backend + auth) ============
if [ $AUTH_READY -eq 1 ]; then
  run_gate "health_check (isi endpoint kritis)" "python scripts/health_check.py"
  run_gate "audit_endpoint_sweep (semua GET → 5xx)" "python scripts/audit_endpoint_sweep.py"
  run_gate "guardrails/verify_adversarial_5xx (RC-E11)" "python scripts/guardrails/verify_adversarial_5xx.py"
  run_gate "verify_state_machine (RC-E4/6/7/8)" "python scripts/verify_state_machine.py"
  run_gate "verify_concurrency (RC-E3 oversell runtime)" "python scripts/verify_concurrency.py"
  run_gate "mutation_smoke (write-path)" "python scripts/mutation_smoke.py"
  run_gate "product_io_core (E10 export/import: fuzz + integritas + konkurensi)" "python scripts/test_product_io_core.py"
  run_gate "forensic:fa_fuzz (payload rusak → no 5xx)" "python forensic/fa_fuzz.py"
  run_gate "forensic:fa_5xx (adversarial GET → no 5xx)" "python forensic/fa_5xx.py"
  run_gate "forensic:fa_session (RC-E15 token/sesi)" "python forensic/fa_session.py"
  run_gate "forensic:fa_idor (RBAC/authz)" "python forensic/fa_idor.py"
  run_gate "forensic:fa_idor_matrix (role×endpoint)" "python forensic/fa_idor_matrix.py"
  run_gate "forensic:fa_write_idor (write IDOR)" "python forensic/fa_write_idor.py"
  run_gate "forensic:fa_race (anti-oversell)" "python forensic/fa_race.py"
else
  for gname in health_check audit_endpoint_sweep verify_adversarial_5xx verify_state_machine \
               verify_concurrency mutation_smoke fa_fuzz fa_5xx fa_session fa_idor fa_idor_matrix \
               fa_write_idor fa_race; do
    skip_gate "$gname" "auth belum ada / backend down"
  done
fi

# ============ RECEIPT ============
{
  echo "# 🧾 GATE RECEIPT — Collector Parfum (suite lengkap)"
  echo ""
  echo "> Bukti verifikasi otomatis (\`scripts/gate.sh\`). JANGAN edit manual. Kelas ancaman: docs/09_THREAT_MODEL.md."
  echo ""
  echo "- **Waktu:** $TS"
  if [ $AUTH_READY -eq 1 ]; then echo "- **Backend:** RUNNING + auth siap (gate runtime dijalankan)"; elif [ $BACKEND_UP -eq 1 ]; then echo "- **Backend:** RUNNING, auth belum ada (runtime di-skip)"; else echo "- **Backend:** DOWN (runtime di-skip)"; fi
  echo ""
  echo "| Gate | Hasil |"
  echo "|------|-------|"
  for i in "${!NAMES[@]}"; do echo "| ${NAMES[$i]} | ${RESULTS[$i]} |"; done
  echo ""
  if [ $OVERALL -eq 0 ]; then echo "## ✅ VERDICT: HIJAU — semua gate (non-skip) PASS."; else echo "## ❌ VERDICT: MERAH — ADA GATE GAGAL. DILARANG klaim selesai."; fi
  echo ""
  echo "_Catatan: SKIP ≠ PASS. Gate runtime & state-machine/concurrency AKTIF PENUH saat endpoint business-logic ada._"
} > "$RECEIPT"

echo -e "\n${CYAN}${BOLD}==============================================================${RST}"
if [ $OVERALL -eq 0 ]; then echo -e "  ${GREEN}${BOLD}✓ SEMUA GATE (non-skip) HIJAU.${RST}  Receipt: $RECEIPT";
else echo -e "  ${RED}${BOLD}✗ ADA GATE MERAH.${RST}  Lihat detail di atas & $RECEIPT"; fi
echo -e "${CYAN}${BOLD}==============================================================${RST}\n"
exit $OVERALL
