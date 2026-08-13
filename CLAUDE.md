# CLAUDE.md — sentinel-agents 维护指引

> **每次开工先读本文件 + `docs/architecture.md` + `docs/roadmap.md`，再动手。**
> 本仓的存在就是为了让任何一次会话（Claude Code / Cowork / 其他机器 clone）都能拿到完整上下文，不再各说各话。

## 这是什么
sentinel-agents 是一个**可审计的开源 AI 红队 agent team**：
- **agent0 — 情报采集专家**：采集 / 预处理 / 结构化存储，全流程可观测、可复现，为红队提供上下文相关的情报。
- **agent1 — 自主红队专家**：把"攻击"当作**运行时求解的优化问题**（attacker-LLM 生成 → judge-LLM 打分剪枝 → 读 tape 定下一向量），能定时、定探针、主动泛化与难度升级；产出发现报告 + 蓝队策略升级方案。

对外是**红队垂直产品**；对内是一个通用、可搬、契约解耦的 agent team 平台。**垂直的脸，平台的骨。**

## 铁律（house rules）
1. **依赖 bub，不 fork**。微内核用 [bub](https://github.com/bubbuild/bub)（Python，hook-first，tape-based，`pip install bub`）。自己的东西一律以插件/skill 存在。借鉴 pi 哲学但不作为运行时。
2. **契约是本体，代码是可替换实现**。三份契约见 `docs/architecture.md`（C1 tape / C2 事件 / C3 skill 包）。
3. **kernel strict, plugins loose**：内核从严 review，插件谁用谁维护。
4. **本仓是"空弹匣"**：只放红队**编排能力**（attacker/judge 回路、事件、报告框架、对 garak/PyRIT/promptfoo 的适配器接口）。**绝不提交任何攻击载荷/种子/绕过话术**——那些是私有 skill，走单独授权制仓库。
5. **仅对授权目标测试**：`redteam.target.registered` 必带授权范围，无授权不启动。产出用于加固，不用于利用。
6. **一切状态外部化、可观测**：计划落文件，过程落 tape。
7. 讨论用中文，回复简洁直接。

## 当前阶段
Phase 0（契约先行）。详见 `docs/roadmap.md`。下一步 = 写 `spec/`（C1/C2/C3 的 JSON Schema + 一致性测试），零外部依赖、可先落地立信。

## 设计来源
详尽的设计演进史与决策记录保存在维护者的**私有规划库**（不在本仓）。本仓 `docs/` 是其面向公开的浓缩版，足以让本仓自洽运行。
