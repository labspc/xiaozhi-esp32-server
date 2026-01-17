# CI Guardrails（简化版落地指南）

> 目的：在各语言层面阻止不符合简化规范的提交，确保核心层稳定、扩展层可控。

## 必跑检查（建议接入 GitHub Actions/GitLab CI）
- `git status --porcelain` 确认无意外文件（防止覆盖用户未跟踪修改）。
- Lint/Build：
  - Python：`python -m py_compile` 入口/核心模块；可选 `ruff`/`flake8`（禁用复杂反射/魔术）。
  - Rust：`cargo fmt --check && cargo check`（遵守 `RUST_SIMPLE_GUIDE`；可加自定义 deny 列表禁闭包/泛型/unsafe）。
  - Svelte：`npm run lint`（或 `svelte-check`）；禁用 context/actions/复杂 stores。
  - Mojo：格式检查与显式类型审查（当前手工）；FFI 冒烟用最小音频样本。
- OpenAPI 合规：生成与仓库中的契约 diff，禁止未注册版本的破坏性变更。

## 禁止特性（自动化规则示例）
- Rust：`deny(unsafe_code)`；禁止闭包/泛型/复杂迭代器（自定义 lint 或正则扫描 `|`、`impl Trait`、`<T>`）；禁止 tower 中间件、复杂 Axum 提取器。
- Svelte：扫描 `setContext/getContext`、`use:` actions、`derived`/复杂 store 链。
- Mojo：要求显式类型；拒绝无类型推断或隐式转换；FFI 需批处理接口。
- Python：禁止过度反射（`getattr`/`setattr`/`eval` 扫描）；鼓励显式类型注解；插件层可灵活，但需隔离。

## 入/出条件挂钩
- Phase0 出口：CI guardrails 在主分支与 `orica-refactor` 分支必跑且为必需检查。
- 其他 Phase PR：必须通过 guardrails；对核心层改动需内部 reviewer。

## 回退与例外
- CI 宕机时：禁止合并核心层改动；可通过两名核心维护者书面确认的例外流程。
- 如需临时放宽规则，必须在 PR 说明并在合并后 24h 内恢复默认。
