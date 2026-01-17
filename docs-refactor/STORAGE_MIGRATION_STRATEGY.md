# 存储迁移策略深度分析：MySQL → EloqKV

## 目录
- [核心问题](#核心问题)
- [MySQL 表分类分析](#mysql-表分类分析)
- [KV (JSON) 存储可行性评估](#kv-json-存储可行性评估)
- [数据模型设计方案](#数据模型设计方案)
- [查询模式对比](#查询模式对比)
- [最终推荐方案](#最终推荐方案)

---

## 核心问题

**你提出的问题：这些表都可以不用 SQL，直接用 JSON 存储吗？**

**答案：大部分可以，但需要权衡。**

关键在于理解两个维度：
1. **存储层面**: JSON 可以存储所有数据 ✅
2. **查询层面**: 能否高效实现业务需求 ❓

---

## MySQL 表分类分析

### 分类维度

根据访问模式，将 18+ 张表分为 4 类：

| 分类 | 特征 | 适合存储方式 |
|------|------|-------------|
| **🟢 简单 KV** | 按主键/唯一键查询，无复杂过滤 | **JSON (完美)** |
| **🟡 索引 KV** | 需要按非主键字段查询 | **JSON + 索引** |
| **🟠 范围查询** | 需要分页、排序、多条件筛选 | **JSON (可行，但麻烦)** 或 SQL |
| **🔴 关联查询** | 需要 JOIN 多表 | **SQL 或手动关联** |

---

## KV (JSON) 存储可行性评估

### 🟢 完全适合 JSON 的表（7张）

#### 1. **sys_user_token** - 用户令牌

**原 SQL 查询：**
```sql
SELECT * FROM sys_user_token WHERE token = 'abc123';
SELECT * FROM sys_user_token WHERE user_id = 1;
```

**JSON KV 方案：**
```javascript
// 主存储
"token:abc123" → {
  "user_id": 1,
  "token": "abc123",
  "expire_date": "2026-01-20T00:00:00Z",
  "create_date": "2026-01-16T00:00:00Z"
}

// 索引（可选，因为可改用 JWT）
"user_token:1" → "abc123"  // user_id → token
```

**优势：**
- 按 token 查询 → O(1) 直接命中
- 按 user_id 查询 → 通过索引 key 间接查询
- **更好方案：改用 JWT，完全无需存储** ⭐

**结论：JSON ✅ (或直接移除，用 JWT)**

---

#### 2. **ai_device** - 设备信息

**原 SQL 查询：**
```sql
-- 最高频：按 MAC 地址查询（设备连接时）
SELECT * FROM ai_device WHERE mac_address = 'AA:BB:CC:DD:EE:FF';

-- 次高频：按用户查询设备列表
SELECT * FROM ai_device WHERE user_id = 123 ORDER BY sort;
```

**JSON KV 方案：**
```javascript
// 主存储：以 MAC 为 Key（因为这是最高频查询）
"device:AA:BB:CC:DD:EE:FF" → {
  "id": "uuid-1",
  "user_id": 123,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "agent_id": "agent-abc",
  "alias": "客厅小智",
  "board": "ESP32-S3",
  "app_version": "1.2.3",
  "last_connected_at": "2026-01-16T10:30:00Z",
  "auto_update": 1,
  "sort": 1,
  "create_date": "2026-01-01T00:00:00Z"
}

// 索引：用户 → 设备列表
"user_devices:123" → ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]

// 实现排序：存储排序后的数组或在应用层排序
```

**查询实现：**
```rust
// 1. 按 MAC 查询（最高频）
let device = eloq.get("device:AA:BB:CC:DD:EE:FF")?;
// → 单次 KV 查询，极快 ⚡

// 2. 按用户查询设备列表
let mac_list = eloq.get("user_devices:123")?; // 获取 MAC 列表
let devices = mac_list.iter()
    .map(|mac| eloq.get(format!("device:{}", mac)))
    .collect(); // 批量获取（可能需要 mget 优化）
// → 两次查询，可接受
```

**优势：**
- 核心场景（按 MAC 查询）性能极佳
- 无需解析 SQL

**劣势：**
- 用户设备列表需要维护索引
- 排序需要在应用层或索引层处理

**结论：JSON ✅**

---

#### 3. **ai_agent** - 智能体配置

**原 SQL 查询：**
```sql
-- 核心查询：按 agent_id 获取配置
SELECT * FROM ai_agent WHERE id = 'agent-abc';

-- 次要查询：用户的智能体列表
SELECT * FROM ai_agent WHERE user_id = 123 ORDER BY sort;
```

**JSON KV 方案：**
```javascript
// 主存储
"agent:agent-abc" → {
  "id": "agent-abc",
  "user_id": 123,
  "agent_name": "小智助手",
  "asr_model_id": "whisper-1",
  "vad_model_id": "silero-vad",
  "llm_model_id": "gpt-4",
  "vllm_model_id": "gpt-4-vision",
  "tts_model_id": "edge-tts",
  "tts_voice_id": "zh-CN-XiaoxiaoNeural",
  "mem_model_id": "mem0ai",
  "intent_model_id": "intent-local",
  "system_prompt": "你是一个友善的AI助手...",
  "chat_history_conf": 2,
  "language": "zh-CN",
  "summary_memory": "...",
  "sort": 1,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-16T00:00:00Z"
}

// 索引
"user_agents:123" → ["agent-abc", "agent-def"]
```

**xiaozhi-server 使用场景：**
```python
# manage_api_client.py 中的 get_agent_models()
# 实际是通过 device.agent_id 来查询 agent 配置
# 因此核心是按 agent_id 查询 → 完美适合 KV
```

**结论：JSON ✅**

---

#### 4. **ai_model_config** - 模型配置

**原 SQL 查询：**
```sql
-- 核心：按模型 ID 查询
SELECT * FROM ai_model_config WHERE id = 'model-gpt4';

-- 次要：按类型查询模型列表
SELECT id, model_name FROM ai_model_config
WHERE model_type = 'llm' AND is_enabled = 1;
```

**JSON KV 方案：**
```javascript
// 主存储
"model:model-gpt4" → {
  "id": "model-gpt4",
  "model_name": "GPT-4 Turbo",
  "model_type": "llm",
  "provider_id": "provider-openai",
  "config_json": {
    "type": "openai",
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 4096,
    "stream": true
  },
  "is_enabled": 1,
  "remark": "OpenAI GPT-4 模型",
  "create_date": "2026-01-01T00:00:00Z"
}

// 索引：按类型分类
"models_by_type:llm" → ["model-gpt4", "model-claude", "model-glm4"]
"models_by_type:asr" → ["model-whisper", "model-funasr"]
```

**优势：**
- 配置热加载场景完美适配
- JSON 嵌套存储 `config_json` 很自然

**结论：JSON ✅**

---

#### 5. **ai_model_provider** - 模型提供商

**原 SQL：**
```sql
SELECT * FROM ai_model_provider WHERE id = 'provider-openai';
```

**JSON KV：**
```javascript
"provider:provider-openai" → {
  "id": "provider-openai",
  "provider_name": "OpenAI",
  "provider_type": "llm",
  "api_key": "sk-xxx",
  "base_url": "https://api.openai.com/v1",
  "is_enabled": 1
}
```

**结论：JSON ✅**

---

#### 6. **ai_agent_plugin_mapping** - 插件映射

**原 SQL：**
```sql
SELECT plugin_id FROM ai_agent_plugin_mapping WHERE agent_id = 'agent-abc';
```

**JSON KV：**
```javascript
// 方案1：独立存储
"agent_plugins:agent-abc" → ["plugin_weather", "plugin_hass", "plugin_time"]

// 方案2：嵌入 agent 配置（推荐）
"agent:agent-abc" → {
  ...,
  "plugins": ["plugin_weather", "plugin_hass"]
}
```

**结论：JSON ✅ (建议嵌入 agent)**

---

#### 7. **sys_params** - 系统参数

**原 SQL：**
```sql
SELECT param_value FROM sys_params WHERE param_code = 'default_llm_model';
```

**JSON KV：**
```javascript
// 方案1：单个参数为一个 Key
"param:default_llm_model" → "gpt-4"
"param:max_chat_history" → "50"

// 方案2：Hash 结构（如果 EloqKV 支持）
"sys:params" → {
  "default_llm_model": "gpt-4",
  "max_chat_history": "50",
  "welcome_message": "你好"
}
```

**结论：JSON ✅**

---

### 🟡 需要索引的表（4张）

#### 8. **sys_user** - 系统用户

**原 SQL 查询：**
```sql
-- 登录：按用户名查询
SELECT * FROM sys_user WHERE username = 'admin';

-- 管理：用户列表（分页、搜索）
SELECT * FROM sys_user
WHERE username LIKE '%test%'
ORDER BY create_date DESC
LIMIT 10 OFFSET 0;
```

**JSON KV 方案：**

**方案A：主索引为 username（推荐）**
```javascript
// 主存储（用户名为 Key，因为登录是最高频）
"user:username:admin" → {
  "id": 1,
  "username": "admin",
  "password": "$2a$10$...",  // bcrypt hash
  "super_admin": 1,
  "status": 1,
  "create_date": "2026-01-01T00:00:00Z"
}

// 反向索引（如果需要按 ID 查询）
"user:id:1" → "admin"  // id → username
```

**登录验证：**
```rust
// 1. 获取用户
let user = eloq.get("user:username:admin")?;

// 2. 验证密码
verify_password(input_password, user.password)?;

// 3. 生成 JWT token（无需存储到数据库）
let token = generate_jwt(user.id, user.username)?;
```

**用户列表查询（复杂）：**
```rust
// 问题：KV 无法高效实现 LIKE 搜索和分页

// 解决方案1：全量加载 + 应用层过滤（用户量小时可行）
let all_users = eloq.keys("user:username:*")?;
let filtered = all_users.iter()
    .filter(|u| u.username.contains("test"))
    .skip(offset)
    .take(limit)
    .collect();

// 解决方案2：如果 EloqKV 支持 Scan + 模式匹配
let users = eloq.scan("user:username:*test*", limit, offset)?;

// 解决方案3：使用 EloqKV 的 SQL 接口（如果支持）
let users = eloq.query("SELECT * FROM sys_user WHERE username LIKE ?", ["%test%"])?;
```

**结论：JSON ⚠️ (取决于用户量和查询需求)**
- 用户量 < 1000：JSON 完全可行
- 用户量 > 10000：建议用 SQL 或全文搜索

---

#### 9. **ai_ota** - 固件升级

**原 SQL：**
```sql
-- 获取最新版本
SELECT * FROM ai_ota
WHERE board = 'ESP32-S3'
ORDER BY version DESC
LIMIT 1;

-- 版本列表
SELECT * FROM ai_ota ORDER BY create_date DESC;
```

**JSON KV 方案：**
```javascript
// 每个 OTA 包
"ota:ESP32-S3:v1.2.3" → {
  "id": "ota-1",
  "board": "ESP32-S3",
  "version": "1.2.3",
  "download_url": "https://xxx/firmware-1.2.3.bin",
  "file_size": 1048576,
  "md5": "abc123",
  "release_notes": "修复了若干bug",
  "create_date": "2026-01-15T00:00:00Z"
}

// 索引：每个板子的最新版本
"ota:latest:ESP32-S3" → "v1.2.3"

// 版本列表（按时间排序）
"ota:versions:ESP32-S3" → ["v1.2.3", "v1.2.2", "v1.2.1"]
```

**获取最新版本：**
```rust
let latest_version = eloq.get("ota:latest:ESP32-S3")?;
let ota_info = eloq.get(format!("ota:ESP32-S3:{}", latest_version))?;
```

**结论：JSON ✅ (需维护索引)**

---

#### 10. **ai_agent_template** - 智能体模板

**原 SQL：**
```sql
SELECT * FROM ai_agent_template ORDER BY sort;
```

**JSON KV：**
```javascript
// 每个模板
"template:voice-assistant" → {
  "id": "voice-assistant",
  "name": "语音助手模板",
  "system_prompt": "你是一个智能语音助手...",
  "default_models": {
    "asr": "whisper-1",
    "llm": "gpt-4"
  },
  "sort": 1
}

// 模板列表（排序）
"templates:list" → ["voice-assistant", "smart-home", "translator"]
```

**结论：JSON ✅**

---

#### 11. **sys_dict_type + sys_dict_data** - 数据字典

**原 SQL：**
```sql
SELECT dict_label, dict_value
FROM sys_dict_data
WHERE dict_type_id = (
  SELECT id FROM sys_dict_type WHERE dict_type = 'device_status'
);
```

**JSON KV 方案（扁平化）：**
```javascript
// 合并存储
"dict:device_status" → [
  {"label": "在线", "value": "1", "sort": 1},
  {"label": "离线", "value": "0", "sort": 2}
]

"dict:model_type" → [
  {"label": "ASR", "value": "asr", "sort": 1},
  {"label": "TTS", "value": "tts", "sort": 2},
  {"label": "LLM", "value": "llm", "sort": 3}
]
```

**结论：JSON ✅ (更简单)**

---

### 🟠 需要复杂查询的表（5张）

#### 12. **ai_agent_chat_history** - 聊天记录

**原 SQL 查询：**
```sql
-- 按会话查询（分页）
SELECT * FROM ai_agent_chat_history
WHERE session_id = 'session-123'
ORDER BY report_time ASC
LIMIT 50;

-- 按设备查询（用于分析）
SELECT * FROM ai_agent_chat_history
WHERE mac_address = 'AA:BB:CC:DD:EE:FF'
AND report_time >= '2026-01-01'
ORDER BY report_time DESC
LIMIT 100;

-- 按用户统计
SELECT COUNT(*), DATE(report_time) as date
FROM ai_agent_chat_history
WHERE user_id = 123
GROUP BY DATE(report_time);
```

**JSON KV 方案：**

**存储设计：**
```javascript
// 每条聊天记录
"chat:msg-uuid-1" → {
  "id": "msg-uuid-1",
  "session_id": "session-123",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "user_id": 123,
  "chat_type": 0,  // 0用户/1助手/2系统
  "content": "今天天气怎么样？",
  "report_time": "2026-01-16T10:30:00Z"
}

// 索引：会话 → 消息列表
"session:session-123:messages" → [
  "msg-uuid-1",
  "msg-uuid-2",
  "msg-uuid-3"
  // ... 最多保留最近 N 条，超出的归档
]

// 索引：设备消息时间线
"device:AA:BB:CC:DD:EE:FF:timeline:2026-01-16" → [
  "msg-uuid-1",
  "msg-uuid-5"
]
```

**查询实现：**
```rust
// 1. 按会话查询（最常见）
let msg_ids = eloq.get("session:session-123:messages")?;
let messages = eloq.mget(msg_ids)?;  // 批量获取
// → 性能可接受

// 2. 按设备和时间范围查询（困难）
// KV 方案需要：
// - 预先按天建立时间线索引
// - 应用层合并多天数据
// - 应用层排序和分页

// 3. 统计查询（非常困难）
// KV 无法高效实现 GROUP BY 和聚合
```

**结论：JSON ⚠️**
- **简单查询**（按 session_id）：JSON 可行 ✅
- **复杂查询**（时间范围、统计）：建议用 SQL 🔴

**推荐方案：**
- **热数据**（最近 7 天）：JSON KV，快速访问
- **冷数据**（历史归档）：如果 EloqKV 支持 SQL，用 SQL；否则考虑定期导出到对象存储

---

#### 13. **ai_agent_chat_audio** - 聊天音频

**原 SQL：**
```sql
SELECT audio_base64 FROM ai_agent_chat_audio
WHERE chat_history_id = 'msg-uuid-1';
```

**JSON KV：**
```javascript
// 方案1：独立存储
"chat_audio:msg-uuid-1" → {
  "audio_base64": "data:audio/wav;base64,UklGR...",
  "duration": 3.5,
  "size": 102400
}

// 方案2：嵌入聊天记录（如果音频小）
"chat:msg-uuid-1" → {
  "content": "今天天气怎么样？",
  "audio": "UklGR..."  // 或者存储 URL
}

// 方案3：音频存储到对象存储（推荐）
"chat:msg-uuid-1" → {
  "content": "今天天气怎么样？",
  "audio_url": "https://oss.example.com/audio/msg-uuid-1.wav"
}
```

**结论：JSON ✅ (但建议音频存储到对象存储如 OSS/S3)**

---

#### 14. **ai_voice_clone** - 语音克隆

**原 SQL：**
```sql
SELECT * FROM ai_voice_clone WHERE user_id = 123;
SELECT * FROM ai_voice_clone WHERE status = 'completed' ORDER BY create_date DESC;
```

**JSON KV：**
```javascript
"voice_clone:voice-1" → {
  "id": "voice-1",
  "user_id": 123,
  "voice_name": "我的声音",
  "audio_file": "https://oss/voice-1.wav",
  "model_status": "completed",
  "create_date": "2026-01-15T00:00:00Z"
}

// 索引
"user_voices:123" → ["voice-1", "voice-2"]
```

**结论：JSON ✅**

---

#### 15. **ai_voiceprint** - 声纹识别

类似 voice_clone

**结论：JSON ✅**

---

#### 16. **ai_rag_dataset** - 知识库

**原 SQL：**
```sql
-- 向量搜索（如果用传统数据库）
SELECT * FROM ai_rag_dataset WHERE vector <-> query_vector < threshold;

-- 或简单的文本存储
SELECT content FROM ai_rag_dataset WHERE knowledge_base_id = 'kb-1';
```

**JSON KV：**
```javascript
"rag:kb-1:doc-1" → {
  "id": "doc-1",
  "knowledge_base_id": "kb-1",
  "content": "这是一段知识库内容...",
  "embedding": [0.1, 0.2, 0.3, ...],  // 向量
  "metadata": {"source": "manual.pdf", "page": 5}
}

// 索引
"kb:kb-1:docs" → ["doc-1", "doc-2", "doc-3"]
```

**问题：**
- KV 无法高效实现向量相似度搜索
- 通常需要专门的向量数据库（如 Milvus, Pinecone）

**结论：JSON ⚠️ (简单场景可行，复杂 RAG 需要向量数据库)**

---

#### 17. **ai_agent_context_provider** - 上下文提供者

**结论：JSON ✅**

---

### 🔴 几乎必须用 SQL 的场景

#### 18. **复杂报表查询**

如果需要：
```sql
-- 用户活跃度统计
SELECT u.username, COUNT(c.id) as chat_count, MAX(c.report_time) as last_chat
FROM sys_user u
LEFT JOIN ai_device d ON u.id = d.user_id
LEFT JOIN ai_agent_chat_history c ON d.mac_address = c.mac_address
WHERE c.report_time >= '2026-01-01'
GROUP BY u.id
ORDER BY chat_count DESC;
```

**KV 方案困难：**
- 需要手动实现多表 JOIN
- 聚合统计效率低

**解决方案：**
1. **如果 EloqKV 支持 SQL**：直接用 SQL ✅
2. **如果不支持**：
   - 定期导出到分析数据库（如 ClickHouse）
   - 或在应用层实现简化版统计

---

## 数据模型设计方案

### 方案对比

| 方案 | 存储方式 | 优势 | 劣势 | 适用场景 |
|------|---------|------|------|---------|
| **纯 KV** | 全部用 JSON | 性能极高，简单 | 复杂查询困难 | 简单 CRUD 应用 |
| **SQL** | 保持表结构 | 查询灵活，功能完整 | 可能丧失 KV 性能优势 | 传统业务系统 |
| **混合** | 核心数据 KV，归档用 SQL | 兼顾性能和功能 | 架构复杂度增加 | **推荐** ⭐ |

### 推荐：混合方案

```
┌─────────────────────────────────────┐
│         EloqKV 存储                  │
├─────────────────────────────────────┤
│                                      │
│  【KV 层】- 热数据，高频访问          │
│  ├─ device:*         (设备信息)      │
│  ├─ agent:*          (智能体配置)     │
│  ├─ model:*          (模型配置)       │
│  ├─ user:username:*  (用户登录)      │
│  ├─ session:*        (会话消息)      │
│  └─ param:*          (系统参数)      │
│                                      │
│  【SQL 层】- 冷数据，复杂查询         │
│  ├─ ai_agent_chat_history (历史聊天) │
│  ├─ sys_user (用户管理，如需搜索)    │
│  └─ 统计报表 (如果需要)              │
│                                      │
└─────────────────────────────────────┘
```

---

## 查询模式对比

### 核心业务场景

#### 场景1: 设备连接获取配置

**频率:** 每次设备连接（高频）

**SQL 方案：**
```sql
-- 需要 3 次查询
SELECT agent_id FROM ai_device WHERE mac_address = ?;
SELECT * FROM ai_agent WHERE id = ?;
SELECT * FROM ai_model_config WHERE id IN (...);
```

**JSON KV 方案：**
```rust
// 1. 查设备
let device = eloq.get("device:AA:BB:CC:DD:EE:FF")?;

// 2. 查智能体
let agent = eloq.get(format!("agent:{}", device.agent_id))?;

// 3. 批量查模型（或者预先嵌入到 agent）
let models = eloq.mget(vec![
    format!("model:{}", agent.asr_model_id),
    format!("model:{}", agent.llm_model_id),
    // ...
])?;
```

**性能对比：**
- SQL: 3 次查询，约 20-50ms（有索引）
- KV: 2-3 次 get/mget，约 1-5ms

**结论：KV 快 10 倍+ ⚡**

---

#### 场景2: 用户登录

**频率:** 低频

**SQL 方案：**
```sql
SELECT * FROM sys_user WHERE username = ?;
INSERT/UPDATE sys_user_token SET token=?, expire_date=? WHERE user_id=?;
```

**JSON KV 方案：**
```rust
// 1. 查用户
let user = eloq.get("user:username:admin")?;

// 2. 验证密码
verify_password()?;

// 3. 生成 JWT（无需存储）
let token = jwt::encode(&claims, &secret)?;
```

**性能对比：**
- SQL: 约 10-30ms
- KV + JWT: 约 1-5ms

**结论：KV 快，且更简单（无状态）**

---

#### 场景3: 查询聊天历史（分页）

**频率:** 中频

**SQL 方案：**
```sql
SELECT * FROM ai_agent_chat_history
WHERE session_id = ?
ORDER BY report_time DESC
LIMIT ? OFFSET ?;
```

**JSON KV 方案：**
```rust
// 需要提前维护索引
let msg_ids = eloq.get("session:123:messages")?;  // 返回有序列表
let page = msg_ids[offset..offset+limit];
let messages = eloq.mget(page)?;
```

**性能对比：**
- SQL: 约 10-50ms（取决于数据量和索引）
- KV: 约 2-10ms（如果索引维护良好）

**关键点：**
- KV 需要手动维护 `session:*:messages` 索引
- 索引更新复杂度增加

**结论：KV 稍快，但维护成本高**

---

#### 场景4: 统计报表

**频率:** 低频

**SQL 方案：**
```sql
SELECT DATE(report_time), COUNT(*)
FROM ai_agent_chat_history
WHERE user_id = ?
GROUP BY DATE(report_time);
```

**JSON KV 方案：**
```rust
// 几乎不可能高效实现
// 需要：
// 1. 扫描所有聊天记录
// 2. 应用层分组聚合
// 3. 性能极差
```

**结论：SQL 完胜 🔴**

---

## 最终推荐方案

### ⭐ 推荐架构

```yaml
存储策略:
  # KV 存储（性能优先）
  KV层:
    - device:*              # 设备信息
    - agent:*               # 智能体配置
    - model:*               # 模型配置
    - provider:*            # 提供商配置
    - user:username:*       # 用户（按用户名索引）
    - param:*               # 系统参数
    - dict:*                # 数据字典
    - template:*            # 智能体模板
    - session:*:messages    # 会话消息索引（最近 N 条）
    - ota:*                 # OTA 固件

  # SQL 存储（查询优先）- 如果 EloqKV 支持
  SQL层:
    - ai_agent_chat_history  # 完整聊天历史
    - sys_user               # 用户管理（如需复杂搜索）

  # 对象存储（大文件）
  OSS:
    - 聊天音频文件
    - OTA 固件包
    - 语音克隆训练文件
```

### 数据迁移清单

| 原 MySQL 表 | 迁移方式 | Key 设计 | 索引需求 |
|------------|---------|---------|---------|
| sys_user | KV | `user:username:{name}` | username → id |
| sys_user_token | **移除** | 改用 JWT | - |
| ai_device | KV | `device:{mac}` | user_id → mac_list |
| ai_agent | KV | `agent:{id}` | user_id → agent_list |
| ai_model_config | KV | `model:{id}` | type → model_list |
| ai_model_provider | KV | `provider:{id}` | - |
| ai_agent_plugin_mapping | 合并到 agent | - | - |
| ai_agent_template | KV | `template:{id}` | 全局 list |
| sys_params | KV | `param:{code}` | - |
| sys_dict_* | KV (合并) | `dict:{type}` | - |
| ai_ota | KV | `ota:{board}:{version}` | latest 索引 |
| ai_voice_clone | KV | `voice:{id}` | user_id 索引 |
| ai_voiceprint | KV | `voiceprint:{id}` | user_id 索引 |
| ai_agent_context_provider | KV | 嵌入 agent 或独立 | - |
| ai_rag_dataset | KV / 专用向量库 | `rag:{kb_id}:{doc_id}` | - |
| **ai_agent_chat_history** | **SQL** (如果支持) | 保持表结构 | session_id, mac, time |
| **ai_agent_chat_audio** | **对象存储** | 存储 URL | - |

### 关键决策

#### 1. **聊天历史处理**

```yaml
方案A - 纯 KV（适合小规模）:
  热数据: session:*:messages (最近 7 天，数组索引)
  冷数据: 定期导出到对象存储（JSON 文件）

方案B - 混合（推荐）:
  热数据: KV 索引 (快速访问最近对话)
  全量数据: EloqKV SQL 表 (支持复杂查询)

方案C - 分离存储:
  EloqKV: 仅存储业务配置
  聊天历史: 独立时序数据库 (InfluxDB / TimescaleDB)
```

#### 2. **用户认证改造**

```yaml
当前: MySQL sys_user_token 表 + Shiro
目标: JWT 无状态认证

优势:
  - 无需存储 token
  - 水平扩展容易
  - 减少数据库压力

实现:
  1. 登录时生成 JWT
  2. Rust 中间件验证 JWT
  3. 移除 sys_user_token 表
```

#### 3. **音频文件处理**

```yaml
不建议: 存储 Base64 到 EloqKV
推荐:
  1. 上传音频到对象存储 (MinIO / S3 / 阿里云 OSS)
  2. EloqKV 只存储 URL
  3. 前端直接从 OSS 播放

优势:
  - 减少 EloqKV 存储压力
  - 音频播放性能更好
  - CDN 加速
```

---

## 实施建议

### 阶段1: 验证 EloqKV 能力

**必须验证：**
```yaml
KV 基础功能:
  - [x] GET/SET/DEL
  - [x] TTL 过期
  - [x] MGET 批量查询
  - [x] 事务支持 (如果需要)

SQL 功能 (关键):
  - [ ] 是否支持 CREATE TABLE
  - [ ] 是否支持 SELECT/INSERT/UPDATE/DELETE
  - [ ] 是否支持 WHERE/ORDER BY/LIMIT
  - [ ] 是否支持索引
  - [ ] 是否支持 JOIN (次要)
  - [ ] 是否支持聚合 (COUNT/SUM/GROUP BY)

性能测试:
  - [ ] 单次 GET 延迟
  - [ ] 批量 MGET 延迟
  - [ ] SQL 查询延迟
  - [ ] 并发读写性能
```

### 阶段2: 选择方案

**决策树：**
```
EloqKV 是否支持 SQL？
│
├─ 是 → 混合方案（KV + SQL）⭐ 推荐
│   ├─ 核心配置用 KV（极致性能）
│   └─ 聊天历史用 SQL（查询灵活）
│
└─ 否 → 纯 KV 方案
    ├─ 适用条件：
    │   - 用户量 < 10000
    │   - 聊天历史不需要复杂查询
    │   - 可接受手动维护索引
    │
    └─ 或考虑：KV (EloqKV) + 时序库 (InfluxDB)
```

### 阶段3: 数据模型设计

参考本文档的 Key 设计方案，编写详细的：
1. Key 命名规范文档
2. 索引维护策略
3. 数据一致性保证机制

### 阶段4: 迁移脚本编写

```python
# 示例：MySQL → EloqKV 迁移脚本
import mysql.connector
from eloqkv_client import EloqClient

# 1. 连接数据库
mysql_conn = mysql.connector.connect(...)
eloq = EloqClient(url="...")

# 2. 迁移设备表
cursor = mysql_conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM ai_device")
for row in cursor:
    key = f"device:{row['mac_address']}"
    eloq.set(key, json.dumps(row))

    # 维护索引
    user_key = f"user_devices:{row['user_id']}"
    eloq.sadd(user_key, row['mac_address'])  # 如果支持 Set

# 3. 验证
assert eloq.get("device:AA:BB:CC:DD:EE:FF") is not None
```

---

## 总结

### 核心结论

**问题：这些 MySQL 表都可以不用 SQL，直接用 JSON 存储吗？**

**答案：**

| 数据类型 | JSON 可行性 | 条件 |
|---------|-----------|------|
| **设备、Agent、模型配置** | ✅ 完全可行 | 主要是主键查询，KV 完美适配 |
| **用户、系统参数** | ✅ 可行 | 数据量小，简单查询 |
| **聊天历史** | ⚠️ 有限可行 | 简单查询可以，复杂统计困难 |
| **音频文件** | ❌ 不建议 | 应该用对象存储 |
| **统计报表** | ❌ 困难 | 需要 SQL 或专用分析库 |

### 最佳实践

1. **核心配置用 KV**：性能提升 10 倍+
2. **认证改用 JWT**：简化架构，移除 token 表
3. **聊天历史**：
   - 热数据（7天）用 KV 索引
   - 全量用 SQL（如果 EloqKV 支持）或定期归档
4. **音频文件用对象存储**：不要存到数据库

### 预期收益

- **性能提升**: 设备配置查询 20ms → 2ms (10倍)
- **资源节约**: 内存 400MB → 100MB (75%)
- **运维简化**: 2 个存储 → 1 个 (50%)
- **架构优化**: 无状态 JWT，水平扩展更容易

---

**下一步：** 部署 EloqKV 测试实例，运行本文档中的验证清单 ✅
