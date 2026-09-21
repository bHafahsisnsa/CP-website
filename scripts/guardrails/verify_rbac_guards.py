#!/usr/bin/env python3
"""INV-RBAC-01/02/03 — Penegakan RBAC berlapis (STATIK) untuk Collector Parfum.

Kelas bug dicegah: RC-9 RBAC leakage (customer mengakses modul admin via URL / endpoint tanpa guard).

  INV-RBAC-01 (BE enforcement): setiap router SENSITIF (admin-only) WAJIB memakai
     require_role / require_section. Router baru yang lupa guard => MERAH. Anchor anti-regresi
     bila guard dihapus dari router lama.
  INV-RBAC-02 (route admin bertanda): endpoint yang path-nya mengandung '/admin' WAJIB
     dijaga require_role('admin')/require_section admin di file router-nya.
  INV-RBAC-03 (matrix SSOT): permissions_config.py WAJIB mendefinisikan section admin_* hanya
     untuk role 'admin' (tidak bocor ke 'customer').

Registry SENSITIVE_ROUTERS bertumbuh: saat file router itu dibuat, gate langsung menagih guard.
Usage: cd /app && python scripts/guardrails/verify_rbac_guards.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import BACKEND, Guard  # noqa: E402

# Router admin-only yang WAJIB menegakkan guard SAAT file-nya ada (grow-with-code).
SENSITIVE_ROUTERS = [
    "admin", "admin_products", "admin_orders", "admin_categories", "admin_vouchers",
    "admin_shipping", "admin_payments", "admin_reviews", "admin_users", "admin_settings",
    "dashboard", "audit", "users", "settings",
]


def main() -> int:
    g = Guard("INV-RBAC-01/02/03", "RBAC berlapis: endpoint admin dijaga + matrix SSOT konsisten")
    routers_dir = BACKEND / "routers"

    # ---- INV-RBAC-01: router sensitif harus ber-guard (bila filenya ada) ----
    if routers_dir.exists():
        for r in SENSITIVE_ROUTERS:
            fp = routers_dir / f"{r}.py"
            if not fp.exists():
                continue
            g.bump()
            src = fp.read_text(encoding="utf-8", errors="ignore")
            if not re.search(r"require_section|require_role", src):
                g.add(f"BE router '{r}.py' (sensitif/admin) TANPA require_section/require_role → RBAC backend bocor.")

        # ---- INV-RBAC-02: endpoint dgn path '/admin' harus dijaga ----
        for fp in routers_dir.glob("*.py"):
            src = fp.read_text(encoding="utf-8", errors="ignore")
            has_admin_path = bool(re.search(r"@router\.[a-z]+\([\'\"][^\'\"]*admin", src)) or \
                bool(re.search(r"prefix\s*=\s*[\'\"][^\'\"]*admin", src))
            if has_admin_path:
                g.bump()
                if not re.search(r"require_section|require_role", src):
                    g.add(f"BE router '{fp.name}' punya path '/admin' TANPA guard require_role/require_section.")

    # ---- INV-RBAC-03: matrix SSOT (permissions_config) tak bocor ke customer ----
    pc = BACKEND / "permissions_config.py"
    if pc.exists():
        txt = pc.read_text(encoding="utf-8", errors="ignore")
        # cari blok admin_* dan pastikan 'customer' tidak ada di set aksesnya
        for m in re.finditer(r'"(admin_[a-z_]+|audit)"\s*:\s*\{([^}]*)\}', txt):
            section, members = m.group(1), m.group(2)
            g.bump()
            if re.search(r'[\'\"]customer[\'\"]', members):
                g.add(f"permissions_config: section admin '{section}' MEMBERI akses ke 'customer' → kebocoran hak.")
    else:
        g.add("permissions_config.py tidak ditemukan — SSOT RBAC hilang.")

    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
