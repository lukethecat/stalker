# agent1-orchestrator

Phase 2 红队旗舰 MVP 的编排骨架：attacker/judge 双模型 Crescendo 回路 + 预算熔断 +
`redteam.target.registered` 授权门 + garak subprocess 适配器 + tape 落盘 + OWASP/ATLAS 报告。

## ⚠️ 空弹匣

本包只有**方法**，没有**载荷**（CLAUDE.md 铁律 4）：

- `policies.py` 只定义 `AttackerPolicy` / `JudgePolicy` / `TargetClient` 三个 `Protocol`，
  不含任何越狱提示词、种子或绕过话术。真实的 Crescendo/GOAT/TAP 提示词是私有 skill，运行时注入。
- 所有测试用的 attacker/judge 都是纯机械的哑桩（比如"响应里有没有 `REFUSED` 关键词"），
  不构成任何攻击方法论。

## 模块

| 模块 | 职责 | 依赖 bub？ |
|---|---|---|
| `policies.py` | Attacker/Judge/Target 的 Protocol 定义 | 否 |
| `budget.py` | 预算熔断（轮数/成本/时间） | 否 |
| `crescendo.py` | 回合循环：attacker → target → judge，读预算熔断，`on_round` 回调 | 否 |
| `authorization.py` | 授权门：扫 C2 事件找未过期的 `redteam.target.registered`，无授权 `raise` | 否 |
| `runner.py` | `run_authorized_crescendo`：授权门 + crescendo 的唯一推荐入口 | 否 |
| `garak_adapter.py` | subprocess 安全调用 garak（argv list，非 shell）+ JSONL 结果解析 | 否 |
| `tape_bridge.py` | 把回合/finding 转成 C2 事件、按 `spec/schema/c2_events.schema.json` 校验、写入 bub tape | 是（懒加载） |
| `report.py` | 从 finding 列表聚合出 OWASP 分组 + Markdown 报告 | 否 |

除 `tape_bridge.py` 外全部框架无关——按 `docs/architecture.md` 的 "operator equivalence"，
agent1 的方法不应该绑死某一个 kernel 实现。

## 授权门是硬门，不是建议

```python
from agent1_orchestrator.runner import run_authorized_crescendo
from agent1_orchestrator.authorization import NotAuthorized

try:
    result = run_authorized_crescendo(
        events=events_read_from_tape,   # 之前落过的 C2 事件
        target_id="demo-target",
        probe_id="probe-1",
        attacker=my_attacker,           # 私有 skill 提供
        judge=my_judge,                 # 私有 skill 提供
        target=my_target_client,
        expected_behavior="...",
        rubric={...},
        budget=Budget(max_rounds=8, max_cost_usd=5.0),
    )
except NotAuthorized:
    ...  # target_id 没有未过期的 redteam.target.registered，一轮都不会跑
```

`run_authorized_crescendo` 在跑第一轮之前就检查授权——测试
（`tests/test_runner.py::test_does_not_run_attacker_when_unauthorized`）验证了未授权时
attacker 一次都不会被调用，不是"跑完再报错"。

## 测试

```bash
python3 -m pytest agent1/orchestrator/tests/ -v          # 39 项里 tape_bridge 相关会 skip（无 bub）
.venv/bin/python -m pytest agent1/orchestrator/tests/ -v # 全量 39 项，含 tape_bridge + 与 agent0-ipo-dispatcher 的互操作校验
```

## 还没做的（Phase 2 剩余）

- 真实 attacker/judge 策略（私有 skill，不进本仓）。
- garak 真实调用的一次手动验证（本仓开发环境没装 garak，也没有已授权的测试端点）。
- CLI 入口（`bub run` 风格，把 `run_authorized_crescendo` 接到 agent0-ipo-dispatcher 的
  `redteam.target.registered` 触发链路上，实现"注册目标 → 自动起 probe"）。
