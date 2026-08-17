# plugins — 作战室 dsh 插件清单

插件按 dsh 生态惯例**独立成仓**（`dsh-plugin-*`），本目录是清单与 bundle 组装说明。

## 已有

| 插件 | 仓 | 状态 |
|------|----|------|
| `dsh-plugin-warroom-garak` | [lukethecat/dsh-plugin-warroom-garak](https://github.com/lukethecat/dsh-plugin-warroom-garak) | ✅ v0 已发布。`garak_scan` 工具：授权门 + 预算 + garak 基线扫描 + 证据报告。本机 dsh profile `web` 已挂载。 |
| `dsh-plugin-warroom-redloop` | [lukethecat/dsh-plugin-warroom-redloop](https://github.com/lukethecat/dsh-plugin-warroom-redloop) | ✅ v0 已发布。`redloop_attack` 工具：attacker/judge Crescendo 回路 + 预算熔断 + C2 事件 + 证据报告（空弹匣）。本机 dsh profile `web` 已挂载。 |

## 规划

| 插件（暂名） | 职责 | 对应 Phase |
|------|------|-----------|
| `dsh-plugin-warroom-evidence` | 从 session log 派生一页证据报告（现由 `scripts/derive-evidence.mjs` 承担） | Phase 2 |
| ~~`dsh-plugin-warroom-redloop`~~ | ✅ 已发布：attacker/judge 优化回路（Crescendo + 预算熔断 + `redteam.strategy.adjusted`） | Phase 3 |
| `dsh-bundle-warroom-cn` / `-eu` | 区域合规包（GB/T 45654 / EU AI Act），bundle/profile 形态 | Phase 4 |
| `dsh-plugin-warroom-pyrit` | PyRIT subprocess/sidecar 桥 | Phase 4 |
| 私有弹药插件（不进公开索引） | 攻击 / 舆情 / 题库 skill，授权制分发 | Phase 5 |

## 组装约定

- 所有插件注册领域事件用 C2 `redteam.*` 命名空间，payload 对齐 `spec/schema/c2_events.schema.json`。
- 公开插件 = 空弹匣（无载荷/种子/话术）；弹药只在私有插件。
- 依赖 dsh/Cordis 不 fork；dsh 版本锁在本机 profile 的实际版本，破坏性变更时对齐。
