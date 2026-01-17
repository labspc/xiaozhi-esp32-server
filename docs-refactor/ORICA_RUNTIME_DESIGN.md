# ORica Runtime 设计：多语言协同运行方案

## 文档目的

回答核心问题：**需要什么东西让 Rust + Mojo + Python 三层协同运行？**

本文档设计 **ORica Runtime（运行时协调器）**，作为整个框架的"大脑"，负责：
1. ✅ 启动和初始化各语言模块
2. ✅ 协调跨语言调用
3. ✅ 管理模块生命周期
4. ✅ 提供统一的消息路由机制

---

## 第一部分：问题分析

### 1.1 当前架构的挑战

**三种语言，三种运行时：**
```
┌─────────────────────────────────────────────┐
│ Layer 3: Python AI Engine (CPython)         │
├─────────────────────────────────────────────┤
│ Layer 2: Mojo Accelerator (Mojo Runtime)    │
├─────────────────────────────────────────────┤
│ Layer 1: Rust Infrastructure (Native Binary)│
└─────────────────────────────────────────────┘

问题：
❓ 谁先启动？
❓ 如何通信？
❓ 如何保证初始化顺序？
❓ 如何处理错误和重启？
```

---

### 1.2 需要解决的核心问题

| 问题 | 说明 | 影响 |
|------|------|------|
| **主进程选择** | Rust 还是 Python 作为入口？ | 决定架构模式 |
| **跨语言调用** | Rust ↔ Python, Python ↔ Mojo | 性能和复杂度 |
| **生命周期管理** | 启动顺序、优雅关闭、错误恢复 | 系统稳定性 |
| **消息路由** | 层间数据传递机制 | 解耦程度 |
| **配置管理** | 各层如何读取配置 | 一致性 |

---

## 第二部分：方案对比

### 2.1 方案一：Rust 主导（推荐 ⭐⭐⭐⭐⭐）

**架构图：**
```
┌────────────────────────────────────────────────────┐
│           ORica Runtime (Rust 主进程)               │
│  ┌──────────────────────────────────────────────┐  │
│  │  1. Rust WebSocket Server (axum/actix-web)  │  │
│  │     - Connection Management                  │  │
│  │     - Message Routing                        │  │
│  │     - Storage Operations                     │  │
│  └────────────────┬─────────────────────────────┘  │
│                   │ PyO3 (Embedded Python)         │
│  ┌────────────────▼─────────────────────────────┐  │
│  │  2. Python AI Engine (Embedded Interpreter)  │  │
│  │     - AI SDK Calls (OpenAI, FunASR...)       │  │
│  │     - Plugin Execution                       │  │
│  │     - AI Orchestration Logic                 │  │
│  └────────────────┬─────────────────────────────┘  │
│                   │ FFI / Python C API             │
│  ┌────────────────▼─────────────────────────────┐  │
│  │  3. Mojo Accelerator (Shared Library .so)   │  │
│  │     - Opus Codec (decode/encode)             │  │
│  │     - Audio Processing (SIMD)                │  │
│  │     - VAD Computation                        │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

**启动流程：**
```rust
// main.rs (Rust 主入口)
#[tokio::main]
async fn main() -> Result<()> {
    // 1. 初始化 ORica Runtime
    let runtime = ORicaRuntime::new()?;

    // 2. 加载配置
    let config = runtime.load_config("config.yaml").await?;

    // 3. 初始化 Rust 层（数据库、存储）
    runtime.init_rust_layer(&config).await?;

    // 4. 初始化 Python 引擎（嵌入式解释器）
    runtime.init_python_engine(&config).await?;

    // 5. 加载 Mojo 加速库
    runtime.load_mojo_accelerator().await?;

    // 6. 启动 WebSocket 服务器
    runtime.start_server("0.0.0.0:8000").await?;

    Ok(())
}
```

**优点：**
- ✅ **性能最优** - Rust 直接处理网络 I/O
- ✅ **控制力强** - 完全掌控进程生命周期
- ✅ **内存安全** - Rust 保证内存安全
- ✅ **便于部署** - 单一二进制文件（嵌入 Python）

**缺点：**
- ⚠️ PyO3 嵌入复杂度（需要静态链接 Python）
- ⚠️ Python GIL 可能影响并发（需要多进程）

**技术栈：**
- Rust: axum + tokio + PyO3
- Python: 嵌入式解释器（通过 PyO3）
- Mojo: 编译为 .so 共享库

---

### 2.2 方案二：独立进程 + IPC

**架构图：**
```
┌─────────────────────────────────────────────┐
│  Rust WebSocket Server (独立进程 :8000)     │
│  - Connection Management                    │
│  - Message Routing                          │
│  - Storage Operations                       │
└────────────┬────────────────────────────────┘
             │ HTTP / gRPC / 消息队列
┌────────────▼────────────────────────────────┐
│  Python AI Engine (独立进程 :8001)          │
│  - AI SDK Calls                             │
│  - Plugin Execution                         │
│  - Orchestration Logic                      │
└────────────┬────────────────────────────────┘
             │ FFI
┌────────────▼────────────────────────────────┐
│  Mojo Accelerator (Shared Library)          │
│  - Audio Processing                         │
└─────────────────────────────────────────────┘
```

**通信方式：**
```rust
// Rust → Python (HTTP 调用)
let client = reqwest::Client::new();
let response = client
    .post("http://localhost:8001/ai/process")
    .json(&AudioRequest {
        session_id: "abc123",
        audio_data: base64_audio,
    })
    .send()
    .await?;

let result: AIResponse = response.json().await?;
```

**优点：**
- ✅ **解耦彻底** - 各模块独立开发、部署
- ✅ **可独立扩展** - Python Engine 可横向扩展（多实例）
- ✅ **语言独立** - 不需要 PyO3 嵌入

**缺点：**
- ❌ **网络开销** - HTTP/gRPC 有序列化和网络延迟（~1-5ms）
- ❌ **部署复杂** - 多个进程需要监控和管理
- ❌ **状态同步** - 需要额外的状态管理机制

---

### 2.3 方案三：Python 主导（不推荐 ⭐⭐）

**架构图：**
```
┌────────────────────────────────────────────┐
│  Python Main Process (app.py)              │
│  ┌──────────────────────────────────────┐  │
│  │  Python WebSocket Server (websockets)│  │
│  │  + AI Engine                         │  │
│  └───────────┬──────────────────────────┘  │
│              │ ctypes / PyO3              │
│  ┌───────────▼──────────────────────────┐  │
│  │  Rust Modules (Shared Library .so)  │  │
│  │  - Storage                           │  │
│  │  - Database                          │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │  Mojo Modules (Shared Library .so)  │  │
│  │  - Audio Processing                  │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

**优点：**
- ✅ 开发快速（保持当前 Python 模式）
- ✅ 调试方便（Python 生态工具丰富）

**缺点：**
- ❌ **性能差** - Python WebSocket 性能不如 Rust（~10 倍差距）
- ❌ **GIL 限制** - 多线程并发受限
- ❌ **违反设计原则** - Python 应专注 AI，不应处理 WebSocket

---

## 第三部分：ORica Runtime 设计（方案一详细实现）

### 3.1 核心组件

**ORica Runtime 包含 4 个核心组件：**
```
ORicaRuntime
├── 1. ConfigManager      (配置管理器)
├── 2. ModuleLoader       (模块加载器)
├── 3. MessageRouter      (消息路由器)
└── 4. LifecycleManager   (生命周期管理器)
```

---

### 3.2 组件一：ConfigManager（配置管理器）

**职责：**
- 加载 `config.yaml`
- 验证配置完整性
- 提供配置热更新机制
- 将配置分发到各层

**Rust 实现：**
```rust
// orica-runtime/src/config.rs

use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ORicaConfig {
    pub server: ServerConfig,
    pub providers: ProviderConfig,
    pub storage: StorageConfig,
    pub mojo: MojoConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub max_connections: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderConfig {
    pub asr: ProviderSettings,
    pub tts: ProviderSettings,
    pub llm: ProviderSettings,
}

pub struct ConfigManager {
    config: ORicaConfig,
    config_path: String,
}

impl ConfigManager {
    pub fn load(path: &str) -> Result<Self, ConfigError> {
        let content = std::fs::read_to_string(path)?;
        let config: ORicaConfig = serde_yaml::from_str(&content)?;

        // 验证配置
        Self::validate(&config)?;

        Ok(Self {
            config,
            config_path: path.to_string(),
        })
    }

    pub fn get_config(&self) -> &ORicaConfig {
        &self.config
    }

    pub async fn reload(&mut self) -> Result<(), ConfigError> {
        let new_config = Self::load(&self.config_path)?;
        self.config = new_config.config;
        Ok(())
    }

    fn validate(config: &ORicaConfig) -> Result<(), ConfigError> {
        // 检查必需字段
        if config.server.port == 0 {
            return Err(ConfigError::InvalidPort);
        }

        // 检查 Provider 配置
        if config.providers.llm.name.is_empty() {
            return Err(ConfigError::MissingProvider("llm"));
        }

        Ok(())
    }
}
```

---

### 3.3 组件二：ModuleLoader（模块加载器）

**职责：**
- 初始化 Python 解释器（PyO3）
- 加载 Mojo 共享库
- 初始化 Rust 存储层
- 按依赖顺序启动模块

**Rust 实现：**
```rust
// orica-runtime/src/loader.rs

use pyo3::prelude::*;
use pyo3::types::PyModule;
use libloading::Library;

pub struct ModuleLoader {
    py: Python<'static>,
    mojo_lib: Option<Library>,
}

impl ModuleLoader {
    /// 初始化 Python 解释器
    pub fn init_python() -> Result<Self, LoaderError> {
        pyo3::prepare_freethreaded_python();

        Python::with_gil(|py| {
            // 设置 Python 路径
            let sys = py.import("sys")?;
            let path: &PyList = sys.getattr("path")?.downcast()?;
            path.insert(0, "./orica-core/python")?;

            // 导入 ORica Python 模块
            let orica_module = PyModule::import(py, "orica.core")?;

            println!("✅ Python Engine 初始化成功");

            Ok(Self {
                py,
                mojo_lib: None,
            })
        })
    }

    /// 加载 Mojo 共享库
    pub fn load_mojo(&mut self, lib_path: &str) -> Result<(), LoaderError> {
        unsafe {
            let lib = Library::new(lib_path)?;

            // 验证符号
            let _decode_fn: libloading::Symbol<unsafe extern fn()> =
                lib.get(b"mojo_opus_decode")?;

            self.mojo_lib = Some(lib);
            println!("✅ Mojo Accelerator 加载成功: {}", lib_path);

            Ok(())
        }
    }

    /// 调用 Python AI Engine
    pub fn call_python_ai(
        &self,
        session_id: &str,
        audio_data: &[u8],
    ) -> Result<Vec<u8>, LoaderError> {
        Python::with_gil(|py| {
            let orica = py.import("orica.core")?;
            let ai_engine = orica.getattr("AIOrchestrator")?;
            let instance = ai_engine.call0()?;

            // 调用 process_audio 方法
            let result = instance.call_method1(
                "process_audio",
                (session_id, audio_data),
            )?;

            // 转换返回值
            let audio_bytes: Vec<u8> = result.extract()?;
            Ok(audio_bytes)
        })
    }
}
```

---

### 3.4 组件三：MessageRouter（消息路由器）

**职责：**
- 路由 WebSocket 消息到对应处理器
- 协调跨层调用（Rust → Python → Mojo）
- 管理消息序列化/反序列化

**Rust 实现：**
```rust
// orica-runtime/src/router.rs

use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ORicaMessage {
    // 来自 ESP32 的消息
    AudioData { session_id: String, data: Vec<u8> },
    TextInput { session_id: String, text: String },
    Heartbeat { session_id: String },

    // 内部消息
    AIRequest { session_id: String, audio: Vec<u8> },
    AIResponse { session_id: String, audio: Vec<u8> },

    // 错误消息
    Error { session_id: String, message: String },
}

pub struct MessageRouter {
    // Rust → Python 通道
    python_tx: mpsc::Sender<ORicaMessage>,
    python_rx: mpsc::Receiver<ORicaMessage>,

    // 模块加载器（用于调用 Python）
    loader: Arc<ModuleLoader>,
}

impl MessageRouter {
    pub fn new(loader: Arc<ModuleLoader>) -> Self {
        let (python_tx, python_rx) = mpsc::channel(100);

        Self {
            python_tx,
            python_rx,
            loader,
        }
    }

    /// 路由消息到对应处理器
    pub async fn route(&self, msg: ORicaMessage) -> Result<ORicaMessage, RouterError> {
        match msg {
            ORicaMessage::AudioData { session_id, data } => {
                // 1. Rust 层：存储原始音频（可选）
                // storage.save_audio(&session_id, &data).await?;

                // 2. 调用 Python AI Engine
                let response_audio = self.loader
                    .call_python_ai(&session_id, &data)
                    .map_err(|e| RouterError::PythonCallFailed(e))?;

                // 3. 返回响应
                Ok(ORicaMessage::AIResponse {
                    session_id,
                    audio: response_audio,
                })
            }

            ORicaMessage::TextInput { session_id, text } => {
                // 直接调用 LLM（通过 Python）
                // ... 类似逻辑
                todo!()
            }

            ORicaMessage::Heartbeat { session_id } => {
                // Rust 层直接处理心跳
                Ok(ORicaMessage::Heartbeat { session_id })
            }

            _ => Err(RouterError::UnknownMessage),
        }
    }
}
```

---

### 3.5 组件四：LifecycleManager（生命周期管理器）

**职责：**
- 管理模块启动顺序
- 优雅关闭（Graceful Shutdown）
- 错误恢复和重启
- 健康检查

**Rust 实现：**
```rust
// orica-runtime/src/lifecycle.rs

use tokio::signal;
use std::sync::Arc;

pub struct LifecycleManager {
    config: Arc<ConfigManager>,
    loader: Arc<ModuleLoader>,
    router: Arc<MessageRouter>,
}

impl LifecycleManager {
    pub fn new(
        config: ConfigManager,
        loader: ModuleLoader,
        router: MessageRouter,
    ) -> Self {
        Self {
            config: Arc::new(config),
            loader: Arc::new(loader),
            router: Arc::new(router),
        }
    }

    /// 启动整个系统
    pub async fn start(&self) -> Result<(), LifecycleError> {
        println!("🚀 ORica Runtime 启动中...");

        // 1. 初始化 Rust 层
        println!("📦 初始化 Rust Infrastructure...");
        self.init_rust_layer().await?;

        // 2. 初始化 Python 引擎
        println!("🐍 初始化 Python AI Engine...");
        self.loader.init_python()?;

        // 3. 加载 Mojo 加速库
        println!("⚡ 加载 Mojo Accelerator...");
        self.loader.load_mojo("./orica-core/mojo/libaudio.so")?;

        // 4. 启动 WebSocket 服务器
        println!("🌐 启动 WebSocket Server...");
        let server_config = &self.config.get_config().server;
        self.start_websocket_server(server_config).await?;

        println!("✅ ORica Runtime 启动成功！");

        // 5. 等待关闭信号
        self.wait_for_shutdown().await;

        Ok(())
    }

    /// 优雅关闭
    async fn shutdown(&self) {
        println!("🛑 ORica Runtime 关闭中...");

        // 1. 停止接受新连接
        println!("  ⏹️  停止 WebSocket Server...");

        // 2. 等待现有请求完成（最多 30 秒）
        println!("  ⏳ 等待现有请求完成...");
        tokio::time::sleep(Duration::from_secs(30)).await;

        // 3. 关闭 Python 解释器
        println!("  🐍 关闭 Python Engine...");
        // PyO3 会在 Drop 时自动清理

        // 4. 卸载 Mojo 库
        println!("  ⚡ 卸载 Mojo Library...");
        drop(&self.loader.mojo_lib);

        println!("✅ ORica Runtime 已安全关闭");
    }

    /// 等待 SIGINT/SIGTERM 信号
    async fn wait_for_shutdown(&self) {
        let ctrl_c = signal::ctrl_c();

        #[cfg(unix)]
        let mut sigterm = signal::unix::signal(
            signal::unix::SignalKind::terminate()
        ).expect("Failed to create SIGTERM handler");

        tokio::select! {
            _ = ctrl_c => {
                println!("\n收到 SIGINT 信号");
            }
            #[cfg(unix)]
            _ = sigterm.recv() => {
                println!("\n收到 SIGTERM 信号");
            }
        }

        self.shutdown().await;
    }
}
```

---

## 第四部分：完整启动流程

### 4.1 启动序列图

```
用户运行: ./orica-server
         │
         ▼
┌────────────────────────────────────────┐
│  main.rs (Rust 入口)                   │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  1. ConfigManager::load("config.yaml") │
│     - 加载配置                          │
│     - 验证完整性                        │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  2. ModuleLoader::init_python()        │
│     - pyo3::prepare_freethreaded()     │
│     - 导入 orica.core 模块              │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  3. ModuleLoader::load_mojo()          │
│     - libloading::Library::new()       │
│     - 验证符号是否存在                  │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  4. RustInfrastructure::init()         │
│     - 初始化数据库连接池                │
│     - 初始化存储后端                    │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  5. WebSocketServer::start()           │
│     - 绑定 0.0.0.0:8000                │
│     - 启动 tokio runtime               │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  系统运行中                             │
│  - 接受 WebSocket 连接                 │
│  - 处理音频数据                         │
│  - 调用 Python AI Engine               │
└────────────┬───────────────────────────┘
             │ 收到 SIGINT/SIGTERM
             ▼
┌────────────────────────────────────────┐
│  6. LifecycleManager::shutdown()       │
│     - 停止接受新连接                    │
│     - 等待现有请求完成                  │
│     - 清理资源                          │
└────────────────────────────────────────┘
```

---

### 4.2 主入口代码示例

**完整的 `main.rs`：**
```rust
// orica-runtime/src/main.rs

use orica_runtime::{
    ConfigManager, ModuleLoader, MessageRouter, LifecycleManager,
};
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    // 打印启动横幅
    print_banner();

    // 1. 加载配置
    println!("📄 加载配置文件...");
    let config = ConfigManager::load("config.yaml")?;

    // 2. 初始化模块加载器
    println!("🔧 初始化模块加载器...");
    let mut loader = ModuleLoader::new();

    // 3. 初始化 Python 引擎
    loader.init_python()?;

    // 4. 加载 Mojo 加速库
    loader.load_mojo("./lib/liborica_audio.so")?;

    // 5. 创建消息路由器
    let router = MessageRouter::new(Arc::new(loader));

    // 6. 创建生命周期管理器
    let lifecycle = LifecycleManager::new(config, loader, router);

    // 7. 启动系统
    lifecycle.start().await?;

    Ok(())
}

fn print_banner() {
    println!(r#"
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║    ░█▀█░█▀▄░▀█▀░█▀▀░█▀█                ║
    ║    ░█░█░█▀▄░░█░░█░░░█▀█                ║
    ║    ░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀░▀                ║
    ║                                       ║
    ║    AI Companion Hardware Framework    ║
    ║    Version: 0.1.0                     ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    "#);
}
```

---

## 第五部分：跨语言调用机制

### 5.1 Rust → Python（PyO3）

**示例：调用 Python AI Engine**
```rust
// Rust 侧
use pyo3::prelude::*;

pub fn process_with_ai(audio: &[u8]) -> PyResult<Vec<u8>> {
    Python::with_gil(|py| {
        // 导入 Python 模块
        let orica = py.import("orica.ai_engine")?;

        // 创建 AI Orchestrator 实例
        let orchestrator = orica.getattr("AIOrchestrator")?.call0()?;

        // 调用处理方法
        let result = orchestrator.call_method1("process_audio", (audio,))?;

        // 提取结果
        let output: Vec<u8> = result.extract()?;
        Ok(output)
    })
}
```

**Python 侧：**
```python
# orica/ai_engine.py

class AIOrchestrator:
    def __init__(self):
        self.asr = get_asr_provider()
        self.llm = get_llm_provider()
        self.tts = get_tts_provider()

    async def process_audio(self, audio_data: bytes) -> bytes:
        """
        被 Rust 调用的主入口
        """
        # 1. ASR
        text = await self.asr.transcribe(audio_data)

        # 2. LLM
        response = await self.llm.chat(text)

        # 3. TTS
        audio_response = await self.tts.synthesize(response)

        return audio_response
```

---

### 5.2 Python → Mojo（FFI）

**Mojo 侧（编译为 .so）：**
```mojo
# orica-core/mojo/audio/codec.mojo

from sys.ffi import external_call
from memory.unsafe import DTypePointer

@export
fn mojo_opus_decode(
    opus_data: DTypePointer[DType.uint8],
    opus_len: Int,
    pcm_out: DTypePointer[DType.int16],
    frame_size: Int,
) -> Int:
    """
    导出给 Python 调用的 Opus 解码函数
    """
    let decoded_samples = external_call[
        "opus_decode",
        Int
    ](
        opus_decoder,
        opus_data,
        Int32(opus_len),
        pcm_out,
        Int32(frame_size),
        Int32(0)
    )

    return int(decoded_samples)
```

**Python 侧（调用 Mojo）：**
```python
# orica/core/audio/codec.py

import ctypes
import numpy as np

# 加载 Mojo 编译的 .so 库
mojo_lib = ctypes.CDLL("./lib/liborica_audio.so")

# 声明函数签名
mojo_lib.mojo_opus_decode.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),  # opus_data
    ctypes.c_int,                     # opus_len
    ctypes.POINTER(ctypes.c_int16),   # pcm_out
    ctypes.c_int,                     # frame_size
]
mojo_lib.mojo_opus_decode.restype = ctypes.c_int

def decode_opus(opus_bytes: bytes) -> np.ndarray:
    """
    Python 调用 Mojo 加速的 Opus 解码
    """
    opus_data = np.frombuffer(opus_bytes, dtype=np.uint8)
    pcm_out = np.zeros(960, dtype=np.int16)  # 20ms @ 48kHz

    decoded_len = mojo_lib.mojo_opus_decode(
        opus_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        len(opus_data),
        pcm_out.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
        960,
    )

    return pcm_out[:decoded_len]
```

---

## 第六部分：部署和运行

### 6.1 构建流程

**完整构建脚本 `build.sh`：**
```bash
#!/bin/bash
set -e

echo "🔨 开始构建 ORica Framework..."

# 1. 构建 Mojo 加速库
echo "⚡ 构建 Mojo Accelerator..."
cd orica-core/mojo
mojo build audio/codec.mojo -o ../../lib/liborica_audio.so
cd ../..

# 2. 打包 Python 模块
echo "🐍 打包 Python AI Engine..."
cd orica-core/python
pip install -e .
cd ../..

# 3. 构建 Rust 运行时
echo "🦀 构建 Rust Runtime..."
cd orica-runtime
cargo build --release
cd ..

# 4. 复制二进制到 bin/
echo "📦 打包二进制文件..."
mkdir -p bin/
cp orica-runtime/target/release/orica-server bin/
cp lib/liborica_audio.so bin/

echo "✅ 构建完成！"
echo ""
echo "运行命令："
echo "  cd bin/"
echo "  ./orica-server"
```

---

### 6.2 目录结构

```
orica-framework/
├── bin/
│   ├── orica-server           # Rust 主程序
│   └── liborica_audio.so      # Mojo 加速库
│
├── lib/                       # 共享库
│   └── liborica_audio.so
│
├── orica-runtime/             # Rust 运行时
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs            # 主入口
│       ├── config.rs          # 配置管理
│       ├── loader.rs          # 模块加载
│       ├── router.rs          # 消息路由
│       └── lifecycle.rs       # 生命周期
│
├── orica-core/
│   ├── python/                # Python AI 引擎
│   │   ├── orica/
│   │   │   ├── __init__.py
│   │   │   ├── ai_engine.py  # AI 协调器
│   │   │   ├── providers/    # AI Providers
│   │   │   └── plugins/      # 插件系统
│   │   └── setup.py
│   │
│   └── mojo/                  # Mojo 加速层
│       └── audio/
│           ├── codec.mojo     # Opus 编解码
│           └── processing.mojo
│
└── config.yaml                # 配置文件
```

---

### 6.3 运行示例

**启动服务器：**
```bash
$ ./bin/orica-server

    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║    ░█▀█░█▀▄░▀█▀░█▀▀░█▀█                ║
    ║    ░█░█░█▀▄░░█░░█░░░█▀█                ║
    ║    ░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀░▀                ║
    ║                                       ║
    ║    AI Companion Hardware Framework    ║
    ║    Version: 0.1.0                     ║
    ║                                       ║
    ╚═══════════════════════════════════════╝

🚀 ORica Runtime 启动中...
📄 加载配置文件...
✅ 配置加载成功

🔧 初始化模块加载器...
🐍 初始化 Python AI Engine...
✅ Python Engine 初始化成功

⚡ 加载 Mojo Accelerator...
✅ Mojo Accelerator 加载成功: ./lib/liborica_audio.so

🌐 启动 WebSocket Server...
✅ WebSocket Server 监听: 0.0.0.0:8000

✅ ORica Runtime 启动成功！

📊 系统状态:
   - Python Engine: ✅ 运行中
   - Mojo Accelerator: ✅ 已加载
   - WebSocket Server: ✅ 监听中 (8000)
   - 活跃连接: 0

等待连接中...
```

---

## 第七部分：总结

### 7.1 ORica Runtime 核心价值

**回答用户的问题："需要什么东西让整个系统运行起来？"**

答案是：**ORica Runtime（Rust 实现）**

**它提供：**
1. ✅ **统一的入口** - 单一二进制文件启动整个系统
2. ✅ **模块协调** - 按正确顺序初始化 Rust、Python、Mojo
3. ✅ **跨语言通信** - 封装 PyO3、FFI 调用细节
4. ✅ **生命周期管理** - 优雅启动和关闭
5. ✅ **配置管理** - 统一配置分发到各层

---

### 7.2 推荐方案：Rust 主导（方案一）

**理由：**
- ⭐ **性能最优** - Rust 直接处理网络 I/O
- ⭐ **控制力强** - 完全掌控进程生命周期
- ⭐ **部署简单** - 单一二进制文件
- ⭐ **符合设计原则** - Rust 做系统编程，Python 专注 AI

**技术栈：**
```
主进程: Rust (tokio + axum + PyO3)
AI 引擎: Python (嵌入式解释器)
加速库: Mojo (.so 共享库)
```

---

### 7.3 实施路线图

**Phase 1: 基础 Runtime（2 周）**
- [ ] 实现 ConfigManager
- [ ] 实现 ModuleLoader（PyO3 嵌入）
- [ ] 基础 WebSocket 服务器

**Phase 2: 完整集成（2 周）**
- [ ] 实现 MessageRouter
- [ ] 实现 LifecycleManager
- [ ] 集成 Mojo 加速库

**Phase 3: 优化和测试（1 周）**
- [ ] 性能测试
- [ ] 内存泄漏检测
- [ ] 压力测试（1000 并发连接）

---

### 7.4 关键决策总结

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **主进程语言** | Rust | 性能、控制力、部署便利 |
| **Python 集成方式** | 嵌入式（PyO3） | 避免网络开销，简化部署 |
| **Mojo 集成方式** | 共享库 (.so) | 标准做法，通过 Python FFI 调用 |
| **通信机制** | 内存调用（非网络） | 最低延迟 |
| **配置管理** | 统一 YAML | 简单、可读、易于维护 |

---

**文档版本**: 1.0
**创建日期**: 2026-01-16
**维护者**: Claude Code
**依赖文档**:
- `ORICA_FRAMEWORK_VISION.md`
- `ORICA_REFACTORING_BOUNDARIES.md`
- `ORICA_ARCHITECTURE_QUICKREF.md`
