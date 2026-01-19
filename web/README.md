# ORica Svelte 前端（预览）

> 遵循 `SVELTE_SIMPLE_GUIDE.md` 与 `SHADCN_SVELTE_CODING_GUIDE.md`：无复杂 stores/context/actions，组件含简洁日志。

## 目录
- `src/routes/+layout.svelte`：基础布局、主题色。
- `src/routes/+page.svelte`：首页占位卡片。
- `package.json`：SvelteKit 基础依赖（未安装，需联网）。

## 开发
```bash
cd web
npm install           # 需 Node 18+，联网
npm run dev -- --open
npm run build
```

## 备注
- 保持与旧 Vue 前端并行发布；可通过预览域验证后再切换。
- 后续任务：接入 shadcn-svelte 组件、登录/设备/Agent 页、API 客户端（对接 Phase2 OpenAPI）。
