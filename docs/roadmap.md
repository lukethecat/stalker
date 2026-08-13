# 路线图

原则：不写框架，先跑通最细的竖切面；从第一天起产出全落 tape（吃自己的狗粮）。

## Phase 0 — 契约先行（立信）✅ 已完成
`spec/`：把 C1 / C2 / C3 写成 JSON Schema + 一致性测试（tape 读写 roundtrip、跨版本读取、事件 payload 校验）。
- 零外部依赖（不需 bub、不需 API key），可完整落地并测试。
- 三份决策共同指认的"第一个可信物"，也是开源立信的地基。
- 交付物：`spec/schema/*.json` + `spec/tests/`（pytest，57 cases 全绿）+ `spec/README.md`。

## Phase 1 — 内核竖切面 ✅ 闭环已验证（工具链细节见下）
`agent0/dispatcher/`：`agent0-ipo-dispatcher` 插件（bub `Lifecycle` channel，~95 行）监听 tape 新
`event` entry → 按 skill 声明的订阅 pattern 匹配 → 触发 turn。
- **环境陷阱**：真正的 bub（pluggy hook-first）要求 Python ≥3.12；`pip install bub` 在 3.11 下会静默
  装到一个不相关的旧版同名包（无 pluggy/tape）。用 `uv venv --python 3.13` 在仓内建隔离环境，详见
  `agent0/dispatcher/README.md`。
- 已验证：`bub hooks` 确认插件挂载到 `provide_channels`；手动跑 `bub gateway` + 追加一条
  `redteam.target.registered` tape entry，日志证实 dispatcher 正确匹配、转发、触发了
  `process_inbound`，链路在模型调用这一步因缺 `OPENROUTER_API_KEY` 报错终止（预期内——本仓开发环境
  未配置任何 provider key，这一步需要用户在自己机器上配 key 手动跑一次）。
- 离线单元测试（10 cases，`agent0/dispatcher/tests/`）覆盖匹配/去重/无订阅/无 tape store，不需要 key。

## Phase 2 — 红队旗舰 MVP（能 demo 的垂直）← 编排骨架已完成，等私有 skill + 授权靶场接入
`agent1/orchestrator/`：Crescendo 回合循环 + 预算熔断 + `redteam.target.registered` 授权门
（硬门，未授权 attacker 一轮都不会跑，见 `tests/test_runner.py`）+ garak subprocess 适配器
（argv list 调用，不猜测 garak 报告 schema，交给调用方过滤）+ tape 落盘（C2 事件校验后写 bub
tape，与 `agent0-ipo-dispatcher` 互操作已测）+ OWASP 分组 Markdown 报告。39 个测试全绿
（`tape_bridge` 相关需 bub，其余框架无关）。
- **"空弹匣"边界**：`policies.py` 只有 `AttackerPolicy`/`JudgePolicy`/`TargetClient` 三个
  Protocol，零提示词/种子/话术；真实 Crescendo/GOAT/TAP 内容是私有 skill，本仓无法、也不应该
  产出完整可跑的攻击演示。
- **待办**（需要私有 skill + 已授权测试端点，不在本仓范围内）：真实 attacker/judge 策略、
  一次真实 garak 调用验证、`bub run` 风格 CLI 把 `redteam.target.registered` 接上
  `agent0-ipo-dispatcher` 触发链路、ASR/queries-per-attack/heatmap 指标聚合、tape 回放 UI。

## Phase 3 — agent0 情报 + team 组合
agent0 recon 喂 agent1（`redteam.intel.ingested`），验证 operator equivalence 的跨 agent 协作；可接 Raft/dispatcher。Aperture（日报）留在自己的仓，作为"同一引擎另一垂直"的旁证，不进本仓。

## Phase 4 — 私有 contrib + 分发
弹药（攻击 / 舆情 / 备案题库 skill）进**私有仓**、授权制（私有 pip index / license key）。打包与公开发布（三仓：spec / kernel+agent0+harness / 私有 skill）。

## 贯穿事项
- 每步产出（含失败）落 tape。
- 冷搬家验证：tar Home → 另一台机器 / clone 即运行 → tape replay 验证决策历史完整。
- README 的"另一台机器 clone 即部署运行"随 Phase 1–2 补全为可复现步骤。
