# 路线图

原则：不写框架，先跑通最细的竖切面；从第一天起产出全落 tape（吃自己的狗粮）。

## Phase 0 — 契约先行（立信）← 当前
`spec/`：把 C1 / C2 / C3 写成 JSON Schema + 一致性测试（tape 读写 roundtrip、跨版本读取、事件 payload 校验）。
- 零外部依赖（不需 bub、不需 API key），可完整落地并测试。
- 三份决策共同指认的"第一个可信物"，也是开源立信的地基。
- 交付物：`spec/schema/*.json` + `spec/tests/`（pytest）+ `spec/README.md`。

## Phase 1 — 内核竖切面
依赖 bub，写 `agent0-ipo-dispatcher` 插件（<150 行：监听 tape 新 entry → 匹配 C2 订阅 → 触发 turn）。CLI 跑通一个 turn。
- 需要：`pip install bub` + 一个模型 provider key。
- 验证：tape → 事件 → turn 闭环成立。

## Phase 2 — 红队旗舰 MVP（能 demo 的垂直）
attacker/judge 双模型最小回路（先上 Crescendo 一种方法 + 预算熔断）+ garak 适配器（subprocess）打一个**授权**测试端点 → 发现落 tape → 出 OWASP/ATLAS 映射报告。
- 带 `redteam.target.registered` 授权门；"空弹匣"（不内置种子）。
- 这是 GitHub 上吸睛的脸：可审计报告 + tape 回放 + ASR/heatmap。

## Phase 3 — agent0 情报 + team 组合
agent0 recon 喂 agent1（`redteam.intel.ingested`），验证 operator equivalence 的跨 agent 协作；可接 Raft/dispatcher。Aperture（日报）留在自己的仓，作为"同一引擎另一垂直"的旁证，不进本仓。

## Phase 4 — 私有 contrib + 分发
弹药（攻击 / 舆情 / 备案题库 skill）进**私有仓**、授权制（私有 pip index / license key）。打包与公开发布（三仓：spec / kernel+agent0+harness / 私有 skill）。

## 贯穿事项
- 每步产出（含失败）落 tape。
- 冷搬家验证：tar Home → 另一台机器 / clone 即运行 → tape replay 验证决策历史完整。
- README 的"另一台机器 clone 即部署运行"随 Phase 1–2 补全为可复现步骤。
