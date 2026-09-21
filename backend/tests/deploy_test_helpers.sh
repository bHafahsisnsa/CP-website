#!/usr/bin/env bash
# Helper: extract deploy.sh header (baris 1..STEP 1-1), non-aktifkan cek EUID,
# tambahkan echo variabel untuk diperiksa. Panggilan: source dan lalu jalankan.
set -euo pipefail
DEPLOY="/app/deploy.sh"
OUT="${1:-/tmp/deploy_head.sh}"

STEP1_LINE="$(grep -n '^# STEP 1 ' "${DEPLOY}" | head -1 | cut -d: -f1)"
if [[ -z "${STEP1_LINE}" ]]; then echo "cannot find STEP 1 marker" >&2; exit 2; fi
END_LINE=$((STEP1_LINE - 1))

# Ambil header (baris 1..END_LINE) lalu nonaktifkan cek root: [[ 0 -ne 0 ]] selalu false
sed -n "1,${END_LINE}p" "${DEPLOY}" \
  | sed 's|\[\[ "${EUID}" -ne 0 \]\]|[[ 0 -ne 0 ]]|' \
  > "${OUT}"

cat >> "${OUT}" <<'PROBE'
echo "PROBE SERVER_IP=${SERVER_IP}"
echo "PROBE DOMAIN=${DOMAIN:-}"
echo "PROBE SETUP_SSL=${SETUP_SSL}"
echo "PROBE INCLUDE_WWW=${INCLUDE_WWW}"
echo "PROBE SERVER_NAMES=${SERVER_NAMES}"
echo "PROBE PUBLIC_URL=${PUBLIC_URL}"
echo "PROBE CORS_ORIGINS_VALUE=${CORS_ORIGINS_VALUE}"
echo "PROBE CERT_DOMAINS=${CERT_DOMAINS[*]-}"
PROBE
echo "${OUT}"
