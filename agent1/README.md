# agent1 — 自主红队专家

把"攻击"当作**运行时求解的优化问题**：attacker-LLM 生成候选 → judge-LLM 打分/剪枝 → 读 tape 决定下一向量。能定时、定探针、主动泛化与难度升级，产出**发现报告 + 蓝队策略升级方案**，并支持 purple team 回归闭环。

## IPO（`redteam.*` 事件）
Recon → BuildProbes → Attack(多轮/优化) → Score → Report →(闭环)→ Retest

## 工具（是 tool，不是本体）
garak（广度基线）/ PyRIT（多轮深挖）/ promptfoo（CI/CD 回归），经适配器以 subprocess/库调用。

## ⚠️ 空弹匣
本目录只放**编排能力**（attacker/judge 回路、事件、报告框架、工具适配器接口）。
**不含任何攻击载荷 / 种子 / 绕过话术**——那些是私有 skill，走单独授权制分发。
仅对**授权目标**测试：`redteam.target.registered` 必带授权范围，无授权不启动；产出用于加固。

详见 `docs/architecture.md`。
