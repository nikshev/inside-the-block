#!/usr/bin/env python3
"""Генератор і валідатор матриці трасування проекту cross-cluster.

Замикає ланцюг, оголошений принципом I конституції:

    PRD §X -> FR-003-07 -> T-034 -> crates/ingest/src/trongrid.rs -> tests/pagination.rs

Джерела:
  specs/NNN-*/spec.md    вимоги FR-NNN-MM
  specs/NNN-*/tasks.md   задачі T-xxx [FR-NNN-MM], статус через чекбокс
  весь код              маркери "impl: FR-..." і "verifies: FR-..."

Пише docs/traceability.md і виходить з ненульовим кодом, якщо ланцюг розірваний.
Задача, ще не позначена виконаною, коду не потребує — гейт спрацьовує на
задачах зі статусом [x].

Використання:
    python3 scripts/trace.py                 згенерувати і перевірити
    python3 scripts/trace.py --check         тільки перевірити, нічого не писати
    python3 scripts/trace.py --root <шлях>   сканувати інше дерево (для тестів)
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
OUT = ROOT / "docs" / "traceability.md"


def set_root(root: Path) -> None:
    """Перенацілити сканер на інше дерево — потрібно тестам scripts/test_trace.py."""
    global ROOT, SPECS, OUT
    ROOT = Path(root).resolve()
    SPECS = ROOT / "specs"
    OUT = ROOT / "docs" / "traceability.md"

FR_RE = re.compile(r"\bFR-(\d{3})-(\d{2,3})\b")
TASK_RE = re.compile(r"\bT-(\d{3,4})\b")
DONE_RE = re.compile(r"^\s*[-*]\s*\[([ xX])\]")
NO_CHECKBOX_RE = re.compile(r"^[-*]\s+T-\d{3,4}\b")
IMPL_RE = re.compile(r"impl:\s*(FR-\d{3}-\d{2,3}(?:\s*,\s*FR-\d{3}-\d{2,3})*)")
VERIFIES_RE = re.compile(r"verifies:\s*(FR-\d{3}-\d{2,3}(?:\s*,\s*FR-\d{3}-\d{2,3})*)")
SPEC_DIR_RE = re.compile(r"^(\d{3})-")
# Опт-аут для файлів, що містять FR-ID як дані, а не як заявку на ланку
# ланцюга: фікстури, тести самого валідатора, генератори прикладів.
IGNORE_FILE_RE = re.compile(r"trace:\s*ignore-file")

SKIP_DIRS = {
    ".git", ".specify", ".claude", ".codex", ".agents", "data", "vault", "graphify-out",
    "target", "node_modules", "__pycache__", ".venv", ".ipynb_checkpoints",
}
# Маркери живуть у коді. .md свідомо виключено: докам і специфікаціям
# потрібне право наводити FR-ID як приклад, не претендуючи на ланку ланцюга.
TEXT_SUFFIXES = {
    ".rs", ".py", ".toml", ".yaml", ".yml", ".sql", ".sh", ".ipynb",
}
# Каталоги, у яких лежить імплементація. Файл коду тут мусить нести маркер
# або явно вийти з ланцюга через "trace: ignore-file". Це другий бік
# принципу I: мало щоб у вимоги був файл — не має бути коду поза вимогами.
IMPL_ROOTS = {"crates", "python", "src", "lib", "app"}
IMPL_SUFFIXES = {".rs", ".py"}

# English display labels for the generated matrix. Source specifications remain
# the authoritative requirement text; these summaries are presentation only.
EN_REQUIREMENT_TITLES = {
    "FR-001-01": "Start the pipeline with docker compose up in safe dry-run mode",
    "FR-001-02": "Require explicit live mode before mainnet sends",
    "FR-001-03": "Store the spend cap in versioned YAML configuration",
    "FR-001-04": "Calculate maximum batch fees and reject over-cap sends",
    "FR-001-05": "Maintain a persistent append-only spend ledger",
    "FR-001-06": "Emit structured JSON logs with microsecond timestamps",
    "FR-001-07": "Store sent, landed, block, and validator snapshot data",
    "FR-001-08": "Recompute transaction positions from raw block data",
    "FR-001-09": "Load keys from volumes and RPC URLs from environment variables",
    "FR-001-10": "Scan for secrets and require trace checks in CI",
    "FR-001-11": "Record the configuration version for every run",
    "FR-001-12": "Provide a local validator and devnet workflow",
    "FR-002-01": "Build Solana transactions with ComputeBudget and Memo instructions",
    "FR-002-02": "Sign and verify transactions with Ed25519",
    "FR-002-03": "Encode and decode Solana addresses and signatures with base58",
    "FR-002-04": "Implement experimental arms A through D",
    "FR-002-05": "Randomize send order reproducibly from a recorded seed",
    "FR-002-06": "Read leader schedules and snapshot validator versions",
    "FR-002-07": "Support RPC sending and a direct TPU transport interface",
    "FR-002-08": "Record send times and exclude off-target transactions",
    "FR-002-09": "Collect transaction positions from getBlock entries",
    "FR-002-10": "Require an accepted spend-guard decision before sending",
    "FR-003-01": "Calculate pairwise agreement for fee, reward-cost, and send-order hypotheses",
    "FR-003-02": "Calculate Kendall tau and batch-bootstrap confidence intervals",
    "FR-003-03": "Run a within-slot permutation test against random ordering",
    "FR-003-04": "Measure gaps between our transactions and normalized block positions",
    "FR-003-05": "Assign strict, statistical, none, or insufficient-data verdicts",
    "FR-003-06": "Export validator-by-hypothesis results to Markdown and CSV",
    "FR-004-01": "Document design validity, budget controls, and non-isolated factors",
    "FR-004-02": "Provide a CLI to analyze a data directory and render results",
    "FR-004-03": "Re-fetch blocks from RPC and verify recorded positions",
    "FR-004-04": "Include dates, versions, verdicts, charts, and failures in the report",
    "FR-004-05": "Map submission deliverables to a completion checklist",
}


@dataclass
class Requirement:
    fid: str
    feature: str
    title: str
    tasks: list[str] = field(default_factory=list)
    impls: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)


@dataclass
class Task:
    tid: str
    feature: str
    frs: list[str]
    done: bool
    critical: bool
    text: str


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def feature_dirs() -> list[Path]:
    if not SPECS.is_dir():
        return []
    return sorted(d for d in SPECS.iterdir() if d.is_dir() and SPEC_DIR_RE.match(d.name))


def parse_requirements(errors: list[str]) -> dict[str, Requirement]:
    reqs: dict[str, Requirement] = {}
    for d in feature_dirs():
        num = SPEC_DIR_RE.match(d.name).group(1)
        spec = d / "spec.md"
        if not spec.is_file():
            continue
        for line in spec.read_text(encoding="utf-8").splitlines():
            for m in FR_RE.finditer(line):
                fid = m.group(0)
                if m.group(1) != num:
                    errors.append(
                        f"{rel(spec)}: {fid} не належить фічі {num} — "
                        f"номер вимоги мусить збігатися з номером каталогу"
                    )
                    continue
                if fid in reqs:
                    continue
                title = FR_RE.sub("", line).strip(" \t-*:|#").strip()
                reqs[fid] = Requirement(fid=fid, feature=d.name, title=title[:110])
    return reqs


def parse_tasks(reqs: dict[str, Requirement], errors: list[str]) -> list[Task]:
    tasks: list[Task] = []
    for d in feature_dirs():
        tf = d / "tasks.md"
        if not tf.is_file():
            continue
        for line in tf.read_text(encoding="utf-8").splitlines():
            tm = TASK_RE.search(line)
            if not tm:
                continue
            tid = tm.group(0)
            # Задача — це рядок-чекбокс. Усе інше (граф залежностей, пояснення,
            # рядки escalated:) вільно згадує T-034 як текст, не претендуючи на
            # роль задачі. Без цього правила валідатор змушував би переписувати
            # прозу, щоб у ній не траплялись ідентифікатори.
            dm = DONE_RE.match(line)
            if not dm:
                # Пункт списку, що починається з ідентифікатора, але без
                # чекбокса — майже напевно задача, якій забули статус.
                if NO_CHECKBOX_RE.match(line.lstrip()):
                    errors.append(
                        f"{rel(tf)}: {tid} — пункт списку без чекбокса статусу; "
                        f"задача мусить мати вигляд '- [ ] {tid} [FR-...] ...'"
                    )
                continue
            frs = sorted({m.group(0) for m in FR_RE.finditer(line)})
            done = dm.group(1).lower() == "x"
            task = Task(
                tid=tid, feature=d.name, frs=frs, done=done,
                critical="critical:" in line, text=line.strip(),
            )
            tasks.append(task)
            if not frs:
                errors.append(f"{rel(tf)}: {tid} не посилається на жодну вимогу FR")
            for fid in frs:
                if fid not in reqs:
                    errors.append(f"{rel(tf)}: {tid} посилається на невідому вимогу {fid}")
                else:
                    reqs[fid].tasks.append(tid)
    return tasks


def scan_markers(reqs: dict[str, Requirement], errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_relative_to(SPECS) or path == OUT:
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if IGNORE_FILE_RE.search(body):
            continue
        parts = path.relative_to(ROOT).parts
        found_marker = False
        for regex, bucket in ((IMPL_RE, "impls"), (VERIFIES_RE, "tests")):
            for m in regex.finditer(body):
                for fm in FR_RE.finditer(m.group(1)):
                    fid = fm.group(0)
                    if fid not in reqs:
                        errors.append(f"{rel(path)}: маркер посилається на невідому вимогу {fid}")
                        continue
                    found_marker = True
                    target = getattr(reqs[fid], bucket)
                    if rel(path) not in target:
                        target.append(rel(path))
        if (
            not found_marker
            and path.suffix in IMPL_SUFFIXES
            and parts[0] in IMPL_ROOTS
        ):
            errors.append(
                f"{rel(path)}: файл коду без маркера трасування; додай "
                f"'impl: FR-...' чи 'verifies: FR-...' у шапку, або "
                f"'trace: ignore-file', якщо файл свідомо поза ланцюгом"
            )


def check_closure(reqs: dict[str, Requirement], tasks: list[Task], errors: list[str]) -> int:
    by_fr: dict[str, list[Task]] = defaultdict(list)
    for t in tasks:
        for fid in t.frs:
            by_fr[fid].append(t)

    # Фіча між /speckit-specify і /speckit-tasks не має tasks.md. Її вимоги ще
    # не мусять бути покриті: ланцюг незавершений законно, а не розірваний.
    # Щойно tasks.md зʼявився — непокрита вимога знову є порушенням.
    planned = {d.name for d in feature_dirs() if (d / "tasks.md").is_file()}

    pending = 0
    for fid, req in sorted(reqs.items()):
        related = by_fr.get(fid, [])
        if not related:
            if req.feature in planned:
                errors.append(f"{fid}: вимога не покрита жодною задачею ({req.feature})")
            else:
                pending += 1
            continue
        if not all(t.done for t in related):
            pending += 1
            continue
        if not req.impls:
            errors.append(
                f"{fid}: усі задачі виконані, але немає файла з маркером "
                f"'impl: {fid}'"
            )
        if not req.tests:
            errors.append(
                f"{fid}: усі задачі виконані, але немає тесту з маркером "
                f"'verifies: {fid}'"
            )
    return pending


def render(reqs: dict[str, Requirement], tasks: list[Task], pending: int, errors: list[str]) -> str:
    done = sum(1 for t in tasks if t.done)
    lines = [
        "# Traceability Matrix",
        "",
        "<!-- GENERATED by scripts/trace.py — DO NOT EDIT MANUALLY -->",
        "",
        f"Requirements: **{len(reqs)}** · Tasks: **{len(tasks)}** "
        f"({done} done) · requirements in progress: **{pending}** · "
        f"violations: **{len(errors)}**",
        "",
    ]

    if not reqs:
        lines += [
            "No requirements yet. The matrix will fill after the first "
            "`/speckit-specify`.",
            "",
        ]

    for d in feature_dirs():
        frs = [r for r in reqs.values() if r.feature == d.name]
        if not frs:
            continue
        lines += [f"## {d.name}", "", "| Requirement | Description | Tasks | Implementation | Tests |",
                  "|---|---|---|---|---|"]
        for r in sorted(frs, key=lambda x: x.fid):
            lines.append(
                f"| `{r.fid}` | {EN_REQUIREMENT_TITLES.get(r.fid, r.title or '—')} | "
                f"{', '.join(f'`{t}`' for t in sorted(set(r.tasks))) or '—'} | "
                f"{', '.join(f'`{p}`' for p in r.impls) or '—'} | "
                f"{', '.join(f'`{p}`' for p in r.tests) or '—'} |"
            )
        lines.append("")

    escalations = [t for t in tasks if t.critical]
    if escalations:
        lines += ["## Critical Tasks", ""]
        lines += [f"- `{t.tid}` ({t.feature}) — {'done' if t.done else 'in progress'}"
                  for t in escalations]
        lines.append("")

    if errors:
        lines += ["## Chain Violations", ""]
        lines += [f"- {e}" for e in errors]
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check_only = "--check" in argv
    if "--root" in argv:
        set_root(Path(argv[argv.index("--root") + 1]))
    errors: list[str] = []

    reqs = parse_requirements(errors)
    tasks = parse_tasks(reqs, errors)
    scan_markers(reqs, errors)
    pending = check_closure(reqs, tasks, errors)

    if not check_only:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(render(reqs, tasks, pending, errors), encoding="utf-8")

    if errors:
        print(f"trace: CHAIN BROKEN — {len(errors)} violations", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"trace: ok — {len(reqs)} requirements, {len(tasks)} tasks, {pending} in progress")
    return 0


if __name__ == "__main__":
    sys.exit(main())
