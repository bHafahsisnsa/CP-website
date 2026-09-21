#!/usr/bin/env bash
#
# ============================================================================
#  Collector Parfum — Skrip Deploy SEKALI JADI untuk VPS Ubuntu (22.04 / 24.04)
# ----------------------------------------------------------------------------
#  Dirancang agar BISA JALAN BERDAMPINGAN dengan aplikasi lain di SATU VPS
#  (mis. KBS8 di port 8001, Garment ERP di port 8002) TANPA konflik
#  port / service / database / nginx server block.
#
#  Stack : React (build statis) + FastAPI (uvicorn) + MongoDB lokal
#  Proses: Supervisor (backend) + Nginx (frontend & reverse proxy) + Certbot (opsional)
#
#  CARA PAKAI (di VPS, sebagai root):
#     wget -O deploy.sh https://raw.githubusercontent.com/pandekomangyogaswastika-dot/cpweb/main/deploy.sh
#     sudo bash deploy.sh
#
#  Tanpa domain -> otomatis dilayani lewat IP VPS (http://<IP>).
#  Sudah arahkan A record domain ke IP VPS? jalankan:
#     sudo DOMAIN=collectorparfum.com SETUP_SSL=yes bash deploy.sh
#  (skrip cek DNS dulu; www ikut otomatis bila DNS-nya sudah ke VPS; pilihan domain
#   diingat di /etc/collector-parfum.deploy.conf untuk `sudo bash deploy.sh` berikutnya)
#
#  Skrip ini IDEMPOTEN: aman dijalankan berulang untuk update (git pull + rebuild).
# ============================================================================

set -euo pipefail

# ── Ingat pilihan deploy sebelumnya (DOMAIN, SSL, www) ──────────────────────
# Setelah domain dipasang sekali, `sudo bash deploy.sh` berikutnya otomatis
# memakai domain yang sama (tidak "turun" lagi ke IP). Env var saat menjalankan
# selalu menang: mis. `sudo DOMAIN= bash deploy.sh` untuk kembali ke mode IP.
APP_NAME="${APP_NAME:-collector-parfum}"        # nama service/folder (unik per app)
DEPLOY_CONF="/etc/${APP_NAME}.deploy.conf"
if [[ -f "${DEPLOY_CONF}" ]]; then
  while IFS='=' read -r k v; do
    [[ -z "${k}" || "${k}" == \#* ]] && continue
    [[ -z "${!k+x}" ]] && export "${k}=${v}"
  done < "${DEPLOY_CONF}"
fi

# ============================================================================
#  KONFIGURASI (semua bisa dioverride lewat environment variable saat menjalankan)
# ============================================================================
APP_USER="${APP_USER:-collector}"               # user linux khusus aplikasi ini
DOMAIN="${DOMAIN:-}"                            # KOSONG = pakai IP VPS (belum ada domain)
SERVER_IP="${SERVER_IP:-148.230.102.29}"        # kosongkan = auto-deteksi IP publik
REPO_URL="${REPO_URL:-https://github.com/pandekomangyogaswastika-dot/cpweb.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"

BACKEND_PORT="${BACKEND_PORT:-8003}"            # 8001 KBS8, 8002 Garment ERP -> app ini 8003
DB_NAME="${DB_NAME:-collector_parfum}"          # database TERPISAH dari app lain
MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
UVICORN_WORKERS="${UVICORN_WORKERS:-2}"

# SSL / HTTPS — hanya relevan bila DOMAIN diisi
SETUP_SSL="${SETUP_SSL:-auto}"                  # auto | yes | no  (auto = yes bila DOMAIN ada)
SSL_EMAIL="${SSL_EMAIL:-cs@collectorparfum.com}"
# www.DOMAIN ikut dilayani + masuk sertifikat?
#   auto = ya HANYA bila DNS www.DOMAIN sudah mengarah ke SERVER_IP (aman bila www
#          masih dipakai hosting lain / belum diarahkan -> Certbot tidak gagal)
#   yes  = paksa ikut · no = hanya domain utama
INCLUDE_WWW="${INCLUDE_WWW:-auto}"

# Seed data awal (admin, kategori, voucher, konten storefront, 3 lokasi toko)
#   auto = seed HANYA bila database masih kosong (aman untuk update berikutnya)
#   yes  = paksa seed ulang (PERINGATAN: konten CMS dikembalikan ke default)
#   no   = jangan seed
SEED_DATA="${SEED_DATA:-auto}"

# Data persisten (media upload & file backup) — DI LUAR folder repo supaya tidak
# hilang saat update/rebuild.
DATA_ROOT="${DATA_ROOT:-/var/lib/${APP_NAME}}"

# Build frontend (naikkan bila VPS RAM kecil & build gagal "out of memory")
NODE_BUILD_MEMORY="${NODE_BUILD_MEMORY:-2048}"
SKIP_BUILD="${SKIP_BUILD:-no}"                  # yes = lewati yarn install+build (debug cepat)
# ============================================================================
#  AKHIR KONFIGURASI
# ============================================================================

APP_DIR="/home/${APP_USER}/${APP_NAME}"
BACKEND_DIR="${APP_DIR}/backend"
FRONTEND_DIR="${APP_DIR}/frontend"
VENV_DIR="${BACKEND_DIR}/venv"
SUPERVISOR_PROG="${APP_NAME}-backend"
MEDIA_DIR="${DATA_ROOT}/media"
BACKUP_DIR="${DATA_ROOT}/backups"
TOTAL_STEPS=13

# ── Warna log ───────────────────────────────────────────────────────────────
C_BLUE="\033[1;34m"; C_GREEN="\033[1;32m"; C_YELLOW="\033[1;33m"; C_RED="\033[1;31m"; C_OFF="\033[0m"
log()  { echo -e "${C_BLUE}==>${C_OFF} $1"; }
ok()   { echo -e "${C_GREEN}\u2713${C_OFF} $1"; }
warn() { echo -e "${C_YELLOW}!${C_OFF} $1"; }
err()  { echo -e "${C_RED}\u2717 $1${C_OFF}"; }

# ── Validasi awal ───────────────────────────────────────────────────────────
if [[ "${EUID}" -ne 0 ]]; then
  err "Skrip harus dijalankan sebagai root. Coba: sudo bash deploy.sh"
  exit 1
fi

if [[ -z "${SERVER_IP}" ]]; then
  SERVER_IP="$(curl -fsS --max-time 8 https://api.ipify.org 2>/dev/null || true)"
  [[ -z "${SERVER_IP}" ]] && SERVER_IP="$(hostname -I | awk '{print $1}')"
fi

# Resolusi DNS A record (pakai resolver publik agar tidak tertipu cache lokal / /etc/hosts)
resolve_a() { getent ahostsv4 "$1" 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ' '; }
dns_points_here() { [[ " $(resolve_a "$1") " == *" ${SERVER_IP} "* ]]; }

CERT_DOMAINS=()
if [[ -n "${DOMAIN}" ]]; then
  if ! dns_points_here "${DOMAIN}"; then
    warn "DNS ${DOMAIN} -> [$(resolve_a "${DOMAIN}")] BELUM mengarah ke ${SERVER_IP}."
    if [[ "${SETUP_SSL}" != "no" ]]; then
      err "Certbot pasti gagal sebelum A record '@' ${DOMAIN} = ${SERVER_IP} (propagasi 5-60 menit)."
      err "Cek dulu:  dig +short ${DOMAIN} @1.1.1.1     lalu jalankan ulang skrip ini."
      err "Atau paksa lanjut tanpa SSL: sudo DOMAIN=${DOMAIN} SETUP_SSL=no bash deploy.sh"
      exit 1
    fi
  fi
  CERT_DOMAINS+=("${DOMAIN}")
  SERVER_NAMES="${DOMAIN}"
  INCLUDE_WWW_REQUESTED="${INCLUDE_WWW}"
  if [[ "${INCLUDE_WWW}" == "auto" ]]; then
    if dns_points_here "www.${DOMAIN}"; then INCLUDE_WWW="yes"; else INCLUDE_WWW="no"; fi
  fi
  if [[ "${INCLUDE_WWW}" == "yes" ]]; then
    CERT_DOMAINS+=("www.${DOMAIN}")
    SERVER_NAMES="${SERVER_NAMES} www.${DOMAIN}"
  elif [[ "${INCLUDE_WWW_REQUESTED}" == "auto" ]]; then
    warn "www.${DOMAIN} dilewati (DNS www belum ke ${SERVER_IP}; pakai INCLUDE_WWW=yes untuk memaksa)"
  fi
  SERVER_NAMES="${SERVER_NAMES} ${SERVER_IP}"
  [[ "${SETUP_SSL}" == "auto" ]] && SETUP_SSL="yes"
  PUBLIC_HOST="${DOMAIN}"
else
  SERVER_NAMES="${SERVER_IP}"
  SETUP_SSL="no"
  INCLUDE_WWW="no"; INCLUDE_WWW_REQUESTED="auto"
  PUBLIC_HOST="${SERVER_IP}"
  warn "DOMAIN kosong -> aplikasi dilayani lewat IP VPS: http://${SERVER_IP}"
fi
PROTO="http"; [[ "${SETUP_SSL}" == "yes" ]] && PROTO="https"
PUBLIC_URL="${PROTO}://${PUBLIC_HOST}"
SSL_REQUESTED="${SETUP_SSL}"; [[ -z "${DOMAIN}" ]] && SSL_REQUESTED="auto"

# CORS: semua origin yang mungkin dipakai browser (domain https/http, www, IP)
CORS_LIST="${PUBLIC_URL}"
if [[ -n "${DOMAIN}" ]]; then
  [[ "${PROTO}" == "https" ]] && CORS_LIST="${CORS_LIST},http://${DOMAIN}"
  [[ "${INCLUDE_WWW}" == "yes" ]] && CORS_LIST="${CORS_LIST},${PROTO}://www.${DOMAIN},http://www.${DOMAIN}"
  CORS_LIST="${CORS_LIST},http://${SERVER_IP}"
fi
CORS_ORIGINS_VALUE="${CORS_ORIGINS:-${CORS_LIST}}"

echo ""
log "Deploy '${APP_NAME}' -> ${PUBLIC_URL}  (backend 127.0.0.1:${BACKEND_PORT}, DB ${DB_NAME})"
echo ""

# ============================================================================
# STEP 1 — Dependency dasar sistem
# ============================================================================
log "STEP 1/${TOTAL_STEPS} — apt update & dependency dasar"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y -qq
apt-get install -y -qq curl wget git build-essential ca-certificates gnupg lsb-release \
  python3 python3-venv python3-dev python3-pip \
  nginx supervisor ufw openssl
ok "Dependency dasar terpasang"

# ============================================================================
# STEP 2 — Node.js 20 + Yarn
# ============================================================================
log "STEP 2/${TOTAL_STEPS} — Node.js 20 + Yarn"
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -d. -f1 | tr -d v)" -lt 18 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -qq nodejs
fi
if ! command -v yarn >/dev/null 2>&1; then
  npm install -g yarn >/dev/null 2>&1
fi
ok "Node $(node -v) / Yarn $(yarn -v) siap"

# ============================================================================
# STEP 3 — MongoDB lokal (dipakai bersama app lain, database terpisah)
# ============================================================================
log "STEP 3/${TOTAL_STEPS} — MongoDB"
if command -v mongod >/dev/null 2>&1; then
  systemctl enable --now mongod >/dev/null 2>&1 || true
  ok "MongoDB sudah ada (database aplikasi ini: ${DB_NAME})"
else
  warn "MongoDB belum terpasang — memasang MongoDB Community"
  CODENAME="$(lsb_release -cs)"
  install_mongo() { # $1=versi mongo, $2=codename repo
    curl -fsSL "https://pgp.mongodb.com/server-$1.asc" \
      | gpg -o "/usr/share/keyrings/mongodb-server-$1.gpg" --dearmor --yes
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-$1.gpg ] https://repo.mongodb.org/apt/ubuntu $2/mongodb-org/$1 multiverse" \
      > "/etc/apt/sources.list.d/mongodb-org-$1.list"
    apt-get update -y -qq && apt-get install -y -qq mongodb-org
  }
  if ! install_mongo "8.0" "${CODENAME}"; then
    warn "Repo MongoDB 8.0/${CODENAME} gagal — mencoba 7.0/jammy"
    install_mongo "7.0" "jammy"
  fi
  systemctl enable --now mongod
  ok "MongoDB terpasang & berjalan"
fi

# ============================================================================
# STEP 4 — User aplikasi + kode (clone / update)
# ============================================================================
log "STEP 4/${TOTAL_STEPS} — User '${APP_USER}' & kode aplikasi"
if ! id "${APP_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${APP_USER}" >/dev/null
  ok "User ${APP_USER} dibuat"
fi
git config --global --add safe.directory "${APP_DIR}" 2>/dev/null || true

if [[ -d "${APP_DIR}/.git" ]]; then
  log "Repo sudah ada — mengambil versi terbaru (git fetch + reset --hard)"
  sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch --all --quiet
  sudo -u "${APP_USER}" git -C "${APP_DIR}" reset --hard "origin/${REPO_BRANCH}" --quiet
else
  log "Cloning ${REPO_URL} (${REPO_BRANCH})"
  sudo -u "${APP_USER}" git clone --quiet -b "${REPO_BRANCH}" "${REPO_URL}" "${APP_DIR}"
fi
ok "Kode aplikasi siap di ${APP_DIR} ($(sudo -u "${APP_USER}" git -C "${APP_DIR}" rev-parse --short HEAD))"

# ============================================================================
# STEP 5 — Folder data persisten (media upload & backup)
# ============================================================================
log "STEP 5/${TOTAL_STEPS} — Folder data persisten di ${DATA_ROOT}"
mkdir -p "${MEDIA_DIR}" "${BACKUP_DIR}"
# Pindahkan media bawaan repo (sekali saja) supaya gambar contoh tetap tampil.
if [[ -d "${BACKEND_DIR}/media" ]]; then
  cp -n "${BACKEND_DIR}/media/"* "${MEDIA_DIR}/" 2>/dev/null || true
fi
chown -R "${APP_USER}:${APP_USER}" "${DATA_ROOT}"
chmod -R 755 "${DATA_ROOT}"
ok "media: ${MEDIA_DIR} · backup: ${BACKUP_DIR} (tahan update/rebuild)"

# ============================================================================
# STEP 6 — Backend: virtualenv + dependency Python
# ============================================================================
log "STEP 6/${TOTAL_STEPS} — Setup backend (Python venv)"
[[ -d "${VENV_DIR}" ]] || sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --quiet --upgrade pip wheel setuptools
REQ_FILE="${BACKEND_DIR}/requirements-prod.txt"
[[ -f "${REQ_FILE}" ]] || REQ_FILE="${BACKEND_DIR}/requirements.txt"
log "Memasang dependency dari $(basename "${REQ_FILE}")"
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --quiet -r "${REQ_FILE}"
ok "Dependency Python terpasang"

# ============================================================================
# STEP 7 — backend/.env
# ============================================================================
log "STEP 7/${TOTAL_STEPS} — Tulis backend/.env"
cat > "${BACKEND_DIR}/.env" <<EOF
MONGO_URL=${MONGO_URL}
DB_NAME=${DB_NAME}
CORS_ORIGINS=${CORS_ORIGINS_VALUE}
MEDIA_ROOT=${MEDIA_DIR}
BACKUP_ROOT=${BACKUP_DIR}
EOF
chown "${APP_USER}:${APP_USER}" "${BACKEND_DIR}/.env"
chmod 600 "${BACKEND_DIR}/.env"
ok "backend/.env dibuat (DB ${DB_NAME}, CORS ${CORS_ORIGINS_VALUE})"

# ============================================================================
# STEP 8 — Frontend: .env + install + build produksi
# ============================================================================
log "STEP 8/${TOTAL_STEPS} — Build frontend React"
cat > "${FRONTEND_DIR}/.env" <<EOF
REACT_APP_BACKEND_URL=${PUBLIC_URL}
ENABLE_HEALTH_CHECK=false
GENERATE_SOURCEMAP=false
EOF
chown "${APP_USER}:${APP_USER}" "${FRONTEND_DIR}/.env"

if [[ "${SKIP_BUILD}" == "yes" ]]; then
  warn "SKIP_BUILD=yes -> build frontend dilewati"
else
  sudo -u "${APP_USER}" bash -lc "cd '${FRONTEND_DIR}' && (yarn install --frozen-lockfile --silent || yarn install --silent)"
  sudo -u "${APP_USER}" bash -lc "cd '${FRONTEND_DIR}' && NODE_OPTIONS=--max-old-space-size=${NODE_BUILD_MEMORY} yarn build"
  ok "Frontend ter-build di ${FRONTEND_DIR}/build"
fi

# Nginx (www-data) harus bisa membaca folder build di dalam /home
chmod 755 "/home/${APP_USER}"
chmod -R 755 "${FRONTEND_DIR}/build" 2>/dev/null || true

# ============================================================================
# STEP 9 — Supervisor: jalankan backend di port khusus app ini
# ============================================================================
log "STEP 9/${TOTAL_STEPS} — Supervisor (${SUPERVISOR_PROG} :${BACKEND_PORT})"
cat > "/etc/supervisor/conf.d/${SUPERVISOR_PROG}.conf" <<EOF
[program:${SUPERVISOR_PROG}]
command=${VENV_DIR}/bin/uvicorn server:app --host 127.0.0.1 --port ${BACKEND_PORT} --workers ${UVICORN_WORKERS}
directory=${BACKEND_DIR}
user=${APP_USER}
autostart=true
autorestart=true
startsecs=8
stopsignal=TERM
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/${SUPERVISOR_PROG}.err.log
stdout_logfile=/var/log/${SUPERVISOR_PROG}.out.log
environment=PATH="${VENV_DIR}/bin:%(ENV_PATH)s"
EOF
supervisorctl reread >/dev/null
supervisorctl update >/dev/null
supervisorctl restart "${SUPERVISOR_PROG}" >/dev/null 2>&1 || supervisorctl start "${SUPERVISOR_PROG}" >/dev/null
sleep 6
ok "Backend berjalan via Supervisor (127.0.0.1:${BACKEND_PORT})"

# ============================================================================
# STEP 10 — Seed data awal (admin, kategori, konten, lokasi toko)
# ============================================================================
log "STEP 10/${TOTAL_STEPS} — Seed data awal (mode: ${SEED_DATA})"
NEED_SEED=0
if [[ "${SEED_DATA}" == "yes" ]]; then
  NEED_SEED=1
elif [[ "${SEED_DATA}" == "auto" ]]; then
  PROD_COUNT="$("${VENV_DIR}/bin/python" - <<PY 2>/dev/null || echo -1
from pymongo import MongoClient
try:
    c = MongoClient("${MONGO_URL}", serverSelectionTimeoutMS=5000)
    print(c["${DB_NAME}"]["users"].count_documents({}))
except Exception:
    print(-1)
PY
)"
  [[ "${PROD_COUNT}" == "0" ]] && NEED_SEED=1
  [[ "${PROD_COUNT}" == "0" ]] || warn "Database sudah berisi (users=${PROD_COUNT}) -> seed dilewati (pakai SEED_DATA=yes untuk memaksa)"
fi
if [[ "${NEED_SEED}" == "1" ]]; then
  sudo -u "${APP_USER}" bash -lc "cd '${APP_DIR}' && '${VENV_DIR}/bin/python' scripts/seed_data.py" || warn "Seed gagal — cek log di atas"
  ok "Seed selesai (admin: admin@collectorparfum.id / Admin#2026)"
fi

# ============================================================================
# STEP 11 — Nginx: server block khusus app ini (tidak mengganggu app lain)
# ============================================================================
ACME_ROOT="/var/www/letsencrypt"
LE_LIVE="/etc/letsencrypt/live/${DOMAIN:-none}"
mkdir -p "${ACME_ROOT}"

# write_nginx_conf <ssl:yes|no>
write_nginx_conf() {
  local ssl="$1" conf="/etc/nginx/sites-available/${APP_NAME}"
  local app_block
  app_block="$(cat <<EOF
    # impor katalog (xlsx/csv) & restore backup butuh body besar
    client_max_body_size 64M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript image/svg+xml;
    gzip_min_length 1024;

    # Frontend React (build statis)
    root ${FRONTEND_DIR}/build;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API + media -> FastAPI (port khusus app ini)
    # PENTING: '^~' WAJIB agar blok regex aset statis di bawah TIDAK menangkap
    # URL media '/api/media/*.jpg|webp|png' (kalau tertangkap, gambar upload jadi
    # 404 "broken" karena dilayani dari folder build, bukan diproksi ke FastAPI).
    location ^~ /api {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;   # commit impor 6.000+ baris bisa lama
    }

    # Cache aset statis hasil build
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp|woff2?|mp4)\$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }
EOF
)"

  if [[ "${ssl}" == "yes" ]]; then
    cat > "${conf}" <<EOF
# ${APP_NAME} — dibuat otomatis oleh deploy.sh (HTTPS aktif). Jangan edit manual:
# jalankan ulang deploy.sh bila ingin mengubah.
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_NAMES};

    # Verifikasi Let's Encrypt (perpanjangan otomatis) tetap lewat HTTP
    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_ROOT};
        default_type "text/plain";
    }

    # Semua akses HTTP (termasuk lewat IP / www) -> HTTPS domain utama
    location / {
        return 301 https://${DOMAIN}\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${SERVER_NAMES};

    ssl_certificate     ${LE_LIVE}/fullchain.pem;
    ssl_certificate_key ${LE_LIVE}/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL_${APP_NAME//-/_}:10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    add_header Strict-Transport-Security "max-age=31536000" always;

${app_block}
}
EOF
  else
    cat > "${conf}" <<EOF
# ${APP_NAME} — dibuat otomatis oleh deploy.sh (HTTP). Jangan edit manual:
# jalankan ulang deploy.sh bila ingin mengubah.
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_NAMES};

    # Verifikasi Let's Encrypt (dipakai saat pasang SSL)
    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_ROOT};
        default_type "text/plain";
    }

${app_block}
}
EOF
  fi
  ln -sf "${conf}" "/etc/nginx/sites-enabled/${APP_NAME}"
  nginx -t
  systemctl reload nginx
}

log "STEP 11/${TOTAL_STEPS} — Nginx untuk ${SERVER_NAMES}"
# Bila sertifikat sudah ada dari deploy sebelumnya, langsung pakai konfigurasi HTTPS
# (supaya situs tidak sempat "turun" ke HTTP saat update).
if [[ "${SETUP_SSL}" == "yes" && -s "${LE_LIVE}/fullchain.pem" ]]; then
  write_nginx_conf yes
  ok "Nginx aktif (HTTPS, sertifikat sudah ada)"
else
  write_nginx_conf no
  ok "Nginx aktif (server block terpisah: ${APP_NAME})"
fi

# ============================================================================
# STEP 12 — SSL (hanya bila DOMAIN diisi)
# ============================================================================
if [[ "${SETUP_SSL}" == "yes" ]]; then
  log "STEP 12/${TOTAL_STEPS} — SSL Let's Encrypt untuk ${CERT_DOMAINS[*]}"
  command -v certbot >/dev/null 2>&1 || apt-get install -y -qq certbot
  CERT_ARGS=(); for d in "${CERT_DOMAINS[@]}"; do CERT_ARGS+=(-d "$d"); done
  if certbot certonly --webroot -w "${ACME_ROOT}" "${CERT_ARGS[@]}" \
       --cert-name "${DOMAIN}" --non-interactive --agree-tos -m "${SSL_EMAIL}" \
       --keep-until-expiring --expand --deploy-hook "systemctl reload nginx"; then
    write_nginx_conf yes
    systemctl enable --now certbot.timer >/dev/null 2>&1 || true
    ok "SSL terpasang — ${PUBLIC_URL} (perpanjangan otomatis oleh certbot.timer)"
  else
    err "Certbot GAGAL. Situs tetap jalan di http://${DOMAIN}. Penyebab umum:"
    err "  - DNS belum propagasi -> cek: dig +short ${DOMAIN} @1.1.1.1  (harus ${SERVER_IP})"
    err "  - Port 80 tertutup    -> ufw allow 80,443/tcp ; cek Firewall rule di panel VPS"
    err "  Ulangi:  sudo DOMAIN=${DOMAIN} SETUP_SSL=yes bash deploy.sh"
    SETUP_SSL="no"; PROTO="http"; PUBLIC_URL="http://${DOMAIN}"
  fi
else
  log "STEP 12/${TOTAL_STEPS} — SSL dilewati. Situs jalan di ${PUBLIC_URL}"
fi

# ============================================================================
# STEP 13 — Firewall + verifikasi kesehatan
# ============================================================================
log "STEP 13/${TOTAL_STEPS} — Firewall & verifikasi"
ufw allow OpenSSH >/dev/null 2>&1 || true
ufw allow 'Nginx Full' >/dev/null 2>&1 || true
if ! ufw status | grep -q "Status: active"; then yes | ufw enable >/dev/null 2>&1 || true; fi

HEALTH_LOCAL="$(curl -fsS --max-time 10 "http://127.0.0.1:${BACKEND_PORT}/api/health" 2>/dev/null || echo 'GAGAL')"
HEALTH_PUBLIC="$(curl -fsS --max-time 10 "http://127.0.0.1/api/health" -H "Host: ${PUBLIC_HOST}" 2>/dev/null || echo 'GAGAL')"
if [[ "${HEALTH_LOCAL}" == *'"status":"ok"'* ]]; then ok "Backend health OK: ${HEALTH_LOCAL}"; else err "Backend health GAGAL — cek: tail -n 50 /var/log/${SUPERVISOR_PROG}.err.log"; fi
if [[ "${HEALTH_PUBLIC}" == *'"status":"ok"'* ]]; then ok "Nginx -> API OK"; else warn "Akses lewat Nginx belum OK — cek: nginx -t && tail -n 50 /var/log/nginx/error.log"; fi
if [[ "${SETUP_SSL}" == "yes" ]]; then
  HEALTH_TLS="$(curl -fsS --max-time 10 "https://${DOMAIN}/api/health" 2>/dev/null || echo 'GAGAL')"
  if [[ "${HEALTH_TLS}" == *'"status":"ok"'* ]]; then ok "HTTPS OK: https://${DOMAIN}/api/health"; else warn "HTTPS belum bisa diakses dari VPS ini — cek: curl -vI https://${DOMAIN}"; fi
  certbot certificates --cert-name "${DOMAIN}" 2>/dev/null | grep -E "Domains|Expiry" | sed 's/^/    /' || true
fi

# Simpan pilihan agar `sudo bash deploy.sh` berikutnya memakai domain/SSL yang sama
cat > "${DEPLOY_CONF}" <<EOF
# Ditulis otomatis oleh deploy.sh — pilihan deploy terakhir ${APP_NAME}
DOMAIN=${DOMAIN}
SETUP_SSL=${SSL_REQUESTED}
INCLUDE_WWW=${INCLUDE_WWW_REQUESTED}
SSL_EMAIL=${SSL_EMAIL}
SERVER_IP=${SERVER_IP}
EOF

# ============================================================================
#  SELESAI
# ============================================================================
echo ""
echo -e "${C_GREEN}============================================================${C_OFF}"
echo -e "${C_GREEN} DEPLOY SELESAI \U1F389${C_OFF}"
echo -e "${C_GREEN}============================================================${C_OFF}"
echo -e " Storefront   : ${PUBLIC_URL}"
echo -e " Admin panel  : ${PUBLIC_URL}/admin"
echo -e " API health   : ${PUBLIC_URL}/api/health"
echo -e " Login admin  : admin@collectorparfum.id / Admin#2026"
echo -e "   ${C_YELLOW}>> SEGERA GANTI password admin setelah login pertama!${C_OFF}"
echo ""
echo -e " Port backend : 127.0.0.1:${BACKEND_PORT}   (tidak bentrok dengan app lain)"
echo -e " Database     : ${DB_NAME}"
echo -e " Data persist : ${MEDIA_DIR} (media) · ${BACKUP_DIR} (backup)"
echo -e " Service      : sudo supervisorctl status ${SUPERVISOR_PROG}"
echo -e " Log backend  : sudo tail -f /var/log/${SUPERVISOR_PROG}.err.log"
echo -e " Nginx conf   : /etc/nginx/sites-available/${APP_NAME}"
echo ""
echo -e " Update nanti : cd ${APP_DIR} && sudo bash deploy.sh   (idempoten, domain/SSL diingat)"
echo -e " Pasang domain: sudo DOMAIN=collectorparfum.com SETUP_SSL=yes bash deploy.sh"
echo -e " Pilihan aktif: ${DEPLOY_CONF}"
echo -e " Impor katalog: login admin -> Produk -> Impor / Ekspor -> unggah .xlsx"
echo -e "${C_GREEN}============================================================${C_OFF}"
