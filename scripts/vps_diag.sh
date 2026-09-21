#!/usr/bin/env bash
# Ringkasan kondisi VPS untuk diagnosa deploy Collector Parfum (aman: hanya membaca).
# Pakai: bash scripts/vps_diag.sh   (salin seluruh output bila minta bantuan)
APP_NAME="${APP_NAME:-collector-parfum}"
DOMAIN="${DOMAIN:-collectorparfum.com}"
PORT="${BACKEND_PORT:-8003}"
h() { echo; echo "===== $1 ====="; }

h "IP publik & OS"; curl -fsS --max-time 5 https://api.ipify.org; echo; lsb_release -ds 2>/dev/null; nginx -v 2>&1
h "DNS ${DOMAIN} (resolver publik)"
for n in "${DOMAIN}" "www.${DOMAIN}"; do printf '%-28s -> %s\n' "$n" "$(dig +short "$n" @1.1.1.1 2>/dev/null | tr '\n' ' ')"; done
h "Pilihan deploy tersimpan"; cat "/etc/${APP_NAME}.deploy.conf" 2>/dev/null || echo "(belum ada)"
h "Service backend"; supervisorctl status "${APP_NAME}-backend" 2>/dev/null || echo "(supervisor tidak ada)"
h "Health"; echo "local : $(curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/api/health" || echo GAGAL)"
echo "nginx : $(curl -fsS --max-time 5 "http://127.0.0.1/api/health" -H "Host: ${DOMAIN}" || echo GAGAL)"
echo "https : $(curl -fsS --max-time 8 "https://${DOMAIN}/api/health" 2>/dev/null || echo GAGAL/belum)"
h "Port listen (80/443/${PORT})"; ss -ltnp 2>/dev/null | grep -E ':(80|443|'"${PORT}"')\b' || echo "(tidak ada)"
h "Firewall UFW"; ufw status 2>/dev/null | head -15
h "Nginx server_name aktif"; grep -Hn "server_name\|listen" /etc/nginx/sites-enabled/* 2>/dev/null
h "nginx -t"; nginx -t 2>&1
h "Sertifikat"; certbot certificates 2>/dev/null || echo "(certbot belum terpasang)"
systemctl is-active certbot.timer 2>/dev/null | sed 's/^/certbot.timer: /'
h "Log backend (15 baris terakhir)"; tail -n 15 "/var/log/${APP_NAME}-backend.err.log" 2>/dev/null
h "Log nginx error (10 baris)"; tail -n 10 /var/log/nginx/error.log 2>/dev/null
h "Env aplikasi"; sed 's/\(MONGO_URL=\).*/\1***/' "/home/collector/${APP_NAME}/backend/.env" 2>/dev/null; cat "/home/collector/${APP_NAME}/frontend/.env" 2>/dev/null
h "Git"; git -C "/home/collector/${APP_NAME}" log -1 --pretty='%h %ad %s' --date=short 2>/dev/null
