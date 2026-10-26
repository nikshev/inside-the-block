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
- [x] Live-дані mainnet: 1350 tx, 135 батчів, вердикти по 5 валідаторах (Evn statistical; DRpb/CAo1/JUP/HEL none), приклади блоків (слот 460850708: 10/10 наших у DRpb; verify --live-check проходить)
- [x] Граф `graphify update . && graphify export obsidian --dir ./vault` (vault/ оновлено)
- [x] Атрибуція клієнтів через validators.app: усі 5 — jito:true (Jito-Solana, версії 4.3.2/26.10.4); чистих Agave/Frankendancer/Firedancer з великим стейком у розкладі немає — зафіксовано як обмеження в docs/validators.md
- [x] Поріг PRD (≥15 батчів з ≥2 tx в слоті на валідатора): CAo1 29, Evn 25, DRpb 23, JUP 19, HEL 17 — закрито всіма
