# Feature Specification: Вимірювальний контур (measurement)

**Feature Branch**: `002-measurement`

**Created**: 2026-10-23

**Status**: Draft

**Input**: PRD «Inside the Block» — розділи «Дизайн експерименту», «Що треба
врахувати», «Архітектура», гіпотези H0–H4, рукави A–D.

## User Scenarios & Testing

### User Story 1 — Батч реальних tx у leader-вікно (Priority: P1)

Дослідник запускає вимірювання рукава A на валідатора: система бере вікно
лідера з розкладу, будує 10 tx з Memo `batch_id:idx` і різними CU price,
підписує реальним ed25519, відправляє з рандомізованим порядком (seed у лозі)
і записує `sent.csv`. Жодна tx не йде повз guard.

**Independent Test**: dry-run з фікстурним розкладом і фікстурним blockhash
будує 10 валідних (за структурою) підписаних tx без мережі; кожна
верифікується `ed25519.verify`; порядок відправки відтворюється за seed.

**Acceptance Scenarios**:

1. **Given** фікстурний blockhash і 10 рівнів CU price, **When** dry-run
   рукава A, **Then** 10 різних payload, усі підписи валідні, `sent.csv`
   містить seed перестановки.
2. **Given** cap менший за вартість батча, **When** запуск live, **Then**
   відправки немає, у леджері `rejected` (перевикористання 001).

### User Story 2 — Позиції наших tx зібрано з блоків (Priority: P1)

Після вікна система тягне `getBlock` для цільових слотів, знаходить наші
сигнатури в порядку entries і пише `landed.csv` + `blocks/`. Пропущені слоти —
`missing`, а не помилка.

**Independent Test**: на фікстурі з 2 слотів і 6 наших tx `collect` дає точні
позиції; `verify` (001) проходить.

### User Story 3 — Рукави A–D ізольовано за змінними (Priority: P2)

Конфіг задає рукав: A (fee gradient, незалежні платники), B (порядок
відправки, однакова винагорода), C (reward/cost при фіксованому CU price і
навпаки), D (спільний writable-акаунт). Рандомізація всього, крім дослідної
змінної; платники незалежні, крім D.

**Independent Test**: для кожного рукава згенерований батч задовольняє свій
інваріант (A: різні CU price + різні платники; B: однаковий price; C: різні
CU limit при однаковому price; D: один спільний writable).

## Edge Cases

- Розклад без вікон валідатора в епосі → батч `no-window`, пропуск з причиною.
- Слот лідера змінився (фактичний лідер ≠ цільовий за `getSlotLeaders`) → tx
  поза цільовим вікном не йдуть в аналіз (мітка `off-target`).
- `getBlock` → null (пропущений слот) → `missing`, continue.
- RPC недоступний → повтор з бек-оффом, потім контрольована зупинка;
  жодної витрати без підтвердження guard.
- Чужі tx з вищими комісіями витісняють наші → нормально: аналізуємо
  відносний порядок наших; заповненість блоку пишемо в контекст.

## Requirements

### Functional Requirements

- **FR-002-01**: Система MUST будувати tx з інструкцій ComputeBudget
  (SetComputeUnitLimit + SetComputeUnitPrice) і Memo `batch_id:idx`; серіалізація
  MUST відповідати формату Solana message/transaction (compact-u16, порядок
  акаунтів, блок `signatures[]`).
- **FR-002-02**: Система MUST підписувати tx справжнім ed25519; вендорена
  реалізація MUST проходити вектори RFC 8032; кожен підпис MUST верифікуватися
  перед відправкою.
- **FR-002-03**: Система MUST кодувати base58 для адрес/сигнатур; реалізація
  MUST проходити відомі вектори (порожній вхід, ведучі нулі → `1...`).
- **FR-002-04**: Система MUST реалізовувати рукави A–D за таблицею PRD:
  A різні CU price / незалежні платники; B однаковий price / фіксований
  інтервал; C різні CU limit при однаковому price; D спільний writable-акаунт.
- **FR-002-05**: Порядок відправки в батчі MUST рандомізуватися з seed, що
  пишеться в лог і `sent.csv`; за seed порядок MUST відтворюватися побайтово.
- **FR-002-06**: Система MUST читати leader-розклад (`getLeaderSchedule`) і
  обирати вікна цільового валідатора; версія клієнта MUST фіксуватися з
  `getClusterNodes` у `validators_snapshot.json` на кожен прогін.
- **FR-002-07**: Відправка MUST підтримувати шлях `direct-tpu` (інтерфейс +
  документований заглушковий транспорт у 002) і шлях `rpc` (реальний
  `sendTransaction` через stdlib-HTTP з `maxRetries=0`, без форвардингу);
  шлях кожної tx MUST писатися в дані як змінна.
- **FR-002-08**: Час відправки кожної tx MUST фіксуватися в мікросекундах;
  цільовий слот і фактичний лідер слота MUST звірятися (`getSlotLeaders`),
  розбіжність MUST мітити батч `off-target` і виключати з аналізу.
- **FR-002-09**: Збір позицій MUST парсити `getBlock` у порядку entries і
  писати `landed.csv`/`blocks/` за контрактом 001; пропущені слоти MUST
  ставати `missing`.
- **FR-002-10**: Жодна відправка MUST НЕ відбуватися без `decide==accepted`
  guard 001; dry-run MUST будувати і підписувати без мережі.

### Key Entities

- **SignedTx**: `payload_bytes, signature, signer_pubkey, memo_tag, cu_limit, cu_price, payer, writable_accounts[]`.
- **Arm**: `A|B|C|D` + параметри рівнів; генератор `build_arm_batch(arm, seed)`.
- **LeaderWindow**: `validator, epoch, start_slot, end_slot, version`.
- **SendRecord**: `signature, sent_at_us, path, target_slot, actual_leader, off_target: bool`.

## Success Criteria

- **SC-001**: Dry-run 20 батчів × 10 tx без мережі: 100% підписів валідні,
  100% порядків відтворюються за seed, `verify` проходить.
- **SC-002**: Збір на фікстурі 3 слотів / 15 tx: 100% позицій точні, включно з
  `missing`.
- **SC-003**: Кожен рукав проходить свій інваріант-тест (незалежні платники vs
  спільний writable; рівні price/limit за таблицею).
- **SC-004**: `sendTransaction`-шлях покритий тестом проти локального
  HTTP-стаб-сервера (stdlib, без зовнішньої мережі).

## Assumptions

- Recent blockhash: у dry-run — фікстура; у live — з RPC перед вікном.
- Прямий QUIC на TPU: у 002 — інтерфейс + заглушка і документація;
  реальний QUIC-клієнт — операційне рішення після вимірювання landing rate
  (ризик PRD: unstaked QUIC vs staked sender; шлях пишеться як змінна).
- Devnet-прогін end-to-end — перед mainnet (критерій PRD), на devnet-ключах.
