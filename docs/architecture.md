# 架构概览

> 本文件是维护者私有规划库的公开浓缩版，目标是让本仓**自洽**：任何人 clone 下来即可理解全貌。

## 定位：垂直的脸，平台的骨

对外是**红队垂直产品**（sentinel-agents = 可审计的开源 AI 红队 agent team）；对内是一个通用、可搬、契约解耦的 **agent team 平台**。通用性是"打开后的惊喜"，不是"门口的招牌"。

## 判据：agentic vs 脚本化

是否 agentic 不取决于用没用 LLM，而取决于**运行时谁决定下一步**：
- 脚本化 = 下一步在设计/生成时写死。
- Agentic = 下一步由策略（LLM + 当前观察）在运行时决定。
红队因此被建模成 **attacker-LLM 生成候选 → judge-LLM 打分/剪枝 → 读 tape 决定下一向量** 的优化回路，而非"依次跑 probe 1..N"。

## 共享底座

```
底座 = 微内核 bub + 三份契约 + Home 目录 + tape/datapool 能力
        ▲                         ▲
   agent0 情报采集            agent1 自主红队
   (采集/结构化 skill)        (attacker/judge + 工具适配器 skill)
        └──── operator equivalence，可经 dispatcher / Raft 组合调度 ────┘
```

- **微内核**：直接用 [bub](https://github.com/bubbuild/bub)（Python，~200 行内核，turn pipeline 七阶段皆 pluggy hook，tape-based context）。**不 fork**，自有能力全走插件。
- **借鉴不依赖**：pi（earendil-works）的极简哲学（"if I don't need it, it won't be built"）作为纪律来源；如需其生态，照 bub-codex 模式做成可选 `run_model` 插件。

## 三份契约（本体）

| 契约 | 内容 |
|------|------|
| **C1 Tape 格式** | JSONL append-only：entry（不可变事实，含决策理由）、anchor（阶段边界 + state）、view（按需组装）。修正靠 supersede 不靠删除。冷/热搬家皆基于此（tar Home / tape handoff）。 |
| **C2 事件 taxonomy** | IPO 领域事件命名与 payload schema。命名空间：`ingest.*`（agent0）/ `redteam.*`（agent1）。 |
| **C3 Skill 包格式** | Agent Skills 标准 + L0–L3 分层加载 + "订阅哪些事件、在哪挂载"的声明。 |

架构本体是契约；内核与插件都是契约的可替换实现。

## agent0 — 情报采集
IPO：Collect → Structure → Judge → Publish。产出结构化情报进 datapool，供 agent1 做**上下文相关**的探针构建。全流程落 tape。

## agent1 — 自主红队
IPO + `redteam.*` 事件：
```
Recon → BuildProbes → Attack(多轮/优化) → Score → Report →(闭环)→ Retest
  redteam.target.registered      # 目标 + 授权范围（硬门）
  redteam.intel.ingested         # 读 agent0 情报 → 上下文
  redteam.probe.built            # probe + 期望行为 + rubric
  redteam.attack.round.completed # 每轮 attacker/judge 结果落 tape
  redteam.strategy.adjusted      # 读 view 决定下一向量（agentic 核心）
  redteam.finding.logged         # 映射 OWASP + ATLAS + NIST
  redteam.metric.updated         # ASR / queries-per-attack / heatmap
  redteam.report.ready           # 发现 → 修复路径
  redteam.remediation.retested   # 蓝队补丁后回归（purple team 闭环）
```

### 工具三件套（是 tool，不是本体）
- **garak**（NVIDIA / Apache-2.0）：广度基线扫描，JSONL 直入 tape/datapool。
- **PyRIT**（Microsoft / MIT）：多轮编排（Crescendo / TAP / Skeleton Key），深度对抗主力。
- **promptfoo**（MIT）：YAML 驱动 CI/CD 回归，OWASP 映射，蓝队补丁后 re-test。
组合：garak 基线 → PyRIT 多轮深挖 → promptfoo 回归。

### 方法档位（难度升级）
Crescendo（多轮渐进，ASR 高）/ GOAT（低 query 外科手术）/ TAP（树搜索，暴露弱类目）+ 变换叠加（编码 / 角色扮演 / 多模态，会复利）。

### 度量（报告一等公民）
ASR（攻击成功率）、queries-per-attack（效率 = 检测风险 + 成本 + time-to-exploit）、harm-category heatmap。

## 报告与 purple team 闭环
每条发现四要素：**类别（OWASP/ATLAS）+ 受影响组件 + 可复现用例 + 修复路径**。补丁必须 **re-test**（挡住载荷 ≠ 挡住语义变体）。持续而非周期：模型/prompt/工具任一更新触发定向重测。

## 开源 / 私有边界
- **公开（本仓，Apache-2.0）**：契约 + 底座 + agent0 + 红队**编排骨架**（空弹匣）。
- **私有（授权制）**：具体攻击 skill、舆情 skill、备案题库 skill —— 种子 / 载荷 / 话术。
- 切分线：**方法公开，载荷私有。** 护城河在可审计 tape 底座 + agent team 编排 + 契约解耦，不在攻击载荷。
- 靠 C3 契约，私有 skill 与公开 harness 天生解耦：**一套代码两种形态——开源版空弹匣，授权版装弹。**

## 相邻能力：舆情（防御向）
同一骨架可迁移到舆情鲁棒性压测：agent0 采集舆情情报 → agent1 构建敏感输入探针 → 压测**自有 / 授权产品** → 出话术 / 围栏升级 + 危机预演。**仅限防御性自测，不做面向公众的操纵。** 属私有 skill。
