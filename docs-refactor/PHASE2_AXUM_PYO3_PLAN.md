# Phase 2 原型计划（Axum + PyO3）

目标：替换 Java/ Python 网络层，提供兼容 `/xiaozhi/*` 与新 `/orica/*`，最小化 API 集与 WebSocket 入口，嵌入 Python AI 逻辑。

## 路由与协议
- WebSocket：`/xiaozhi/v1/`（兼容）与 `/orica/v1/` → 同一处理器。
- REST 最小集：
  - `POST /api/auth/login`（JWT）
  - `GET /api/devices`、`GET/PUT /api/devices/:mac`
  - `GET /api/agents`、`GET/PUT /api/agents/:id`
  - `GET /api/config`（xiaozhi-server 配置拉取）
- 版本：`v1legacy`（兼容输出） + `v2orica`（新字段）。

## 状态与存储
- 依赖 EloqKV 存储抽象（Key 规范参照 `ELOQKV_KEYS.md`）。
- JWT 秘钥/配置从 env 或 EloqKV 读取。

## 代码规范
- 遵守 `AXUM_SIMPLE_GUIDE.md` 与 `RUST_SIMPLE_GUIDE.md`：无复杂提取器、中间件、泛型、闭包、unsafe。
- Python 嵌入：PyO3 调用 Python AI 逻辑（仅处理请求，不承载网络 I/O）。

## 任务清单（建议分支 `feat/p2-axum-ws-api`）
1) 创建 Axum 服务骨架：日志、CORS、JWT 校验占位。
2) WebSocket 处理器：接入 PyO3 调用，兼容路径。
3) REST Handler：设备/Agent/配置/登录最小实现，读取 EloqKV。
4) 配置：env + EloqKV 地址/秘钥；OpenAPI 契约草案。
5) 验证：旧前端/固件连通；基础性能基线。

## 开放问题
- PyO3 与 Python 环境打包方式；错误处理与回退。
- JWT 策略与密钥轮换。
