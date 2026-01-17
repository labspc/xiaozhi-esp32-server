# ORica 重构任务台账

> 用于跟踪各阶段任务、分支和状态。核心层任务默认仅内部维护；社区贡献仅限扩展层（插件/前端主题）。

| ID | Phase | 任务 | 分支 | 负责人 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P0-BASE | 0 基础设施 | CI 运行 lint/build，接入规范检查脚本（禁用闭包/泛型等）；监控脚手架 | feat/p0-ci-guardrails | Codex | 进行中 | `ci-guardrails.yml` 已添加初版 |
| P1-STORAGE | 1 存储迁移 | EloqKV 影子迁移 + 校验脚本（全量/增量/比对）；回滚脚本 | feat/p1-storage-eloqkv-migrate | 待指派 | 待启动 | 依赖：EloqKV 实例可用 |
| P2-RUST-WS | 2 Rust 迁移 | Axum WebSocket/HTTP 兼容旧路径 `/xiaozhi/*` + 新 `/orica/*`；PyO3 桥 | feat/p2-axum-ws-api | 待指派 | 待启动 | 依赖：P1 抽象；遵守 `AXUM_SIMPLE_GUIDE` |
| P3-MOJO | 3 性能 | Mojo Opus/PCM/VAD 批处理 + Python FFI 可回退 | feat/p3-mojo-audio | 待指派 | 待启动 | 依赖：P2 稳定接口 |
| P4-FE | 4 前端 | SvelteKit + shadcn-svelte 基架；认证/路由/国际化 MVP | feat/p4-svelte-mvp | 待指派 | 待启动 | 依赖：`v2orica` API 契约 |
| P5-API | 5 API 统一 | OpenAPI v2orica 契约冻结；SDK 生成（ts/python/rust）；文档发布 | feat/p5-openapi-sdk | 待指派 | 待启动 | 依赖：P2 接口定稿 |
| P6-E2E | 6 集成 | 端到端语音压测脚本；灰度/回滚脚本 | feat/p6-e2e-benchmark | 待指派 | 待启动 | 依赖：前置阶段完成 |
