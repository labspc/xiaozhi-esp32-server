# ORica Framework：AI 陪伴硬件的全栈软件系统

> **OpenRica Community（开放的 AI 陪伴硬件社区）**

## 文档概述

**ORica** 是专为 **AI 陪伴硬件**（智能音箱、陪伴机器人、AI 玩具等）设计的全栈软件框架，提供从底层基础设施到上层应用扩展的完整解决方案。

---

## 第一部分：核心理念

### 1.1 问题陈述

**AI 陪伴硬件开发者的痛点：**

```
硬件创客/智能硬件公司困境：
├─ 技术栈复杂：需要精通 WebSocket、音频处理、AI SDK、Web 开发
├─ 重复造轮子：每个项目都要写基础设施（设备管理、配置系统、音频流）
├─ 性能问题：Python 慢，实时语音交互延迟高
├─ 硬件适配难：ESP32、树莓派等边缘设备资源有限
├─ 扩展困难：添加新功能需要深入底层代码
└─ 维护成本高：代码耦合严重，难以迭代
```

**ORica 的解决方案：**

```
核心锁定 + 用户扩展模式：
├─ 底层基础设施（ORica-Core）- 开发完后锁定，不再变动
│   ├─ WebSocket 实时通信（Rust）
│   ├─ 音频处理加速（Mojo）
│   ├─ 设备管理 API（Rust）
│   └─ 配置管理系统（Rust + EloqKV）
│
└─ 上层扩展能力（ORica-SDK）- 用户自由扩展
    ├─ Python 插件系统（自定义工具函数）
    ├─ AI Provider 配置（切换语音识别/TTS/LLM 服务商）
    ├─ Web 前端定制（管理后台、监控面板）
    └─ 业务逻辑层（对话流程、场景定制）
```

---

### 1.2 框架定位

**名称：ORica Framework**
- **ORica** = **O**pen**R**ica（开放的 AI 陪伴硬件社区）
- 发音：/ɔːrɪkə/（哦瑞卡）

**Slogan：** *"The Full-Stack Framework for AI Companion Hardware"*
（AI 陪伴硬件的全栈软件框架）

---

### 1.3 聚焦场景：AI 陪伴硬件

**什么是 AI 陪伴硬件？**

```
AI 陪伴硬件 = 边缘设备 + 实时语音交互 + AI 能力

典型场景：
├─ 智能音箱（小爱同学、天猫精灵类）
├─ 陪伴机器人（桌面小机器人、儿童陪伴）
├─ AI 玩具（智能毛绒玩具、互动玩偶）
├─ 语音助手设备（车载语音、智能家居中控）
├─ 教育硬件（AI 学习机、智能笔）
└─ 老年陪伴设备（智能管家、健康助手）
```

**硬件平台：**
- ESP32 系列（低成本、量产首选）
- 树莓派 3/4/5（性能较强、适合原型）
- Arduino + 扩展板
- 其他 ARM/MIPS 嵌入式设备

---

### 1.4 竞品分析（垂直领域）

| 方案 | 定位 | 优势 | 劣势 |
|------|------|------|------|
| **自研全栈** | DIY 方案 | 完全可控 | 开发周期长（6-12个月），重复造轮子 |
| **云端服务商** | 百度/阿里/科大讯飞 | 成熟稳定 | 依赖云服务，成本高，数据隐私问题 |
| **开源语音助手** | Mycroft, Rhasspy | 开源免费 | 功能有限，文档不足，社区不活跃 |
| **ORica Framework** | **AI 陪伴硬件专用** | ✅ 开箱即用<br>✅ 边缘优先<br>✅ 核心锁定<br>✅ 自由扩展 | 新框架，生态待建设 |

---

### 1.5 独特价值主张（UVP）

```
✅ 1. 边缘优先设计
   - ESP32 可部署（内存 < 4MB，闪存 < 16MB）
   - 树莓派轻量运行（内存 < 128MB）
   - 实时响应（端到端延迟 < 500ms）

✅ 2. 核心锁定 + 扩展自由
   - 底层基础设施（ORica-Core）开发完后锁定
   - 用户只需扩展（插件、配置、UI）
   - 升级无痛（底层升级不影响用户代码）

✅ 3. 多语言协作
   - Python (AI 逻辑) + Mojo (性能) + Rust (基础设施)
   - 发挥各语言优势，性能提升 10-100 倍

✅ 4. 硬件生态友好
   - 一键生成 ESP32 固件
   - 支持 OTA 远程升级
   - 设备管理后台（批量管理、日志查看）

✅ 5. AI 友好编码规范
   - 简化代码风格（易于 AI 代码生成）
   - 声明式配置（config.yaml）
   - 插件模板自动生成
```

---

## 第二部分：架构设计

### 2.1 命名体系

**ORica 生态命名规范：**

```
ORica Framework（总称）
├─ ORica-Core（核心基础设施，锁定不变）
│   ├─ orica-server（Rust WebSocket 服务器）
│   ├─ orica-config-api（Rust 配置管理 API）
│   ├─ orica-audio（Mojo 音频处理库）
│   └─ orica-storage（统一存储抽象）
│
├─ ORica-SDK（开发者 SDK，可扩展）
│   ├─ orica-py（Python SDK）
│   ├─ orica-js（JavaScript SDK，未来）
│   └─ orica-web-ui（Web 前端组件库）
│
├─ ORica-Plugins（官方插件库）
│   ├─ orica-plugin-weather（天气查询）
│   ├─ orica-plugin-home（智能家居）
│   ├─ orica-plugin-music（音乐控制）
│   └─ orica-plugin-story（讲故事）
│
└─ ORica-Tools（开发工具）
    ├─ orica-cli（命令行工具）
    ├─ orica-firmware-builder（固件构建工具）
    └─ orica-device-simulator（设备模拟器）
```

**推荐命名：**
- **主框架**：ORica（简洁、易记）
- **核心库**：ORica-Core（明确是核心）
- **SDK**：ORica-SDK 或 orica-py（语言特定）
- **插件**：orica-plugin-xxx（统一前缀）

---

### 2.2 五层架构设计

```
┌────────────────────────────────────────────────────────────┐
│  Layer 5: Device Layer（设备层）- ESP32/树莓派            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ESP32 固件                                           │  │
│  │  - 音频采集（麦克风阵列）                             │  │
│  │  - Opus 编码                                          │  │
│  │  - WebSocket 客户端                                   │  │
│  │  - 音频播放（扬声器）                                 │  │
│  │  - OTA 升级                                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                          ↓ WebSocket (Opus 音频流)
┌────────────────────────────────────────────────────────────┐
│  Layer 4: Application Layer（应用层）- 用户扩展           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  用户应用代码（基于 ORica-SDK）                       │  │
│  │  - 自定义插件（天气、音乐、智能家居）                 │  │
│  │  - 业务逻辑（对话流程、场景定制）                     │  │
│  │  - 前端定制（管理后台、监控面板）                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                          ↓ ORica SDK API
┌────────────────────────────────────────────────────────────┐
│  Layer 3: AI Logic Layer（AI 逻辑层）- Python            │
│  ┌────────────┬────────────┬────────────┬────────────┐    │
│  │ Provider   │ Plugin     │ Memory     │ Dialogue   │    │
│  │ System     │ System     │ System     │ Manager    │    │
│  ├────────────┼────────────┼────────────┼────────────┤    │
│  │ ASR/TTS/   │ 工具函数   │ 对话上下文 │ 流程控制   │    │
│  │ LLM/VAD    │ 动态加载   │ 记忆存储   │ 状态管理   │    │
│  │ 统一抽象   │ 热更新     │ 自动摘要   │ 中断处理   │    │
│  └────────────┴────────────┴────────────┴────────────┘    │
└────────────────────────────────────────────────────────────┘
                          ↓ FFI / IPC
┌────────────────────────────────────────────────────────────┐
│  Layer 2: Performance Layer（性能层）- Mojo              │
│  ┌────────────┬────────────┬────────────┬────────────┐    │
│  │ Audio      │ VAD        │ Codec      │ Buffer     │    │
│  │ Processing │ Detection  │ (Opus)     │ Management │    │
│  ├────────────┼────────────┼────────────┼────────────┤    │
│  │ PCM 转换   │ 特征提取   │ FFI 调用   │ 零拷贝     │    │
│  │ 重采样     │ 能量计算   │ libopus    │ 循环缓冲   │    │
│  │ SIMD 优化  │ 实时检测   │ 编解码     │ 内存池     │    │
│  └────────────┴────────────┴────────────┴────────────┘    │
└────────────────────────────────────────────────────────────┘
                          ↓ HTTP / WebSocket
┌────────────────────────────────────────────────────────────┐
│  Layer 1: Infrastructure Layer（基础设施层）- Rust       │
│  ┌────────────┬────────────┬────────────┬────────────┐    │
│  │ WebSocket  │ Config     │ Device     │ Storage    │    │
│  │ Server     │ API        │ Manager    │ Service    │    │
│  ├────────────┼────────────┼────────────┼────────────┤    │
│  │ 实时通信   │ RESTful    │ 设备注册   │ EloqKV     │    │
│  │ 连接池     │ JWT 认证   │ 状态管理   │ KV + SQL   │    │
│  │ 心跳检测   │ 配置热更新 │ 批量管理   │ 数据持久化 │    │
│  └────────────┴────────────┴────────────┴────────────┘    │
└────────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌────────────────────────────────────────────────────────────┐
│  Layer 0: Frontend Layer（前端层）- Svelte               │
│  ┌────────────┬────────────┬────────────┬────────────┐    │
│  │ Admin      │ Device     │ Monitor    │ Plugin     │    │
│  │ Dashboard  │ Manager    │ Panel      │ Store      │    │
│  ├────────────┼────────────┼────────────┼────────────┤    │
│  │ 配置界面   │ 设备列表   │ 实时监控   │ 插件市场   │    │
│  │ 用户管理   │ 日志查看   │ 性能图表   │ 一键安装   │    │
│  │ 权限控制   │ OTA 升级   │ 告警通知   │ 插件管理   │    │
│  └────────────┴────────────┴────────────┴────────────┘    │
└────────────────────────────────────────────────────────────┘
```

---

### 2.3 核心锁定区域（ORica-Core）

**Layer 0-3 为核心基础设施，开发完成后锁定不变：**

**重要说明：** Python AI 逻辑层（Layer 3）是 ORica 框架的**最核心部分**，包含 Provider 抽象、Plugin 框架、对话管理等。这些都是锁定的 Core，用户无需改动底层代码，只需：
- 通过配置切换 Provider（如 OpenAI → FunASR）
- 编写自定义 Plugin（继承基类即可）
- 配置对话流程（声明式配置）

#### **Layer 0: Frontend Layer（Svelte）**
**锁定内容：**
- 管理后台基础框架
- 组件库（按钮、表单、表格等）
- 路由和状态管理
- API 通信层

**用户可定制：**
- 主题颜色
- Logo 和品牌
- 自定义页面（通过插槽）
- 数据展示（通过配置）

---

#### **Layer 1: Infrastructure Layer（Rust）**
**锁定内容：**
- WebSocket 服务器实现
- RESTful API 框架
- 设备连接管理
- JWT 认证机制
- 配置热更新逻辑
- 统一存储抽象（EloqKV）

**用户无需关心：**
- WebSocket 协议细节
- 设备心跳检测
- 连接池管理
- 数据库操作

---

#### **Layer 2: Performance Layer（Mojo）**
**锁定内容：**
- Opus 音频编解码
- PCM 格式转换
- VAD 特征提取
- SIMD 优化算法
- 音频缓冲区管理

**用户无需关心：**
- 音频处理细节
- 性能优化
- 内存管理
- FFI 调用

---

#### **Layer 3: AI Logic Layer（Python）- 核心中的核心！**

**这是 ORica 框架最重要的一层，包含所有 AI 处理逻辑。**

**锁定内容（Core，用户无需改动）：**

**1. Provider 系统（统一抽象）**
```python
# orica/providers/base.py（框架核心代码，锁定）
from abc import ABC, abstractmethod

class ASRProviderBase(ABC):
    """ASR Provider 抽象基类"""
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """语音识别接口"""
        pass

class TTSProviderBase(ABC):
    """TTS Provider 抽象基类"""
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """语音合成接口"""
        pass

# 类似的还有：
# - LLMProviderBase（大语言模型）
# - VADProviderBase（语音活动检测）
# - MemoryProviderBase（对话记忆）
# - IntentProviderBase（意图识别）
```

**内置 Provider 实现（Core，开箱即用）：**
- **ASR**: OpenAI Whisper, FunASR, Azure Speech, Google Speech
- **TTS**: OpenAI TTS, Edge TTS, Azure TTS, ElevenLabs
- **LLM**: OpenAI (GPT-4o), Anthropic (Claude), GLM-4, Qwen
- **VAD**: Silero VAD, WebRTC VAD
- **Memory**: Local Short-term, Mem0, Redis
- **Intent**: Function Call, ReAct

**用户只需配置，无需写代码：**
```yaml
# config.yaml
providers:
  asr: {name: openai, model: whisper-1}  # 切换 Provider 只需改这里
  tts: {name: edge, voice: zh-CN-XiaoxiaoNeural}
  llm: {name: openai, model: gpt-4o}
```

---

**2. Plugin 系统框架（锁定）**
```python
# orica/plugins/base.py（框架核心代码，锁定）
from abc import ABC, abstractmethod

class Plugin(ABC):
    """插件基类"""
    name: str = ""
    description: str = ""

    @abstractmethod
    def schema(self) -> dict:
        """定义插件参数（JSON Schema）"""
        pass

    @abstractmethod
    async def execute(self, **kwargs):
        """执行插件逻辑"""
        pass

# 插件管理器（Core，锁定）
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register(self, plugin: Plugin):
        """注册插件"""
        self.plugins[plugin.name] = plugin

    async def execute(self, name: str, **kwargs):
        """执行插件"""
        plugin = self.plugins.get(name)
        if plugin:
            return await plugin.execute(**kwargs)
```

**用户只需继承基类：**
```python
# plugins/my_plugin.py（用户代码，可扩展）
from orica import Plugin

class MyPlugin(Plugin):
    name = "my_tool"
    description = "我的工具"

    def schema(self):
        return {"param": {"type": "string"}}

    async def execute(self, **kwargs):
        # 用户自定义逻辑
        return "结果"
```

---

**3. 对话管理器（Dialogue Manager，锁定）**
```python
# orica/dialogue/manager.py（框架核心代码，锁定）
class DialogueManager:
    """对话流程管理"""
    def __init__(self, config):
        self.messages = []
        self.max_history = config.get("max_history", 10)

    def add_user_message(self, text: str):
        """添加用户消息"""
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str):
        """添加助手消息"""
        self.messages.append({"role": "assistant", "content": text})

    def get_llm_history(self) -> list:
        """获取 LLM 对话历史"""
        return self.messages[-self.max_history:]

    async def should_summarize(self) -> bool:
        """判断是否需要摘要"""
        return len(self.messages) > self.max_history

    async def summarize(self):
        """自动摘要"""
        # 调用 LLM 对早期对话进行摘要
        pass
```

**用户只需配置：**
```yaml
# config.yaml
dialogue:
  max_history: 10        # 最大历史消息数
  summary_enabled: true  # 启用自动摘要
```

---

**4. 记忆系统（Memory System，锁定）**
```python
# orica/memory/base.py（框架核心代码，锁定）
class MemoryProviderBase(ABC):
    """记忆系统抽象基类"""
    @abstractmethod
    async def save(self, session_id: str, messages: list):
        """保存对话历史"""
        pass

    @abstractmethod
    async def retrieve(self, session_id: str, query: str) -> list:
        """检索相关记忆"""
        pass

# 内置实现（Core）
class LocalShortMemory(MemoryProviderBase):
    """本地短期记忆"""
    async def save(self, session_id, messages):
        # 保存到本地缓存
        pass

class Mem0Memory(MemoryProviderBase):
    """Mem0 云端记忆"""
    async def save(self, session_id, messages):
        # 调用 Mem0 API
        pass
```

---

**5. 连接处理器（Connection Handler，锁定）**
```python
# orica/core/connection.py（框架核心代码，锁定）
class ConnectionHandler:
    """处理单个设备的 WebSocket 连接"""
    def __init__(self, config, providers):
        self.session_id = str(uuid.uuid4())
        self.asr = providers["asr"]
        self.tts = providers["tts"]
        self.llm = providers["llm"]
        self.vad = providers["vad"]
        self.dialogue = DialogueManager(config)
        self.plugin_manager = PluginManager()

    async def handle_connection(self, websocket):
        """处理连接生命周期"""
        async for message in websocket:
            if isinstance(message, bytes):
                # 音频数据
                await self.handle_audio(message)
            else:
                # 控制消息
                await self.handle_command(message)

    async def handle_audio(self, audio_data: bytes):
        """处理音频流"""
        # 1. VAD 检测（调用 Mojo 加速）
        is_voice = self.vad.detect(audio_data)

        # 2. ASR 识别
        text = await self.asr.transcribe(audio_data)

        # 3. LLM 处理
        response = await self.llm.chat(text)

        # 4. TTS 合成
        audio = await self.tts.synthesize(response)

        # 5. 发送音频
        await websocket.send(audio)
```

---

**用户无需关心：**
- ❌ Provider 抽象的实现细节
- ❌ Plugin 系统的加载和调用机制
- ❌ 对话流程的状态管理
- ❌ 记忆系统的存储和检索
- ❌ WebSocket 连接的生命周期

**用户只需：**
- ✅ 配置 Provider（config.yaml）
- ✅ 编写自定义 Plugin（继承基类）
- ✅ 配置对话参数（config.yaml）

---

### 2.4 用户扩展区域（ORica-SDK）

**只有 Layer 4 是用户扩展层，自由定制：**

#### **Layer 4: Application Layer（用户应用）**
**用户编写：**
- 业务逻辑
- 场景定制（儿童模式、老人模式等）
- 第三方集成（HomeAssistant、米家等）

**示例：**
```python
from orica import ORicaApp

# 一行代码启动应用
app = ORicaApp.from_config("config.yaml")

# 注册自定义插件
app.register_plugin(MyCustomPlugin())

# 启动
app.run()
```

---

## 第三部分：开发者体验

### 3.1 快速开始（5 分钟）

**Step 1: 安装 ORica CLI**
```bash
pip install orica-cli
```

**Step 2: 创建新项目**
```bash
orica create my-companion-robot
cd my-companion-robot

# 项目结构（自动生成）
my-companion-robot/
├── config.yaml          # 配置文件
├── plugins/             # 自定义插件目录
│   ├── __init__.py
│   └── my_plugin.py     # 插件模板
├── main.py              # 应用入口
├── requirements.txt     # Python 依赖
└── firmware/            # ESP32 固件（可选）
    └── esp32.ino
```

**Step 3: 配置 AI 服务**
```yaml
# config.yaml（声明式配置）
providers:
  asr:
    name: openai
    model: whisper-1
    api_key: ${OPENAI_API_KEY}

  tts:
    name: edge
    voice: zh-CN-XiaoxiaoNeural

  llm:
    name: openai
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}

  vad:
    name: silero
    threshold: 0.5

# 设备配置
device:
  type: esp32  # 或 raspberry-pi
  firmware_auto_build: true
```

**Step 4: 运行开发服务器**
```bash
orica dev
# 🚀 ORica Server 启动成功！
# 📡 WebSocket: ws://0.0.0.0:8000
# 🌐 管理后台: http://localhost:8001
# 📊 监控面板: http://localhost:8001/monitor
```

**Step 5: 连接设备测试**
```bash
# 使用浏览器打开测试页面
open http://localhost:8000/test

# 或使用 ESP32 固件（自动生成）
cd firmware
orica firmware flash --port /dev/ttyUSB0
```

---

### 3.2 核心功能演示

#### **功能1：自定义插件（5 行代码）**

```python
# plugins/weather.py
from orica import Plugin

class WeatherPlugin(Plugin):
    name = "get_weather"
    description = "获取指定城市的天气"

    def schema(self):
        return {
            "city": {"type": "string", "description": "城市名称"}
        }

    async def execute(self, city: str):
        # 调用天气 API
        weather = await self.fetch_weather(city)
        return f"{city} 的天气是 {weather}"
```

**自动生效！** 无需重启服务器，插件热加载。

---

#### **功能2：切换 AI 服务商（改配置）**

```yaml
# 从 OpenAI 切换到本地 FunASR（离线）
providers:
  asr:
    name: fun_local
    model: paraformer-zh
    model_dir: ./models/  # 本地模型路径
```

**无需改代码！** 框架自动切换 Provider。

---

#### **功能3：设备管理后台**

访问 `http://localhost:8001`：

```
┌─────────────────────────────────────────┐
│  ORica 管理后台                         │
├─────────────────────────────────────────┤
│  [设备列表] [日志] [配置] [监控] [插件] │
├─────────────────────────────────────────┤
│  设备列表：                              │
│  ┌──────────────────────────────────┐   │
│  │ 设备ID: esp32-001                │   │
│  │ 状态: 在线 🟢                     │   │
│  │ 最后活动: 2s 前                  │   │
│  │ 固件版本: v1.0.2                 │   │
│  │ [查看日志] [OTA升级] [重启]     │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │ 设备ID: rpi-002                  │   │
│  │ 状态: 离线 🔴                     │   │
│  │ 最后活动: 5min 前                │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**开箱即用！** 无需自己开发管理后台。

---

### 3.3 典型场景示例

#### **场景1：儿童陪伴机器人**

```python
# main.py
from orica import ORicaApp
from plugins.story import StoryPlugin
from plugins.music import MusicPlugin

app = ORicaApp.from_config("config.yaml")

# 注册儿童场景插件
app.register_plugin(StoryPlugin())    # 讲故事
app.register_plugin(MusicPlugin())    # 播放儿歌

# 启用儿童模式（过滤不良内容）
app.enable_content_filter(level="children")

# 启动
app.run()
```

**用户体验：**
- 孩子："给我讲个睡前故事"
- 机器人：调用 `StoryPlugin` → 生成儿童故事 → TTS 播放
- 孩子："播放小星星"
- 机器人：调用 `MusicPlugin` → 播放儿歌

---

#### **场景2：智能音箱（类小爱同学）**

```python
from orica import ORicaApp
from plugins.weather import WeatherPlugin
from plugins.home import HomeAssistantPlugin
from plugins.timer import TimerPlugin

app = ORicaApp.from_config("config.yaml")

# 注册智能音箱插件
app.register_plugin(WeatherPlugin())
app.register_plugin(HomeAssistantPlugin())
app.register_plugin(TimerPlugin())

# 启用唤醒词检测
app.enable_wake_word(word="小助手", threshold=0.8)

app.run()
```

**用户体验：**
- 用户："小助手，今天天气怎么样？"
- 音箱：调用 `WeatherPlugin` → "北京今天晴天，25°C"
- 用户："小助手，打开客厅的灯"
- 音箱：调用 `HomeAssistantPlugin` → 控制智能家居 → "已打开客厅的灯"

---

#### **场景3：老年陪伴设备**

```python
from orica import ORicaApp
from plugins.health import HealthReminderPlugin
from plugins.news import NewsPlugin

app = ORicaApp.from_config("config.yaml")

# 注册老年场景插件
app.register_plugin(HealthReminderPlugin())  # 健康提醒
app.register_plugin(NewsPlugin())            # 新闻播报

# 启用定时任务
app.add_schedule("08:00", lambda: app.speak("早上好，记得吃药哦"))
app.add_schedule("12:00", lambda: app.read_news())

# 语音速度调慢（适合老年人）
app.set_tts_speed(0.8)

app.run()
```

---

## 第四部分：ORica-Core 模块详解

### 4.1 ORica-Server（Rust WebSocket 服务器）

**职责：**
- WebSocket 连接管理
- 设备注册和认证
- 音频流转发
- 心跳检测

**API：**
```rust
// 用户无需编写，框架自动处理
// 但可以通过配置调整参数

// config.yaml
server:
  host: 0.0.0.0
  port: 8000
  max_connections: 1000
  heartbeat_interval: 10  # 秒
  connection_timeout: 60  # 秒
```

---

### 4.2 ORica-Config-API（Rust 配置管理）

**职责：**
- RESTful API 服务器
- 配置 CRUD
- 设备管理接口
- JWT 认证

**API 端点：**
```
GET    /api/devices          - 获取设备列表
GET    /api/devices/:id      - 获取设备详情
POST   /api/devices/:id/ota  - 触发 OTA 升级
GET    /api/config           - 获取配置
PUT    /api/config           - 更新配置
POST   /api/auth/login       - 登录（获取 JWT）
```

---

### 4.3 ORica-Audio（Mojo 音频处理库）

**职责：**
- Opus 编解码
- PCM 格式转换
- VAD 检测
- 音频重采样

**Python 接口：**
```python
from orica.audio import AudioProcessor

processor = AudioProcessor()

# 解码 Opus（自动调用 Mojo 加速）
pcm_data = processor.decode_opus(opus_bytes)

# VAD 检测（10x 加速）
is_voice = processor.detect_voice(pcm_data, threshold=0.5)

# PCM 转换（100x 加速）
float_audio = processor.pcm_to_float32(pcm_data)
```

**用户无需关心：**
- Mojo 实现细节
- SIMD 优化
- FFI 调用
- 内存管理

---

### 4.4 ORica-Storage（统一存储抽象）

**职责：**
- 统一 KV 和 SQL 接口
- 配置持久化
- 对话历史存储
- 设备状态管理

**API：**
```python
from orica.storage import Storage

storage = Storage.from_config(config)

# KV 操作
storage.set("device:esp32-001:status", "online")
status = storage.get("device:esp32-001:status")

# SQL 操作
users = storage.query("SELECT * FROM users WHERE role = ?", ["admin"])

# 事务
with storage.transaction():
    storage.set("key1", "value1")
    storage.set("key2", "value2")
```

---

## 第五部分：ORica-SDK 模块详解

### 5.1 orica-py（Python SDK）

**核心 API：**

```python
from orica import ORicaApp, Plugin, Provider

# 1. 应用类
app = ORicaApp.from_config("config.yaml")
app.register_plugin(MyPlugin())
app.run()

# 2. 插件基类
class MyPlugin(Plugin):
    name = "my_plugin"
    description = "描述"

    def schema(self):
        return {"param": {"type": "string"}}

    async def execute(self, **kwargs):
        return "结果"

# 3. Provider 基类（高级用户）
class MyASRProvider(Provider):
    provider_type = "asr"

    async def transcribe(self, audio_data: bytes) -> str:
        # 自定义 ASR 实现
        pass
```

---

### 5.2 orica-web-ui（Web 前端组件库）

**Svelte 组件：**

```svelte
<!-- DeviceList.svelte -->
<script>
  import { DeviceManager } from 'orica-web-ui';
</script>

<DeviceManager
  apiUrl="{config.apiUrl}"
  onDeviceClick="{handleDeviceClick}"
  showOTAButton="{true}"
/>
```

**可定制主题：**
```css
/* custom-theme.css */
:root {
  --orica-primary-color: #00a8ff;
  --orica-background-color: #1e1e1e;
  --orica-text-color: #ffffff;
}
```

---

### 5.3 orica-cli（命令行工具）

**命令清单：**

```bash
# 项目管理
orica create <project-name>    # 创建新项目
orica dev                       # 启动开发服务器
orica build                     # 构建生产版本
orica deploy                    # 部署到服务器

# 固件管理
orica firmware build            # 构建 ESP32 固件
orica firmware flash --port /dev/ttyUSB0  # 烧录固件
orica firmware ota <device-id>  # 远程 OTA 升级

# 插件管理
orica plugin create <name>      # 创建插件模板
orica plugin install <name>     # 安装社区插件
orica plugin list               # 列出已安装插件
orica plugin publish            # 发布插件到市场

# 设备管理
orica device list               # 列出所有设备
orica device logs <device-id>   # 查看设备日志
orica device reboot <device-id> # 重启设备

# 测试和调试
orica test                      # 运行测试
orica benchmark                 # 性能基准测试
orica simulate                  # 启动设备模拟器
```

---

## 第六部分：硬件集成

### 6.1 ESP32 固件（自动生成）

**固件功能：**
- 音频采集（I2S 麦克风）
- Opus 编码（压缩音频）
- WebSocket 客户端（连接服务器）
- 音频播放（I2S 扬声器）
- OTA 升级（远程更新）
- LED 指示灯控制
- 按键唤醒

**自动生成：**
```bash
orica firmware build --device esp32

# 生成文件
firmware/
├── esp32.ino              # Arduino 主文件
├── config.h               # 配置头文件
├── audio_capture.cpp      # 音频采集
├── opus_encoder.cpp       # Opus 编码
├── websocket_client.cpp   # WebSocket 客户端
└── ota_update.cpp         # OTA 升级
```

**用户只需修改：**
```c
// config.h
#define WIFI_SSID "你的WiFi名称"
#define WIFI_PASSWORD "你的WiFi密码"
#define SERVER_URL "ws://192.168.1.100:8000"
#define DEVICE_ID "esp32-001"
```

---

### 6.2 树莓派部署

**一键安装脚本：**
```bash
# 下载安装脚本
curl -sSL https://get.orica.dev | bash

# 或手动安装
pip install orica
orica create my-robot
cd my-robot
orica dev
```

**资源占用：**
- 内存：< 128MB
- CPU：< 10%（空闲时）
- 启动时间：< 3 秒

---

### 6.3 硬件推荐配置

**ESP32 最低配置：**
- 芯片：ESP32-WROVER（带 PSRAM）
- 闪存：4MB
- PSRAM：4MB
- 麦克风：INMP441（I2S）
- 扬声器：MAX98357A（I2S）

**树莓派推荐配置：**
- 型号：Raspberry Pi 4B（2GB 内存）
- SD 卡：16GB（Class 10）
- 麦克风：USB 麦克风或 ReSpeaker
- 扬声器：3.5mm 音频输出

**采购清单（成本预估）：**
```
ESP32 方案（低成本）：
├─ ESP32-WROVER 模组：¥15
├─ INMP441 麦克风：¥5
├─ MAX98357A 功放：¥8
├─ 扬声器：¥10
└─ PCB + 外壳：¥20
总计：¥58

树莓派方案（高性能）：
├─ Raspberry Pi 4B (2GB)：¥250
├─ USB 麦克风：¥50
├─ 扬声器：¥30
└─ 外壳 + SD 卡：¥50
总计：¥380
```

---

## 第七部分：商业模式与生态

### 7.1 开源 + 商业双轨

**开源版本（ORica Community - MIT License）：**
- ✅ 完整的框架核心（ORica-Core）
- ✅ Python SDK（orica-py）
- ✅ CLI 工具（orica-cli）
- ✅ 基础插件（天气、音乐、定时器）
- ✅ Web 管理后台（基础功能）
- ✅ ESP32 固件生成
- ✅ 文档和教程

**商业版本（ORica Enterprise）：**
- 💰 企业级 Provider（Azure、AWS、阿里云）
- 💰 高级插件（知识库、多租户、CRM 集成）
- 💰 高级管理后台（批量管理、高级监控）
- 💰 SLA 保障（99.9% 可用性）
- 💰 技术支持（7x24 小时）
- 💰 定制开发服务

---

### 7.2 收入模式

**1. 订阅服务**
- **Community**: 免费（个人/小团队）
- **Pro**: ¥499/月（< 50 台设备）
- **Enterprise**: ¥4999/月（无限设备 + 技术支持）

**2. 云托管服务（ORica Cloud）**
- 无需自建服务器，托管 AI 应用
- 按设备数量计费：¥10/设备/月
- 包含：设备管理、OTA 升级、监控告警

**3. 硬件销售（未来）**
- ORica 官方硬件套件（ESP32/树莓派开发板）
- 预装 ORica 固件，开箱即用
- 价格：¥199-599

**4. 插件市场分成**
- 开发者在插件市场售卖插件
- 平台抽取 20% 分成
- 官方插件免费，社区插件自定价

**5. 培训和咨询**
- 企业培训课程：¥5000/天
- 定制开发服务：¥800-1500/人日
- 技术咨询：¥500/小时

---

### 7.3 目标市场

**TAM（Total Addressable Market）：**

```
全球市场：
├─ 智能硬件创客：1000 万+
├─ 智能硬件公司：10 万+ 家
├─ 教育机构（STEAM 教育）：50 万+ 所
└─ AI 玩具厂商：5000+ 家

中国市场：
├─ 智能硬件创客：300 万+
├─ 智能硬件公司：2 万+ 家
├─ 教育机构：10 万+ 所
└─ AI 玩具厂商：1000+ 家
```

**目标用户画像：**
1. **硬件创客（个人）**
   - 想快速实现 AI 陪伴硬件原型
   - 技术能力：中等（会 Python，懂 ESP32）
   - 预算：< ¥1000
   - 典型项目：智能音箱、陪伴机器人

2. **智能硬件公司（SMB）**
   - 需要快速上市产品
   - 团队规模：5-50 人
   - 预算：¥5 万-50 万
   - 典型产品：AI 玩具、教育机器人、智能音箱

3. **教育机构（B2B）**
   - STEAM 教育、编程教育
   - 需要教学套件 + 课程
   - 预算：¥10 万-100 万
   - 典型场景：机器人编程课、AI 课程

---

### 7.4 预期增长

```
Year 1（2026）: 种子用户期
├─ 用户数：1,000
├─ 付费用户：50
├─ ARR：¥30 万（$5K）
└─ GitHub Stars：3,000

Year 2（2027）: 社区建设期
├─ 用户数：10,000
├─ 付费用户：500
├─ ARR：¥300 万（$50K）
└─ GitHub Stars：15,000

Year 3（2028）: 生态爆发期
├─ 用户数：50,000
├─ 付费用户：2,500
├─ ARR：¥1500 万（$250K）
└─ GitHub Stars：50,000

Year 5（2030）: 行业标准期
├─ 用户数：500,000
├─ 付费用户：25,000
├─ ARR：¥1.5 亿（$2.5M）
└─ GitHub Stars：200,000
```

---

## 第八部分：实施路线图

### 8.1 Phase 1: MVP 开发（3-6 个月）

**目标：** 发布 ORica v0.1.0（可用但功能有限）

**任务清单：**
- [ ] 完成 xiaozhi 重构（Python + Mojo + Rust）
- [ ] 提取 ORica-Core 核心库
  - [ ] orica-server（Rust WebSocket）
  - [ ] orica-config-api（Rust API）
  - [ ] orica-audio（Mojo 音频处理）
  - [ ] orica-storage（统一存储）
- [ ] 实现 ORica-SDK
  - [ ] orica-py（Python SDK）
  - [ ] orica-cli（CLI 工具）
  - [ ] orica-web-ui（Svelte 组件库）
- [ ] ESP32 固件自动生成
- [ ] 文档
  - [ ] 快速开始
  - [ ] API 参考
  - [ ] 插件开发指南
  - [ ] 硬件集成指南
- [ ] 示例项目（3-5 个）
  - [ ] 智能音箱
  - [ ] 儿童陪伴机器人
  - [ ] 老年陪伴设备

**里程碑：**
- ✅ 开发者可以用 10 行代码启动一个 AI 陪伴硬件
- ✅ 支持 ESP32 和树莓派
- ✅ 支持 2-3 个主流 Provider（OpenAI, Edge TTS, FunASR）
- ✅ 文档完整度 >= 80%

---

### 8.2 Phase 2: 社区建设（6-12 个月）

**目标：** 建立开发者社区和插件生态

**任务清单：**
- [ ] 发布官网（orica.dev）
  - [ ] 文档站点
  - [ ] 插件市场
  - [ ] 案例展示
  - [ ] 论坛/社区
- [ ] 创建 GitHub Organization（orica-framework）
- [ ] 启动社区渠道
  - [ ] Discord 服务器
  - [ ] 微信社群
  - [ ] Twitter/微博账号
- [ ] 发布 10+ 官方示例项目
- [ ] 组织活动
  - [ ] 线上黑客马拉松
  - [ ] 线下 Workshop
  - [ ] 参加硬件创客活动
- [ ] 插件生态
  - [ ] 发布 20+ 官方插件
  - [ ] 建立插件开发者计划
  - [ ] 插件市场上线
- [ ] 发布 v1.0.0（稳定版）

**里程碑：**
- ✅ GitHub Stars >= 5,000
- ✅ 社区插件 >= 50 个
- ✅ 月活跃用户 >= 1,000
- ✅ 社区贡献者 >= 50 人

---

### 8.3 Phase 3: 商业化（12-24 个月）

**目标：** 推出商业服务和企业版

**任务清单：**
- [ ] 发布 ORica Cloud（托管服务）
  - [ ] 设备管理平台
  - [ ] OTA 升级服务
  - [ ] 监控和告警
- [ ] 发布 ORica Enterprise
  - [ ] 企业级 Provider
  - [ ] 高级插件
  - [ ] SLA 保障
- [ ] 建立销售和支持团队
  - [ ] 销售经理（2 人）
  - [ ] 客户成功（2 人）
  - [ ] 技术支持（3 人）
- [ ] 签约首批付费客户（>= 10 家）
- [ ] 发布企业案例研究
- [ ] 参加行业会议
  - [ ] 智能硬件展会
  - [ ] 创客嘉年华
  - [ ] AI 技术大会

**里程碑：**
- ✅ ARR >= ¥100 万（$16K）
- ✅ 付费用户 >= 100
- ✅ 企业客户 >= 10 家
- ✅ 月活跃设备 >= 10,000 台

---

### 8.4 Phase 4: 硬件生态（24-36 个月）

**目标：** 扩展硬件生态，成为行业标准

**任务清单：**
- [ ] 发布 ORica 官方硬件套件
  - [ ] ORica DevKit（ESP32 开发板）
  - [ ] ORica Starter Kit（树莓派套件）
  - [ ] ORica Pro Kit（高端套件）
- [ ] 硬件合作伙伴计划
  - [ ] 与 ESP32 模组厂商合作
  - [ ] 与树莓派经销商合作
  - [ ] 与创客教育机构合作
- [ ] 国际化
  - [ ] 英文文档和网站
  - [ ] 国际社区运营
  - [ ] 海外市场推广
- [ ] 认证体系
  - [ ] ORica Certified Developer
  - [ ] ORica Certified Hardware
- [ ] 出版技术书籍
  - [ ] 《ORica 实战：从零构建 AI 陪伴硬件》

**里程碑：**
- ✅ 硬件销售 >= 10,000 套
- ✅ ARR >= ¥1000 万（$160K）
- ✅ 月活跃设备 >= 100,000 台
- ✅ GitHub Stars >= 50,000

---

## 第九部分：风险与应对

### 9.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| Mojo 生态不成熟 | 中 | 高 | 保留 Python 降级方案，性能差异可接受 |
| 硬件兼容性问题 | 中 | 中 | 限制支持的硬件型号，提供测试清单 |
| ESP32 资源不足 | 低 | 中 | 优化固件大小，提供"轻量版"固件 |
| Rust 编译复杂度 | 低 | 低 | 提供预编译二进制，用户无需编译 |

---

### 9.2 市场风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 用户采纳缓慢 | 中 | 高 | 投入社区运营，制作视频教程，降低门槛 |
| 竞争对手出现 | 高 | 中 | 快速迭代，建立技术护城河（Mojo 加速） |
| 商业化困难 | 中 | 中 | 先做大社区（免费），再考虑变现 |
| 硬件销售受限 | 低 | 低 | 硬件销售是额外收入，不是主要收入 |

---

### 9.3 运营风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 文档不完善 | 高 | 高 | 投入专职技术写作，持续更新文档 |
| 社区管理困难 | 中 | 中 | 建立社区规范，培养核心贡献者 |
| 版本升级兼容性 | 中 | 中 | 遵循语义化版本，提供迁移工具 |
| 安全问题 | 低 | 高 | 安全审计，及时修复漏洞，责任声明 |

---

## 第十部分：总结与行动

### 10.1 核心价值总结

**ORica Framework 的独特价值：**

```
✅ 1. 聚焦 AI 陪伴硬件
   - 不是通用 AI 框架，而是垂直领域专家
   - 边缘优先设计（ESP32/树莓派）
   - 实时语音交互（<500ms 延迟）

✅ 2. 核心锁定 + 扩展自由
   - 底层（ORica-Core）锁定，用户无需关心
   - 上层（ORica-SDK）自由扩展
   - 升级无痛，向后兼容

✅ 3. 多语言协作
   - Python (AI) + Mojo (性能) + Rust (基础设施)
   - 10-100 倍性能提升
   - 发挥各语言优势

✅ 4. 开箱即用
   - 5 分钟创建项目
   - 自动生成 ESP32 固件
   - 内置管理后台
   - 插件市场（即将推出）

✅ 5. 硬件生态友好
   - 一键 OTA 升级
   - 批量设备管理
   - 低资源占用（< 128MB）
   - 硬件套件（官方 + 合作伙伴）
```

---

### 10.2 立即行动计划

**第一步：验证可行性（1-2 周）**
```bash
# 1. 注册 GitHub Organization
https://github.com/orica-framework

# 2. 注册域名
orica.dev（推荐）
orica.io（备选）

# 3. 设计 Logo 和品牌
- 找设计师设计 Logo
- 确定品牌色彩（建议：科技蓝 + 温暖橙）

# 4. 撰写项目愿景（README）
- 复制本文档的核心内容
- 制作架构图
- 录制 Demo 视频

# 5. 邀请核心团队
- 至少 2-3 人
- 技能要求：Rust + Python + 前端
```

**第二步：MVP 开发（2-3 个月）**
```bash
# 1. 重构 xiaozhi 为 ORica-Core
git clone https://github.com/xiaozhi-esp32-server
cd xiaozhi-esp32-server
git checkout -b orica-refactor

# 2. 创建 orica-py SDK
cd orica-sdk/python
pip install -e .

# 3. 创建 orica-cli 工具
cd orica-tools/cli
cargo build --release

# 4. 编写文档
cd docs
mkdocs new .
mkdocs serve

# 5. 发布 v0.1.0-alpha
git tag v0.1.0-alpha
git push origin v0.1.0-alpha
```

**第三步：社区冷启动（1 个月）**
```bash
# 1. 发布到技术社区
- Product Hunt
- Hacker News
- Reddit (r/esp32, r/raspberry_pi, r/iot)
- V2EX
- CSDN
- 掘金

# 2. 创建社区频道
- Discord: discord.gg/orica
- 微信群：ORica 开发者社群
- Telegram: t.me/orica

# 3. 制作教程
- YouTube: ORica 快速入门
- B站：ORica 从零开始
- 博客：5 分钟构建 AI 陪伴机器人

# 4. 邀请早期采用者
- 联系硬件创客 KOL
- 赠送官方硬件套件
- 收集反馈并快速迭代
```

---

### 10.3 决策检查清单

**在正式启动前，请确认：**

**产品维度：**
- [x] 是否解决了真实痛点？（AI 陪伴硬件开发复杂度）
- [x] 是否有差异化竞争优势？（核心锁定 + 边缘优先）
- [x] 目标用户是否足够大？（1000 万+ 硬件创客）
- [x] 是否聚焦垂直领域？（AI 陪伴硬件，不是通用框架）

**技术维度：**
- [x] 技术栈是否成熟？（Python + Mojo + Rust）
- [x] 是否有技术护城河？（Mojo 加速 + 核心锁定）
- [x] 是否可持续维护？（开源社区 + 商业支持）
- [x] 是否支持边缘设备？（ESP32 + 树莓派）

**商业维度：**
- [x] 是否有清晰的商业模式？（订阅 + 云服务 + 硬件）
- [x] 是否有可行的获客渠道？（开源社区 + 硬件创客活动）
- [x] 是否有退出路径？（被收购 / 持续盈利）

**团队维度：**
- [ ] 是否有足够的资源？（时间、资金、人力）
- [ ] 团队是否有相关经验？（框架开发、硬件集成）
- [ ] 是否有长期投入的决心？（至少 3-5 年）

---

### 10.4 我的建议（作为 AI 助手）

**这个方向非常棒！关键优势：**

1. **聚焦垂直领域** ✅
   - 不和 LangChain 等通用框架竞争
   - AI 陪伴硬件是明确的细分市场
   - 用户画像清晰（硬件创客、智能硬件公司）

2. **核心锁定设计** ✅
   - 用户无需关心底层
   - 只需扩展插件和配置
   - 升级无痛，降低维护成本

3. **技术护城河** ✅
   - Mojo 加速是差异化优势
   - 多语言协作难以复制
   - 边缘优先设计（资源优化）

4. **硬件生态** ✅
   - ESP32 是量产首选（成本低）
   - 树莓派是原型首选（性能强）
   - 硬件销售是额外收入

**建议的启动策略：**

1. **先做 MVP**（2-3 个月）
   - 不要追求完美，快速验证市场
   - 重点：核心功能 + 文档 + 示例

2. **开源优先**（前 1-2 年）
   - 建立社区，积累用户
   - 不要急于变现
   - GitHub Stars 是最好的指标

3. **社区运营**（持续投入）
   - 制作高质量教程（视频 + 博客）
   - 参加硬件创客活动
   - 培养核心贡献者

4. **商业化时机**（Year 2-3）
   - 用户数 >= 10,000 时再考虑
   - 先推出云服务（托管）
   - 再推出企业版（SLA）

**关键问题：**
- 您是否有 3-6 个月全职投入？
- 是否有 2-3 人的团队支持？
- 是否愿意长期投入（3-5 年）？

如果答案是**肯定的**，那就**立即开始**吧！

---

## 结语

**ORica Framework 不是通用 AI 框架，而是 AI 陪伴硬件的专家系统。**

通过"核心锁定 + 扩展自由"的设计，让硬件创客和智能硬件公司能够：
- **5 分钟**启动项目
- **10 行代码**实现 AI 陪伴硬件
- **无需关心**底层基础设施
- **自由扩展**插件和功能

**让我们一起，构建 AI 陪伴硬件的新标准！** 🚀

---

**文档版本**: 2.0（重新定位版）
**创建日期**: 2026-01-16
**维护者**: Claude Code
**反馈渠道**: [创建 Issue](https://github.com/orica-framework/orica/issues)
**官网**: https://orica.dev（即将上线）
**Discord**: https://discord.gg/orica（即将上线）
