# Phase4 Svelte 重构状态

## 目标
- 搭建 SvelteKit + shadcn-svelte 基架，遵守 `SVELTE_SIMPLE_GUIDE.md` 与 `SHADCN_SVELTE_CODING_GUIDE.md`。
- 路由/布局/认证占位，后续对接 `v2orica` API（Phase2 输出）。
- 保持与旧 Vue 前端并行（预览域/双路径），可随时回滚。

## 分支
- 工作分支：`feat/p4-svelte-refactor`
- 集成目标：`orica-refactor`

## 当前进展
- 初始化 SvelteKit 骨架（未安装依赖）：`web/` 目录，基础路由/布局、简单日志。
- 首页、登录、设备列表占位（示例数据 + API stub `apiGet`），无复杂 store/context/actions。
- 约束内置：组件包含显式日志，样式为简洁暗色基调。

## 待办（优先级）
1) 安装依赖并验证 `npm run dev`/`npm run check`（需联网）。
2) 引入 UI 基础组件（shadcn-svelte 或自定义简化版），完善登录/侧边栏/设备/Agent 页面。
3) 封装真实 API 客户端（对接 Phase2 OpenAPI），打通登录 + 设备/Agent 数据。
4) 国际化/主题占位，准备预览域发布脚本。

## 运行提示
- 切到 `web/`：`npm install`（需 Node 18+，联网）。
- 本地开发：`npm run dev -- --open`
- 构建：`npm run build`

## 风险与回滚
- 网络限制可能阻塞依赖安装，需在可联网环境执行。
- 保持旧前端可用；Svelte 仅在新域/路径发布，遇故障可直接停用新前端。
