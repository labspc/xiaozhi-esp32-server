# 小智 ESP32 系统架构与 API 完整文档

> 文档版本：1.0
> 创建日期：2026-01-16
> 系统版本：基于当前代码库

---

## 目录

1. [系统架构概览](#系统架构概览)
2. [技术栈](#技术栈)
3. [业务模块与功能](#业务模块与功能)
4. [核心业务流程](#核心业务流程)
5. [完整 API 清单](#完整-api-清单)
6. [前后端协调关系](#前后端协调关系)
7. [数据流与通信协议](#数据流与通信协议)
8. [部署架构](#部署架构)

---

## 系统架构概览

### 系统组成

小智 ESP32 是一个完整的物联网语音交互系统，由以下四个核心模块组成：

```
┌─────────────────────────────────────────────────────────────────┐
│                        小智 ESP32 系统                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ ESP32 设备   │  │ MQTT 网关   │  │  手机 APP   │             │
│  │             │  │             │  │             │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         │    WebSocket   │    WebSocket   │   HTTP REST        │
│         └────────┬───────┴────────────────┴──────┐             │
│                  │                                │             │
│         ┌────────▼─────────┐            ┌────────▼──────────┐  │
│         │ xiaozhi-server   │            │  manager-api      │  │
│         │ (Python)         │◄───HTTP────┤  (Java Spring)    │  │
│         │ Port: 8000       │            │  Port: 8002       │  │
│         └──────────────────┘            └───────┬───────────┘  │
│                                                 │               │
│                                        ┌────────▼──────────┐    │
│                                        │  MySQL + Redis    │    │
│                                        └───────────────────┘    │
│                                                 │               │
│                  ┌──────────────────────────────┴───────┐       │
│                  │                                      │       │
│         ┌────────▼──────────┐            ┌─────────▼─────────┐ │
│         │  manager-web      │            │ manager-mobile    │ │
│         │  (Vue 2)          │            │ (uni-app)         │ │
│         │  Port: 8001       │            │ (跨平台)          │ │
│         └───────────────────┘            └───────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 模块说明

#### 1. xiaozhi-server（Python，端口 8000）
**职责**：AI 语音交互核心引擎
- WebSocket 服务器，接收 ESP32 设备的音频流
- 集成 ASR（语音识别）、TTS（语音合成）、LLM（大语言模型）
- VAD（语音活动检测）实时处理
- 插件系统（天气查询、智能家居控制等）
- MCP（Model Context Protocol）协议支持

**关键特性**：
- 每个设备连接独立的 ConnectionHandler 实例
- 支持多种 AI 提供商（OpenAI、阿里云、百度等）
- Provider 插件化架构
- 实时音频流处理（Opus 编码）

#### 2. manager-api（Java Spring Boot，端口 8002）
**职责**：管理后台 RESTful API 服务
- 用户认证与权限管理（Apache Shiro）
- 智能体配置管理（CRUD）
- 设备绑定与激活
- 模型配置管理
- 知识库管理
- OTA 固件管理
- 聊天记录存储与查询

**关键特性**：
- MyBatis-Plus ORM
- Redis 缓存
- Liquibase 数据库版本管理
- Swagger API 文档
- JWT Token 认证

#### 3. manager-web（Vue 2，端口 8001）
**职责**：Web 管理控制台
- 智能体配置界面
- 设备管理界面
- 模型配置界面
- 知识库管理
- 用户管理（管理员）
- 聊天记录查看

**关键特性**：
- Element UI 组件库
- Vuex 状态管理
- PWA 支持
- 国际化（6 种语言）

#### 4. manager-mobile（uni-app + Vue 3）
**职责**：跨平台移动端应用
- 智能体管理
- 设备绑定与配置
- 聊天记录查看
- 声纹管理

**关键特性**：
- TypeScript
- Pinia 状态管理
- Alova HTTP 库
- 支持 H5/微信小程序/iOS/Android

---

## 技术栈

### 后端技术

| 模块 | 语言/框架 | 端口 | 数据库 | 主要依赖 |
|------|----------|------|--------|---------|
| **xiaozhi-server** | Python 3.10 | 8000 (WS) <br> 8003 (HTTP) | - | websockets, asyncio, torch, transformers |
| **manager-api** | Java 21 <br> Spring Boot 3.4.3 | 8002 | MySQL 8.0 <br> Redis | MyBatis-Plus, Shiro, Druid, Liquibase |

### 前端技术

| 模块 | 框架 | 端口 | 状态管理 | HTTP 库 | UI 库 |
|------|------|------|---------|---------|-------|
| **manager-web** | Vue 2.6 | 8001 | Vuex 3 | Flyio | Element UI |
| **manager-mobile** | Vue 3 <br> uni-app | - | Pinia | Alova | uni-app 组件 |

### AI 服务提供商支持

| 类型 | 支持的提供商 |
|------|------------|
| **ASR** | FunASR (本地), OpenAI, Azure, 阿里云, 讯飞, 火山引擎 |
| **TTS** | EdgeTTS (免费), Azure, OpenAI, 阿里云, 火山引擎, Fish Speech (本地) |
| **LLM** | OpenAI, Claude, Gemini, 通义千问, GLM, Deepseek, Kimi |
| **VAD** | Silero VAD (本地), FunASR VAD |
| **Memory** | Mem0, 本地短期记忆 |

---

## 业务模块与功能

### 1. 用户与认证模块

**功能**：
- 用户注册（手机号 + 短信验证）
- 用户登录（支持 SM2 加密）
- 密码找回
- 验证码生成（图形、短信）
- JWT Token 管理

**权限级别**：
- **普通用户** (normal)：管理自己的智能体和设备
- **超级管理员** (superAdmin)：系统配置、用户管理、全局设置

**相关 API**：
- `POST /user/login` - 登录
- `POST /user/register` - 注册
- `GET /user/captcha` - 图形验证码
- `POST /user/smsVerification` - 短信验证码
- `GET /user/info` - 获取用户信息

---

### 2. 智能体管理模块

**业务对象**：Agent（智能体）

**核心属性**：
```json
{
  "agentId": "智能体ID",
  "agentName": "智能体名称",
  "userId": "所属用户ID",
  "llmModel": "LLM模型名称",
  "asrModel": "ASR模型名称",
  "ttsModel": "TTS模型名称",
  "personality": "个性设定",
  "greeting": "欢迎语",
  "voicePrint": "声纹配置",
  "knowledgeBase": "关联知识库",
  "plugins": "启用的插件列表"
}
```

**功能**：
- 创建智能体（基于模板或自定义）
- 配置 AI 模型（ASR、TTS、LLM）
- 设置个性化提示词
- 声纹管理（多声纹支持）
- 知识库关联
- 插件启用/禁用
- 聊天记录查看
- 对话总结生成

**智能体生命周期**：
```
创建 → 配置 → 绑定设备 → 激活 → 运行中 → 停用 → 删除
```

**相关 API**：
- `POST /agent` - 创建智能体
- `PUT /agent/{id}` - 更新智能体
- `DELETE /agent/{id}` - 删除智能体（级联删除设备、聊天记录）
- `GET /agent/list` - 获取用户智能体列表
- `GET /agent/{id}` - 获取智能体详情

---

### 3. 设备管理模块

**业务对象**：Device（ESP32 设备）

**核心属性**：
```json
{
  "deviceId": "设备ID",
  "macAddress": "MAC地址",
  "deviceCode": "6位验证码",
  "agentId": "绑定的智能体ID",
  "status": "online|offline",
  "firmwareVersion": "固件版本",
  "autoUpdate": "自动更新开关"
}
```

**设备绑定流程**：

```
┌─────────────┐
│ ESP32 设备   │
│ 首次启动    │
└──────┬──────┘
       │
       │ 1. 连接 xiaozhi-server (WebSocket)
       ▼
┌─────────────────────────────┐
│ xiaozhi-server             │
│ - 检测到未绑定设备          │
│ - 生成 6 位验证码           │
│ - 播报绑定提示             │
└──────┬──────────────────────┘
       │
       │ 2. 用户听到验证码
       ▼
┌─────────────────────────────┐
│ manager-web/mobile         │
│ - 输入 6 位验证码           │
│ - 选择智能体               │
│ - 提交绑定请求             │
└──────┬──────────────────────┘
       │
       │ 3. POST /device/bind/{agentId}/{deviceCode}
       ▼
┌─────────────────────────────┐
│ manager-api                │
│ - 验证验证码               │
│ - 绑定设备到智能体         │
│ - 激活设备                 │
└──────┬──────────────────────┘
       │
       │ 4. 绑定成功
       ▼
┌─────────────────────────────┐
│ ESP32 设备                 │
│ - 播报绑定成功提示         │
│ - 开始正常服务             │
└─────────────────────────────┘
```

**相关 API**：
- `POST /device/register` - 注册设备（生成验证码）
- `POST /device/bind/{agentId}/{deviceCode}` - 绑定设备
- `POST /device/unbind` - 解绑设备
- `GET /device/bind/{agentId}` - 获取已绑定设备列表
- `PUT /device/update/{id}` - 更新设备信息

---

### 4. 对话交互模块

**核心流程**：

```
ESP32 录音
    ↓
WebSocket 二进制消息（Opus 音频）
    ↓
xiaozhi-server 接收
    ↓
VAD（语音活动检测）
    ├─ 检测到语音开始
    ├─ 检测到语音中
    └─ 检测到语音结束
    ↓
ASR（语音识别）
    ↓
文本输出："你好小智"
    ↓
Intent Recognition（意图识别）
    ├─ 普通对话 → LLM
    ├─ 插件调用 → Function Calling
    └─ IoT 控制 → 设备命令
    ↓
LLM 生成回复
    ↓
TTS（语音合成）
    ↓
Opus 音频流
    ↓
WebSocket 发送到 ESP32
    ↓
ESP32 播放
```

**消息类型**：

| 类型 | 方向 | 格式 | 说明 |
|------|------|------|------|
| **hello** | 客户端 → 服务器 | JSON | 握手消息，交换音频参数 |
| **listen** | 客户端 → 服务器 | JSON | 手动控制拾音（start/stop/detect） |
| **abort** | 客户端 → 服务器 | JSON | 中断当前对话 |
| **iot** | 客户端 → 服务器 | JSON | 物联网设备状态上报 |
| **mcp** | 双向 | JSON | MCP 协议消息 |
| **ping/pong** | 双向 | JSON | 心跳消息 |
| **audio** | 双向 | Binary | Opus 编码的音频流 |
| **tts** | 服务器 → 客户端 | JSON | TTS 状态（start/middle/stop） |

**聊天记录存储**：
- xiaozhi-server 上报到 manager-api
- 存储用户消息、AI 回复、音频 ID
- 支持按会话查询
- 支持导出（当前会话、前 20 条会话）

**相关 API**：
- `POST /agent/chat-history/report` - 上报聊天记录
- `GET /agent/{id}/sessions` - 获取会话列表
- `GET /agent/{id}/chat-history/{sessionId}` - 获取聊天记录
- `POST /agent/chat-summary/{sessionId}/save` - 生成会话总结

---

### 5. 模型配置模块

**业务对象**：Model（AI 模型配置）

**模型类型**：
- **ASR**：自动语音识别
- **TTS**：文本转语音
- **LLM**：大语言模型
- **VAD**：语音活动检测
- **Intent**：意图识别
- **Memory**：记忆管理
- **VLLM**：视觉语言模型

**核心属性**：
```json
{
  "modelId": "模型ID",
  "modelType": "ASR|TTS|LLM|VAD|...",
  "providerCode": "提供商代码",
  "modelCode": "模型代码",
  "modelName": "显示名称",
  "apiKey": "API密钥（加密存储）",
  "apiUrl": "API地址",
  "isDefault": "是否默认",
  "isEnabled": "是否启用",
  "config": "JSON配置（模型特定参数）"
}
```

**音色管理**：
- TTS 模型支持多音色
- 每个音色有唯一的 voiceCode
- 支持音色克隆（上传样本音频）

**相关 API**：
- `GET /models/names` - 获取所有模型名称
- `POST /models/{modelType}/{provideCode}` - 新增模型配置
- `PUT /models/{modelType}/{provideCode}/{id}` - 更新模型配置
- `DELETE /models/{id}` - 删除模型配置
- `GET /models/{modelId}/voices` - 获取模型音色列表

---

### 6. 知识库模块

**业务对象**：Dataset（知识库）、Document（文档）、Chunk（切片）

**核心流程**：

```
创建知识库
    ↓
上传文档（PDF/Word/TXT/Markdown）
    ↓
文档解析和切块
    ├─ 固定长度切块
    ├─ 智能段落切块
    └─ 自定义分隔符切块
    ↓
向量化（Embedding）
    ↓
存储到向量数据库
    ↓
智能体关联知识库
    ↓
对话时检索（RAG）
    ↓
增强 LLM 上下文
```

**核心属性**：
```json
{
  "datasetId": "知识库ID",
  "datasetName": "知识库名称",
  "description": "描述",
  "embeddingModel": "向量化模型",
  "documents": [
    {
      "documentId": "文档ID",
      "fileName": "文件名",
      "status": "parsing|completed|failed",
      "chunkMethod": "fixed|paragraph|custom",
      "chunkSize": 500,
      "chunkOverlap": 50
    }
  ]
}
```

**相关 API**：
- `POST /datasets` - 创建知识库
- `POST /datasets/{id}/documents` - 上传文档
- `POST /datasets/{id}/chunks` - 解析文档（切块）
- `GET /datasets/{id}/documents/{docId}/chunks` - 获取文档切片
- `POST /datasets/{id}/retrieval-test` - RAG 召回测试

---

### 7. OTA 固件管理模块

**业务对象**：OTA（Over-The-Air 更新）

**更新流程**：

```
ESP32 设备
    ↓
定期检查更新（POST /ota/）
    ↓
manager-api 检查
    ├─ 设备是否激活
    ├─ 固件版本对比
    └─ 返回更新信息
    ↓
设备下载固件（GET /otaMag/download/{uuid}）
    ↓
验证 MD5
    ↓
刷写固件
    ↓
重启设备
```

**核心属性**：
```json
{
  "otaId": "固件ID",
  "firmwareType": "firmware_type",
  "version": "1.0.0",
  "filePath": "data/bin/firmware.bin",
  "md5": "文件MD5",
  "description": "更新说明",
  "forceUpdate": "是否强制更新"
}
```

**相关 API**：
- `POST /ota/` - 检查更新（设备端）
- `POST /otaMag/upload` - 上传固件（管理端）
- `GET /otaMag/download/{uuid}` - 下载固件
- `DELETE /otaMag/{id}` - 删除固件

---

### 8. 声纹与声音克隆模块

**业务对象**：VoicePrint（声纹）、VoiceClone（声音克隆）

**声纹管理**：
- 智能体支持多声纹
- 声纹优先级排序
- 声纹激活/禁用

**声音克隆流程**：

```
用户上传音频样本（10-30秒）
    ↓
调用声音克隆服务
    ├─ FishSpeech（本地）
    ├─ Azure TTS
    └─ 其他TTS平台
    ↓
生成声纹模型
    ↓
保存声纹配置
    ↓
智能体绑定声纹
    ↓
TTS 使用克隆音色
```

**相关 API**：
- `POST /agent/voice-print` - 创建声纹
- `PUT /agent/voice-print` - 更新声纹
- `DELETE /agent/voice-print/{id}` - 删除声纹
- `POST /voiceClone/upload` - 上传音频克隆
- `POST /voiceClone/cloneAudio` - 复刻音频

---

## 核心业务流程

### 流程1：新用户注册到首次对话

```mermaid
sequenceDiagram
    participant U as 用户
    participant MW as manager-web
    participant MA as manager-api
    participant DB as MySQL
    participant ESP as ESP32设备
    participant XS as xiaozhi-server

    U->>MW: 1. 注册账号
    MW->>MA: POST /user/register
    MA->>DB: 保存用户信息
    MA-->>MW: 注册成功

    U->>MW: 2. 登录
    MW->>MA: POST /user/login
    MA->>DB: 验证用户
    MA-->>MW: 返回 JWT Token

    U->>MW: 3. 创建智能体
    MW->>MA: POST /agent
    MA->>DB: 保存智能体配置
    MA-->>MW: 返回智能体ID

    U->>ESP: 4. ESP32 开机
    ESP->>XS: WebSocket 连接
    XS->>XS: 检测未绑定
    XS->>ESP: 播报6位验证码

    U->>MW: 5. 输入验证码绑定
    MW->>MA: POST /device/bind/{agentId}/{code}
    MA->>DB: 绑定设备到智能体
    MA->>XS: 通知设备已绑定
    XS->>ESP: 播报绑定成功

    U->>ESP: 6. 说话"你好小智"
    ESP->>XS: 音频流（Opus）
    XS->>XS: VAD + ASR
    XS->>XS: LLM 生成回复
    XS->>XS: TTS 合成
    XS->>ESP: 音频流（Opus）
    ESP->>U: 播放回复
```

---

### 流程2：对话过程详细流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant ESP as ESP32
    participant XS as xiaozhi-server
    participant VAD as VAD模块
    participant ASR as ASR模块
    participant LLM as LLM模块
    participant TTS as TTS模块
    participant MA as manager-api

    U->>ESP: 1. 开始说话
    ESP->>XS: 发送音频流（二进制）
    XS->>VAD: 音频数据
    VAD-->>XS: 检测到语音开始

    loop 持续录音
        ESP->>XS: 音频数据
        XS->>VAD: 持续检测
    end

    VAD-->>XS: 检测到语音结束
    XS->>ASR: 完整音频
    ASR-->>XS: 识别文本："今天天气怎么样"

    XS->>LLM: 发送文本 + 上下文
    LLM->>LLM: 判断需要调用天气插件
    LLM-->>XS: Function Call: get_weather()

    XS->>XS: 执行插件
    XS->>LLM: 插件返回结果
    LLM-->>XS: 生成回复文本

    XS->>TTS: 回复文本
    TTS-->>XS: 音频流（Opus）

    XS->>ESP: 发送 TTS 开始消息
    XS->>ESP: 音频数据包1
    XS->>ESP: 音频数据包2
    XS->>ESP: ...
    XS->>ESP: 发送 TTS 结束消息

    ESP->>U: 播放音频

    XS->>MA: POST /agent/chat-history/report
    MA->>MA: 保存聊天记录
```

---

### 流程3：知识库 RAG 检索流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant ESP as ESP32
    participant XS as xiaozhi-server
    participant LLM as LLM模块
    participant MA as manager-api
    participant KB as 知识库
    participant VDB as 向量数据库

    U->>ESP: 提问："公司的请假政策是什么"
    ESP->>XS: 音频流
    XS->>XS: ASR识别

    XS->>MA: GET /agent/{id}
    MA-->>XS: 智能体配置（包含知识库ID）

    XS->>MA: POST /datasets/{id}/retrieval-test
    Note over MA: 查询文本："请假政策"
    MA->>VDB: 向量化查询
    VDB-->>MA: Top-K 相关切片
    MA-->>XS: 检索结果

    XS->>LLM: 用户问题 + 知识库内容
    Note over LLM: 上下文增强
    LLM-->>XS: 基于知识库的回复

    XS->>XS: TTS 合成
    XS->>ESP: 音频回复
    ESP->>U: 播放答案
```

---

### 流程4：配置动态更新流程

```mermaid
sequenceDiagram
    participant MW as manager-web
    participant MA as manager-api
    participant XS as xiaozhi-server
    participant ESP as ESP32设备

    MW->>MA: 1. 修改智能体配置
    Note over MW: 例如：更换 LLM 模型
    MA->>MA: 保存配置到数据库

    MW->>MA: 2. 通知服务端更新
    Note over MW: POST /admin/server/emit-action
    MA->>MA: 构造更新消息

    MA->>XS: 3. HTTP请求通知更新
    Note over MA,XS: config_update_url
    XS->>XS: 重新加载配置

    XS->>ESP: 4. WebSocket消息
    Note over XS,ESP: {"type":"server","action":"update_config"}
    ESP->>ESP: 更新本地配置

    Note over ESP,XS: 下次对话使用新配置
```

---

## 完整 API 清单

### manager-api（Java Spring Boot）REST API

#### 认证与用户 (Login & User)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/user/captcha?uuid={uuid}` | - | 获取图形验证码 |
| POST | `/user/smsVerification` | - | 发送短信验证码 |
| POST | `/user/login` | - | 用户登录 |
| POST | `/user/register` | - | 用户注册 |
| GET | `/user/info` | normal | 获取当前用户信息 |
| PUT | `/user/change-password` | normal | 修改密码 |
| PUT | `/user/retrieve-password` | - | 找回密码 |
| GET | `/user/pub-config` | - | 获取公共配置 |

#### 智能体管理 (Agent)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/agent/list` | normal | 获取用户智能体列表 |
| GET | `/agent/all` | superAdmin | 获取所有智能体（分页） |
| GET | `/agent/{id}` | normal | 获取智能体详情 |
| POST | `/agent` | normal | 创建智能体 |
| PUT | `/agent/{id}` | normal | 更新智能体 |
| PUT | `/agent/saveMemory/{macAddress}` | - | 保存设备记忆 |
| DELETE | `/agent/{id}` | normal | 删除智能体 |
| GET | `/agent/template` | normal | 获取智能体模板列表 |
| GET | `/agent/{id}/sessions` | normal | 获取智能体会话列表 |
| GET | `/agent/{id}/chat-history/{sessionId}` | normal | 获取聊天记录 |
| GET | `/agent/{id}/chat-history/user` | normal | 获取用户聊天记录 |
| GET | `/agent/{id}/chat-history/audio` | normal | 获取音频内容 |
| POST | `/agent/audio/{audioId}` | normal | 获取音频下载ID |
| GET | `/agent/play/{uuid}` | - | 播放音频 |
| POST | `/agent/chat-summary/{sessionId}/save` | - | 生成聊天总结 |

#### 智能体模板 (Agent Template)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/agent/template/page` | superAdmin | 分页获取模板 |
| GET | `/agent/template/{id}` | superAdmin | 获取模板详情 |
| POST | `/agent/template` | superAdmin | 创建模板 |
| PUT | `/agent/template` | superAdmin | 更新模板 |
| DELETE | `/agent/template/{id}` | superAdmin | 删除模板 |
| POST | `/agent/template/batch-remove` | superAdmin | 批量删除模板 |

#### MCP 接入点 (Agent MCP)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/agent/mcp/address/{agentId}` | normal | 获取MCP地址 |
| GET | `/agent/mcp/tools/{agentId}` | normal | 获取MCP工具列表 |

#### 声纹管理 (Voice Print)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| POST | `/agent/voice-print` | normal | 创建声纹 |
| PUT | `/agent/voice-print` | normal | 更新声纹 |
| DELETE | `/agent/voice-print/{id}` | normal | 删除声纹 |
| GET | `/agent/voice-print/list/{id}` | normal | 获取声纹列表 |

#### 聊天记录 (Chat History)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| POST | `/agent/chat-history/report` | - | 上报聊天记录 |
| POST | `/agent/chat-history/getDownloadUrl/{agentId}/{sessionId}` | normal | 获取下载链接 |
| GET | `/agent/chat-history/download/{uuid}/current` | - | 下载当前会话 |
| GET | `/agent/chat-history/download/{uuid}/previous` | - | 下载前20条会话 |

#### 设备管理 (Device)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| POST | `/device/bind/{agentId}/{deviceCode}` | normal | 绑定设备 |
| POST | `/device/register` | - | 注册设备 |
| GET | `/device/bind/{agentId}` | normal | 获取已绑定设备 |
| POST | `/device/bind/{agentId}` | normal | 查询设备在线状态 |
| POST | `/device/unbind` | normal | 解绑设备 |
| PUT | `/device/update/{id}` | normal | 更新设备信息 |
| POST | `/device/manual-add` | normal | 手动添加设备 |

#### OTA 管理 (OTA)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| POST | `/ota/` | - | 检查OTA更新 |
| POST | `/ota/activate` | - | 检查激活状态 |
| GET | `/ota/` | - | OTA状态检查 |
| GET | `/otaMag` | superAdmin | 分页查询固件 |
| GET | `/otaMag/{id}` | superAdmin | 获取固件详情 |
| POST | `/otaMag` | superAdmin | 保存固件信息 |
| PUT | `/otaMag/{id}` | superAdmin | 修改固件信息 |
| DELETE | `/otaMag/{id}` | superAdmin | 删除固件 |
| GET | `/otaMag/getDownloadUrl/{id}` | superAdmin | 获取下载链接 |
| GET | `/otaMag/download/{uuid}` | - | 下载固件 |
| POST | `/otaMag/upload` | superAdmin | 上传固件 |

#### 知识库 (Knowledge Base)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/datasets` | normal | 分页查询知识库 |
| GET | `/datasets/{dataset_id}` | normal | 获取知识库详情 |
| POST | `/datasets` | normal | 创建知识库 |
| PUT | `/datasets/{dataset_id}` | normal | 更新知识库 |
| DELETE | `/datasets/{dataset_id}` | normal | 删除知识库 |
| DELETE | `/datasets/batch` | normal | 批量删除知识库 |
| GET | `/datasets/rag-models` | normal | 获取RAG模型列表 |

#### 知识库文档 (Knowledge Files)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/datasets/{dataset_id}/documents` | normal | 分页查询文档 |
| GET | `/datasets/{dataset_id}/documents/status/{status}` | normal | 按状态查询文档 |
| POST | `/datasets/{dataset_id}/documents` | normal | 上传文档 |
| DELETE | `/datasets/{dataset_id}/documents/{document_id}` | normal | 删除文档 |
| POST | `/datasets/{dataset_id}/chunks` | normal | 解析文档 |
| GET | `/datasets/{dataset_id}/documents/{document_id}/chunks` | normal | 获取文档切片 |
| POST | `/datasets/{dataset_id}/retrieval-test` | normal | RAG召回测试 |

#### 模型管理 (Model)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/models/names` | normal | 获取模型名称列表 |
| GET | `/models/llm/names` | normal | 获取LLM模型列表 |
| GET | `/models/{modelType}/provideTypes` | superAdmin | 获取供应器列表 |
| GET | `/models/list` | superAdmin | 分页获取模型配置 |
| POST | `/models/{modelType}/{provideCode}` | superAdmin | 新增模型配置 |
| PUT | `/models/{modelType}/{provideCode}/{id}` | superAdmin | 更新模型配置 |
| DELETE | `/models/{id}` | superAdmin | 删除模型配置 |
| GET | `/models/{id}` | superAdmin | 获取模型详情 |
| PUT | `/models/enable/{id}/{status}` | superAdmin | 启用/禁用模型 |
| PUT | `/models/default/{id}` | superAdmin | 设置默认模型 |
| GET | `/models/{modelId}/voices` | normal | 获取模型音色列表 |

#### 模型供应器 (Model Provider)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/models/provider` | superAdmin | 分页获取供应器 |
| POST | `/models/provider` | superAdmin | 新增供应器 |
| PUT | `/models/provider` | superAdmin | 修改供应器 |
| POST | `/models/provider/delete` | superAdmin | 删除供应器 |
| GET | `/models/provider/plugin/names` | - | 获取插件名称 |

#### 音色管理 (Timbre)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/ttsVoice` | superAdmin | 分页查询音色 |
| POST | `/ttsVoice` | superAdmin | 保存音色 |
| PUT | `/ttsVoice/{id}` | superAdmin | 修改音色 |
| POST | `/ttsVoice/delete` | superAdmin | 删除音色 |

#### 声音克隆 (Voice Clone)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/voiceClone` | normal | 分页查询声音克隆 |
| POST | `/voiceClone/upload` | normal | 上传音频克隆 |
| POST | `/voiceClone/updateName` | normal | 更新克隆名称 |
| POST | `/voiceClone/audio/{id}` | normal | 获取音频下载ID |
| GET | `/voiceClone/play/{uuid}` | - | 播放音频 |
| POST | `/voiceClone/cloneAudio` | normal | 复刻音频 |

#### 语音资源 (Voice Resource)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/voiceResource` | superAdmin | 分页查询语音资源 |
| GET | `/voiceResource/{id}` | superAdmin | 获取语音资源详情 |
| POST | `/voiceResource` | superAdmin | 新增语音资源 |
| DELETE | `/voiceResource/{id}` | superAdmin | 删除语音资源 |
| GET | `/voiceResource/user/{userId}` | normal | 按用户查询资源 |
| GET | `/voiceResource/ttsPlatforms` | superAdmin | 获取TTS平台列表 |

#### 配置管理 (Config)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| POST | `/config/server-base` | - | 获取服务器基础配置 |
| POST | `/config/agent-models` | - | 获取智能体模型配置 |

#### 系统管理 (Admin)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/admin/users` | superAdmin | 分页查询用户 |
| PUT | `/admin/users/{id}` | superAdmin | 重置用户密码 |
| DELETE | `/admin/users/{id}` | superAdmin | 删除用户 |
| PUT | `/admin/users/changeStatus/{status}` | superAdmin | 批量修改用户状态 |
| GET | `/admin/device/all` | superAdmin | 分页查询所有设备 |

#### 服务端管理 (Server Side)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/admin/server/server-list` | superAdmin | 获取WebSocket服务列表 |
| POST | `/admin/server/emit-action` | superAdmin | 通知Python服务更新配置 |

#### 字典管理 (Dict)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/admin/dict/type/page` | superAdmin | 分页查询字典类型 |
| GET | `/admin/dict/type/{id}` | superAdmin | 获取字典类型详情 |
| POST | `/admin/dict/type/save` | superAdmin | 保存字典类型 |
| PUT | `/admin/dict/type/update` | superAdmin | 修改字典类型 |
| POST | `/admin/dict/type/delete` | superAdmin | 删除字典类型 |
| GET | `/admin/dict/data/page` | superAdmin | 分页查询字典数据 |
| GET | `/admin/dict/data/{id}` | superAdmin | 获取字典数据详情 |
| POST | `/admin/dict/data/save` | superAdmin | 新增字典数据 |
| PUT | `/admin/dict/data/update` | superAdmin | 修改字典数据 |
| POST | `/admin/dict/data/delete` | superAdmin | 删除字典数据 |
| GET | `/admin/dict/data/type/{dictType}` | normal | 按类型获取字典数据 |

#### 系统参数 (Params)

| 方法 | 端点 | 权限 | 功能 |
|------|------|------|------|
| GET | `/admin/params/page` | superAdmin | 分页查询参数 |
| GET | `/admin/params/{id}` | superAdmin | 获取参数详情 |
| POST | `/admin/params` | superAdmin | 保存参数 |
| PUT | `/admin/params` | superAdmin | 修改参数 |
| POST | `/admin/params/delete` | superAdmin | 删除参数 |

---

### xiaozhi-server（Python）WebSocket & HTTP API

#### WebSocket 端点

| 端点 | 协议 | 功能 |
|------|------|------|
| `ws://[IP]:8000/xiaozhi/v1/` | WebSocket | 主连接端点（音频流+控制消息） |

**请求头**：
- `device-id`（必需）：设备唯一标识
- `client-id`（可选）：客户端标识
- `authorization`（可选）：JWT Token

#### WebSocket 消息类型

**文本消息（JSON）**：

| 类型 | 方向 | 格式示例 | 说明 |
|------|------|---------|------|
| **hello** | 客户端→服务器 | `{"type":"hello","audio_params":{"format":"opus"}}` | 握手消息 |
| **listen** | 客户端→服务器 | `{"type":"listen","state":"start"}` | 手动拾音控制 |
| **abort** | 客户端→服务器 | `{"type":"abort"}` | 中断对话 |
| **iot** | 客户端→服务器 | `{"type":"iot","descriptors":[]}` | IoT设备状态 |
| **mcp** | 双向 | `{"type":"mcp","payload":{}}` | MCP协议消息 |
| **server** | 服务器→客户端 | `{"type":"server","action":"update_config"}` | 服务器命令 |
| **ping** | 客户端→服务器 | `{"type":"ping"}` | 心跳消息 |
| **pong** | 服务器→客户端 | `{"type":"pong","timestamp":"2026-01-16 10:30:45"}` | 心跳响应 |
| **tts** | 服务器→客户端 | `{"type":"tts","state":"start","text":"..."}` | TTS状态 |

**二进制消息（音频）**：
- Opus 编码的音频数据包
- 来自 MQTT 网关的音频需要 16 字节头部

#### HTTP 端点

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `http://[IP]:8003/xiaozhi/ota/` | 获取OTA固件信息 |
| POST | `http://[IP]:8003/xiaozhi/ota/` | 提交OTA请求 |
| GET | `http://[IP]:8003/xiaozhi/ota/download/{filename}` | 下载固件文件 |
| POST | `http://[IP]:8003/mcp/vision/explain` | 图像分析（需JWT认证） |
| GET | `http://[IP]:8003/mcp/vision/explain` | 获取接口信息 |

---

## 前后端协调关系

### 数据流向图

```
┌──────────────────────────────────────────────────────┐
│                   前端应用层                          │
│  ┌────────────────┐      ┌──────────────────┐       │
│  │ manager-web    │      │ manager-mobile   │       │
│  │ (Vue 2)        │      │ (uni-app)        │       │
│  └────────┬───────┘      └──────┬───────────┘       │
│           │                     │                    │
│           │  HTTP REST API      │                    │
│           └─────────┬───────────┘                    │
└─────────────────────┼──────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  manager-api   │
              │  (Java)        │
              │  Port: 8002    │
              └───────┬────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────────┐
   │  MySQL  │  │  Redis  │  │ xiaozhi-    │
   │         │  │         │  │ server      │
   └─────────┘  └─────────┘  └────┬────────┘
                                   │
                              ┌────▼────────┐
                              │  ESP32      │
                              │  设备       │
                              └─────────────┘
```

### API 调用关系表

#### manager-web → manager-api

| 前端模块 | API文件 | 后端Controller | 主要功能 |
|---------|---------|---------------|---------|
| 登录页面 | `user.js` | `LoginController` | 登录、注册、验证码 |
| 智能体管理 | `agent.js` | `AgentController` | 智能体CRUD、聊天记录 |
| 设备管理 | `device.js` | `DeviceController` | 设备绑定、解绑、状态 |
| 模型配置 | `model.js` | `ModelController` | 模型管理、音色列表 |
| 知识库 | `knowledgeBase.js` | `KnowledgeBaseController` | 知识库文档管理 |
| 系统管理 | `admin.js` | `AdminController` | 用户管理、参数配置 |

#### manager-mobile → manager-api

| 前端模块 | API文件 | 后端Controller | 主要功能 |
|---------|---------|---------------|---------|
| 登录注册 | `auth.ts` | `LoginController` | 认证相关 |
| 智能体 | `agent/agent.ts` | `AgentController` | 智能体管理 |
| 设备 | `device/device.ts` | `DeviceController` | 设备管理 |
| 聊天记录 | `chat-history/chat-history.ts` | `AgentChatHistoryController` | 聊天记录查询 |
| 声纹 | `voiceprint/voiceprint.ts` | `AgentVoicePrintController` | 声纹管理 |

#### manager-api → xiaozhi-server

| 场景 | API调用 | 功能 |
|------|---------|------|
| 配置更新 | `POST config_update_url` | 通知Python服务重载配置 |
| 获取服务列表 | `GET server_list_url` | 查询WebSocket服务状态 |

#### xiaozhi-server → manager-api

| 场景 | API调用 | 功能 |
|------|---------|------|
| 上报聊天 | `POST /agent/chat-history/report` | 保存对话记录 |
| 获取配置 | `POST /config/server-base` | 拉取远程配置 |
| 获取智能体模型 | `POST /config/agent-models` | 获取设备绑定的模型配置 |

---

## 数据流与通信协议

### 音频数据流

```
┌─────────────────────────────────────────────────────────┐
│                      音频处理链                          │
└─────────────────────────────────────────────────────────┘

ESP32 录音（PCM 16kHz）
    ↓
Opus 编码器（压缩）
    ↓
WebSocket 发送（二进制）
    ↓
xiaozhi-server 接收
    ↓
VAD 处理（语音活动检测）
    ├─ 静音：丢弃
    └─ 有效语音：继续
    ↓
ASR 模型（语音识别）
    ↓
文本输出
    ↓
LLM 处理（生成回复）
    ↓
TTS 模型（语音合成）
    ↓
Opus 编码
    ↓
WebSocket 发送（分包，60ms/包）
    ↓
ESP32 接收
    ↓
Opus 解码器
    ↓
DAC 播放
```

### WebSocket 消息格式规范

#### 握手消息（HELLO）

**客户端发送**：
```json
{
  "type": "hello",
  "audio_params": {
    "format": "opus",
    "sample_rate": 16000,
    "channels": 1
  },
  "features": {
    "mcp": true,
    "iot": false
  }
}
```

**服务器响应**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "xiaozhi": {
    "version": "1.0.0",
    "agent_name": "小智"
  },
  "audio_params": {
    "format": "opus"
  }
}
```

#### 拾音控制（LISTEN）

```json
{
  "type": "listen",
  "state": "start",    // start | stop | detect
  "mode": "manual",    // manual | auto
  "text": "识别文本"   // 仅 state=detect 时需要
}
```

#### 中断对话（ABORT）

**客户端发送**：
```json
{
  "type": "abort"
}
```

**服务器响应**：
```json
{
  "type": "tts",
  "state": "stop",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### TTS 状态消息

```json
{
  "type": "tts",
  "state": "start",      // start | middle | stop
  "text": "你好，我是小智",
  "sentence_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### HTTP REST API 请求/响应规范

#### 标准成功响应

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    // 业务数据
  }
}
```

#### 标准错误响应

```json
{
  "code": 1001,
  "msg": "错误描述",
  "data": null
}
```

#### 分页响应

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "list": [...],
    "total": 100
  }
}
```

#### 认证头

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 部署架构

### 简化部署（仅 xiaozhi-server）

```
┌─────────────────────────────┐
│   Docker Container          │
│                             │
│  ┌───────────────────────┐ │
│  │  xiaozhi-server       │ │
│  │  Port: 8000 (WS)      │ │
│  │  Port: 8003 (HTTP)    │ │
│  └───────────────────────┘ │
│                             │
│  ┌───────────────────────┐ │
│  │  config.yaml          │ │
│  └───────────────────────┘ │
└─────────────────────────────┘
        │
        │ WebSocket
        ▼
┌─────────────────┐
│   ESP32 设备    │
└─────────────────┘
```

**适用场景**：
- 个人使用
- 单用户单设备
- 低资源环境（2核2GB）

---

### 完整部署（所有模块）

```
                ┌──────────────────────────┐
                │   Nginx (反向代理)       │
                │   Port: 80/443           │
                └────────┬─────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐    ┌─────▼──────┐   ┌────▼────────┐
   │manager- │    │manager-    │   │xiaozhi-    │
   │web      │    │api         │   │server      │
   │Port:8001│    │Port:8002   │   │Port:8000   │
   └─────────┘    └──────┬─────┘   └─────────────┘
                         │
                ┌────────┴────────┐
                │                 │
           ┌────▼────┐      ┌────▼────┐
           │  MySQL  │      │  Redis  │
           │Port:3306│      │Port:6379│
           └─────────┘      └─────────┘
```

**适用场景**：
- 多用户管理
- 企业部署
- 需要 Web 管理界面
- 推荐配置：4核8GB

---

### 网络拓扑

```
Internet
    │
    ├─── Web浏览器 → manager-web (8001)
    │                    ↓
    ├─── 手机APP → manager-mobile
    │                    ↓
    │              manager-api (8002)
    │                    ↓
    │              MySQL + Redis
    │
    ├─── ESP32设备 → xiaozhi-server (8000)
    │
    └─── MQTT网关 → xiaozhi-server (8000)
```

---

## 附录

### A. 配置文件位置

| 模块 | 配置文件 | 路径 |
|------|---------|------|
| xiaozhi-server | config.yaml | `main/xiaozhi-server/config.yaml` |
| manager-api | application.yml | `main/manager-api/src/main/resources/application.yml` |
| manager-web | .env | `main/manager-web/.env.*` |
| manager-mobile | .env | `main/manager-mobile/env/.env.*` |

### B. 默认端口列表

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| xiaozhi-server (WebSocket) | 8000 | WebSocket | ESP32 连接端点 |
| xiaozhi-server (HTTP) | 8003 | HTTP | OTA/Vision API |
| manager-web | 8001 | HTTP | Web 前端 |
| manager-api | 8002 | HTTP | REST API |
| MySQL | 3306 | TCP | 数据库 |
| Redis | 6379 | TCP | 缓存 |

### C. 环境变量

**xiaozhi-server**：
- `CONFIG_PATH`：配置文件路径

**manager-api**：
- `SPRING_DATASOURCE_URL`：数据库连接
- `SPRING_REDIS_HOST`：Redis 主机

**manager-web**：
- `VUE_APP_API_BASE_URL`：API 基础地址

**manager-mobile**：
- `VITE_SERVER_BASEURL`：服务器地址

### D. 关键文件路径

**xiaozhi-server**：
- WebSocket 服务器：`core/websocket_server.py`
- 连接处理器：`core/connection.py`
- 消息处理器：`core/handle/`
- Provider 实现：`core/providers/`
- 插件函数：`plugins_func/functions/`

**manager-api**：
- Controller 层：`src/main/java/xiaozhi/modules/*/controller/`
- Service 层：`src/main/java/xiaozhi/modules/*/service/`
- DAO 层：`src/main/java/xiaozhi/modules/*/dao/`
- Entity 层：`src/main/java/xiaozhi/modules/*/entity/`

**manager-web**：
- API 层：`src/apis/module/`
- 页面组件：`src/views/`
- 可复用组件：`src/components/`
- 状态管理：`src/store/index.js`

**manager-mobile**：
- API 层：`src/api/`
- 页面：`src/pages/`
- Store：`src/store/`
- HTTP 配置：`src/http/request/alova.ts`

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-01-16 | 初始版本，基于当前代码库完整梳理 |

---

**文档结束**
