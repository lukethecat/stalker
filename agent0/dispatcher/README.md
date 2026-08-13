# agent0-ipo-dispatcher

Phase 1 内核竖切面：一个 [bub](https://github.com/bubbuild/bub) 插件，监听 tape 上新出现的
`event` 类型 entry，把匹配 C2 命名空间订阅的 entry 转成一次 bub turn。验证的是
`tape → 事件 → turn` 这条链路能不能闭环，不是完整红队回路。

## 依赖与环境

真正的 bub（pluggy hook-first 架构，见 `docs/architecture.md`）要求 **Python ≥3.12**。
`pip install bub` 在 Python <3.12 环境下会静默装到一个 2024 年之前、完全不同的旧包
（无 pluggy、无 tape）——如果 `bub hooks` 看不到 `provide_channels: builtin, agent0_ipo_dispatcher`
这一行，先检查 Python 版本。

本仓用 [uv](https://docs.astral.sh/uv/) 在仓库内建隔离虚拟环境，不碰系统 Python：

```bash
uv venv --python 3.13 .venv          # 或任何 >=3.12 的解释器
uv pip install --python .venv/bin/python bub
uv pip install --python .venv/bin/python -e agent0/dispatcher
```

验证插件被 bub 发现（通过 `[project.entry-points.bub]`）：

```bash
.venv/bin/bub hooks | grep provide_channels
# provide_channels: builtin, agent0_ipo_dispatcher
```

## 它做什么

- `TapeDispatchChannel`（一个 bub `Lifecycle` channel）每秒轮询当前 tape（默认 tape 名 `main`）里
  `kind == "event"` 的新 entry。
- entry 的 `payload["name"]` 如果匹配任意已发现 skill 声明的订阅 pattern（`fnmatch` 风格，如
  `redteam.*`），就把这条 entry 包成一个 `ChannelMessage` 送进 bub 的正常 turn pipeline
  （`resolve_session → build_prompt → run_model → ...`）。
- 已处理过的 entry id 不会重复触发（每次 tick 只看 `id > last_seen_id` 的新 entry）。

## Skill 怎么声明订阅

bub 的 SKILL.md frontmatter 里 `metadata` 字段只能是 `dict[str, str]`（见
`bub.skills._is_valid_metadata_field`），所以订阅列表用逗号分隔的字符串声明——这是
`spec/schema/c3_skill.schema.json` 里 `subscribes`（JSON 字符串数组）在 bub 具体运行时下的
落地编码，不是两套不同的契约：

```markdown
---
name: probe-builder
description: ...
metadata:
  subscribes: "redteam.target.registered,redteam.intel.ingested"
---
```

## 跑通闭环（需要一个模型 provider key）

```bash
export BUB_HOME=/path/to/isolated/home     # 避免污染 ~/.bub
export OPENROUTER_API_KEY=...              # 或 BUB_PROVIDER/BUB_MODEL_NAME 指定的其他 provider
cd your-workspace                          # 需要 .agents/skills/*/SKILL.md 声明了 subscribes
.venv/bin/bub gateway --enable-channel agent0-ipo-dispatcher
```

另开一个终端，往同一个 `BUB_HOME` 下的 tape 追加一条 C2 事件：

```python
from bub.builtin.store import FileTapeStore
from bub.tape import TapeEntry
import pathlib

store = FileTapeStore(directory=pathlib.Path("/path/to/isolated/home/tapes"))
store.append("main", TapeEntry.event(
    "redteam.target.registered",
    {"target": {"id": "demo"}, "authorization": {"scope": ["POST /demo"], "authorized_by": "you"}},
))
```

gateway 的日志应该在 ~1 秒内出现一次 `loop.step` / `session.run.outbound`，证明 dispatcher
已经把事件转成了 turn 并送进了模型调用——这就是 Phase 1 要验证的闭环。本仓 CI /
开发环境没有配置任何模型 key，所以这一步无法自动化验证，需要在本机手动跑一次。

## 测试

```bash
.venv/bin/python -m pytest agent0/dispatcher/tests/ -v
```

纯离线：用 bub 的 `InMemoryTapeStore` + 假 framework 验证匹配/去重/无订阅/无 tape store
这几种情况，不需要模型 key。
