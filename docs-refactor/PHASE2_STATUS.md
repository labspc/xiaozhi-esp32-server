# Phase2 Axum + PyO3 进度追踪

## 当前完成
- 路由：REST（devices/agents/config）、WS `/xiaozhi/v1/` `/orica/v1/`。
- 存储：读取 EloqKV（redis 兼容），key 可通过 env 配置。
- WS 处理：PyO3 调用 `py_ai_handler`，文本/二进制协议已约定（content/error/data），返回 JSON 包含 content 或 error。
- Python Handler：示例逻辑（文本模拟回复，二进制回传或错误），协议清晰，可替换为真实 AI。
- 认证：JWT HS256 占位（`JWT_SECRET`，默认 dummy，1h），AUTH_TOKEN fallback；OpenAPI 含 bearer 与 401。
- OpenAPI：stub + baseline，CI guardrails 已启用生成+diff。
- CI/构建：Axum+Redis+PyO3 编译通过。

## 未完成/待收口
- AI 逻辑：替换 `py_ai_handler` 示例为真实 LLM/ASR/TTS 调用，定义音频 meta/格式约定与错误处理。
- 认证：用真实密钥管理/过期/刷新替代占位；OpenAPI 增加 401/403 示例与错误 schema。
- OpenAPI：丰富 schema/示例，确保与最终协议一致（content/error/data）。
- 迁移 Phase（依赖上游）：仍需 Phase1 收口（EloqKV 迁移增量/校验），但不阻塞 Phase2 编码。

## 可继续开发？
- 是。Phase2 原型可继续迭代：接入真实 AI handler、完善 JWT、完善 OpenAPI。
- 推送后 CI 会跑 OpenAPI diff；需确保 baseline 同步更新。

## 建议下一步
1) 设计并实现真实 `py_ai_handler` 协议（文本/音频）与错误返回，替换模拟逻辑。
2) 完善 JWT（真实密钥/过期/刷新）并同步 OpenAPI 401/403 示例。
3) 推送分支，验证 CI guardrails（OpenAPI diff）。
