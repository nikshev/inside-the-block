# Submission Checklist (maps to Deliverables PRD)

- [x] Repository with code (Python 3.12, stdlib-only)
- [x] Single-command launch: `docker compose up` (dry-run); live only `MODE=live`
- [x] Keys only via volume/env, never in repo (`.gitignore` + CI scan)
- [x] Dry-run by default; live send only with flag and spend cap
- [x] Raw data: `data/sent.csv`, `landed.csv`, `blocks/`, `validators_snapshot.json`
- [x] Script `verify` (locally + `--live-check` vs chain)
- [x] README: design, 6 validity points, 3 undifferentiated items
- [x] `scripts/analyze.py`: metrics → tables for report
- [x] Report skeleton `docs/report.md` (verdicts, charts, what-went-wrong)
- [x] Live mainnet data: 1350 tx, 135 батчів, verdicts for 5 validators (Evn statistical; DRpb/CAo1/JUP/HEL none), block examples (slot 460850708: 10/10 our txs in DRpb; verify --live-check passes)
- [x] Graph `graphify update . && graphify export obsidian --dir ./vault` (vault/ updated)
- [x] Client attribution via validators.app: all 5 — jito:true (Jito-Solana, versions 4.3.2/26.10.4); no clean Agave/Frankendancer/Firedancer with large stake in schedule — recorded as limitation in docs/validators.md
- [x] PRD threshold (≥15 batches with ≥2 tx in slot per validator): CAo1 29, Evn 25, DRpb 23, JUP 19, HEL 17 — closed by all
