# ORica 重构增强版 SOP（含并行协作与分支策略）

> 适用范围：基于 `docs-refactor` 全部文档的综合方案，支持多 Codex/多人并行协作与可追踪交付。

## 0. 总原则
- 目标：演进为 ORica 五层架构（Rust 基础设施 / Python AI 逻辑 / Mojo 性能层 / Svelte 前端 / 用户扩展层）。
- 优先级：存储统一 > 基础网络与 API 迁移 > 性能与前端迭代 > 统一规范与测试。
- 可追踪性：每个子任务独立分支 + PR + 可复现的脚本/验收清单。

## 1. 分支与协作策略（多 Codex/多人并行）
- 主干：`main` 保持可发布；建立长期集成分支 `orica-refactor`（汇总各 PR）。
- 工作分支命名：`feat/{phase}-{scope}-{short-desc}`，例如 `feat/p1-storage-eloqkv-migrate`。
- 并行规则：不同子域互不改文件夹或提前约定文件锁（如 `main/xiaozhi-server/core/*`）。
- 每个分支至少 1 次小步提交，消息使用 `<type>(scope): <action>`（如 `feat(storage): add eloqkv adapter`）。
- PR 模板：背景/变更/测试/回滚方式/风险；要求最小可评审增量。
- 任务登记：在 `docs-refactor/TASKS.md`（可新增）记录负责人、分支、预计完成时间、阻塞项。

## 2. Phase 概览（与原 SOP 对齐，补充责任与并行策略）
- Phase 0 基础设施：环境、CI、监控。并行启动后续评估，但禁止合入核心改动前未通过基础检查。
- Phase 1 存储（P0）：EloqKV 部署、数据模型映射、迁移脚本与校验。其他 Phase 以只读方式依赖迁移前旧库。
- Phase 2 Rust 迁移（P1）：Java manager-api + Python WebSocket/HTTP 网络层 → Rust Axum；保持 `/xiaozhi/*` 兼容并暴露 `/orica/*`。
- Phase 3 Mojo 性能（P1）：Opus/PCM/VAD 批处理加速，PyO3/ctypes FFI 接入 Python；不改网络协议。
- Phase 4 前端（P2）：Vue2 → Svelte（shadcn-svelte），API 以 Phase2 OpenAPI 规范为准，双路径兼容。
- Phase 5 API 统一（P1）：OpenAPI 契约、SDK 生成、版本标识（`v1legacy`/`v2orica`），文档与回滚预案。
- Phase 6 集成测试与灰度（P0）：端到端语音链路、并发、资源、回滚脚本。

## 3. 详细执行指南（入/出条件）
- Phase 0
  - 入：确认工具链 (Rust, Mojo, Python3.10, Node20, Docker)；CI 能跑 lint+build。
  - 出：基础镜像/工具缓存可用；监控栈可接入。
- Phase 1
  - 入：EloqKV 实例可连接；数据模型（用户/设备/agent/配置/会话）Key 设计确定。
  - 任务：迁移脚本（全量 + 增量/校验）、热/冷分层（EloqKV + OSS），影子读验证。
  - 出：校验报告（行数、哈希、一致性）；回滚脚本；旧库只读旗标。
- Phase 2
  - 入：EloqKV 抽象可用；OpenAPI 草案；兼容层策略确认。
  - 任务：Axum WebSocket/HTTP 服务（遵循 `AXUM_SIMPLE_GUIDE`），PyO3 桥，JWT 中间件，设备/配置 API，路径兼容 `/xiaozhi` + `/orica`。
  - 出：替换 Java 部署脚本；兼容验证（旧前端/固件连通）；性能基线报告。
- Phase 3
  - 入：Python AI 流程稳定；FFI 接口定义。
  - 任务：Mojo 模块（Opus 解码/编码、PCM 转换、VAD 特征），批处理接口；Python 侧切换点可配置回退。
  - 出：性能对比（P50/P90/P99）、失败回退开关；CI 增加 FFI 冒烟。
- Phase 4
  - 入：稳定的 `v2orica` API；UI 组件映射表。
  - 任务：SvelteKit + shadcn-svelte 架子、认证/路由/国际化、关键页面逐步替换；保持旧 Vue 线上，Svelte 走预览域。
  - 出：主要功能（登录、设备、智能体、模型、OTA、音色）可用；回滚指令。
- Phase 5
  - 入：Rust API 就绪；前后端联调。
  - 任务：OpenAPI 生成 SDK（ts/python/rust），版本策略，弃用计划；文档自动发布。
  - 出：契约冻结；客户端升级指引。
- Phase 6
  - 入：全链路可跑。
  - 任务：端到端语音压测脚本（延迟/并发/资源/错误率）、灰度开关、回滚脚本。
  - 出：上线 checklist；监控 SLO。

## 4. API 与兼容策略
- 双路径：`/xiaozhi/*`（legacy，不拆固件/旧前端），`/orica/*`（新路径）；WebSocket `/xiaozhi/v1/` 与 `/orica/v1/` 同路由处理。
- OpenAPI 版本：`v1legacy`（只做兼容补丁，不加新字段），`v2orica`（新特性）；响应码与错误体统一。
- 变更要求：添加字段保持向后兼容；破坏性变更需版本前缀 + 迁移文档 + 回滚开关。

## 5. 数据与存储
- EloqKV Key 规范：`user:{id}`，`device:{mac}`，`agent:{id}`，`session:{token}`，`chat:{device}:{date}`；索引 Key 显式列出。
- 热/冷数据：热数据存 EloqKV；冷数据归档 OSS（JSON/Parquet + 压缩）。提供归档/回补脚本。
- 校验：迁移后对比行数、字段哈希、抽样业务查询；提供双写/比对阶段。

## 6. 质量与度量
- 基准：端到端语音延迟（VAD/ASR/LLM/TTS/总时延 P50/P90/P99）、WebSocket 并发、CPU/内存、错误率。
- 阶段验收：每 Phase 出具基线与对比；Mojo/Rust 需附带回退方案。
- 测试矩阵：旧前端 + 新后端；新前端 + 新后端；固件旧路径与新路径。

## 7. 自动化与脚本
- 推荐脚本目录：`scripts/`（迁移、基准、回滚、发布）。
- CI：lint/build/test + FFI 冒烟 + OpenAPI 生成校验；PR 必跑。
- 发布：Rust 二进制、Svelte 产物、Python 依赖锁，版本号与变更记录。

## 8. 并行开发示例（可直接使用）
1) 创建任务记录：在 `docs-refactor/TASKS.md` 登记。
2) 新建分支：`git checkout -b feat/p1-storage-eloqkv-migrate`.
3) 开发与小步提交：
   - `feat(storage): add eloqkv adapter`
   - `chore(scripts): add migrate validator`
4) PR 目标 `orica-refactor`，模板填写测试和回滚。
5) 定期同步：`git fetch origin && git rebase origin/orica-refactor`。
6) 合并后更新 TASKS 状态，删除分支。

## 9. 风险与回滚
- 高风险：协议路径、存储迁移、认证逻辑；必须有开关或回退脚本。
- 回滚预案：存储保留旧库只读；Rust 服务可蓝绿切换；Mojo 可配置回退到 Python 实现；前端可双域切换。

## 10. 当前建议的优先落地序列
1) 建立 `orica-refactor` 分支与 TASKS 台账，补齐 CI 基础任务。
2) 完成 EloqKV 影子迁移与校验脚本；冻结旧库写入计划。
3) Axum + PyO3 原型跑通旧路径兼容；完成最小 API 集。
4) Mojo Opus/PCM/VAD 批处理替换验证，保留回退开关。
5) OpenAPI 契约冻结 `v2orica`，启动 Svelte MVP 与 SDK 生成。
6) 端到端压测 + 灰度上线。

## 11. 编码规范与贡献边界（务必遵守）
- 规范引用：`RUST_SIMPLE_GUIDE.md`、`AXUM_SIMPLE_GUIDE.md`、`SVELTE_SIMPLE_GUIDE.md`、`SHADCN_SVELTE_CODING_GUIDE.md`、`PYTHON_MOJO_HYBRID_STRATEGY.md`、`AI_FRIENDLY_CODING_GUIDE.md`。
- 核心层（锁定，仅内部维护）：Rust 基础设施、Mojo 加速模块、Python Provider/对话/记忆核心框架。禁止外部贡献者改动，PR 默认拒绝，需内部审批。
- 扩展层（开放）：Python 插件与自定义 Provider 实现、Svelte 主题/页面扩展。社区贡献限制在此层。
- 强制 CI 检查（建议落地）：检测禁止特性（Rust 闭包/泛型/unsafe/复杂迭代器；Axum 复杂提取器/中间件；Svelte context/actions/复杂 stores；Mojo 非显式类型；Python 过度反射），不符合即拒绝。
- 代码生成要求：所有自动生成代码需遵守各语言简化规范，保持显式类型、简单流程、可读日志。

## 12. 文档与执行纪律
- 本 SOP 为开发主参照，迭代须 PR 审核；重大调整需在文件顶部注明版本与日期。
- 开发前复核相关指南；实现时引用对应章节，避免自创模式。
- TASKS 台账记录每项是否符合规范、是否触及核心层；对外贡献者仅可在扩展层登记任务。

## 13. 近期行动清单（Phase0/Phase1）
- Phase0 立即动作：
  - 在 CI/Actions 中接入 `CI_GUARDRAILS.md` 指定的必跑检查（lint/build/禁用特性扫描）。
  - 准备基础镜像/缓存（Rust/Node/Python/Mojo）；监控栈占位。
  - 确认 `orica-refactor` 为集成分支，所有 PR 先合入此分支。
- Phase1 立即动作：
  - 落实 EloqKV 实例可用性与访问配置；编写数据模型 Key 列表（用户/设备/agent/会话/聊天）。
  - 起草迁移与校验脚本框架（全量 + 增量 + 校验），定义回滚命令。
  - 在 TASKS 中分配负责人与时间点，准备影子读对照测试。
