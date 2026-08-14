# 架构概览

> 本文件是维护者私有规划库的公开浓缩版，目标是让本仓**自洽**：任何人 clone 下来即可理解全貌。

## 定位：垂直的脸，平台的骨

对外是**红队垂直产品**（stalker = 可审计的红蓝攻防作战室）；对内是**运行时中立的契约层**。
通用性是"打开后的惊喜"，不是"门口的招牌"。

## 判据：agentic vs 脚本化

是否 agentic 不取决于用没用 LLM，而取决于**运行时谁决定下一步**：
- 脚本化 = 下一步在设计/生成时写死。
- Agentic = 下一步由策略（LLM + 当前观察）在运行时决定。
红队因此被建模成 **attacker-LLM 生成候选 → judge-LLM 打分/剪枝 → 读日志(tape)决定下一向量** 的优化回路，而非"依次跑 probe 1..N"。

## 形态：混合 B（dsh 运行时 + 契约 spec 层）

```
        ┌───────────────────────────────────────────────┐
        │  stalker 产品层 = 作战室 dsh 插件 + bundle       │
        │   • agent1 红队 agent-loop 插件（attacker/judge）  │
        │   • 区域 bundle：cn-pack / eu-pack（profile 选择） │
        │   • 工具 seam：garak(CLI) / PyRIT(sidecar) /       │
        │     promptfoo(TS 原生)                            │
        │   • 证据包报告插件（从 session log 派生）          │
        │   • 私有弹药插件（授权制，不进公开 topic）         │
        └───────────────────────────────────────────────┘
                         ▲ 实现（可替换）
        ┌───────────────────────────────────────────────┐
        │  spec 层（IP，运行时中立）C1/C2/C3 + 一致性测试    │
        └───────────────────────────────────────────────┘
                         ▲ 运行在
        ┌───────────────────────────────────────────────┐
        │  dsh / Cordis 运行时（session log / 沙箱 / MCP /  │
        │  subagent / provider / profile-bundle-patch）     │
        └───────────────────────────────────────────────┘
```

dsh 与本项目架构高度趋同：**append-only session log = C1 tape**（连 "model-visible means logged" 不变量都一样）、**skill 包 = C3**、**事件 = C2**、seam = provider 契约。所以骑在 dsh 上是"贴合"不是"较劲"。

## 三份契约（本体）

| 契约 | 内容 | dsh 上的映射 |
|------|------|-------------|
| **C1 Tape 格式** | JSONL append-only：entry（不可变事实，含决策理由）、anchor（阶段边界 + state）、view（按需组装）。修正靠 supersede 不靠删除。 | dsh session log |
| **C2 事件 taxonomy** | 领域事件命名与 payload schema。命名空间：`ingest.*`（agent0）/ `redteam.*`（agent1）。**授权门**（无授权不可登记目标）编码为硬不变量。 | dsh 事件域 |
| **C3 Skill 包格式** | Agent Skills + L0–L3 分层加载 + "订阅哪些事件、在哪挂载"的声明 + 公开/私有边界（含弹药即强制私有） | dsh skill 包 |

架构本体是契约；运行时（dsh）与插件都是契约的可替换实现。契约保持中立 = 若 dsh 破坏性变更伤及业务，可回退其他运行时（如 bub 部署选项）的**可移植保险**。

## agent1 — 自主红队（主体）

IPO + `redteam.*` 事件：

```
Recon → BuildProbes → Attack(多轮/优化) → Score → Report →(闭环)→ Retest
  redteam.target.registered      # 目标 + 授权范围（硬门）
  redteam.intel.ingested         # 读 agent0 情报 → 上下文
  redteam.probe.built            # probe + 期望行为 + rubric
  redteam.attack.round.completed # 每轮 attacker/judge 结果落日志
  redteam.strategy.adjusted      # 读 view 决定下一向量（agentic 核心）
  redteam.finding.logged         # 映射 OWASP + ATLAS + NIST（+GB/T 45654）
  redteam.metric.updated         # ASR / queries-per-attack / heatmap
  redteam.report.ready           # 发现 → 修复路径
  redteam.remediation.retested   # 蓝队补丁后回归（purple team 闭环）
```

### 工具三件套（是 tool，不是本体）

- **garak**（NVIDIA / Apache-2.0）：静态广度基线，JSONL 直入日志/datapool。CLI，subprocess 调用。
- **PyRIT**（Microsoft / MIT）：动态多轮编排（Crescendo / TAP / Skeleton Key），深度对抗主力。Python 库，先 subprocess 桥，必要时常驻 sidecar。
- **promptfoo**（MIT）：YAML 驱动 CI/CD 回归，OWASP 映射，蓝队补丁后 re-test。TS 原生，天然契合 dsh。

组合：**garak 基线 → PyRIT 多轮深挖 → promptfoo 回归**。

### 方法档位（难度升级）

Crescendo（多轮渐进，ASR 高）/ GOAT（低 query 外科手术）/ TAP（树搜索，暴露弱类目）+ 变换叠加（编码 / 角色扮演 / 多模态，会复利）。

### 度量（报告一等公民）

ASR（攻击成功率）、queries-per-attack（效率 = 检测风险 + 成本 + time-to-exploit）、harm-category heatmap。

## agent0 — 情报（recon 薄适配器）

定位修订：采集是**商品化能力**（OpenBiliClaw 等已有成熟 dsh 集成），agent0 **不自造采集引擎**，
收窄为「情报塑形薄适配器 + 可插拔采集源 seam」。差异化只在"目标/竞品/舆情情报 → agent1 探针上下文"
的下游语义。IPO：Collect → Structure → Judge → Publish，全流程落日志。

## 报告与 purple team 闭环

每条发现四要素：**类别（OWASP/ATLAS）+ 受影响组件 + 可复现用例 + 修复路径**。补丁必须 **re-test**（挡住载荷 ≠ 挡住语义变体）。持续而非周期：模型/prompt/工具任一更新触发定向重测。

## 区域合规包（dsh bundle/profile）

- 中立技术核心默认开；
- `cn`（GB/T 45654 备案：五类31种；合格率 ≥90%、应拒答拒答率 ≥95%、非拒答拒答率 ≤5%）/ `eu`（AI Act 第5/15/50/55条；第55条对系统性风险 GPAI 强制红队 + 方法论留痕——证据包直接是卖点）可选。

## 开源 / 私有边界

- **公开（本仓 + 公开插件仓，Apache-2.0）**：契约 + 作战室编排骨架 + 工具适配器（**空弹匣**）。
- **私有（授权制）**：具体攻击 skill、舆情 skill、备案题库 skill —— 种子 / 载荷 / 话术。
- 切分线：**方法公开，载荷私有。** 护城河在可审计留痕 + agent team 编排 + 契约解耦，不在攻击载荷。
- 靠 C3 契约，私有 skill 与公开 harness 天生解耦：**一套代码两种形态——开源版空弹匣，授权版装弹。**

## 相邻能力：舆情（防御向）

同一骨架可迁移到舆情鲁棒性压测：agent0 采集舆情情报 → agent1 构建敏感输入探针 → 压测**自有 / 授权产品** → 出话术 / 围栏升级 + 危机预演。**仅限防御性自测，不做面向公众的操纵。** 属私有 skill。

## 风险与对冲（dsh 是 developer preview）

| 风险 | 对冲 |
|------|------|
| dsh 破坏性变更、不收 PR | 锁版本 + 契约层隔离 + CI 对齐；破坏性变更当例行维护 |
| 合规产品用中国大厂底座的观感（EU 尤甚） | 依赖名义写 Cordis（MIT）；运行时可换；必要时提供 bub 部署选项 |
| PyRIT（Python）与 dsh（Node）错位 | 先 subprocess/CLI 桥；热路径再上常驻 sidecar |
