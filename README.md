<!-- 语言 / Language: 中文 -->

# stalker — 红蓝攻防作战室（war room）

**建在 DeepSeek Harness (dsh) 上的可审计红队 / AI 合规垂直产品。**

对外是**红队垂直产品**（指挥 / 编排 / 可视化 / 留痕 / 出报告 / 驱动蓝队闭环）；
对内是**运行时中立的契约层**（C1 tape / C2 事件 / C3 skill 包）。

> **垂直的脸，平台的骨。**
> 业内现有的是**红队工具/库**（garak / PyRIT / promptfoo）或**闭源商业平台**；
> stalker 补的是中间空白：一个**可 GitHub 安装、以可审计留痕为底座、把情报与红队编排成作战室**的开源项目。

## 形态：dsh 插件 / bundle（"混合 B"）

- **运行时与分发**：骑在 dsh 上（session log = tape、skill = C3、事件 = C2，架构天然趋同）。
  白嫖其沙箱 / MCP / subagent / provider / session-log 基建。
- **契约层**：C1/C2/C3 保持**运行时中立**（见 `spec/`）——既是 IP，也是"若 dsh 破坏性变更就能撤"的可移植保险。
- **主体**：agent1（红队即优化：attacker-LLM 生成 → judge-LLM 打分剪枝 → 读日志定下一向量）；
  agent0（情报）降为 recon 阶段 / 薄适配器，采集复用现成插件，不自造引擎。
- **工具三件套是 tool 不是本体**：garak（广度基线）→ PyRIT（多轮深挖）→ promptfoo（CI/CD 回归）。

## 仓库结构

```
spec/      # Phase 0 契约层（C1/C2/C3 JSON Schema + 一致性测试）—— 本体，运行时中立
plugins/   # dsh 插件清单与 bundle 组装（各插件独立成仓，dsh-plugin 生态惯例）
docs/      # 架构与路线图（公开浓缩版；详尽决策记录在维护者私有规划库）
```

## 空弹匣声明（Responsible Use）

本仓只包含红队的**编排能力**与**契约**：**不含任何攻击载荷、种子或绕过话术**（弹药是私有授权制 skill）。
两条硬不变量已编码进 `spec/schema/` 并由一致性测试强制：

1. **授权门**：`redteam.target.registered` 必须携带授权范围，无授权不启动；
2. **空弹匣边界**：含攻击载荷的 skill 强制 `visibility: private` 且需授权。

仅用于**对你自己拥有或获授权的系统**做防御性测试。发现映射 OWASP LLM Top 10 / MITRE ATLAS /
NIST AI RMF，国内叠加 GB/T 45654。

## 现状（诚实说明）

| Phase | 产物 | 状态 |
|---|---|---|
| 0 契约先行 | `spec/`：4 schema + 参考校验器 + 一致性测试 | ✅ 26 测试全绿，零外部依赖 |
| 1 第一个 dsh 插件 | [`lukethecat/dsh-plugin-warroom-garak`](https://github.com/lukethecat/dsh-plugin-warroom-garak)：授权门 + 预算 + garak 基线扫描 + 证据报告 | ✅ 已发布、已挂载进本机 dsh、可调用 |
| 2 最小竖切面 | `garak_scan` 打授权端点 → 从 session log 派生一页证据报告 | 🔄 进行中 |
| 3 红队优化回路 | attacker/judge 插件（先 Crescendo + 预算熔断 + `redteam.strategy.adjusted`） | ⏳ 规划 |
| 4 区域包 + recon | cn/eu 合规包做成 dsh bundle/profile；agent0 recon 接现成采集插件 | ⏳ 规划 |
| 5 私有弹药 | 攻击/舆情/题库 skill，授权制分发 | ⏳ 规划 |

详见 `docs/roadmap.md`。

## 快速开始

```bash
# 契约层测试（零外部依赖，无需 dsh / API key）
cd spec && pip install jsonschema pytest && pytest -q

# 作战室用法：安装 dsh 后，把 dsh-plugin-warroom-garak 挂进 profile（见该插件 README），
# 然后在 dsh 会话里对授权目标调用 garak_scan 工具。
```

## 文档

- 架构与契约：[`docs/architecture.md`](docs/architecture.md)
- 路线图：[`docs/roadmap.md`](docs/roadmap.md)
- 上下文锚点：[`AGENTS.md`](AGENTS.md)（dsh 会话自动加载）

## License & 致谢

Apache-2.0。运行于 dsh / Cordis（MIT）；红队能力包装 garak（Apache-2.0）/ PyRIT（MIT）/
promptfoo（MIT）；契约模型借鉴 tape.systems。
