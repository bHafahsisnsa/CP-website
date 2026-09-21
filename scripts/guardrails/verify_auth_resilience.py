#!/usr/bin/env python3
"""INV-AUTH-01 — Sesi TIDAK boleh dihapus karena gangguan jaringan. (STATIK, jalan sekarang)

Kelas bug dicegah (BUG-AUTH-01, ditemukan 2026-08-03): `AuthContext` memanggil `apiLogout()`
pada SETIAP kegagalan `GET /api/auth/me`. Akibatnya satu blip jaringan / timeout / 502 saat
ingress-pod restart MENGHAPUS token dari localStorage sehingga user (termasuk admin yang sedang
mengerjakan wizard impor 6.426 baris) dipaksa login ulang dan kehilangan konteks kerja.

Invariant yang ditegakkan:
  A1. Setiap `apiLogout()` di store/AuthContext.js harus BERPAGAR pemeriksaan status penolakan
      definitif (401/403) — kecuali di dalam aksi `logout` eksplisit milik user.
  A2. AuthContext harus punya mekanisme percobaan ulang (backoff) untuk kegagalan transient.
  A3. AuthContext harus mengekspor `sessionError` + `retrySession` (UI bisa membedakan
      "server tak terjangkau" dari "sesi kedaluwarsa").
  A4. Permukaan ber-gate auth (AdminLayout, AccountPage) harus MENAMPILKAN status pemulihan
      (data-testid admin-session-offline / account-session-offline) alih-alih langsung
      melempar user ke form login.

Usage: cd /app && python scripts/guardrails/verify_auth_resilience.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import FRONTEND, Guard  # noqa: E402

SRC = FRONTEND / "src"
AUTH_CTX = SRC / "store" / "AuthContext.js"
ADMIN_LAYOUT = SRC / "components" / "admin" / "AdminLayout.js"
ACCOUNT_PAGE = SRC / "pages" / "AccountPage.js"

STATUS_GUARD = re.compile(r"isAuthReject|response\?\.status|response\.status")
EXPLICIT_LOGOUT = re.compile(r"const\s+logout\s*=")


def check_auth_context(g: Guard) -> None:
    if not AUTH_CTX.exists():
        g.add("frontend/src/store/AuthContext.js tidak ada.")
        return
    lines = AUTH_CTX.read_text(encoding="utf-8", errors="ignore").splitlines()
    text = "\n".join(lines)

    # A1 — setiap apiLogout() harus berpagar status 401/403 (atau di aksi logout eksplisit).
    for i, ln in enumerate(lines):
        if "apiLogout(" not in ln:
            continue
        stripped = ln.strip()
        # Baris komentar/import/alias bukan pemanggilan.
        if stripped.startswith(("//", "*", "/*", "import", "export")) or " as apiLogout" in ln:
            continue
        g.bump()
        window = "\n".join(lines[max(0, i - 8):i + 1])
        if STATUS_GUARD.search(window) or EXPLICIT_LOGOUT.search(window):
            continue
        g.add(
            f"AuthContext.js:{i + 1} `apiLogout()` dipanggil TANPA memeriksa status 401/403. "
            "Kegagalan jaringan/5xx akan menghapus token & memaksa login ulang (BUG-AUTH-01). "
            "Pagar dengan isAuthReject(e) dan coba ulang untuk error transient."
        )

    # A2 — mekanisme retry transient wajib ada.
    g.bump()
    if not re.search(r"RETRY_MS|retryDelays|setTimeout\(\s*\(\)\s*=>\s*restore", text):
        g.add("AuthContext.js: tidak ada percobaan ulang (backoff) untuk kegagalan transient auth/me.")

    # A3 — kontrak konteks.
    for token in ("sessionError", "retrySession"):
        g.bump()
        if token not in text:
            g.add(f"AuthContext.js: `{token}` tidak diekspor — UI tak bisa membedakan "
                  "server-tak-terjangkau dari sesi-kedaluwarsa.")


def check_surface(g: Guard, path, testid: str, label: str) -> None:
    g.bump()
    if not path.exists():
        g.add(f"{label} tidak ada ({path}).")
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    # testid bisa literal ('admin-session-offline') atau lewat konstanta (T.sessionOffline).
    key = "".join(w.capitalize() if n else w for n, w in enumerate(testid.split("-")[1:]))
    has_testid = testid in text or (key and key in text)
    if "sessionError" not in text or not has_testid:
        g.add(f"{label}: belum menampilkan status pemulihan sesi (butuh `sessionError` + "
              f"data-testid `{testid}`), sehingga gangguan jaringan tampak seperti logout.")


def main() -> int:
    g = Guard("INV-AUTH-01", "Sesi tahan gangguan jaringan (token hanya dihapus pada 401/403)")
    check_auth_context(g)
    check_surface(g, ADMIN_LAYOUT, "admin-session-offline", "AdminLayout.js")
    check_surface(g, ACCOUNT_PAGE, "account-session-offline", "AccountPage.js")
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
