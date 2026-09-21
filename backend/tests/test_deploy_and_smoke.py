"""Static tests untuk /app/deploy.sh (logika DNS/CORS + render nginx) dan smoke backend/frontend.

Tidak menjalankan deploy.sh secara penuh — hanya head (sebelum STEP 1) dan fungsi write_nginx_conf.
"""
from __future__ import annotations
import os
import re
import subprocess
import textwrap
from pathlib import Path
import pytest
import requests

REPO = Path("/app")
DEPLOY = REPO / "deploy.sh"
HELPER = REPO / "backend/tests/deploy_test_helpers.sh"
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://parfum-vault-1.preview.emergentagent.com").rstrip("/")


# ─────────────────────── util ───────────────────────
def _run_head(env: dict[str, str]) -> subprocess.CompletedProcess:
    """Bangun deploy head, jalankan, kembalikan CompletedProcess."""
    head = "/tmp/deploy_head.sh"
    subprocess.run(["bash", str(HELPER), head], check=True, capture_output=True)
    full_env = {**os.environ, **env}
    return subprocess.run(["bash", head], env=full_env, capture_output=True, text=True, timeout=60)


def _probes(out: str) -> dict[str, str]:
    d = {}
    for line in out.splitlines():
        m = re.match(r"PROBE (\w+)=(.*)$", line)
        if m:
            d[m.group(1)] = m.group(2)
    return d


# ─────────────────────── SYNTAX ───────────────────────
class TestSyntax:
    def test_deploy_sh_syntax(self):
        r = subprocess.run(["bash", "-n", str(DEPLOY)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    def test_vps_diag_syntax(self):
        r = subprocess.run(["bash", "-n", str(REPO / "scripts/vps_diag.sh")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


# ─────────────────────── LOGIC (a..e) ───────────────────────
class TestDeployHeadLogic:
    def test_a_dns_belum_mengarah(self):
        """DOMAIN=collectorparfum.com -> exit 1 (DNS live 123.253.29.4 != default 148.230.102.29)."""
        r = _run_head({"DOMAIN": "collectorparfum.com"})
        assert r.returncode == 1, f"stdout={r.stdout}\nstderr={r.stderr}"
        assert "BELUM mengarah" in r.stdout or "BELUM mengarah" in r.stderr

    def test_b_domain_setup_ssl_no(self):
        r = _run_head({"DOMAIN": "collectorparfum.com", "SETUP_SSL": "no"})
        assert r.returncode == 0, r.stderr
        p = _probes(r.stdout)
        assert p["SERVER_NAMES"] == "collectorparfum.com 148.230.102.29"
        assert p["INCLUDE_WWW"] == "no"
        assert p["PUBLIC_URL"] == "http://collectorparfum.com"

    def test_c_no_domain(self):
        r = _run_head({"DOMAIN": ""})
        assert r.returncode == 0, r.stderr
        p = _probes(r.stdout)
        assert p["PUBLIC_URL"] == "http://148.230.102.29"
        assert p["SETUP_SSL"] == "no"
        assert p["SERVER_NAMES"] == "148.230.102.29"

    def test_d_dns_correct_https(self):
        """Simulasi DNS sudah menuju SERVER_IP (SERVER_IP=123.253.29.4)."""
        r = _run_head({"DOMAIN": "collectorparfum.com", "SERVER_IP": "123.253.29.4"})
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
        p = _probes(r.stdout)
        assert p["SETUP_SSL"] == "yes"
        # www.collectorparfum.com hanya cocok jika A record-nya juga = 123.253.29.4
        # (biasanya www CNAME/A ke IP yg sama). Uji fleksibel: minimal domain utama masuk.
        assert "collectorparfum.com" in p["CERT_DOMAINS"]
        assert p["PUBLIC_URL"] == "https://collectorparfum.com"
        assert p["CORS_ORIGINS_VALUE"].startswith("https://collectorparfum.com,http://collectorparfum.com")

    def test_d_www_included_when_dns_matches(self):
        """Cek eksplisit: bila www.collectorparfum.com resolve ke SERVER_IP, INCLUDE_WWW=yes."""
        www_ips = subprocess.run(
            ["getent", "ahostsv4", "www.collectorparfum.com"], capture_output=True, text=True
        ).stdout.split()
        # Ambil IP pertama saja
        www_ip = www_ips[0] if www_ips else ""
        if not www_ip:
            pytest.skip("www.collectorparfum.com tidak resolve di container ini")
        r = _run_head({"DOMAIN": "collectorparfum.com", "SERVER_IP": www_ip})
        assert r.returncode == 0, r.stderr
        p = _probes(r.stdout)
        assert p["INCLUDE_WWW"] == "yes"
        assert "www.collectorparfum.com" in p["CERT_DOMAINS"]

    def test_e_include_www_no(self):
        r = _run_head({
            "DOMAIN": "collectorparfum.com",
            "SERVER_IP": "123.253.29.4",
            "INCLUDE_WWW": "no",
        })
        assert r.returncode == 0, r.stderr
        p = _probes(r.stdout)
        assert p["INCLUDE_WWW"] == "no"
        assert "www.collectorparfum.com" not in p["CERT_DOMAINS"]
        # tidak ada warning "www... dilewati" karena INCLUDE_WWW bukan 'auto'
        assert "dilewati" not in r.stdout


# ─────────────────────── NGINX RENDER ───────────────────────
def _render_nginx(ssl: str) -> Path:
    """Ekstrak write_nginx_conf dari deploy.sh, stub nginx/systemctl, jalankan, kembalikan path conf."""
    src = DEPLOY.read_text()
    # ambil fungsi write_nginx_conf {...}
    # Greedy match sampai `}` terakhir sebelum baris `log "STEP 11`
    m = re.search(r"^write_nginx_conf\(\) \{\n(.*)^\}\n\nlog \"STEP 11", src, re.S | re.M)
    assert m, "write_nginx_conf tidak ditemukan"
    body = m.group(1)
    workdir = Path("/tmp/nginx_render")
    workdir.mkdir(exist_ok=True)
    conf_dir = workdir / "sites-available"; conf_dir.mkdir(exist_ok=True)
    enabled_dir = workdir / "sites-enabled"; enabled_dir.mkdir(exist_ok=True)
    stub = workdir / "run.sh"
    stub.write_text(f"""#!/usr/bin/env bash
set -euo pipefail
APP_NAME=collector-parfum
DOMAIN=collectorparfum.com
SERVER_NAMES='collectorparfum.com 148.230.102.29'
FRONTEND_DIR=/x
BACKEND_PORT=8003
ACME_ROOT=/tmp/acme-root
LE_LIVE=/tmp/le
mkdir -p "$ACME_ROOT" "$LE_LIVE"
# stubs
nginx() {{ echo "nginx $*"; }}
systemctl() {{ echo "systemctl $*"; }}
ln() {{ command ln "$@"; }}
# override sites paths by redirecting /etc/nginx to local dir via a wrapper is complex;
# jadi kita ganti path di dalam body:
write_nginx_conf() {{
{body}
}}
# patch: paksa path lokal
type write_nginx_conf | sed 's|/etc/nginx/sites-available/|{conf_dir}/|; s|/etc/nginx/sites-enabled/|{enabled_dir}/|' > /tmp/patched.sh
# Cara aman: definisikan ulang dengan sed di source
""")
    # Cara yang lebih mudah: patch teks body langsung
    patched_body = body.replace("/etc/nginx/sites-available/", f"{conf_dir}/") \
                       .replace("/etc/nginx/sites-enabled/", f"{enabled_dir}/")
    stub2 = workdir / f"render_{ssl}.sh"
    stub2.write_text(f"""#!/usr/bin/env bash
set -euo pipefail
APP_NAME=collector-parfum
DOMAIN=collectorparfum.com
SERVER_NAMES='collectorparfum.com 148.230.102.29'
FRONTEND_DIR=/x
BACKEND_PORT=8003
ACME_ROOT=/tmp/acme-root
LE_LIVE=/tmp/le
mkdir -p "$ACME_ROOT" "$LE_LIVE"
nginx() {{ echo "nginx $*"; }}
systemctl() {{ echo "systemctl $*"; }}
write_nginx_conf() {{
{patched_body}
}}
write_nginx_conf {ssl}
""")
    r = subprocess.run(["bash", str(stub2)], capture_output=True, text=True)
    assert r.returncode == 0, f"render gagal: {r.stderr}"
    conf = conf_dir / "collector-parfum"
    assert conf.exists()
    return conf


def _selfsign(dst: Path):
    key = dst / "privkey.pem"
    crt = dst / "fullchain.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(crt), "-days", "1",
         "-subj", "/CN=collectorparfum.com"],
        check=True, capture_output=True,
    )


class TestNginxRender:
    def test_render_no_ssl(self):
        conf = _render_nginx("no")
        txt = conf.read_text()
        assert "server_name collectorparfum.com 148.230.102.29;" in txt
        assert "location ^~ /.well-known/acme-challenge/" in txt
        assert "location ^~ /api" in txt
        assert "proxy_pass http://127.0.0.1:8003;" in txt
        # validasi via nginx -t dgn wrapper minimal
        wrapper = Path("/tmp/nginx_wrap_no.conf")
        wrapper.write_text(f"""events {{}}
http {{
  include {conf};
}}
""")
        r = subprocess.run(["nginx", "-t", "-c", str(wrapper)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    def test_render_ssl(self):
        # ganti LE_LIVE path menjadi /tmp/le dan buat self-signed
        _selfsign(Path("/tmp/le"))
        conf = _render_nginx("yes")
        txt = conf.read_text()
        assert "listen 80;" in txt
        assert "return 301 https://collectorparfum.com$request_uri;" in txt
        assert "location ^~ /.well-known/acme-challenge/" in txt
        assert "listen 443 ssl http2;" in txt
        assert "location ^~ /api" in txt
        assert "proxy_pass http://127.0.0.1:8003;" in txt

        wrapper = Path("/tmp/nginx_wrap_yes.conf")
        wrapper.write_text(f"""events {{}}
http {{
  include {conf};
}}
""")
        r = subprocess.run(["nginx", "-t", "-c", str(wrapper)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


# ─────────────────────── BACKEND SMOKE ───────────────────────
class TestBackend:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("status") == "ok"
        assert j.get("db") is True

    def test_login_admin(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@collectorparfum.id", "password": "Admin#2026"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        j = r.json()
        assert "token" in j and "user" in j
        assert j["user"]["email"] == "admin@collectorparfum.id"
