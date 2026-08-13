# spec — 三份契约（Phase 0，已完成）

契约是本项目的**本体**；内核与插件都是其可替换实现。本目录容纳可机读的契约与一致性测试。

## 产物
- `schema/c1_tape.schema.json` — C1 Tape 格式（entry / anchor / view，append-only，supersede 修正）
- `schema/c2_events.schema.json` — C2 事件 taxonomy（`ingest.*` 开放命名 / `redteam.*` 封闭枚举，含 9 个 `docs/architecture.md` 定义的事件 + payload 校验）
- `schema/c3_skill.schema.json` — C3 Skill 包格式（manifest：L0–L3 分层加载 + 事件订阅/emit 声明 + bub 挂载点）
- `tests/` — pytest 一致性测试（57 cases）：tape 读写 roundtrip、supersede 语义（append-only，view 侧解析）、跨 schema_version 读取、C2 事件 payload 校验、C3 manifest 与 C2 事件命名的交叉校验

## 已知未决 / 留给后续 Phase
- `ingest.*`（agent0）事件目录暂未枚举具体事件名（只在 `docs/architecture.md` 中定义了 IPO 阶段 Collect/Structure/Judge/Publish），schema 里对该命名空间保持开放（正则约束，非枚举）。计划 Phase 3（agent0 落地）时收紧为封闭枚举，需要 schema_version bump。
- `c3_skill.schema.json` 的 `mount_points` 是自由字符串（bub 的 turn pipeline 七阶段 hook 名称尚未在本仓文档中固定），Phase 1 写 `agent0-ipo-dispatcher` 插件时对照 bub 实际 hook 名补一个枚举。

## 跑测试
```
python3 -m pytest spec/tests/ -v
```
依赖：`pytest`、`jsonschema`（均为 pip 包，非 bub / API key，符合"零外部依赖"的立信要求）。

## 为何先做这个
零外部依赖（不需 bub / API key），可完整落地并测试，是开源立信的第一个可信物。详见 `../docs/roadmap.md`。
