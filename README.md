<!-- 语言 / Language: 中文 (English section below TBD) -->

# sentinel-agents

**可审计的开源 AI 红队 agent team** —— 情报驱动、自主调整策略、全程可复现可审计。

> 业内现有的要么是**红队工具/库**（garak / PyRIT / promptfoo），要么是**闭源商业平台**。
> sentinel-agents 补的是中间那块空白：一个**可 GitHub 安装、以可审计 tape 为底座、把情报 agent 与红队 agent 编排成 team** 的开源项目。

## 它是什么

两个专职 agent，共享一个 tape 审计底座（构建于 [bub](https://github.com/bubbuild/bub)）：

- **agent0 — 情报采集**：采集 / 预处理 / 结构化存储，为红队提供上下文相关的情报。全流程可观测、可复现。
- **agent1 — 自主红队**：把攻击当**优化问题**在运行时求解（attacker-LLM 生成 → judge-LLM 打分剪枝 → 读 tape 定下一向量），而非固定 SOP。能定时、定探针、主动泛化与难度升级，产出**发现报告 + 蓝队策略升级方案**。

## 为什么不一样

- **可复现 / 可审计**：每一轮 prompt / 响应 / 判定 / 理由 / 策略变更都是 append-only 的 tape 记录，整个 campaign 可回放。（业界正把 MLOps 引入红队，本项目的 tape 天然就是这套。）
- **自主，而非脚本**：运行时由策略动态决定下一步攻击向量，难度按 judge 反馈升档（直接请求 → 角色扮演 → 多轮 Crescendo → 变换叠加）。
- **专业标准映射**：发现映射 OWASP LLM Top 10 / MITRE ATLAS / NIST AI RMF（国内可叠 GB/T 45654）。
- **purple team 闭环**：`攻击 → 发现 → 蓝队打补丁 → 回归重测`，可接 schedule 做持续红队。

## 空弹匣声明（Responsible Use）

本仓只包含红队的**编排能力**：attacker/judge 回路、事件 taxonomy、报告框架、以及对 garak / PyRIT / promptfoo 的**适配器接口**。**本仓不含任何攻击载荷、种子或绕过话术**。
- 仅用于**对你自己拥有或获授权的**系统做防御性测试；启动强制登记授权范围。
- 具体攻击 skill（弹药）走单独的私有 / 授权制分发，不在本仓。

## 现状（诚实说明）

处于 Phase 0-2（见 `docs/roadmap.md`）：**契约 + 编排骨架已实现并有测试覆盖，真实攻击能力尚未接入**。

| Phase | 产物 | 状态 |
|---|---|---|
| 0 契约先行 | `spec/schema/{c1_tape,c2_events,c3_skill}.schema.json` | ✅ 57 测试全绿，零外部依赖 |
| 1 内核竖切面 | `agent0/dispatcher/` — bub 插件，tape→事件→turn | ✅ 已手动跑通到模型调用边界 |
| 2 红队 MVP | `agent1/orchestrator/` — Crescendo 回路 + 授权硬门 + garak 适配器 + 报告 | ✅ 骨架完成，`examples/` 有可跑的端到端 toy demo；**真实 attacker/judge 提示词是私有 skill，不在本仓** |

也就是说：`clone` 下来能装环境、能跑测试、能跑一个用完全抽象的玩具目标演示全链路的 demo，但**还不能直接拿它打真实目标**——那一步需要你自己的私有 skill（真实攻击方法论）和已授权的测试端点，这是刻意的架构边界（见下方"空弹匣声明"），不是没写完。

## 快速开始

需要 **Python ≥3.12**（真正的 [bub](https://github.com/bubbuild/bub) 硬性要求）和 [uv](https://docs.astral.sh/uv/)。
`pip install bub` 在更低版本下会**静默装到一个 2024 年之前、完全不相关的旧同名包**（无 pluggy/tape），排错前先确认这一点。

```bash
git clone https://github.com/lukethecat/sentinel-agents.git
cd sentinel-agents

# 隔离环境，不碰系统 Python
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python bub pytest
uv pip install --python .venv/bin/python -e agent0/dispatcher -e agent1/orchestrator

# 冒烟测试：跑通 register → 授权门 → Crescendo → finding → tape → 报告 全链路
# （用完全抽象的玩具目标站位真实攻击内容，见 agent1/orchestrator/examples/README.md）
.venv/bin/python agent1/orchestrator/examples/demo_run.py

# 单元测试
.venv/bin/python -m pytest spec/tests/ agent0/dispatcher/tests/ agent1/orchestrator/tests/ -v
```

各模块的详细说明、已知坑、下一步待办见各自 README：
[`spec/README.md`](spec/README.md) ·
[`agent0/dispatcher/README.md`](agent0/dispatcher/README.md) ·
[`agent1/orchestrator/README.md`](agent1/orchestrator/README.md)

## 文档

- 架构与契约：[`docs/architecture.md`](docs/architecture.md)
- 路线图：[`docs/roadmap.md`](docs/roadmap.md)
- 维护 / 上下文指引：[`CLAUDE.md`](CLAUDE.md)

## License & 致谢

Apache-2.0。构建于 bub（Apache-2.0）；设计哲学借鉴 pi（MIT）；上下文模型采用 tape.systems；红队能力包装 garak（Apache-2.0）/ PyRIT（MIT）/ promptfoo（MIT）。
