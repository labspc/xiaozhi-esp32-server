# ORica 三语言改造边界与职责划分

## 文档目的

重新审视 Python、Mojo、Rust 三种语言在 ORica 框架中的职责边界，确保：
1. **单一职责** - 每种语言做自己最擅长的事
2. **Python 专注 AI** - AI SDK 集成 + 胶水代码
3. **Rust 做 Mojo 不擅长的** - 系统编程、并发、I/O
4. **Mojo 做性能密集型** - 数值计算、音频处理

---

## 第一部分：三语言优势分析

### 1.1 Rust 的优势与适用场景

**核心优势：**
- ✅ 系统编程（无 GC，零成本抽象）
- ✅ 并发和异步（tokio，多线程安全）
- ✅ 网络 I/O（高性能 WebSocket、HTTP）
- ✅ 内存安全（编译时检查）
- ✅ 生态成熟（数据库、序列化、加密）

**适用场景：**
```
✅ WebSocket 服务器（连接管理、心跳检测）
✅ HTTP API 服务器（RESTful、路由、JWT）
✅ 数据库操作（SQL、KV 存储）
✅ 配置管理（YAML 解析、热更新）
✅ 设备管理（注册、状态、OTA）
✅ 并发调度（任务队列、线程池）
✅ 对话历史存储（CRUD 操作）
✅ 文件 I/O（日志、缓存）
```

**不适用场景：**
```
❌ AI SDK 集成（OpenAI、FunASR 只有 Python SDK）
❌ 动态插件系统（Rust 是静态编译语言）
❌ 快速原型（编译慢，学习曲线陡）
❌ 数值密集计算（不如 Mojo 的 SIMD）
```

---

### 1.2 Mojo 的优势与适用场景

**核心优势：**
- ✅ SIMD 向量化（10-100 倍加速）
- ✅ 零开销抽象（类似 Rust）
- ✅ Python 互操作（无缝调用）
- ✅ 数值计算优化（替代 NumPy）
- ✅ 静态编译（性能接近 C）

**适用场景：**
```
✅ 音频编解码（Opus、PCM）
✅ 音频数值处理（重采样、转换）
✅ VAD 特征提取（能量、过零率）
✅ 信号处理（FFT、滤波）
✅ 图像处理（未来扩展）
✅ 机器学习推理（未来，替代 PyTorch）
```

**不适用场景：**
```
❌ 网络 I/O（异步支持有限）
❌ 文件 I/O（标准库不完善）
❌ 数据库操作（无成熟库）
❌ 动态特性（静态编译语言）
❌ 复杂业务逻辑（不如 Python 灵活）
```

---

### 1.3 Python 的优势与适用场景

**核心优势：**
- ✅ AI 生态（OpenAI、FunASR、Whisper 等官方 SDK）
- ✅ 动态性（动态加载、反射、eval）
- ✅ 快速开发（脚本语言，无编译）
- ✅ 胶水语言（连接不同组件）
- ✅ 丰富的库（asyncio、aiohttp、pydantic）

**适用场景：**
```
✅ AI SDK 调用（OpenAI、FunASR、Edge TTS）
✅ Plugin 动态加载和执行（用户自定义插件）
✅ AI 逻辑编排（协调 ASR → LLM → TTS 流程）
✅ 胶水代码（连接 Rust、Mojo、AI SDK）
✅ 业务逻辑（不涉及性能的逻辑）
```

**不适用场景：**
```
❌ 性能密集计算（GIL 限制，慢）
❌ 系统编程（内存管理、并发）
❌ 网络服务器（性能不如 Rust）
❌ 音频编解码（慢，不如 Mojo）
```

---

## 第二部分：当前架构的问题

### 2.1 Layer 3 (Python AI Logic) 的职责过重

**当前 Layer 3 包含的内容：**
```python
Layer 3: AI Logic (Python)
├── Provider 系统（ASR/TTS/LLM/VAD/Memory）
├── Plugin 系统框架
├── Dialogue Manager（对话管理）
├── Memory System（记忆系统）
└── Connection Handler（连接处理）
```

**问题分析：**

**1. Connection Handler 不应该在 Python**
```python
# 当前（错误）：Python 处理 WebSocket 连接
class ConnectionHandler:
    async def handle_connection(self, websocket):
        async for message in websocket:
            # 处理消息...
```

**问题：**
- ❌ WebSocket 连接管理是系统编程，Rust 更合适
- ❌ Python 的 asyncio 性能不如 Rust tokio
- ❌ 并发连接数受限于 GIL

**应该：**
- ✅ Rust 处理 WebSocket 生命周期（连接、心跳、断开）
- ✅ Rust 处理并发调度（多连接管理）
- ✅ Python 只负责 AI 逻辑编排

---

**2. Dialogue Manager 不应该完全在 Python**
```python
# 当前（错误）：Python 管理对话历史
class DialogueManager:
    def __init__(self):
        self.messages = []  # 内存存储

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
```

**问题：**
- ❌ 对话历史存储是数据库操作，Rust 更合适
- ❌ 内存存储不持久化，重启丢失
- ❌ 多连接共享数据需要锁，Python GIL 是瓶颈

**应该：**
- ✅ Rust 处理对话历史的存储和查询（数据库 CRUD）
- ✅ Python 只负责调用 LLM 和摘要逻辑

---

**3. Memory System 不应该完全在 Python**
```python
# 当前（错误）：Python 实现所有记忆逻辑
class LocalShortMemory:
    async def save(self, session_id, messages):
        # 保存到本地文件或内存
        pass
```

**问题：**
- ❌ 本地存储（文件、数据库）应该用 Rust
- ❌ Python 文件 I/O 性能差

**应该：**
- ✅ Rust 处理本地存储（LocalShort）
- ✅ Python 只负责调用云端 API（Mem0）

---

**4. Plugin 系统框架可以部分用 Rust**
```python
# 当前（部分正确）：Python 实现 Plugin 框架
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register(self, plugin):
        self.plugins[plugin.name] = plugin
```

**问题：**
- ⚠️ Plugin 注册和管理可以用 Rust（框架部分）
- ⚠️ Plugin 执行需要 Python（动态性）

**应该：**
- ✅ Rust 处理 Plugin 注册、元数据管理、调度
- ✅ Python 处理 Plugin 执行环境（动态加载和运行）

---

## 第三部分：重新划分的架构

### 3.1 改造后的分层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Device（ESP32/树莓派）                            │
└─────────────────────────────────────────────────────────────┘
                          ↓ WebSocket (Opus)
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Application（用户应用代码）- Python              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 用户自定义 Plugin                                      │  │
│  │ 用户业务逻辑                                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ Plugin API
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: AI Orchestration（AI 编排层）- Python           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✅ AI Provider 调用（OpenAI, FunASR, Edge TTS）       │  │
│  │    - ASR.transcribe()                                  │  │
│  │    - LLM.chat()                                        │  │
│  │    - TTS.synthesize()                                  │  │
│  │                                                        │  │
│  │ ✅ Plugin 执行环境（动态加载和执行）                   │  │
│  │    - 动态 import                                       │  │
│  │    - 沙箱执行                                          │  │
│  │                                                        │  │
│  │ ✅ AI 逻辑编排（协调流程）                             │  │
│  │    - 音频 → ASR → LLM → Plugin → TTS                  │  │
│  │    - 错误处理和重试                                    │  │
│  │                                                        │  │
│  │ ✅ 胶水代码（连接各层）                                │  │
│  │    - 调用 Rust API                                     │  │
│  │    - 调用 Mojo 函数                                    │  │
│  │    - 调用 AI SDK                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ FFI / IPC
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Performance（性能层）- Mojo                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✅ Opus 编解码（FFI libopus）                          │  │
│  │ ✅ PCM 格式转换（SIMD）                                │  │
│  │ ✅ VAD 特征提取（能量、过零率）                        │  │
│  │ ✅ 音频缓冲区管理                                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ Function Call
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Infrastructure（基础设施层）- Rust              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✅ WebSocket 服务器（连接管理、心跳、并发）            │  │
│  │ ✅ HTTP API 服务器（配置、设备管理）                   │  │
│  │ ✅ 对话历史存储（DialogueStorage）                     │  │
│  │ ✅ 记忆系统存储（MemoryStorage）                       │  │
│  │ ✅ Plugin 注册和调度（PluginRegistry）                 │  │
│  │ ✅ 设备管理（注册、状态、OTA）                         │  │
│  │ ✅ 统一存储抽象（EloqKV）                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌─────────────────────────────────────────────────────────────┐
│  Layer 0: Frontend（前端层）- Svelte                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✅ 管理后台                                            │  │
│  │ ✅ 设备管理界面                                        │  │
│  │ ✅ 监控面板                                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.2 各层职责详解

#### **Layer 1: Infrastructure（Rust）**

**核心职责：系统编程 + 并发 + I/O**

**1. WebSocket 服务器（orica-server）**
```rust
// Rust: 处理连接生命周期
pub struct ConnectionManager {
    connections: HashMap<String, WebSocket>,
    heartbeat_interval: Duration,
}

impl ConnectionManager {
    pub async fn handle_connection(&mut self, ws: WebSocket) {
        // 1. 注册连接
        let device_id = self.register_device(&ws).await;

        // 2. 启动心跳检测
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_secs(10)).await;
                if ws.send_ping().await.is_err() {
                    break; // 连接断开
                }
            }
        });

        // 3. 消息路由
        while let Some(msg) = ws.recv().await {
            match msg {
                Message::Binary(audio_data) => {
                    // 转发到 Python AI Orchestrator
                    self.forward_to_ai(device_id, audio_data).await;
                }
                Message::Text(cmd) => {
                    self.handle_command(device_id, cmd).await;
                }
                _ => {}
            }
        }

        // 4. 清理连接
        self.unregister_device(device_id).await;
    }
}
```

---

**2. 对话历史存储（DialogueStorage）**
```rust
// Rust: 对话历史 CRUD
pub struct DialogueStorage {
    db: EloqKV,
}

impl DialogueStorage {
    pub async fn add_message(&self, session_id: &str, role: &str, content: &str) {
        let key = format!("dialogue:{}:messages", session_id);
        let message = json!({
            "role": role,
            "content": content,
            "timestamp": Utc::now().timestamp()
        });
        self.db.rpush(&key, &message.to_string()).await;
    }

    pub async fn get_history(&self, session_id: &str, limit: usize) -> Vec<Message> {
        let key = format!("dialogue:{}:messages", session_id);
        let messages = self.db.lrange(&key, -(limit as i64), -1).await;
        messages.iter().map(|m| serde_json::from_str(m).unwrap()).collect()
    }

    pub async fn clear_history(&self, session_id: &str) {
        let key = format!("dialogue:{}:messages", session_id);
        self.db.del(&key).await;
    }
}
```

---

**3. Plugin 注册和调度（PluginRegistry）**
```rust
// Rust: Plugin 元数据管理和调度
pub struct PluginRegistry {
    plugins: HashMap<String, PluginMetadata>,
}

pub struct PluginMetadata {
    pub name: String,
    pub description: String,
    pub schema: serde_json::Value, // JSON Schema
    pub language: PluginLanguage,  // Python / Rust / Wasm
}

impl PluginRegistry {
    pub fn register(&mut self, plugin: PluginMetadata) {
        self.plugins.insert(plugin.name.clone(), plugin);
    }

    pub fn get_plugin(&self, name: &str) -> Option<&PluginMetadata> {
        self.plugins.get(name)
    }

    pub async fn execute(&self, name: &str, params: serde_json::Value) -> Result<String> {
        let plugin = self.get_plugin(name).ok_or("Plugin not found")?;

        match plugin.language {
            PluginLanguage::Python => {
                // 调用 Python 执行环境
                self.execute_python_plugin(name, params).await
            }
            PluginLanguage::Rust => {
                // 直接调用 Rust 函数（编译时链接）
                self.execute_rust_plugin(name, params).await
            }
        }
    }
}
```

---

#### **Layer 2: Performance（Mojo）**

**核心职责：数值密集计算 + 音频处理**

**1. Opus 编解码**
```mojo
# Mojo: 高性能 Opus 编解码
from sys import ffi

fn decode_opus(
    opus_data: DTypePointer[DType.uint8],
    opus_len: Int,
    pcm_out: DTypePointer[DType.int16],
    frame_size: Int
) -> Int:
    """解码 Opus 音频（FFI 调用 libopus）"""
    return external_call["opus_decode", Int](
        opus_decoder,
        opus_data,
        Int32(opus_len),
        pcm_out,
        Int32(frame_size),
        Int32(0)
    )
```

---

**2. PCM 格式转换（SIMD 加速）**
```mojo
from algorithm import vectorize

fn pcm_to_float32(
    pcm_data: DTypePointer[DType.int16],
    length: Int,
    out: DTypePointer[DType.float32]
):
    """PCM int16 → float32，SIMD 加速"""
    alias simd_width = simdbitwidth() // 16

    @parameter
    fn vectorized[width: Int](idx: Int):
        let pcm_vec = pcm_data.load[width=width](idx)
        let float_vec = pcm_vec.cast[DType.float32]() / 32768.0
        out.store[width=width](idx, float_vec)

    vectorize[vectorized, simd_width](length)
```

---

**3. VAD 特征提取（SIMD 加速）**
```mojo
fn compute_energy(
    audio: DTypePointer[DType.float32],
    length: Int
) -> Float32:
    """计算音频能量（VAD 特征）"""
    var energy: Float32 = 0.0
    alias simd_width = simdbitwidth() // 32

    @parameter
    fn vectorized[width: Int](idx: Int):
        let vec = audio.load[width=width](idx)
        let squared = vec * vec
        energy += squared.reduce_add()

    vectorize[vectorized, simd_width](length)
    return energy / Float32(length)
```

---

#### **Layer 3: AI Orchestration（Python）**

**核心职责：AI SDK 调用 + 逻辑编排 + 胶水代码**

**1. AI Provider 调用（单一职责）**
```python
# Python: 只负责调用 AI SDK
class OpenAIASRProvider:
    """OpenAI Whisper Provider"""
    def __init__(self, config):
        self.client = OpenAI(api_key=config["api_key"])

    async def transcribe(self, audio_data: bytes) -> str:
        """语音识别（调用 OpenAI SDK）"""
        response = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data
        )
        return response.text

class EdgeTTSProvider:
    """Edge TTS Provider"""
    async def synthesize(self, text: str) -> bytes:
        """语音合成（调用 Edge TTS）"""
        communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        return audio_bytes
```

---

**2. AI 逻辑编排（协调流程）**
```python
# Python: 协调 AI 流程（胶水代码）
class AIOrchestrator:
    """AI 逻辑编排器"""
    def __init__(self, config):
        self.asr = create_asr_provider(config["asr"])
        self.llm = create_llm_provider(config["llm"])
        self.tts = create_tts_provider(config["tts"])
        self.plugin_executor = PluginExecutor()

        # 调用 Rust API（胶水）
        self.dialogue_storage = rust_api.DialogueStorage()
        self.plugin_registry = rust_api.PluginRegistry()

    async def process_audio(self, session_id: str, audio_data: bytes) -> bytes:
        """处理音频流（编排 AI 流程）"""
        # 1. 调用 Mojo 解码（胶水）
        pcm_data = mojo_audio.decode_opus(audio_data)

        # 2. 调用 Mojo VAD（胶水）
        is_voice = mojo_audio.detect_voice(pcm_data)
        if not is_voice:
            return b""

        # 3. 调用 AI SDK: ASR
        text = await self.asr.transcribe(audio_data)

        # 4. 从 Rust 获取对话历史（胶水）
        history = await self.dialogue_storage.get_history(session_id)

        # 5. 调用 AI SDK: LLM
        response = await self.llm.chat(history + [{"role": "user", "content": text}])

        # 6. 检测工具调用
        if "<tool_call>" in response:
            tool_result = await self.execute_plugin(response)
            response = tool_result

        # 7. 保存到 Rust 存储（胶水）
        await self.dialogue_storage.add_message(session_id, "user", text)
        await self.dialogue_storage.add_message(session_id, "assistant", response)

        # 8. 调用 AI SDK: TTS
        audio_response = await self.tts.synthesize(response)

        return audio_response

    async def execute_plugin(self, tool_call: str) -> str:
        """执行插件（调用 Rust 调度器）"""
        # 解析工具调用
        plugin_name = parse_plugin_name(tool_call)
        params = parse_params(tool_call)

        # 调用 Rust Plugin Registry（胶水）
        result = await self.plugin_registry.execute(plugin_name, params)
        return result
```

---

**3. Plugin 执行环境（动态加载）**
```python
# Python: Plugin 执行环境（利用动态性）
class PluginExecutor:
    """Plugin 执行环境"""
    def __init__(self):
        self.plugins = {}

    def load_plugin(self, plugin_path: str):
        """动态加载 Plugin（Python 优势）"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 查找 Plugin 类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Plugin):
                plugin = attr()
                self.plugins[plugin.name] = plugin
                break

    async def execute(self, plugin_name: str, **kwargs) -> str:
        """执行 Plugin"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")

        return await plugin.execute(**kwargs)
```

---

#### **Layer 4: Application（用户应用）**

**用户只需编写：**
```python
# 用户自定义 Plugin
from orica import Plugin

class WeatherPlugin(Plugin):
    name = "get_weather"

    async def execute(self, city: str):
        # 用户业务逻辑
        weather = await fetch_weather_from_api(city)
        return f"{city} 的天气是 {weather}"

# 用户启动应用
from orica import ORicaApp

app = ORicaApp.from_config("config.yaml")
app.register_plugin(WeatherPlugin())
app.run()
```

---

## 第四部分：改造边界总结

### 4.1 三语言职责清单

| 组件 | 当前（错误） | 改造后（正确） | 原因 |
|------|------------|--------------|------|
| **WebSocket 服务器** | Python | ✅ **Rust** | 系统编程、并发、I/O |
| **HTTP API 服务器** | Rust | ✅ **Rust** | 正确 ✅ |
| **对话历史存储** | Python | ✅ **Rust** | 数据库操作 |
| **对话逻辑（摘要）** | Python | ✅ **Python** | 调用 LLM |
| **记忆系统存储** | Python | ✅ **Rust** | 数据库操作 |
| **记忆系统云端 API** | Python | ✅ **Python** | 调用 Mem0 SDK |
| **Plugin 注册和调度** | Python | ✅ **Rust** | 框架部分 |
| **Plugin 执行环境** | Python | ✅ **Python** | 动态加载 |
| **Connection Handler** | Python | ✅ **拆分：Rust + Python** | Rust 管理连接，Python 编排 AI |
| **Opus 编解码** | Python (opuslib) | ✅ **Mojo** | 性能密集 |
| **PCM 转换** | Python (numpy) | ✅ **Mojo** | 数值计算 |
| **VAD 检测** | Python (torch) | ✅ **Mojo** | 性能密集 |
| **AI SDK 调用** | Python | ✅ **Python** | 官方 SDK |
| **AI 逻辑编排** | Python | ✅ **Python** | 胶水代码 |

---

### 4.2 改造原则

**Rust 写：**
```
✅ 系统编程（WebSocket、HTTP、并发）
✅ 数据库操作（CRUD、存储）
✅ 文件 I/O（日志、缓存）
✅ 框架部分（Plugin 注册、调度）
✅ 性能要求高但不涉及数值计算的部分
```

**Mojo 写：**
```
✅ 数值密集计算（SIMD 加速）
✅ 音频处理（编解码、转换）
✅ 信号处理（VAD、特征提取）
✅ 替代 NumPy 的场景
```

**Python 写：**
```
✅ AI SDK 调用（OpenAI、FunASR、Edge TTS）
✅ 动态特性（Plugin 动态加载）
✅ 胶水代码（连接 Rust、Mojo、AI SDK）
✅ AI 逻辑编排（协调流程）
✅ 不涉及性能的业务逻辑
```

---

### 4.3 数据流示例（改造后）

**场景：ESP32 发送语音 → AI 处理 → 返回语音**

```
1. ESP32
   ↓ WebSocket (Opus)

2. Rust WebSocket Server
   - 接收 WebSocket 连接
   - 心跳检测
   - 转发音频数据到 Python
   ↓ IPC

3. Python AIOrchestrator
   - 调用 Mojo 解码 Opus
   ↓ FFI

4. Mojo AudioProcessor
   - decode_opus() → PCM 数据
   - detect_voice() → is_voice
   ↑ 返回

5. Python AIOrchestrator
   - 调用 OpenAI Whisper (Python SDK)
   - text = "今天天气怎么样？"
   ↓

6. Python AIOrchestrator
   - 从 Rust 获取对话历史
   ↓ IPC

7. Rust DialogueStorage
   - 查询数据库
   ↑ 返回历史

8. Python AIOrchestrator
   - 调用 OpenAI GPT-4o (Python SDK)
   - 检测到工具调用 <tool_call>get_weather(city="北京")</tool_call>
   ↓

9. Rust PluginRegistry
   - 调度 Plugin 执行
   ↓ IPC

10. Python PluginExecutor
    - 动态加载 WeatherPlugin
    - 执行 execute(city="北京")
    - 返回 "北京今天晴天，25°C"
    ↑ 返回

11. Python AIOrchestrator
    - 调用 LLM 生成最终响应
    - 保存对话到 Rust DialogueStorage
    - 调用 Edge TTS (Python SDK)
    ↓

12. Rust WebSocket Server
    - 发送音频到 ESP32
    ↓ WebSocket

13. ESP32
    - 播放音频
```

---

## 第五部分：实施策略

### 5.1 改造优先级

**Phase 1: 拆分 Connection Handler（高优先级）**
```
拆分前：
Python ConnectionHandler（处理所有逻辑）

拆分后：
Rust ConnectionManager（WebSocket 生命周期）
  ↓ IPC
Python AIOrchestrator（AI 逻辑编排）
```

**Phase 2: 迁移存储到 Rust（中优先级）**
```
迁移前：
Python DialogueManager（内存存储）
Python MemorySystem（内存/文件存储）

迁移后：
Rust DialogueStorage（数据库存储）
Rust MemoryStorage（数据库存储）
Python 只负责调用和 AI 逻辑
```

**Phase 3: 优化 Plugin 系统（低优先级）**
```
优化前：
Python PluginManager（注册 + 执行）

优化后：
Rust PluginRegistry（注册 + 调度）
Python PluginExecutor（动态加载 + 执行）
```

---

### 5.2 渐进式迁移路径

**Step 1: 保持向后兼容**
```python
# 旧 API（保留兼容）
from orica.legacy import ConnectionHandler

# 新 API（推荐）
from orica import AIOrchestrator
```

**Step 2: 逐步弃用**
```python
# v2.0: 标记为 deprecated
@deprecated("Use AIOrchestrator instead")
class ConnectionHandler:
    pass

# v3.0: 移除
# ConnectionHandler 不再存在
```

---

## 第六部分：验收标准

### 6.1 职责单一性检查

**每层只做自己擅长的事：**
- [ ] Rust 不处理 AI SDK 调用
- [ ] Mojo 不处理网络 I/O
- [ ] Python 不处理 WebSocket 连接管理
- [ ] Python 不处理数据库 CRUD
- [ ] Python 专注 AI 逻辑和胶水代码

---

### 6.2 性能指标

**改造后应达到：**
- [ ] WebSocket 并发连接数 >= 10,000（Rust）
- [ ] 音频处理延迟 < 10ms（Mojo）
- [ ] 对话历史查询 < 5ms（Rust）
- [ ] AI 端到端延迟 < 500ms（Python 编排）

---

## 第七部分：总结

### 7.1 核心改造点

**改造前（错误）：**
```
Python 承担过多职责：
❌ WebSocket 连接管理
❌ 对话历史存储
❌ 音频编解码
❌ AI SDK 调用
❌ Plugin 管理
```

**改造后（正确）：**
```
职责清晰划分：
✅ Rust: 系统编程、并发、I/O、存储
✅ Mojo: 数值计算、音频处理
✅ Python: AI SDK、胶水代码、动态特性
```

---

### 7.2 关键原则

1. **单一职责** - 每种语言做自己最擅长的事
2. **Python 专注 AI** - AI SDK 调用 + 逻辑编排
3. **Rust 做 Mojo 不擅长的** - 系统编程、I/O、并发
4. **Mojo 做性能密集型** - 数值计算、音频处理
5. **Python 充当胶水** - 连接 Rust、Mojo、AI SDK

---

**文档版本**: 1.0
**创建日期**: 2026-01-16
**维护者**: Claude Code
**下一步**: 开始 Phase 1 改造（拆分 Connection Handler）
