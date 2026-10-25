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
- [x] Live-дані mainnet: 410 tx, 41 батч (DRpb 18, Evn 11, CAo1 5, JUP 2, HEL 2, smoke 3), вердикти по 5 валідаторах, приклади блоків (слот 460850708: 10/10 наших у DRpb; verify --live-check проходить)
- [ ] Фінальний `graphify update . && graphify export obsidian --dir ./vault`
- [ ] Атрибуція форків за межами Jito (Frankendancer/Firedancer з великим стейком у розкладі не знайдено; версії зафіксовано)
- [ ] Добір до порога PRD (≥15 батчів з ≥2 tx в слоті на валідатора): зараз DRpb 12, Evn 10, CAo1 7, JUP/HEL по 2, 5ZqveVff 2
