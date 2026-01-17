# ORica 架构快速参考

## 核心架构划分（一图看懂）

```
┌────────────────────────────────────────────────────────┐
│  ORica-Core（框架核心，锁定不变）                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 3: AI Logic（Python）- 最核心！                 │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✅ Provider 系统（ASR/TTS/LLM/VAD/Memory）      │  │
│  │    - 抽象基类（锁定）                            │  │
│  │    - 内置实现：OpenAI, FunASR, Edge TTS...      │  │
│  │    - 用户配置：config.yaml 切换                 │  │
│  │                                                  │  │
│  │ ✅ Plugin 框架（插件系统）                       │  │
│  │    - Plugin 基类（锁定）                        │  │
│  │    - PluginManager（锁定）                      │  │
│  │    - 用户扩展：继承基类编写自定义插件           │  │
│  │                                                  │  │
│  │ ✅ Dialogue Manager（对话管理）                 │  │
│  │    - 对话历史管理（锁定）                       │  │
│  │    - 自动摘要（锁定）                           │  │
│  │    - 用户配置：max_history, summary_enabled     │  │
│  │                                                  │  │
│  │ ✅ Memory System（记忆系统）                    │  │
│  │    - 记忆抽象基类（锁定）                       │  │
│  │    - 内置实现：LocalShort, Mem0, Redis         │  │
│  │    - 用户配置：选择记忆类型                     │  │
│  │                                                  │  │
│  │ ✅ Connection Handler（连接处理）               │  │
│  │    - WebSocket 连接生命周期（锁定）             │  │
│  │    - 音频流处理流程（锁定）                     │  │
│  │    - 消息路由（锁定）                           │  │
│  └─────────────────────────────────────────────────┘  │
│                          ↓ 调用                        │
│  Layer 2: Performance（Mojo）                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✅ 音频处理加速（10-100x）                       │  │
│  │    - Opus 编解码 (FFI libopus)                  │  │
│  │    - PCM 转换 (SIMD)                            │  │
│  │    - VAD 检测 (SIMD)                            │  │
│  └─────────────────────────────────────────────────┘  │
│                          ↓ 调用                        │
│  Layer 1: Infrastructure（Rust）                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✅ WebSocket 服务器（连接管理、心跳）            │  │
│  │ ✅ Config API（RESTful、JWT）                   │  │
│  │ ✅ Storage（EloqKV 抽象）                       │  │
│  │ ✅ Device Manager（设备注册、OTA）              │  │
│  └─────────────────────────────────────────────────┘  │
│                          ↓ HTTP                        │
│  Layer 0: Frontend（Svelte）                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✅ 管理后台（开箱即用）                          │  │
│  │ ✅ 组件库（按钮、表单、图表）                    │  │
│  │ ✅ 设备管理界面                                  │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                          ↓ ORica SDK API
┌────────────────────────────────────────────────────────┐
│  ORica-SDK（用户扩展区）                               │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 4: Application（用户应用代码）                  │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 🔧 用户自定义 Plugin                             │  │
│  │ 🔧 业务逻辑（场景定制）                          │  │
│  │ 🔧 第三方集成（HomeAssistant, 米家）             │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 用户体验总结

### **用户完全不需要改动的部分（ORica-Core）：**

```
✅ Layer 0-3 全部锁定

用户无需关心：
❌ WebSocket 如何实现
❌ Opus 如何编解码
❌ VAD 如何检测
❌ Provider 如何抽象
❌ Plugin 如何加载
❌ 对话如何管理
❌ 记忆如何存储
❌ 连接如何处理
```

---

### **用户只需要做的事情（ORica-SDK）：**

#### **1. 配置 AI 服务（config.yaml）**
```yaml
providers:
  asr: {name: openai, model: whisper-1}  # 切换只需改这里
  tts: {name: edge, voice: zh-CN-XiaoxiaoNeural}
  llm: {name: openai, model: gpt-4o}
```

#### **2. 编写自定义插件（5 行代码）**
```python
from orica import Plugin

class WeatherPlugin(Plugin):
    name = "get_weather"
    async def execute(self, city: str):
        return f"{city} 的天气是晴天"
```

#### **3. 启动应用（1 行代码）**
```python
from orica import ORicaApp
app = ORicaApp.from_config("config.yaml")
app.register_plugin(WeatherPlugin())
app.run()
```

---

## Python AI 逻辑层（Layer 3）详解

### **为什么是核心中的核心？**

**Layer 3 包含所有 AI 处理逻辑，是 ORica 框架的灵魂：**

1. **Provider 系统** - 统一所有 AI 服务商接口
   - 用户无需学习每个服务商的 API
   - 切换服务商只需改配置
   - 框架自动处理错误和重试

2. **Plugin 系统** - 让 AI 拥有工具能力
   - 天气查询、音乐控制、智能家居...
   - 用户只需继承基类
   - 框架自动注册和调用

3. **Dialogue Manager** - 管理对话流程
   - 自动管理对话历史
   - 自动摘要（避免 token 爆炸）
   - 处理中断和状态

4. **Memory System** - 让 AI 拥有记忆
   - 记住用户偏好
   - 长期对话上下文
   - 多会话管理

5. **Connection Handler** - 协调所有组件
   - 音频流处理
   - Provider 调用
   - 错误处理

---

## 代码组织结构

```
orica-framework/
├── orica-core/                 # 核心框架（锁定）
│   ├── python/                 # Python AI 逻辑层
│   │   ├── providers/          # Provider 系统
│   │   │   ├── base.py         # 抽象基类（锁定）
│   │   │   ├── asr/
│   │   │   │   ├── openai.py   # OpenAI Whisper 实现
│   │   │   │   ├── fun_local.py # FunASR 实现
│   │   │   │   └── ...
│   │   │   ├── tts/
│   │   │   │   ├── openai.py
│   │   │   │   ├── edge.py     # Edge TTS 实现
│   │   │   │   └── ...
│   │   │   ├── llm/
│   │   │   │   ├── openai.py
│   │   │   │   ├── anthropic.py
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── plugins/            # Plugin 框架
│   │   │   ├── base.py         # Plugin 基类（锁定）
│   │   │   └── manager.py      # PluginManager（锁定）
│   │   ├── dialogue/           # 对话管理
│   │   │   └── manager.py      # DialogueManager（锁定）
│   │   ├── memory/             # 记忆系统
│   │   │   ├── base.py         # 抽象基类（锁定）
│   │   │   ├── local_short.py  # 本地短期记忆
│   │   │   └── mem0.py         # Mem0 集成
│   │   ├── core/               # 连接处理
│   │   │   └── connection.py   # ConnectionHandler（锁定）
│   │   └── __init__.py         # 导出 API
│   │
│   ├── mojo/                   # Mojo 性能层
│   │   ├── audio/
│   │   │   ├── opus_codec.mojo # Opus 编解码
│   │   │   ├── processing.mojo # 音频处理
│   │   │   └── vad.mojo        # VAD 检测
│   │   └── bindings/           # Python 绑定
│   │
│   ├── rust/                   # Rust 基础设施层
│   │   ├── orica-server/       # WebSocket 服务器
│   │   ├── orica-config-api/   # Config API
│   │   └── orica-storage/      # 存储抽象
│   │
│   └── svelte/                 # Svelte 前端层
│       └── orica-web-ui/       # Web 管理后台
│
├── orica-sdk/                  # 开发者 SDK
│   ├── orica-py/               # Python SDK
│   │   └── __init__.py         # 导出 ORicaApp, Plugin 等
│   └── orica-cli/              # CLI 工具
│
├── orica-plugins/              # 官方插件（用户可参考）
│   ├── weather/                # 天气插件
│   ├── music/                  # 音乐插件
│   └── home/                   # 智能家居插件
│
└── examples/                   # 示例项目
    ├── smart-speaker/          # 智能音箱
    ├── companion-robot/        # 陪伴机器人
    └── ...
```

---

## 总结

**ORica-Core = Layer 0 + Layer 1 + Layer 2 + Layer 3**

其中 **Layer 3（Python AI Logic）是最核心的部分**，包含：
- ✅ Provider 系统（统一 AI 服务商接口）
- ✅ Plugin 框架（工具能力扩展）
- ✅ Dialogue Manager（对话流程管理）
- ✅ Memory System（记忆系统）
- ✅ Connection Handler（连接处理器）

**用户只需：**
1. 配置 Provider（config.yaml）
2. 编写自定义 Plugin（继承基类）
3. 启动应用（一行代码）

**框架自动处理：**
- 所有底层基础设施（WebSocket、音频处理、存储）
- AI 服务调用（ASR、TTS、LLM）
- 对话流程和记忆管理
- 错误处理和重试

---

**文档版本**: 3.0
**创建日期**: 2026-01-16
**维护者**: Claude Code
