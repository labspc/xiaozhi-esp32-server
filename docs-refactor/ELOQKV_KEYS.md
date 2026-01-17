# EloqKV Key 设计（草案）

> Phase1 迁移用：列出核心业务数据的 Key 形态，作为迁移脚本与查询适配的依据。

## 热数据（KV）
- 用户：`user:{id}` → Hash `{id, username, password_hash, email, created_at, updated_at}`
- 设备：`device:{mac}` → Hash `{mac, user_id, agent_id, last_seen, firmware_version, board, alias}`
- Agent 配置：`agent:{id}` → Hash `{id, name, asr_config, tts_config, llm_config, vad_config}`
- Session/Token：`session:{token}` → Hash `{user_id, token, expire_at, created_at}`
- 在线设备集合：`online:devices` → Set `{mac}`
- 模型配置：`model:{type}:{name}` → Hash `{type, name, config}`

## 热数据索引（辅助 Key）
- 用户名索引：`user:username:{username}` → String `{id}`
- 设备用户索引：`device:user:{user_id}` → Set `{mac}`
- Agent 名称索引：`agent:name:{name}` → String `{id}`

## 聊天/日志（分片）
- 当日聊天：`chat:{device}:{YYYYMMDD}` → List `[ {timestamp, role, content, meta} ]`
- 归档清单：`chat:archive:index:{device}` → SortedSet `{score=date, member=archive_key}`

## 冷数据（归档到 OSS）
- 归档路径建议：`archive/{year}-{month}/device-{mac}.json.gz` 或 `parquet` 等压缩格式。

## 配置/缓存
- 全局配置缓存：`config:global` → String/Hash
- 字典/枚举类：`dict:{category}` → Hash/Set

## 迁移/校验提示
- 全量迁移后运行：行数校验、字段哈希校验、抽样业务查询对比。
- 双写/影子读阶段：确保写入 EloqKV 同时比对 MySQL/Redis 结果。
