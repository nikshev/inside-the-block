# Чекліст сабміту (мапиться на Deliverables PRD)

- [x] Репозиторій з кодом (Python 3.12, stdlib-only)
- [x] Запуск однією командою: `docker compose up` (dry-run); live лише `MODE=live`
- [x] Ключі лише через volume/env, ніколи в репо (`.gitignore` + CI-скан)
- [x] Dry-run за замовчуванням; реальна відправка з прапорцем і spend cap
- [x] Сирі дані: `data/sent.csv`, `landed.csv`, `blocks/`, `validators_snapshot.json`
- [x] Скрипт `verify` (локально + `--live-check` проти ланцюга)
- [x] README: дизайн, 6 пунктів validity, 3 невідокремлених
- [x] `scripts/analyze.py`: метрики → таблиці для звіту
- [x] Скелет звіту `docs/report.md` (вердикти, графіки, what-went-wrong)
- [ ] Live-дані mainnet (дати, вердикти, приклади блоків) — після виходу на live ≤ 30.10
- [ ] Фінальний `graphify update . && graphify export obsidian --dir ./vault`
