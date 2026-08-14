# 路线图

原则：不写框架，先跑通最细的竖切面；从第一天起所有产出落 dsh session log（吃自己的狗粮）。

## Phase 0 — 契约先行（立信）✅ 已完成

`spec/`：C1 / C2 / C3 写成 JSON Schema + 参考校验器 + 一致性测试。
- 零外部依赖（不依赖任何运行时、不需 API key），可完整落地并测试。
- 两条硬不变量编码进 schema：**授权门**（无授权不可登记目标）、**空弹匣边界**（含弹药即强制私有）。
- 交付物：`spec/schema/*.json` + `spec/sentinel_spec/conformance.py` + `spec/tests/`（pytest，26 cases 全绿）+ 可校验示例。

## Phase 1 — 第一个 dsh 插件 ✅ 已完成

[`lukethecat/dsh-plugin-warroom-garak`](https://github.com/lukethecat/dsh-plugin-warroom-garak)：
- `garak_scan` 工具：授权门（硬拒）+ 预算熔断（`maxGenerations`）+ garak subprocess + JSONL 解析 + 证据报告落盘。
- 已发布 GitHub、已挂载进本机 dsh profile、`garak_scan` 工具可用。

## Phase 2 — 最小竖切面（证据报告）🔄 进行中

**目标**：`garak_scan` 打一个授权端点 → 从 dsh session log 派生一页证据报告——跑通"骑在 dsh 上出可审计红队报告"，这就是 EU AI Act 第55条要的"红队方法论留痕"原型。

- [x] 本机 mock LLM 端点（自授权）端到端验证 garak_scan（插件 seam #2：garak 0.16 JSONL 字段解析）
- [ ] `redteam.target.registered` / `redteam.finding.logged` 等 C2 事件从 session log 派生（与 spec 对齐）
- [ ] 证据报告插件/脚本：session log → 一页 Markdown（目标 + 授权 + per-probe 命中 + OWASP/ATLAS 映射）

## Phase 3 — 红队优化回路（attacker/judge 插件）

- attacker/judge 双模型最小回路（先 **Crescendo** 一种 + 预算熔断），judge 结果落日志；
- `redteam.strategy.adjusted`：读 ASR/覆盖度决定下一向量（验证 agentic，对比"跑死列表"）；
- 全程可回放：整个 campaign 即 session log。

## Phase 4 — 区域包 + agent0 recon + purple team

- cn（GB/T 45654）/ eu（AI Act）合规包做成 dsh **bundle/profile**；
- agent0 recon 接现成采集插件（OpenBiliClaw 类）做薄适配器；
- promptfoo 回归用例 + 蓝队补丁 re-test 闭环。

## Phase 5 — 私有弹药（授权制分发）

攻击 / 舆情 / 备案题库 skill 进私有仓、授权制分发（私有 index / license key）。开源版空弹匣，授权版装弹。

## 贯穿事项

- 每步产出（含失败）落 session log；领域事件用 `redteam.*` 命名空间（C2）。
- 锁 dsh 版本；dsh 破坏性变更当例行维护（契约层隔离）。
- 冷搬家验证：另一台机器 clone + 装 dsh + 重放 session log，验证决策历史完整。

## 开放问题

- agent0 recon 直接消费 OBC 的 Agent Bridge 还是自建轻 Provider（红队要的"目标/竞品/舆情情报"OBC 覆盖多少待评估）。
- PyRIT（Python 库）在 dsh 上走 subprocess 还是常驻 sidecar。
- 区域包/init 用 dsh profile/bundle/patch 的具体落法。
- datapool/finding schema 最终定稿（与 C2/C3 合并推进）。
- 供应商观感对冲的最终形态（Cordis 命名 / 可选 bub 部署）。
