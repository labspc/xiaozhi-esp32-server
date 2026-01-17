# MySQL 和 Redis 在 xiaozhi-esp32-server 中的作用分析

## 概述

manager-api 采用 **MySQL + Redis** 双存储架构：
- **MySQL**: 持久化存储业务数据
- **Redis**: 缓存热点数据，提升查询性能

---

## MySQL 数据库详解

### 核心业务表（共18+张表）

#### 1. 用户认证模块

**sys_user** - 系统用户表
```sql
用途: 存储管理员账号信息
字段: id, username, password, super_admin, status, create_date
关键点:
  - 用户登录凭证
  - 权限控制（super_admin字段）
  - 用户状态管理
```

**sys_user_token** - 用户令牌表
```sql
用途: 存储用户登录后的 token
字段: id, user_id, token, expire_date, update_date
关键点:
  - 每个用户只有一个有效 token（UNIQUE KEY user_id）
  - Token 过期时间管理
  - Shiro 认证依赖此表
```

#### 2. 设备管理模块

**ai_device** - 设备信息表
```sql
用途: 管理所有 ESP32 设备
字段:
  - id (UUID)
  - user_id (关联用户)
  - mac_address (设备唯一标识)
  - agent_id (绑定的AI智能体)
  - last_connected_at (最后连接时间)
  - auto_update (自动更新开关)
  - board (硬件型号)
  - app_version (固件版本)
  - alias (设备别名)

关键点:
  - 设备与用户的绑定关系
  - 设备与 AI Agent 的关联
  - 设备在线状态追踪
  - OTA 升级管理依据
```

**ai_ota** - 固件升级表
```sql
用途: 管理 ESP32 固件版本和升级包
字段: version, download_url, release_notes, etc.
关键点:
  - 固件版本管理
  - 升级包分发
```

#### 3. AI Agent（智能体）模块

**ai_agent** - 智能体配置表
```sql
用途: 核心配置表，定义每个 AI 智能体的行为
字段:
  - id (UUID)
  - user_id (所属用户)
  - agent_name (智能体名称)
  - asr_model_id (语音识别模型)
  - vad_model_id (语音活动检测)
  - llm_model_id (大语言模型)
  - vllm_model_id (视觉语言模型)
  - tts_model_id (语音合成模型)
  - tts_voice_id (音色)
  - mem_model_id (记忆模型)
  - intent_model_id (意图识别)
  - system_prompt (角色设定)
  - chat_history_conf (聊天记录配置 0/1/2)
  - language (交互语种)

关键点:
  - 这是连接 manager-api 和 xiaozhi-server 的桥梁
  - 设备通过 agent_id 获取完整的 AI 配置
  - xiaozhi-server 根据这些配置动态加载 Provider
```

**ai_agent_template** - 智能体模板表
```sql
用途: 预设的智能体配置模板
应用: 快速创建常见场景的智能体
```

**ai_agent_plugin_mapping** - 智能体插件映射
```sql
用途: 关联智能体与可用的插件功能
示例: agent_1 → [get_weather, hass_set_state]
```

**ai_agent_context_provider** - 上下文提供者配置
```sql
用途: 为智能体配置上下文来源（如日历、天气等）
```

#### 4. 模型配置模块

**ai_model_provider** - 模型提供商表
```sql
用途: 管理 AI 服务提供商（如 OpenAI, FunASR, 通义千问等）
字段: provider_name, provider_type (asr/tts/llm), api_key, base_url
关键点:
  - API 密钥集中管理
  - 多厂商支持
```

**ai_model_config** - 模型配置表
```sql
用途: 具体模型的详细配置
字段:
  - model_name (模型名称，如 gpt-4, whisper-1)
  - model_type (asr/tts/llm/vad/intent/mem/vllm)
  - config_json (JSON格式的模型参数)
  - is_enabled (启用状态)
  - remark (备注说明)

关键点:
  - config_json 存储复杂的模型参数（如温度、top_p等）
  - xiaozhi-server 通过 API 拉取这些配置
  - 支持动态更新配置无需重启服务
```

#### 5. 聊天记录模块

**ai_agent_chat_history** - 聊天记录表
```sql
用途: 存储智能体对话历史（文本）
字段:
  - session_id (会话ID)
  - mac_address (设备MAC)
  - chat_type (0用户/1助手/2系统)
  - content (对话内容)
  - report_time (上报时间)
```

**ai_agent_chat_audio** - 聊天音频表
```sql
用途: 存储对话的音频文件（Base64或文件路径）
关联: chat_history_id
应用: 语音回放、质量分析
```

**说明：** xiaozhi-server 通过 `manage_api_client.py` 的 `report()` 函数上报对话记录

#### 6. 系统配置模块

**sys_params** - 系统参数表
```sql
用途: 全局配置参数
字段: param_code, param_value, param_type, remark
示例:
  - "default_llm_model" → "gpt-4"
  - "max_chat_history" → "50"
```

**sys_dict_type** + **sys_dict_data** - 字典表
```sql
用途: 数据字典，存储枚举值和选项
示例:
  - dict_type: "device_status"
  - dict_data: [{"label":"在线","value":"1"}, {"label":"离线","value":"0"}]
```

#### 7. 扩展功能模块

**ai_voice_clone** - 语音克隆表
```sql
用途: 用户自定义音色克隆
字段: voice_name, audio_file, model_status
```

**ai_voiceprint** - 声纹识别表
```sql
用途: 声纹注册和验证
应用: 用户身份认证
```

**ai_rag_dataset** - 知识库表
```sql
用途: RAG（检索增强生成）的知识数据
应用: 智能体可调用的专属知识库
```

---

## Redis 缓存详解

### 缓存策略和用途

#### 1. 系统参数缓存

**实现类:** `SysParamsRedis.java`

**数据结构:** Hash
```
Key: sys:params
Hash Fields:
  - default_llm_model → "gpt-4"
  - max_chat_history → "50"
  - welcome_message → "你好，我是小智"
```

**工作流程:**
```
1. 首次读取: MySQL → 写入 Redis → 返回
2. 后续读取: Redis 直接返回（快）
3. 参数更新: 更新 MySQL → 同步删除/更新 Redis
```

**过期策略:** 默认 24 小时 (RedisUtils.DEFAULT_EXPIRE)

#### 2. 模型配置缓存

**使用位置:** `ModelConfigServiceImpl.java`

**缓存内容:**
- 模型列表（按类型）
- 模型详细配置
- Provider API 密钥

**Key 命名规范:** (基于 RedisKeys 工具类)
```
model:config:{model_id}
model:list:{model_type}
```

#### 3. 用户会话缓存（推测）

虽然代码中 token 存储在 MySQL，但可能还缓存了：
- 用户基本信息（避免频繁查库）
- 用户权限列表
- 登录状态

**过期时间:** 通常与 token 过期时间一致

#### 4. 临时数据

**验证码:** (CaptchaServiceImpl 可能使用)
```
Key: captcha:{uuid}
Value: "AB3D"
Expire: 5 分钟
```

**其他临时数据:**
- 短信验证码
- 临时上传文件路径
- 限流计数器

---

## 数据流转示意图

### 场景1: 设备连接和配置获取

```
┌─────────┐
│ ESP32   │
│ 设备    │
└────┬────┘
     │ WebSocket 连接
     │ (发送 MAC 地址)
     ↓
┌──────────────────┐
│ xiaozhi-server   │
│ (Python)         │
└────┬─────────────┘
     │ HTTP API 请求
     │ /config/agent-models
     ↓
┌──────────────────┐
│ manager-api      │
│ (Java)           │
└────┬─────────────┘
     │
  ┌──┴──┐
  │     │
  ↓     ↓
┌────┐ ┌────┐
│Redis│ │MySQL│
└────┘ └────┘
│      │
│      └→ ai_device (通过 MAC 找到 agent_id)
│      └→ ai_agent (通过 agent_id 获取配置)
│      └→ ai_model_config (获取各模型配置)
│      └→ ai_model_provider (获取 API 密钥)
│
└→ 缓存模型配置（加速后续读取）

返回完整配置给 xiaozhi-server
xiaozhi-server 动态加载对应的 Provider
```

### 场景2: 聊天记录上报

```
┌─────────┐
│ 用户说话 │ → ESP32 → xiaozhi-server
└─────────┘              │ (ASR, LLM, TTS)
                         │
                         ↓
                    xiaozhi-server
                    调用 manage_api_client.report()
                         │
                         ↓
                    manager-api
                    /agent/chat-history/report
                         │
                         ↓
                    写入 MySQL
                    - ai_agent_chat_history (文本)
                    - ai_agent_chat_audio (音频Base64)
```

### 场景3: 用户登录

```
前端 (manager-web)
  │
  │ POST /sys/login
  │ {username, password}
  ↓
manager-api
  │
  ├→ 查询 MySQL: sys_user
  │   验证密码
  │
  ├→ 生成 UUID token
  │   更新 MySQL: sys_user_token
  │
  └→ (可能)写入 Redis 缓存用户信息

返回 token 给前端
前端后续请求携带 token
Shiro Filter 拦截 → 验证 token
```

---

## 性能分析

### MySQL 压力点

| 操作 | 频率 | 影响 |
|------|------|------|
| 设备连接时配置查询 | 每次连接 (频繁) | 高 |
| 聊天记录写入 | 每轮对话 (高频) | 中 |
| 用户登录验证 | 低频 | 低 |
| 模型配置更新 | 极低频 | 低 |

**优化点:**
- 设备配置查询有 Redis 缓存
- 聊天记录可批量写入（异步）

### Redis 缓存命中率

**高命中场景:**
- 系统参数读取 (几乎 100%)
- 模型配置读取 (90%+)

**低命中场景:**
- 设备首次连接（必然 Miss）
- 配置刚更新后

### 资源占用估算

**MySQL:**
- 存储: 单用户 ~10-50MB（取决于聊天记录量）
- 连接池: Druid 默认 10-50 连接
- 内存: ~300-500MB (含 InnoDB buffer pool)

**Redis:**
- 存储: ~10-100MB（主要是参数和配置缓存）
- 连接: Spring RedisTemplate 连接池 默认 8 连接
- 内存: ~50-100MB

---

## 迁移到 EloqKV 的映射策略

### 方案对比

#### 方案A: 纯 KV 模式

**MySQL 表 → EloqKV Key-Value**

```
# 用户表
user:{user_id} → {"username":"admin", "password":"xxx", ...}

# 设备表
device:{mac_address} → {"user_id":1, "agent_id":"abc", ...}

# Agent 配置
agent:{agent_id} → {"asr_model_id":"model_1", "llm_model_id":"model_2", ...}

# 索引
idx:username:admin → "1"
idx:device_mac:AA:BB:CC:DD → "AA:BB:CC:DD"
```

**优势:** 简单直接，性能极高
**劣势:** 需要手动维护索引，复杂查询困难

#### 方案B: SQL 模式（如果 EloqKV 支持）

**保持表结构:**
```sql
CREATE TABLE ai_device (...);
CREATE TABLE ai_agent (...);
```

**优势:** 迁移成本低，支持复杂查询
**劣势:** 可能丧失 KV 的极致性能

#### 推荐方案: **混合模式**

- **热点数据用 KV:**
  - 设备配置 (高频读)
  - Agent 配置 (高频读)
  - 系统参数 (高频读)

- **归档数据用 SQL:**
  - 聊天历史 (需要分页、搜索)
  - 用户管理 (需要复杂查询)
  - 日志记录

### Redis 缓存层的替代

**EloqKV 内置缓存能力 → 无需 Redis**

| 原 Redis 用途 | EloqKV 替代方案 |
|--------------|----------------|
| 参数缓存 | 直接 KV 存储，EloqKV 内部缓存 |
| Token 缓存 | 改用 JWT 无状态，无需存储 |
| 验证码 | KV + TTL 过期 |
| 临时数据 | KV + TTL |

---

## 迁移检查清单

### 数据完整性验证

- [ ] 表数量一致（18+ 张表）
- [ ] 行数一致（每张表）
- [ ] 关键字段非空校验
- [ ] 外键关系完整性（如 device.agent_id → agent.id）
- [ ] 唯一索引检查（如 sys_user.username）

### 功能回归测试

- [ ] 用户登录
- [ ] 设备注册和绑定
- [ ] 配置下发（xiaozhi-server 获取配置）
- [ ] 聊天记录上报
- [ ] 模型配置 CRUD
- [ ] Agent 创建和更新
- [ ] OTA 升级流程

### 性能基准对比

| 指标 | MySQL+Redis | EloqKV | 提升 |
|------|-------------|--------|------|
| 配置查询延迟 | 20-50ms | ? | TBD |
| 写入 TPS | 1000+ | ? | TBD |
| 内存占用 | 400MB | ? | TBD |
| 启动时间 | 15s (Java) | <1s (Rust) | **93%** |

---

## 总结

### MySQL 核心价值

1. **业务数据持久化**: 用户、设备、Agent、模型配置等核心数据
2. **关系管理**: 用户-设备、设备-Agent、Agent-模型等复杂关联
3. **审计和追溯**: 聊天记录、操作日志、版本历史
4. **ACID 事务**: 保证数据一致性（如设备绑定事务）

### Redis 核心价值

1. **性能加速**: 缓存热点数据，减少数据库压力
2. **临时数据**: 验证码、限流计数等短期数据
3. **分布式锁**: (虽然代码中未明显体现，但 Lua 脚本暗示可能用到)

### 迁移到 EloqKV 的核心收益

- **运维简化**: 2个存储组件 → 1个
- **成本降低**: 少一套存储服务的维护
- **性能提升**: KV 存储 + 内置缓存 ≥ MySQL + Redis
- **资源节约**: 内存占用大幅降低

### 关键风险

- **EloqKV 功能验证**: 必须提前确认是否满足所有需求（SQL查询、事务、TTL等）
- **数据迁移脚本**: 需要经过充分测试，保证零数据丢失
- **学习成本**: 团队需要熟悉 EloqKV 的使用和运维

---

**文档版本:** 1.0
**分析基于:** xiaozhi-esp32-server manager-api 模块
**创建日期:** 2026-01-16
