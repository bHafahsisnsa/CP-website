"""scripts/guardrails/_common.py — util bersama untuk Guardrail v2 (Collector Parfum).

Guardrail v2 = penjaga PREVENTIF berbasis analisis STATIK + RUNTIME yang memaksa invariant
lintas-kelas-bug (lihat memory/INVARIANTS.md & docs/09_THREAT_MODEL.md). Dirancang agar sesi
AI / developer baru — TANPA konteks sesi sebelumnya — tetap tertangkap saat memperkenalkan
kembali kelas bug yang sudah pernah ditemukan. Tiap penjaga mencetak: APA yang salah, DI MANA,
dan MENGACU ke INVARIANT-ID / RC.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"


class Guard:
    """Akumulator hasil satu penjaga invariant."""

    def __init__(self, invariant_id: str, title: str):
        self.id = invariant_id
        self.title = title
        self.violations = []
        self.checks = 0

    def add(self, msg: str):
        self.violations.append(msg)

    def bump(self, n: int = 1):
        self.checks += n

    def finish(self) -> int:
        print(f"{C}{B}== {self.id} — {self.title} =={X}")
        if not self.violations:
            print(f"{G}[PASS]{X} {self.checks} cek lolos, 0 pelanggaran.")
            return 0
        print(f"{R}[FAIL]{X} {len(self.violations)} pelanggaran (dari {self.checks} cek):")
        for v in self.violations:
            print(f"  {R}✗{X} {v}")
        print(f"{Y}→ Perbaiki sesuai {self.id} (detail: memory/INVARIANTS.md / docs/09_THREAT_MODEL.md).{X}")
        return 1
