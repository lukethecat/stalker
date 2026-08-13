# spec — 三份契约（Phase 0，进行中）

契约是本项目的**本体**；内核与插件都是其可替换实现。本目录将容纳可机读的契约与一致性测试。

## 目标产物
- `schema/c1_tape.schema.json` — C1 Tape 格式（entry / anchor / view，append-only，supersede 修正）
- `schema/c2_events.schema.json` — C2 事件 taxonomy（`ingest.*` / `redteam.*` 命名与 payload）
- `schema/c3_skill.schema.json` — C3 Skill 包格式（Agent Skills + L0–L3 + 事件订阅声明）
- `tests/` — pytest 一致性测试：tape 读写 roundtrip、跨 schema 版本读取、事件 payload 校验

## 为何先做这个
零外部依赖（不需 bub / API key），可完整落地并测试，是开源立信的第一个可信物。详见 `../docs/roadmap.md`。
