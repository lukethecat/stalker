# spec — 三份契约 (C1 / C2 / C3)

契约是本项目的**本体**;内核与插件都是其可替换实现。本目录含可机读的 JSON Schema、一份参考校验器,以及一致性测试。

## 内容
```
schema/
  c1_tape.schema.json    # C1 tape entry（event/anchor/…，append-only，supersede 修正）
  c1_view.schema.json    # C1 view 查询（按需组装上下文窗口）
  c2_events.schema.json  # C2 事件（ingest.* / redteam.*；含授权门等硬不变量）
  c3_skill.schema.json   # C3 skill 包（Agent Skills + L0-L3 + 事件订阅 + 公开/私有边界）
sentinel_spec/
  conformance.py         # 参考校验器：load/validate、tape 读写、view 组装、跨版本兼容
examples/                # 可校验的示例实例（tape / skill / view）
tests/                   # pytest 一致性测试
```

## 编码进 schema 的两条关键不变量
- **授权门**：`redteam.target.registered` 的 `authorization.authorized` 必须为 `true` 且带 `scope`,否则不合法——无授权不可登记目标。
- **空弹匣边界**：C3 中 `contains_attack_payloads: true` 的 skill 强制 `visibility: private` 且 `authorization_required: true`——弹药不得公开。

## 跑测试
```bash
cd spec
pip install -e ".[test]"     # 或: pip install jsonschema pytest
pytest -q
```

## 覆盖的一致性检查
- 四个 schema 自身合法（Draft 2020-12）
- 示例 tape 全部 entry 合法;JSONL 读写 roundtrip 幂等;id 唯一;supersede 指向已存在的更早 entry
- anchor 必带 state contract（phase/summary/next_steps/source_ids）
- view 组装正确丢弃被 supersede 的 entry、按 kind 与事件名过滤
- C2 授权门负测试（未授权/缺授权即失败）、事件命名空间约束、finding 必须映射标准 taxonomy、metric ASR 值域
- C3 公开/私有边界负测试（公开仓不得含弹药）、L0 必需、挂载点枚举
- 跨版本：同 major 可读,未来 patch 版本 entry 仍可校验
