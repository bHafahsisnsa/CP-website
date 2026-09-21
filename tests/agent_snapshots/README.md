# tests/agent_snapshots — arsip skrip uji buatan testing agent

Berkas di folder ini adalah **arsip historis** (bukan gate resmi). Dibuat oleh testing agent pada
iterasi 30-an untuk memverifikasi epic tertentu, dan disimpan sebagai referensi kasus uji.

- `backend_test_e12.py` — 70 kasus uji kontrak sesi impor E12 (iterasi 36, semua LULUS).
- `backend_test_e11_e12.py`, `backend_test_critical_path.py`, `backend_test.py` — arsip lebih lama.
- `backend_test.py.backup` — salinan mentah, tidak dipakai.

CATATAN: base URL di dalamnya masih hardcode ke URL preview lama. Untuk regresi RESMI pakai:
`scripts/gate.sh`, `scripts/test_import_session_poc.py`, `scripts/test_tier_matrix_poc.py`,
`scripts/verify_user_import.py`, `scripts/test_product_io_core.py`,
`scripts/test_shop_and_import_e2e.py`.
