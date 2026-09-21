#!/usr/bin/env python3
"""verify_roadmap_docs.py — GATE for the roadmap planning docs (docs/roadmap/).

Why this gate exists (RC-E16 under-delivery / anti-hallucination): the user mandated
EXHAUSTIVE, per-Epic blueprints BEFORE any Epic is coded. This gate makes those docs
"code that can FAIL": if a required Epic file is missing or a mandatory section is
dropped, the gate goes RED so the planning contract can never silently rot.

Checks:
  R1 (dir)         : docs/roadmap/ exists.
  R2 (master)      : 00_ROADMAP.md exists, has all master sections, references E1..E8 + UX_BLUEPRINT.md.
  R3 (epic files)  : each Epic E1..E8 has a file docs/roadmap/E{n}_*.md.
  R4 (epic struct) : each Epic file has the title "# E{n} —" + all 13 mandatory sections (incl. UI/UX Blueprint).
  R5 (threat map)  : each Epic file references >= 1 threat class (RC-E<number>).
  R6 (guardrails)  : each Epic file references >= 1 gate/script (verify_*, fa_*, gate.sh, scripts/).
  R7 (DoD)         : each Epic file has >= 1 checkbox "- [ ]" under Definition of Done.
  R8 (UI/UX)       : each Epic UI/UX Blueprint references UX_BLUEPRINT.md and lists data-testid(s).
  R9 (UX SSOT)     : UX_BLUEPRINT.md exists, has all UX sections, extends design_guidelines.md.

Usage: cd /app && python scripts/verify_roadmap_docs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROADMAP = ROOT / "docs" / "roadmap"
MASTER = ROADMAP / "00_ROADMAP.md"
UX_BLUEPRINT = ROADMAP / "UX_BLUEPRINT.md"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"

EPICS = list(range(1, 9))  # E1..E8

MASTER_SECTIONS = [
    "Overview",
    "Epic Index",
    "Sequencing & Dependencies",
    "Global Guardrail Policy",
    "Cross-Epic Data Model Evolution",
    "Definition of Done (Global)",
]

EPIC_SECTIONS = [
    "Epic Summary",
    "Business Requirements",
    "Scope & Non-Goals",
    "Data Model",
    "API Contract",
    "State Machine & Invariants",
    "Execution Steps",
    "Best Practices",
    "Bug Mitigation & Threat Mapping",
    "Guardrail Wiring",
    "Test Plan",
    "UI/UX Blueprint",
    "Definition of Done",
]

# UX_BLUEPRINT.md must cover global standards + every new surface.
UX_SECTIONS = [
    "Purpose & Scope",
    "Design Tokens Recap",
    "Global Data States",
    "Accessibility Standards",
    "Testid Conventions",
    "Customer Account Surface",
    "Voucher Center",
    "Payments UX",
    "Admin Backoffice UX",
    "Growth UX",
    "Responsive Matrix",
    "Per-Epic UX Mapping",
]

fails = []
warns = []


def fail(msg):
    fails.append(msg)
    print(f"  {R}[FAIL]{X} {msg}")


def ok(msg):
    print(f"  {G}[OK]{X}   {msg}")


def has_section(text, title):
    # match "## <n>. <title>" (tolerant to numbering / trailing text like "(Global)")
    esc = re.escape(title)
    pat = re.compile(r"^#{2,3}\s+(?:\d+\.\s+)?" + esc + r"\s*.*$", re.MULTILINE)
    return bool(pat.search(text))


def epic_file(n):
    hits = sorted(ROADMAP.glob(f"E{n}_*.md"))
    return hits[0] if hits else None


def check_master():
    print(f"\n{B}R2 — master 00_ROADMAP.md{X}")
    if not MASTER.exists():
        fail("docs/roadmap/00_ROADMAP.md is missing")
        return
    text = MASTER.read_text(encoding="utf-8", errors="ignore")
    for sec in MASTER_SECTIONS:
        if has_section(text, sec):
            ok(f"master section present: '{sec}'")
        else:
            fail(f"master section MISSING: '{sec}'")
    # must reference each epic file
    for n in EPICS:
        f = epic_file(n)
        ref = f.name if f else f"E{n}_"
        if (f and f.name in text) or re.search(rf"E{n}_[A-Z0-9_]+\.md", text):
            ok(f"master references Epic E{n}")
        else:
            fail(f"master does not reference Epic E{n} (expected a link like E{n}_*.md)")
    # must reference the UX SSOT
    if "UX_BLUEPRINT.md" in text:
        ok("master references UX_BLUEPRINT.md")
    else:
        fail("master does not reference docs/roadmap/UX_BLUEPRINT.md")


def check_epic(n):
    f = epic_file(n)
    print(f"\n{B}R3/R4 — Epic E{n}{X}")
    if f is None:
        fail(f"Epic file docs/roadmap/E{n}_*.md is missing")
        return
    text = f.read_text(encoding="utf-8", errors="ignore")
    rel = f.relative_to(ROOT)
    # R4a title
    if re.search(rf"^#\s+E{n}\b", text, re.MULTILINE):
        ok(f"{rel}: title '# E{n} ...' present")
    else:
        fail(f"{rel}: missing title heading '# E{n} ...'")
    # R4b mandatory sections
    missing = [s for s in EPIC_SECTIONS if not has_section(text, s)]
    if missing:
        fail(f"{rel}: missing sections -> {', '.join(missing)}")
    else:
        ok(f"{rel}: all {len(EPIC_SECTIONS)} mandatory sections present")
    # R5 threat mapping
    if re.search(r"RC-E\d+", text):
        ok(f"{rel}: references threat class(es) RC-E*")
    else:
        fail(f"{rel}: no threat-class reference (expected RC-E<number>) in Bug Mitigation section")
    # R6 guardrail reference
    if re.search(r"verify_\w+|fa_\w+|gate\.sh|scripts/|forensic/", text):
        ok(f"{rel}: references gate/guardrail script(s)")
    else:
        fail(f"{rel}: no guardrail/script reference (expected verify_*/fa_*/gate.sh)")
    # R7 DoD checkboxes
    dod = text.split("Definition of Done", 1)
    if len(dod) > 1 and re.search(r"^- \[[ x]\]", dod[1], re.MULTILINE):
        ok(f"{rel}: Definition of Done has checkbox items")
    else:
        fail(f"{rel}: Definition of Done has no checkbox items ('- [ ] ...')")
    # R8 UI/UX must reference the UX SSOT + expose testids
    if "UX_BLUEPRINT" in text:
        ok(f"{rel}: UI/UX Blueprint references UX_BLUEPRINT.md")
    else:
        fail(f"{rel}: UI/UX Blueprint does not reference docs/roadmap/UX_BLUEPRINT.md")
    if re.search(r"data-testid|Testids?:|`[a-z0-9-]+-(button|input|select|card|row|list|panel)`", text):
        ok(f"{rel}: UI/UX exposes data-testid(s)")
    else:
        fail(f"{rel}: UI/UX Blueprint lists no data-testid (required for testability)")


def check_ux_blueprint():
    print(f"\n{B}R9 — UX_BLUEPRINT.md (design/UX SSOT){X}")
    if not UX_BLUEPRINT.exists():
        fail("docs/roadmap/UX_BLUEPRINT.md is missing")
        return
    text = UX_BLUEPRINT.read_text(encoding="utf-8", errors="ignore")
    for sec in UX_SECTIONS:
        if has_section(text, sec):
            ok(f"UX section present: '{sec}'")
        else:
            fail(f"UX section MISSING: '{sec}'")
    if "design_guidelines.md" in text:
        ok("UX_BLUEPRINT extends design_guidelines.md")
    else:
        fail("UX_BLUEPRINT does not reference design_guidelines.md (must extend the approved system)")
    if re.search(r"data-testid|`[a-z0-9-]+-(button|input|select|card|row|list|panel)`", text):
        ok("UX_BLUEPRINT defines data-testid conventions/examples")
    else:
        fail("UX_BLUEPRINT lacks data-testid conventions/examples")


def main():
    print(f"{B}{C}{'='*64}{X}\n{B}  ROADMAP DOCS GATE — exhaustive per-Epic blueprints{X}\n{B}{C}{'='*64}{X}")
    print(f"\n{B}R1 — docs/roadmap/ exists{X}")
    if not ROADMAP.exists() or not ROADMAP.is_dir():
        fail("docs/roadmap/ directory is missing")
        print(f"\n{B}{'='*64}{X}\n  {R}{B}ROADMAP DOCS INCOMPLETE.{X}\n")
        return 1
    ok("docs/roadmap/ present")

    check_master()
    check_ux_blueprint()
    for n in EPICS:
        check_epic(n)

    print(f"\n{B}{'='*64}{X}")
    if fails:
        print(f"  {R}{B}ROADMAP DOCS GATE: {len(fails)} problem(s). Fix before coding Epics.{X}\n")
        return 1
    print(f"  {G}{B}ROADMAP DOCS OK — master + E1..E8 fully structured.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
