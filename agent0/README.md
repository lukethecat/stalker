# agent0 — 情报采集专家

采集 / 预处理 / 结构化存储的 agent，为 agent1（红队）提供**上下文相关**的情报，也为 UI / Runtime 提供标准化数据源。

## IPO
Collect → Structure → Judge → Publish（结构化情报进 datapool）。

## 设计原则
- 全流程可观测（observable）、可复现（reproducible）
- 生命周期事件完整落 tape（`ingest.*` 命名空间）
- 是共享底座上的一个 skill 集，不是独立框架

> 通用采集能力的另一垂直应用（如日报 Aperture）保留在其各自仓库，不并入本仓，以免稀释红队定位。详见 `docs/architecture.md`。
