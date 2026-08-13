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

## 快速开始（WIP）

```bash
# 底座
pip install bub            # 或 uv tool install bub
# 配置模型 provider（litellm 兼容）与 Home 目录，详见 docs/
bub gateway --home .       # 起服务后，直接在 bub 的 CLI/channel 里对话
```
> 部署与"另一台机器 clone 即运行"的完整步骤见 `docs/`（随 Phase 推进补全）。

## 文档

- 架构与契约：[`docs/architecture.md`](docs/architecture.md)
- 路线图：[`docs/roadmap.md`](docs/roadmap.md)
- 维护 / 上下文指引：[`CLAUDE.md`](CLAUDE.md)

## License & 致谢

Apache-2.0。构建于 bub（Apache-2.0）；设计哲学借鉴 pi（MIT）；上下文模型采用 tape.systems；红队能力包装 garak（Apache-2.0）/ PyRIT（MIT）/ promptfoo（MIT）。
