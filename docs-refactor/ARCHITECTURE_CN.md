# xiaozhi-esp32-server 架构深度分析

## 📋 目录

- [整体架构概览](#整体架构概览)
- [核心部件详解](#核心部件详解)
- [数据流和交互机制](#数据流和交互机制)
- [关键设计模式](#关键设计模式)
- [核心文件清单](#核心文件清单)

---

## 整体架构概览

### 四大核心模块

```
┌─────────────────────────────────────────────────────────────────┐
│                        ESP32 智能硬件设备                          │
│                    (语音输入/输出、IoT控制)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ WebSocket (实时音频流)
                      │ ws://host:8000/xiaozhi/v1/
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│            xiaozhi-server (Python 3.10, Port 8000)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  核心AI引擎                                                │  │
│  │  • WebSocket服务器 (实时通信)                              │  │
│  │  • VAD (语音活动检测)                                      │  │
│  │  • ASR (语音识别)                                          │  │
│  │  • LLM (大语言模型对话)                                     │  │
│  │  • Intent (意图识别)                                       │  │
│  │  • Function Calling (工具调用)                             │  │
│  │  • Memory (对话记忆)                                       │  │
│  │  • TTS (语音合成)                                          │  │
│  │  • HTTP服务器 (OTA、MCP视觉分析)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────┬──────────────────┬────────────────────────────┘
                  │                  │
                  │ HTTP API         │ HTTP API
                  │ 配置拉取         │ 数据上报
                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│         manager-api (Java 21 + Spring Boot, Port 8002)          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  管理后端API                                              │  │
│  │  • RESTful API (业务逻辑)                                 │  │
│  │  • 用户认证授权 (Apache Shiro)                            │  │
│  │  • 配置管理 (动态配置)                                     │  │
│  │  • 设备管理 (注册、绑定、状态)                             │  │
│  │  • 智能体管理 (多智能体)                                   │  │
│  │  • 模型配置 (LLM/ASR/TTS)                                 │  │
│  │  • 聊天历史 (记录、查询)                                   │  │
│  │  • 知识库管理 (RAG)                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │  MySQL 数据库     │         │  Redis 缓存       │           │
│  │  (持久化存储)     │         │  (会话、热数据)   │           │
│  └──────────────────┘         └──────────────────┘           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ HTTP API
                  │ (JSON)
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│          manager-web (Vue.js 2 + Element UI, Port 8001)         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Web管理界面                                              │  │
│  │  • 用户管理 (账户、角色、权限)                             │  │
│  │  • 设备管理 (注册、配置、监控)                             │  │
│  │  • 智能体配置 (多智能体管理)                               │  │
│  │  • AI服务配置 (LLM、ASR、TTS选择)                         │  │
│  │  • 音色管理 (TTS音色定制)                                 │  │
│  │  • OTA管理 (固件更新)                                     │  │
│  │  • 系统参数 (字典、配置)                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│        manager-mobile (uni-app + Vue 3 + Vite)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  移动端管理界面                                            │  │
│  │  • 跨平台支持 (iOS、Android、H5、微信小程序)              │  │
│  │  • 设备管理                                                │  │
│  │  • 智能体配置                                              │  │
│  │  • 用户登录认证                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 端口分配

| 服务 | 端口 | 协议 | 用途 |
|------|------|------|------|
| xiaozhi-server | 8000 | WebSocket | ESP32设备实时通信 |
| xiaozhi-server | 8003 | HTTP | OTA固件更新、MCP视觉分析 |
| manager-web | 8001 | HTTP | Web管理界面 |
| manager-api | 8002 | HTTP | RESTful API |

---

## 核心部件详解

### 1. xiaozhi-server (Python) - 核心AI引擎

#### 1.1 目录结构

```
main/xiaozhi-server/
├── app.py                          # 应用入口
├── config.yaml                     # 主配置文件
├── config/                         # 配置模块
│   ├── config_loader.py            # 配置加载器
│   ├── manage_api_client.py        # manager-api客户端
│   ├── logger.py                   # 日志系统
│   └── settings.py                 # 设置管理
├── core/                           # 核心模块
│   ├── websocket_server.py         # WebSocket服务器
│   ├── http_server.py              # HTTP服务器
│   ├── connection.py               # 连接处理器
│   ├── auth.py                     # 认证模块
│   ├── handle/                     # 消息处理器
│   │   ├── intentHandler.py        # 意图识别处理
│   │   ├── receiveAudioHandle.py   # 音频接收处理
│   │   ├── sendAudioHandle.py      # 音频发送处理
│   │   ├── helloHandle.py          # 唤醒词处理
│   │   ├── reportHandle.py         # 数据上报处理
│   │   ├── abortHandle.py          # 中止处理
│   │   ├── textHandle.py           # 文本消息处理
│   │   └── textHandler/            # 文本子处理器
│   │       ├── helloMessageHandler.py
│   │       ├── iotMessageHandler.py
│   │       ├── mcpMessageHandler.py
│   │       └── ...
│   ├── providers/                  # AI服务提供者
│   │   ├── llm/                    # 大语言模型
│   │   │   ├── base.py             # LLM基类
│   │   │   ├── openai/             # OpenAI
│   │   │   ├── gemini/             # Google Gemini
│   │   │   ├── ollama/             # Ollama本地
│   │   │   ├── AliBL/              # 阿里百炼
│   │   │   ├── coze/               # Coze
│   │   │   ├── dify/               # Dify
│   │   │   └── ...
│   │   ├── asr/                    # 语音识别
│   │   │   ├── base.py
│   │   │   ├── fun_local/          # FunASR本地
│   │   │   ├── xunfei/             # 讯飞
│   │   │   └── ...
│   │   ├── tts/                    # 语音合成
│   │   │   ├── base.py
│   │   │   ├── edge/               # EdgeTTS
│   │   │   ├── linkerai/           # 灵犀
│   │   │   └── ...
│   │   ├── vad/                    # 语音活动检测
│   │   │   └── silero/             # SileroVAD
│   │   ├── intent/                 # 意图识别
│   │   │   ├── function_call/      # Function Calling
│   │   │   └── intent_llm/         # LLM意图
│   │   ├── memory/                 # 记忆管理
│   │   │   ├── mem_local_short/    # 本地短期记忆
│   │   │   ├── mem0ai/             # Mem0 AI
│   │   │   └── nomem/              # 无记忆
│   │   ├── vllm/                   # 向量LLM
│   │   └── tools/                  # 工具执行框架
│   │       ├── base/               # 基础类
│   │       ├── unified_tool_handler.py  # 统一工具处理器
│   │       ├── unified_tool_manager.py  # 工具管理器
│   │       ├── server_plugins/     # 服务端插件
│   │       ├── server_mcp/         # 服务端MCP
│   │       ├── device_iot/         # 设备IoT
│   │       ├── device_mcp/         # 设备MCP
│   │       └── mcp_endpoint/       # MCP接入点
│   └── utils/                      # 工具类
│       ├── modules_initialize.py   # 模块初始化
│       ├── gc_manager.py           # 垃圾回收管理
│       └── util.py                 # 通用工具
├── plugins_func/                   # 插件系统
│   ├── functions/                  # 插件函数
│   │   ├── get_weather.py          # 天气查询
│   │   ├── hass_set_state.py       # Home Assistant
│   │   └── ...
│   ├── loadplugins.py              # 插件加载器
│   └── register.py                 # 插件注册
├── performance_tester.py           # 性能测试工具
└── test/                           # 测试工具
    └── test_page.html              # 音频交互测试
```

#### 1.2 核心组件详解

##### A. 应用启动流程 (app.py)

```python
async def main():
    # 1. 环境检查
    check_ffmpeg_installed()

    # 2. 加载配置
    config = load_config()

    # 3. 生成认证密钥
    # 优先级: config.yaml > manager-api.secret > UUID
    auth_key = generate_auth_key(config)

    # 4. 初始化AI模块
    initialize_modules(config)

    # 5. 启动GC管理器（5分钟清理一次）
    gc_manager = get_gc_manager()

    # 6. 并发启动服务
    await asyncio.gather(
        WebSocketServer(config).start(),     # WebSocket服务
        SimpleHttpServer(config).start(),     # HTTP服务
        monitor_stdin(),                      # 标准输入监控
    )
```

**关键特性：**
- 异步架构（asyncio）：高并发处理多设备连接
- 模块化初始化：Provider模式动态加载AI服务
- 双服务器架构：WebSocket (实时通信) + HTTP (文件传输)

##### B. 连接处理器 (connection.py)

每个WebSocket连接创建一个独立的 `ConnectionHandler` 实例：

```python
class ConnectionHandler:
    # 核心属性
    session_id: str          # 会话ID (UUID)
    device_id: str           # 设备ID
    client_id: str           # 客户端ID
    dialogue: list           # 对话历史
    executor: ThreadPoolExecutor  # 线程池 (max_workers=5)

    # 状态标志
    client_abort: bool       # 客户端中止标志
    client_is_speaking: bool # 客户端正在说话
    server_is_responding: bool  # 服务器正在响应

    # 监听模式
    listen_mode: str         # "auto" 或 "manual"

    # 队列
    report_queue: asyncio.Queue  # 上报队列
```

**职责：**
1. 管理单个设备的WebSocket连接
2. 维护对话状态和历史
3. 协调各个处理器 (handle/) 的工作
4. 状态隔离（每个设备独立）

##### C. Provider模式 - AI服务抽象层

**设计原理：**
- 每种AI服务类型定义一个抽象基类
- 具体实现继承基类并实现接口
- 运行时根据配置动态加载

**LLM Provider示例：**

```python
# core/providers/llm/base.py
class LLMProviderBase(ABC):
    @abstractmethod
    async def response(self, session_id, dialogue):
        """流式响应生成"""
        pass

    @abstractmethod
    async def response_no_stream(self, session_id, dialogue):
        """非流式响应"""
        pass

    @abstractmethod
    async def response_with_functions(self, session_id, dialogue, functions):
        """支持function calling的响应"""
        pass
```

**支持的Provider类型：**
- **LLM**: OpenAI, Gemini, Ollama, 阿里百炼, Coze, Dify, FastGPT...
- **ASR**: FunASR, 讯飞, 火山引擎, 腾讯云, 阿里云...
- **TTS**: EdgeTTS, 灵犀, 火山引擎, 腾讯云, CosyVoice, FishSpeech...
- **VAD**: SileroVAD
- **Intent**: function_call, intent_llm, nointent
- **Memory**: mem_local_short, mem0ai, nomem

##### D. 工具执行框架 (tools/)

**工具类型定义：**

```python
class ToolType(Enum):
    SERVER_PLUGIN = "server_plugin"      # 服务端插件
    SERVER_MCP = "server_mcp"            # 服务端MCP
    DEVICE_IOT = "device_iot"            # 设备IoT控制
    DEVICE_MCP = "device_mcp"            # 设备MCP
    MCP_ENDPOINT = "mcp_endpoint"        # MCP接入点
```

**统一工具处理器：**

```python
class UnifiedToolHandler:
    async def handle_llm_function_call(
        self,
        function_name: str,
        function_args: dict,
        tool_type: ToolType
    ):
        # 根据工具类型分发到不同执行器
        if tool_type == ToolType.SERVER_PLUGIN:
            return await self._execute_server_plugin()
        elif tool_type == ToolType.SERVER_MCP:
            return await self._execute_server_mcp()
        elif tool_type == ToolType.DEVICE_IOT:
            return await self._execute_device_iot()
        # ...
```

**工具注册和发现：**
- 服务端插件：`plugins_func/functions/` 目录下的Python脚本
- 服务端MCP：配置文件中的MCP服务器列表
- 设备IoT/MCP：设备上报的工具列表
- MCP接入点：外部MCP服务器

##### E. 配置系统

**配置加载流程：**

```
1. 读取默认配置 (config.yaml)
   ↓
2. 读取自定义配置 (data/.config.yaml)
   ↓
3. 检查是否配置了 manager-api.url
   ├─ 是 → 调用 get_config_from_api_async()
   │      ├─ 从manager-api获取远程配置
   │      └─ 合并本地和远程配置
   └─ 否 → 仅使用本地配置
   ↓
4. 创建必要目录
   ↓
5. 缓存配置
```

**配置优先级：**
```
远程API配置 > 自定义本地配置 > 默认配置
(当启用 read_config_from_api 时)
```

**动态更新机制：**
- `WebSocketServer.update_config()`: 异步更新配置
- 使用 `asyncio.Lock` 保证线程安全
- 检查VAD/ASR是否需要重新初始化
- 重新加载AI模块

---

### 2. manager-api (Java) - 管理后端

#### 2.1 目录结构

```
main/manager-api/src/main/java/xiaozhi/
├── AdminApplication.java           # Spring Boot入口
├── modules/                        # 业务模块
│   ├── config/                     # 配置管理
│   │   ├── controller/ConfigController.java
│   │   ├── service/ConfigService.java
│   │   ├── dto/AgentModelsDTO.java
│   │   └── init/SystemInitConfig.java
│   ├── device/                     # 设备管理
│   │   ├── controller/DeviceController.java
│   │   ├── service/DeviceService.java
│   │   ├── entity/DeviceEntity.java
│   │   ├── dao/DeviceDao.java
│   │   └── dto/DeviceRegisterDTO.java
│   ├── agent/                      # 智能体管理
│   │   ├── controller/AgentController.java
│   │   ├── service/AgentService.java
│   │   ├── entity/AiAgentEntity.java
│   │   ├── dao/AgentDao.java
│   │   └── service/biz/            # 业务逻辑
│   ├── model/                      # 模型配置
│   │   ├── controller/ModelController.java
│   │   ├── service/ModelService.java
│   │   ├── entity/ModelConfigEntity.java
│   │   └── entity/ModelProviderEntity.java
│   ├── knowledge/                  # 知识库
│   │   ├── controller/KnowledgeController.java
│   │   ├── service/KnowledgeService.java
│   │   ├── entity/KnowledgeBaseEntity.java
│   │   └── rag/                    # RAG实现
│   ├── security/                   # 安全认证
│   │   ├── controller/LoginController.java
│   │   ├── service/SecurityService.java
│   │   ├── oauth2/                 # OAuth2
│   │   ├── password/               # 密码管理
│   │   └── user/SecurityUser.java
│   ├── sys/                        # 系统管理
│   │   ├── controller/SysController.java
│   │   ├── service/SysService.java
│   │   ├── entity/SysUserEntity.java
│   │   ├── entity/SysDictTypeEntity.java
│   │   └── redis/                  # Redis缓存
│   ├── timbre/                     # 音色管理
│   │   ├── controller/TimbreController.java
│   │   └── service/TimbreService.java
│   ├── voiceclone/                 # 声音克隆
│   │   ├── controller/VoiceCloneController.java
│   │   └── service/VoiceCloneService.java
│   └── ota/                        # OTA固件
│       ├── controller/OtaController.java
│       └── service/OtaService.java
├── common/                         # 通用组件
│   ├── config/                     # 框架配置
│   │   ├── MybatisPlusConfig.java  # MyBatis Plus
│   │   ├── SwaggerConfig.java      # Swagger文档
│   │   ├── RedisConfig.java        # Redis
│   │   └── AsyncConfig.java        # 异步任务
│   ├── redis/                      # Redis工具
│   │   ├── RedisUtils.java
│   │   └── RedisKeys.java
│   ├── entity/BaseEntity.java      # 基础实体
│   ├── dao/BaseDao.java            # 基础DAO
│   ├── utils/                      # 工具类
│   │   ├── HashEncryptionUtil.java
│   │   └── AESUtils.java
│   ├── xss/                        # XSS防护
│   │   ├── XssFilter.java
│   │   └── SqlFilter.java
│   ├── annotation/                 # 自定义注解
│   │   ├── LogOperation.java
│   │   └── DataFilter.java
│   ├── interceptor/                # 拦截器
│   └── exception/                  # 异常处理
│       └── RenExceptionHandler.java
└── resources/
    ├── application.yml             # Spring配置
    ├── db/changelog/               # Liquibase变更
    │   ├── 202505182234.sql
    │   └── ...
    └── mapper/                     # MyBatis映射
        ├── agent/AgentDao.xml
        ├── device/DeviceDao.xml
        ├── model/ModelConfigDao.xml
        └── ...
```

#### 2.2 核心模块详解

##### A. 配置管理模块 (config/)

**核心API端点：**

```java
@RestController
@RequestMapping("/config")
public class ConfigController {

    // 获取服务器基础配置
    @PostMapping("/server-base")
    public Result getConfig(@RequestBody ConfigRequestDTO dto) {
        // 1. 从数据库读取智能体配置
        // 2. 读取模型配置 (LLM, ASR, TTS等)
        // 3. 读取工具配置 (plugins, MCP)
        // 4. 组装成YAML格式
        // 5. 返回给xiaozhi-server
    }

    // 获取智能体模型配置
    @PostMapping("/agent-models")
    public Result getAgentModels(
        @RequestParam String macAddress,
        @RequestParam String selectedModule
    ) {
        // 根据设备MAC和选中模块返回配置
    }
}
```

**配置组装流程：**

```
1. 查询智能体配置 (ai_agent表)
   ├─ 基础信息 (名称、描述)
   ├─ 模型配置 (LLM、ASR、TTS)
   └─ 工具配置 (插件、MCP)
   ↓
2. 查询模型详情 (model_config表)
   ├─ 模型名称
   ├─ API密钥
   ├─ 端点URL
   └─ 其他参数
   ↓
3. 查询工具列表 (agent_plugin_mapping表)
   ├─ 服务端插件
   ├─ 服务端MCP
   └─ MCP接入点
   ↓
4. 组装成YAML格式
   ↓
5. 返回给xiaozhi-server
```

##### B. 设备管理模块 (device/)

**设备注册流程：**

```
ESP32设备
  ↓
[发送注册请求]
  ├─ POST /device/register
  ├─ 携带: deviceCode, macAddress, deviceType
  └─ 接收: 6位验证码
  ↓
Redis缓存
  ├─ key: device:captcha:{code}
  ├─ value: macAddress
  └─ TTL: 5分钟
  ↓
用户在Web界面输入验证码
  ↓
[设备绑定]
  ├─ POST /device/bind/{agentId}/{deviceCode}
  ├─ 验证码校验
  ├─ 绑定到智能体
  └─ 设备激活
```

**关键实体：**

```java
@TableName("device")
public class DeviceEntity {
    private Long id;
    private String deviceCode;      // 设备编码
    private String macAddress;      // MAC地址
    private String deviceType;      // 设备类型
    private Long agentId;           // 绑定的智能体ID
    private Integer status;         // 设备状态
    private Date createTime;
    private Date updateTime;
}
```

##### C. 智能体管理模块 (agent/)

**核心功能：**
- 智能体CRUD操作
- 智能体与设备的关联
- 聊天历史记录管理
- 插件映射管理

**关键实体：**

```java
@TableName("ai_agent")
public class AiAgentEntity {
    private Long id;
    private String name;            // 智能体名称
    private String description;     // 描述
    private Long llmModelId;        // LLM模型ID
    private Long asrModelId;        // ASR模型ID
    private Long ttsModelId;        # TTS模型ID
    private String systemPrompt;    // 系统提示词
    private String welcomeMessage;  // 欢迎语
    private Integer status;         // 状态
}
```

##### D. 模型配置模块 (model/)

**支持的模型类型：**
- LLM模型（OpenAI、Gemini、Ollama等）
- ASR模型（FunASR、讯飞、火山等）
- TTS模型（EdgeTTS、灵犀、火山等）
- 向量模型（用于知识库）

**模型配置表结构：**

```sql
CREATE TABLE model_config (
    id BIGINT PRIMARY KEY,
    provider_id BIGINT,          -- 提供者ID
    model_name VARCHAR(100),     -- 模型名称
    api_key VARCHAR(500),        -- API密钥
    base_url VARCHAR(200),       -- 基础URL
    model_type VARCHAR(50),      -- 模型类型 (llm/asr/tts)
    config_json TEXT,            -- 配置JSON
    status INT,
    create_time DATETIME,
    update_time DATETIME
);
```

##### E. 三层架构实现

```
┌─────────────────────────────────────────────┐
│           Controller层 (控制器)              │
│  • 接收HTTP请求                             │
│  • 参数校验                                  │
│  • 调用Service                               │
│  • 返回JSON响应                              │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│           Service层 (业务逻辑)               │
│  • 业务规则实现                              │
│  • 事务管理 (@Transactional)                │
│  • 调用DAO                                   │
│  • 缓存管理                                  │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│           DAO层 (数据访问)                   │
│  • MyBatis-Plus Mapper                      │
│  • 数据库CRUD                                │
│  • 复杂查询                                  │
└─────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│              MySQL数据库                     │
└─────────────────────────────────────────────┘
```

#### 2.3 数据库表结构

**核心表：**

```sql
-- 智能体表
ai_agent (id, name, llm_model_id, asr_model_id, tts_model_id, ...)

-- 设备表
device (id, device_code, mac_address, agent_id, status, ...)

-- 模型配置表
model_config (id, provider_id, model_name, api_key, ...)

-- 模型提供者表
model_provider (id, provider_name, provider_type, ...)

-- 聊天历史表
ai_agent_chat_history (id, agent_id, session_id, user_message, ai_response, ...)

-- 插件映射表
agent_plugin_mapping (id, agent_id, plugin_name, plugin_type, ...)

-- 知识库表
knowledge_base (id, name, description, rag_config, ...)

-- 用户表
sys_user (id, username, password, salt, ...)

-- 字典表
sys_dict_type (id, dict_name, dict_type, ...)
sys_dict_data (id, dict_type_id, dict_label, dict_value, ...)
```

---

### 3. manager-web (Vue.js) - Web管理界面

#### 3.1 目录结构

```
main/manager-web/src/
├── main.js                         # 应用入口
├── App.vue                         # 根组件
├── router/                         # 路由
│   └── index.js                    # 路由配置
├── store/                          # Vuex状态管理
│   └── index.js                    # Store配置
├── views/                          # 页面组件
│   ├── Login.vue                   # 登录页
│   ├── DeviceManagement.vue        # 设备管理
│   ├── AgentManagement.vue         # 智能体管理
│   ├── ModelConfig.vue             # 模型配置
│   └── ...
├── components/                     # 可复用组件
│   ├── HeaderBar.vue               # 顶部导航
│   ├── AddDeviceDialog.vue         # 添加设备对话框
│   └── ...
├── apis/                           # API通信
│   ├── api.js                      # API基础配置
│   ├── httpRequest.js              # HTTP请求封装
│   └── module/                     # 模块化API
│       ├── agent.js                # 智能体API
│       ├── device.js               # 设备API
│       ├── model.js                # 模型API
│       └── ...
├── styles/                         # 样式
│   └── global.scss                 # 全局样式
└── assets/                         # 静态资源
    ├── images/
    └── fonts/
```

#### 3.2 核心特性

**单页应用 (SPA)：**
- 整个应用加载一个HTML文件
- Vue Router管理路由切换
- 无需刷新页面

**Vuex状态管理：**

```javascript
// store/index.js
export default new Vuex.Store({
  state: {
    userInfo: null,      // 用户信息
    deviceList: [],      // 设备列表
    agentList: [],       // 智能体列表
    token: null,         // 认证令牌
  },
  mutations: {
    SET_USER_INFO(state, userInfo) {
      state.userInfo = userInfo;
    },
    SET_TOKEN(state, token) {
      state.token = token;
    }
  },
  actions: {
    async login({ commit }, { username, password }) {
      const res = await loginAPI(username, password);
      commit('SET_TOKEN', res.token);
      commit('SET_USER_INFO', res.userInfo);
    }
  }
});
```

**API通信层：**

```javascript
// apis/module/agent.js
import http from '../httpRequest';

export function getAgentList(params) {
  return http.get('/agent/list', { params });
}

export function createAgent(data) {
  return http.post('/agent/create', data);
}

export function updateAgent(id, data) {
  return http.put(`/agent/update/${id}`, data);
}
```

---

### 4. manager-mobile (uni-app) - 移动端管理

#### 4.1 技术栈

```
uni-app v3
  ├── Vue 3 (Composition API)
  ├── Vite (构建工具)
  ├── pinia (状态管理)
  ├── alova + @alova/adapter-uniapp (网络请求)
  ├── UnoCSS (原子化CSS)
  └── TypeScript (类型安全)
```

#### 4.2 跨平台支持

| 平台 | 支持 | 构建命令 |
|------|------|---------|
| H5 | ✅ | `pnpm dev:h5` |
| iOS | ✅ | `pnpm dev:app-ios` |
| Android | ✅ | `pnpm dev:app-android` |
| 微信小程序 | ✅ | `pnpm dev:mp-weixin` |

---

## 数据流和交互机制

### 1. ESP32 → xiaozhi-server 完整处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                         ESP32设备                                │
│               (麦克风采集音频 → Opus编码)                        │
└────────────────┬────────────────────────────────────────────────┘
                 │ WebSocket连接
                 │ ws://host:8000/xiaozhi/v1/?device-id=xxx
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│              WebSocketServer (websocket_server.py)              │
│  1. 接收连接请求                                                 │
│  2. 验证设备认证 (device-id, authorization)                      │
│  3. 创建ConnectionHandler实例                                    │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│            ConnectionHandler (connection.py)                    │
│  • 会话管理 (session_id, dialogue)                              │
│  • 状态维护 (client_is_speaking, server_is_responding)          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├───────────────────────────────────────────────┐
                 │                                               │
                 ↓                                               ↓
┌────────────────────────────────┐     ┌──────────────────────────────┐
│  音频接收 (receiveAudioHandle)  │     │  文本消息 (textHandle)        │
│  1. 接收Opus音频数据            │     │  • hello消息                  │
│  2. VAD检测 (是否说话)          │     │  • ping消息                   │
│  3. ASR转文本                   │     │  • IoT控制消息                │
│  4. 传递给意图处理器            │     │  • MCP消息                    │
└────────────────┬───────────────┘     └──────────────┬───────────────┘
                 │                                     │
                 └─────────────┬───────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│               意图识别 (intentHandler.py)                        │
│  1. 检查唤醒词                                                   │
│  2. 调用Intent Provider                                          │
│     ├─ function_call: LLM直接生成function call                  │
│     ├─ intent_llm: LLM识别意图类型                              │
│     └─ nointent: 不识别意图                                     │
│  3. 生成action (chat/function_call/report)                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─────────────┬─────────────────────────────┐
                 │             │                             │
                 ↓             ↓                             ↓
    ┌───────────────┐  ┌────────────────┐      ┌──────────────────┐
    │  纯对话       │  │  Function Call  │      │  数据上报        │
    │  (chat)       │  │  (执行工具)     │      │  (report)        │
    └───────┬───────┘  └────────┬───────┘      └──────────┬───────┘
            │                   │                          │
            │                   ↓                          │
            │     ┌─────────────────────────────┐          │
            │     │  UnifiedToolHandler         │          │
            │     │  • server_plugin            │          │
            │     │  • server_mcp               │          │
            │     │  • device_iot               │          │
            │     │  • device_mcp               │          │
            │     │  • mcp_endpoint             │          │
            │     └────────┬────────────────────┘          │
            │              │                               │
            │              ↓                               │
            │     ┌─────────────────────────────┐          │
            │     │  执行结果返回给LLM          │          │
            │     └────────┬────────────────────┘          │
            │              │                               │
            └──────────────┴───────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                  LLM对话生成 (LLM Provider)                     │
│  1. 构建对话上下文                                               │
│     ├─ 系统提示词                                                │
│     ├─ 对话历史 (从Memory Provider获取)                          │
│     ├─ 工具列表 (functions)                                      │
│     └─ 当前用户输入                                              │
│  2. 调用LLM API (流式生成)                                       │
│  3. 返回文本回复                                                 │
│  4. 更新Memory (保存对话历史)                                    │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│               TTS音频生成 (sendAudioHandle)                      │
│  1. 文本分句 (FIRST/MIDDLE/LAST)                                │
│  2. 调用TTS Provider                                             │
│  3. 音频流控管理                                                 │
│  4. Opus编码                                                     │
│  5. 通过WebSocket发送音频包                                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ESP32设备播放音频                           │
└─────────────────────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│             聊天记录上报 (reportHandle.py)                       │
│  • 异步上报到manager-api                                         │
│  • POST /agent/chat-history/report                              │
│  • 保存到数据库 (ai_agent_chat_history)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 配置同步流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    manager-web (用户操作)                        │
│  • 修改LLM模型                                                   │
│  • 修改ASR/TTS配置                                               │
│  • 修改工具列表                                                  │
│  • 修改系统提示词                                                │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP POST
                 │ (JSON)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                manager-api (ConfigController)                   │
│  POST /model/update                                              │
│  POST /agent/update                                              │
│  ...                                                             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MySQL数据库 (持久化)                          │
│  • model_config表                                                │
│  • ai_agent表                                                    │
│  • agent_plugin_mapping表                                        │
│  • ...                                                           │
└─────────────────────────────────────────────────────────────────┘
                 │
                 │ xiaozhi-server定期拉取
                 │ (或启动时拉取)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│              xiaozhi-server (config_loader.py)                  │
│  1. 调用 get_config_from_api_async()                             │
│  2. POST /config/server-base                                     │
│  3. 接收YAML格式配置                                             │
│  4. 合并本地和远程配置                                           │
│  5. 缓存配置                                                     │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│             modules_initialize.py (模块初始化)                  │
│  1. 检查VAD是否需要更新                                          │
│  2. 检查ASR是否需要更新                                          │
│  3. 动态导入Provider类                                           │
│  4. 实例化AI模块                                                 │
│  5. 更新全局配置                                                 │
└─────────────────────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      配置生效                                    │
│  • 新连接使用新配置                                              │
│  • 现有连接保持旧配置                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3. WebSocket vs HTTP 协议使用场景

| 协议 | 端口 | 用途 | 特点 |
|------|------|------|------|
| **WebSocket** | 8000 | ESP32实时通信 | • 全双工双向通信<br>• 低延迟<br>• 持久连接<br>• 支持二进制数据<br>• 音频流传输 |
| **HTTP** | 8003 | OTA、MCP视觉分析 | • 请求-响应模式<br>• 无状态<br>• 支持文件传输<br>• 易于扩展 |
| **HTTP** | 8002 | manager-api | • RESTful API<br>• JSON数据<br>• 标准HTTP方法 |
| **HTTP** | 8001 | manager-web | • 静态资源服务<br>• SPA应用 |

**协议选择原则：**
- 实时性要求高 → WebSocket
- 单次请求-响应 → HTTP
- 大文件传输 → HTTP
- 音频流传输 → WebSocket

---

## 关键设计模式

### 1. Provider模式 (策略模式)

**目的：** 统一AI服务接口，支持动态切换

**实现：**
```python
# 抽象基类
class LLMProviderBase(ABC):
    @abstractmethod
    async def response(self, session_id, dialogue):
        pass

# 具体实现
class OpenAIProvider(LLMProviderBase):
    async def response(self, session_id, dialogue):
        # OpenAI实现
        pass

class GeminiProvider(LLMProviderBase):
    async def response(self, session_id, dialogue):
        # Gemini实现
        pass

# 工厂加载
def load_provider(config):
    provider_name = config['llm']['selected_module']
    if provider_name == 'openai':
        return OpenAIProvider(config)
    elif provider_name == 'gemini':
        return GeminiProvider(config)
```

**优势：**
- 统一接口，降低耦合
- 易于扩展新的AI服务
- 运行时动态切换

### 2. 单例模式

**应用场景：**
- `ManageApiClient`: 全局唯一的API客户端
- `GCManager`: 垃圾回收管理器
- `ConfigLoader`: 配置加载器

**实现：**
```python
class ManageApiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 3. 观察者模式

**应用场景：**
- 配置更新通知
- WebSocket消息分发

### 4. 责任链模式

**应用场景：**
- `textHandler/`: 多个消息处理器链式处理
- 每个handler检查是否能处理，能则处理，否则传递给下一个

```python
# textMessageHandlerRegistry.py
handlers = [
    HelloMessageHandler(),
    PingMessageHandler(),
    IoTMessageHandler(),
    McpMessageHandler(),
    # ...
]

for handler in handlers:
    if handler.can_handle(message):
        await handler.handle(message)
        break
```

### 5. 工厂模式

**应用场景：**
- `modules_initialize.py`: 根据配置创建Provider实例
- `unified_tool_manager.py`: 根据工具类型创建执行器

---

## 核心文件清单

### xiaozhi-server (Python)

| 文件路径 | 核心职责 | 关键方法/类 |
|---------|---------|-----------|
| `app.py` | 应用启动入口 | `main()`, `wait_for_exit()` |
| `connection.py` | 连接管理和会话状态 | `ConnectionHandler`, `handle_connection()` |
| `websocket_server.py` | WebSocket服务器 | `WebSocketServer.start()`, `_handle_connection()` |
| `http_server.py` | HTTP服务器 | `SimpleHttpServer.start()` |
| `config_loader.py` | 配置加载和合并 | `load_config()`, `get_config_from_api_async()` |
| `manage_api_client.py` | manager-api客户端 | `ManageApiClient`, HTTP请求封装 |
| `modules_initialize.py` | AI模块动态加载 | `initialize_modules()`, Provider工厂 |
| `intentHandler.py` | 意图识别核心逻辑 | `handle_user_intent()`, `process_intent_result()` |
| `receiveAudioHandle.py` | 音频接收和ASR | `handleAudioMessage()`, `startToChat()` |
| `sendAudioHandle.py` | TTS和音频发送 | `sendAudioMessage()`, `sendAudio()` |
| `reportHandle.py` | 聊天记录上报 | `report()`, 异步队列处理 |
| `unified_tool_handler.py` | 统一工具执行 | `handle_llm_function_call()` |
| `unified_tool_manager.py` | 工具注册和管理 | `get_all_functions()` |
| `providers/llm/base.py` | LLM抽象基类 | `LLMProviderBase` |
| `providers/asr/base.py` | ASR抽象基类 | `ASRProviderBase` |
| `providers/tts/base.py` | TTS抽象基类 | `TTSProviderBase` |

### manager-api (Java)

| 文件路径 | 核心职责 | 关键方法/类 |
|---------|---------|-----------|
| `AdminApplication.java` | Spring Boot入口 | `main()` |
| `ConfigController.java` | 配置管理接口 | `getConfig()`, `getAgentModels()` |
| `ConfigService.java` | 配置业务逻辑 | 组装配置YAML |
| `DeviceController.java` | 设备管理接口 | `registerDevice()`, `bindDevice()` |
| `DeviceService.java` | 设备业务逻辑 | `deviceActivation()` |
| `AgentController.java` | 智能体管理接口 | CRUD操作 |
| `AgentService.java` | 智能体业务逻辑 | 智能体与设备关联 |
| `ModelController.java` | 模型配置接口 | 模型CRUD |
| `ModelService.java` | 模型业务逻辑 | 模型验证和配置 |
| `MybatisPlusConfig.java` | MyBatis Plus配置 | 分页插件、数据权限 |
| `RedisConfig.java` | Redis配置 | 连接池、序列化 |
| `SwaggerConfig.java` | Swagger文档配置 | API文档生成 |
| `RenExceptionHandler.java` | 全局异常处理 | 统一错误响应 |

### manager-web (Vue.js)

| 文件路径 | 核心职责 | 关键组件/方法 |
|---------|---------|-------------|
| `main.js` | 应用入口 | Vue实例创建 |
| `App.vue` | 根组件 | 应用布局 |
| `router/index.js` | 路由配置 | 路由表、导航守卫 |
| `store/index.js` | Vuex状态管理 | State、Mutations、Actions |
| `apis/httpRequest.js` | HTTP请求封装 | 拦截器、错误处理 |

---

## 总结

xiaozhi-esp32-server 是一个**高度模块化、可扩展的语音AI系统**，核心特点：

1. **分层清晰**：前端(Web/Mobile) → 后端API(Java) → 核心引擎(Python) → 硬件(ESP32)
2. **Provider模式**：统一AI服务接口，支持灵活切换
3. **异步架构**：Python asyncio实现高并发
4. **配置驱动**：动态配置更新，无需重启
5. **工具扩展**：插件化工具系统，支持Function Calling
6. **双协议支持**：WebSocket(实时) + HTTP(管理)

核心数据流：**音频 → VAD → ASR → Intent → LLM → Function Call → TTS → 音频输出**
