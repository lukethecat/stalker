# AGENTS.md — stalker（红蓝攻防作战室）

> **每次开工先读本文件 + `docs/architecture.md` + `docs/roadmap.md`，再动手。**
> 本文件与 `CLAUDE.md` 内容一致（dsh 会话自动加载 AGENTS.md，Claude Code 读 CLAUDE.md），修改时同步更新两份。
> 完整交接文档与私有决策记录在维护者本机规划库（不公开）；本仓文档是其公开浓缩版，足以让本仓自洽运行。

## 一句话

stalker = 建在 DeepSeek Harness (dsh) 上的**可审计红蓝攻防作战室**。对外红队/AI 合规垂直产品，对内运行时中立的契约层。**垂直的脸，平台的骨。**

## 形态与流程

- 形态 = dsh **插件/bundle**（"混合 B"）：dsh 当运行时+分发渠道；C1/C2/C3 契约当运行时中立 spec 层（IP + 可移植保险）。
- 主体 = **agent1 红队**（攻击即优化：attacker→judge→读日志定下一向量）；agent0 情报降为 recon 薄适配器，采集复用现成插件（OBC 类），不自造。
- 工具是 tool 不是本体：garak（基线）/ PyRIT（多轮）/ promptfoo（回归）。发现映射 OWASP + ATLAS + NIST（+ GB/T 45654）。
- 协作：写 dsh 插件 → gh 发布 → 本地 dsh 装测 → 按报错迭代。

## 铁律（house rules）

1. 依赖 dsh/Cordis **不 fork**；自有能力全走插件/bundle。
2. **契约是本体，运行时可换**（保持中立 = 撤退保险）。
3. kernel strict, plugins loose。
4. **安全宪法**：仅授权目标、空弹匣（公开仓不含攻击载荷/种子/话术）、弹药私有授权制、舆情只做防御向自测。
5. dsh 是 developer preview（会破坏性变更/不收 PR）：锁版本、契约层隔离、破坏性变更当例行维护。
6. 讨论用中文，简洁直接；命令代跑并解释。

## 当前阶段

- Phase 0 ✅ 契约 + 一致性测试（`spec/`，26 测试绿）。
- Phase 1 ✅ 第一个插件 `lukethecat/dsh-plugin-warroom-garak`（`garak_scan`：授权门 + 预算 + 子进程 + JSONL 解析 + 证据报告），已发布并挂载进本机 dsh。
- **当前 = Phase 2**：`garak_scan` 打一个授权端点 → 从 session log 派生一页证据报告（跑通"骑在 dsh 上出可审计红队报告"）。详见 `docs/roadmap.md`。

## 契约层位置

`spec/`（C1 tape / C1 view / C2 events / C3 skill 的 JSON Schema + 参考校验器 + 一致性测试）。契约包名 `sentinel_spec`（沿用 Phase 0 命名）。后续插件的领域事件用 `redteam.*` 命名空间。
