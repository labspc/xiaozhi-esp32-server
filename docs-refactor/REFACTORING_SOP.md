# xiaozhi-esp32-server 系统重构 SOP

> **Standard Operating Procedure for System Refactoring**
>
> 版本：v1.0.0
> 更新日期：2024-01-17
> 目标框架：ORica Framework

---

## 目录

1. [项目概览](#1-项目概览)
2. [当前系统架构分析](#2-当前系统架构分析)
3. [目标架构设计](#3-目标架构设计)
4. [重构优先级与依赖关系](#4-重构优先级与依赖关系)
5. [Phase 0: 基础设施准备](#5-phase-0-基础设施准备)
6. [Phase 1: 存储层迁移 (EloqKV)](#6-phase-1-存储层迁移-eloqkv)
7. [Phase 2: Java → Rust (Axum) 迁移](#7-phase-2-java--rust-axum-迁移)
8. [Phase 3: Python 性能优化 (Mojo + Rust)](#8-phase-3-python-性能优化-mojo--rust)
9. [Phase 4: 前端重构 (Vue → Svelte)](#9-phase-4-前端重构-vue--svelte)
10. [Phase 5: API 统一与文档化](#10-phase-5-api-统一与文档化)
11. [Phase 6: 集成测试与灰度发布](#11-phase-6-集成测试与灰度发布)
12. [风险评估与缓解措施](#12-风险评估与缓解措施)
13. [时间线总览](#13-时间线总览)
14. [附录：技术选型速查表](#14-附录技术选型速查表)

---

## 1. 项目概览

### 1.1 重构目标

将 xiaozhi-esp32-server 从单体多语言项目改造为 **ORica Framework**（OpenRica Community）—— 一个专注于 AI 陪伴硬件的垂直框架。

### 1.2 技术栈迁移路线

```
┌─────────────────────────────────────────────────────────────────┐
│                        技术栈迁移路线                             │
├─────────────────────────────────────────────────────────────────┤
│  当前架构                          目标架构                       │
│  ─────────                         ─────────                     │
│                                                                  │
│  Python (xiaozhi-server)                                         │
│    ├─ WebSocket 服务器      →      Rust (基础设施层)              │
│    ├─ HTTP 服务器           →      Rust + Axum                   │
│    ├─ AI 逻辑处理           →      Python (只做 AI 逻辑层)        │
│    └─ 音频编解码            →      Mojo (性能层，10-100x 加速)    │
│                                                                  │
│  Java (manager-api)                                              │
│    ├─ REST API              →      Rust + Axum                   │
│    ├─ 权限管理              →      Rust + JWT                    │
│    └─ 数据库操作            →      Rust + EloqKV                 │
│                                                                  │
│  Vue2 (manager-web)         →      Svelte + SvelteKit (前端层)   │
│  MySQL + Redis              →      EloqKV (统一存储)              │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  关键变化：                                                       │
│  • Rust 接管所有网络通信（WebSocket、HTTP）                       │
│  • Python 只做 AI 逻辑（Provider调度、对话管理、插件执行）        │
│  • Rust 通过 PyO3 调用 Python 进行 AI 处理                       │
│  • Mojo 加速音频处理（Opus编解码、VAD特征提取）                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 预期收益

| 维度 | 现状 | 目标 | 改进幅度 |
|------|------|------|----------|
| 启动时间 | 8-15s (Java) | <1s (Rust) | **90%↓** |
| 内存占用 | 300-500MB | <50MB | **85%↓** |
| 音频处理延迟 | 500μs (Python) | 30-50μs (Mojo) | **90%↓** |
| 运维成本 | MySQL + Redis | EloqKV 单一存储 | **50%↓** |
| 前端构建速度 | 30-60s | <5s | **90%↓** |

---

## 2. 当前系统架构分析

### 2.1 模块组成

```
xiaozhi-esp32-server/
├── main/
│   ├── xiaozhi-server/     # Python, Port 8000
│   │   ├── core/           # 核心业务逻辑
│   │   │   ├── providers/  # ASR/TTS/LLM/VAD 提供者
│   │   │   ├── handle/     # WebSocket 处理器
│   │   │   └── utils/      # 工具函数
│   │   ├── plugins_func/   # 插件系统
│   │   └── config/         # 配置管理
│   │
│   ├── manager-api/        # Java Spring Boot, Port 8002
│   │   └── src/main/java/xiaozhi/
│   │       ├── modules/    # 业务模块
│   │       └── common/     # 通用组件
│   │
│   ├── manager-web/        # Vue2, Port 8001
│   │   └── src/
│   │       ├── views/      # 页面组件
│   │       ├── components/ # 通用组件
│   │       └── apis/       # API 调用层
│   │
│   └── manager-mobile/     # uni-app + Vue3
```

### 2.2 当前痛点分析

| 模块 | 痛点 | 影响 |
|------|------|------|
| **Java (manager-api)** | 启动慢、内存占用高、依赖重 | 资源浪费、部署复杂 |
| **Python (xiaozhi-server)** | 音频处理性能瓶颈 | 延迟高、并发受限 |
| **Vue2 (manager-web)** | 框架过时、选项式 API 冗余 | 维护困难、开发效率低 |
| **存储层 (MySQL+Redis)** | 运维复杂、一致性难保证 | 成本高、易出错 |

### 2.3 依赖关系图

```
                    ┌──────────────┐
                    │   ESP32      │
                    │   设备       │
                    └──────┬───────┘
                           │ WebSocket
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    xiaozhi-server (Python)                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │   ASR   │  │   TTS   │  │   LLM   │  │   VAD   │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                         │                                     │
│                  ┌──────┴──────┐                             │
│                  │   Plugins   │                             │
│                  └─────────────┘                             │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP (配置同步)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    manager-api (Java)                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  设备   │  │  角色   │  │  用户   │  │  配置   │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐   ┌────────┐   ┌────────────┐
         │ MySQL  │   │ Redis  │   │ manager-web│
         └────────┘   └────────┘   │   (Vue2)   │
                                   └────────────┘
```

---

## 3. 目标架构设计

### 3.1 五层架构

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Device Layer                                           │
│ ─────────────────────                                           │
│ ESP32 / 树莓派 / 其他 IoT 硬件                                   │
│ 职责：音频采集、播放、硬件控制                                    │
└────────────────────────────────┬────────────────────────────────┘
                                 │ WebSocket (二进制音频 + JSON控制)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Infrastructure Layer (Rust + Axum) ⭐ 网络入口          │
│ ─────────────────────────────────────────                       │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│ │  WebSocket  │ │  Config API │ │   EloqKV    │ │   Device   │ │
│ │   Server    │ │  (RESTful)  │ │   Storage   │ │   Manager  │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│ 职责：                                                           │
│   • 接收所有网络连接（WebSocket、HTTP）                          │
│   • 管理设备连接生命周期、心跳检测                                │
│   • 提供 RESTful API（用户认证、设备管理、配置管理）             │
│   • 数据持久化（EloqKV 存储）                                    │
│   • 通过 PyO3 调用 Python AI 逻辑层                              │
└────────────────────────────────┬────────────────────────────────┘
                                 │ PyO3 / FFI 调用
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: AI Logic Layer (Python) ⭐ 核心业务逻辑                  │
│ ─────────────────────────────────────                           │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│ │  Provider   │ │   Plugin    │ │  Dialogue   │ │   Memory   │ │
│ │   System    │ │  Framework  │ │   Manager   │ │   System   │ │
│ │ ASR/TTS/LLM │ │ (工具调用)  │ │ (对话编排)  │ │ (上下文)   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│ 职责：                                                           │
│   • AI 服务调度（ASR 识别、LLM 推理、TTS 合成）                  │
│   • 对话状态管理、多轮对话上下文                                  │
│   • 插件/Function Calling 执行                                   │
│   • 记忆系统（短期/长期记忆）                                    │
│   • ⚠️ 不处理网络连接，只接收处理请求，返回结果                  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ ctypes / FFI 调用
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: Performance Layer (Mojo)                               │
│ ─────────────────────────────────                               │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│ │    Opus     │ │     PCM     │ │     VAD     │ │    SIMD    │ │
│ │  Codec      │ │   Convert   │ │   Feature   │ │   Accel    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│ 职责：音频编解码、特征提取、SIMD 加速（10-100x 性能提升）        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: Application Layer (用户扩展区)                          │
│ ─────────────────────────────────────                           │
│ 自定义 Providers / Plugins / Handlers                           │
│ 职责：用户自定义逻辑、特定场景适配、第三方集成                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 0: Frontend Layer (Svelte + SvelteKit)                    │
│ ─────────────────────────────────────────────                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│ │   Admin     │ │  Component  │ │   Theme     │                │
│ │   Console   │ │   Library   │ │   System    │                │
│ └─────────────┘ └─────────────┘ └─────────────┘                │
│ 职责：管理界面、可视化配置、监控面板                              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心调用流程

```
                    ESP32 设备发送音频
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Rust WebSocket Server                            │
│  1. 接收 WebSocket 连接                                           │
│  2. 接收 Opus 音频数据                                            │
│  3. 调用 Mojo 解码音频                                            │
│  4. 通过 PyO3 调用 Python AI 逻辑                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │ PyO3
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Python AI Logic Layer                            │
│  5. VAD 检测（是否有语音）                                        │
│  6. ASR 识别（语音转文字）                                        │
│  7. LLM 推理（生成回复）                                          │
│  8. TTS 合成（文字转语音）                                        │
│  9. 返回结果给 Rust                                               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Rust WebSocket Server                            │
│  10. 调用 Mojo 编码音频                                           │
│  11. 通过 WebSocket 发送给 ESP32                                  │
│  12. 上报聊天记录到 EloqKV                                        │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 各层职责清单

| 层级 | 技术栈 | 职责 | 锁定/开放 |
|------|--------|------|-----------|
| Layer 5 | ESP32/C | 硬件交互、音频采集播放 | 开放（用户定制固件） |
| **Layer 1** | **Rust/Axum** | **所有网络通信（WebSocket、HTTP）、存储、设备管理** | **锁定**（框架核心） |
| **Layer 3** | **Python** | **AI 逻辑（ASR/TTS/LLM 调度、对话管理、插件执行）** | **锁定**（框架核心） |
| Layer 2 | Mojo | 性能加速（音频编解码、VAD 特征） | **锁定**（框架核心） |
| Layer 4 | Python | 用户扩展（自定义 Provider、Plugin） | **开放**（用户自由扩展） |
| Layer 0 | Svelte | 前端界面 | 半开放（可主题定制） |

### 3.4 关键职责边界

```
┌─────────────────────────────────────────────────────────────────┐
│                        职责边界说明                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Rust 负责（基础设施层）：                                    │
│     • WebSocket 服务器（设备连接、心跳、断线重连）               │
│     • HTTP RESTful API（用户认证、设备管理、配置管理）           │
│     • 数据存储（EloqKV 读写）                                    │
│     • 设备管理（注册、绑定、OTA）                                │
│     • 通过 PyO3 嵌入 Python 解释器                               │
│     • 调用 Mojo 进行音频编解码                                   │
│                                                                  │
│  ✅ Python 负责（AI 逻辑层）：                                   │
│     • Provider 调度（ASR、TTS、LLM、VAD、Memory）                │
│     • 对话状态管理（历史记录、上下文）                           │
│     • 插件执行（Function Calling）                               │
│     • AI 模型调用（本地模型 / 云端 API）                         │
│     • ⚠️ 不处理任何网络连接                                     │
│     • ⚠️ 只接收 Rust 传来的请求，返回处理结果                   │
│                                                                  │
│  ✅ Mojo 负责（性能层）：                                        │
│     • Opus 编解码（FFI 调用 libopus）                            │
│     • PCM 格式转换（SIMD 加速）                                  │
│     • VAD 特征提取（MFCC、能量计算）                             │
│     • 数值计算加速（10-100x 性能提升）                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 重构优先级与依赖关系

### 4.1 重构顺序决策树

```
                    ┌──────────────────────┐
                    │  开始重构             │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Phase 0: 基础设施    │
                    │  - 开发环境搭建       │
                    │  - CI/CD 配置         │
                    │  - 监控告警           │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Phase 1: 存储层     │  ← 最底层，所有模块依赖
                    │  - EloqKV 评估部署   │
                    │  - 数据模型设计      │
                    │  - 迁移脚本          │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Phase 2: Rust   │  │ Phase 3: Mojo   │  │ Phase 4: Svelte │
│ (Java→Rust)     │  │ (Python优化)    │  │ (Vue→Svelte)    │
│                 │  │                 │  │                 │
│ 依赖：Phase 1   │  │ 依赖：无        │  │ 依赖：Phase 2   │
│ 阻塞：Phase 4   │  │ 阻塞：无        │  │ 阻塞：无        │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Phase 5: API 统一  │
                    │  - OpenAPI 规范     │
                    │  - 接口文档         │
                    │  - SDK 生成         │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Phase 6: 集成测试  │
                    │  - 端到端测试       │
                    │  - 灰度发布         │
                    │  - 全量上线         │
                    └────────────────────┘
```

### 4.2 优先级矩阵

| Phase | 任务 | 优先级 | 依赖 | 预计时长 | 并行可行性 |
|-------|------|--------|------|----------|------------|
| 0 | 基础设施准备 | P0 | 无 | 3-5 天 | - |
| 1 | EloqKV 存储层 | P0 | Phase 0 | 1-2 周 | - |
| 2 | Java→Rust | P1 | Phase 1 | 4-5 周 | 可与 Phase 3 并行 |
| 3 | Python+Mojo | P1 | 无 | 4-6 周 | 可与 Phase 2 并行 |
| 4 | Vue→Svelte | P2 | Phase 2 | 3-4 周 | 需等 Phase 2 API |
| 5 | API 统一 | P1 | Phase 2,3 | 1-2 周 | - |
| 6 | 集成测试 | P0 | 全部 | 2-3 周 | - |

### 4.3 关键路径

```
Phase 0 → Phase 1 → Phase 2 → Phase 4 → Phase 5 → Phase 6
   │                                         ↑
   └──────────────→ Phase 3 ─────────────────┘

关键路径总时长：12-17 周
考虑 Phase 2 & 3 并行后：10-14 周
```

---

## 5. Phase 0: 基础设施准备

### 5.1 检查清单

- [ ] **开发环境搭建**
  - [ ] Rust 工具链安装 (rustup, cargo)
  - [ ] Mojo SDK 安装
  - [ ] Node.js 20+ 安装
  - [ ] Docker & Docker Compose

- [ ] **代码仓库准备**
  - [ ] 创建 monorepo 结构或多仓库
  - [ ] 配置 Git hooks (pre-commit, husky)
  - [ ] 设置分支保护规则

- [ ] **CI/CD 配置**
  - [ ] GitHub Actions / GitLab CI
  - [ ] 自动化测试流水线
  - [ ] 自动化部署流水线

- [ ] **监控告警**
  - [ ] Prometheus + Grafana 部署
  - [ ] 日志收集 (Loki / ELK)
  - [ ] 告警规则配置

### 5.2 目录结构规划

```
orica-framework/
├── crates/                    # Rust 工作空间
│   ├── orica-core/           # 核心库
│   ├── orica-server/         # WebSocket 服务器
│   ├── orica-api/            # RESTful API (Axum)
│   └── orica-storage/        # EloqKV 存储抽象
│
├── python/                    # Python 包
│   ├── orica/                # 主包
│   │   ├── providers/        # Provider 实现
│   │   ├── plugins/          # 插件框架
│   │   └── handlers/         # 消息处理器
│   └── tests/
│
├── mojo/                      # Mojo 性能模块
│   ├── audio/                # 音频处理
│   ├── vad/                  # VAD 特征提取
│   └── simd/                 # SIMD 加速
│
├── web/                       # Svelte 前端
│   ├── src/
│   │   ├── lib/              # 组件库
│   │   ├── routes/           # 页面路由
│   │   └── stores/           # 状态管理
│   └── static/
│
├── docs/                      # 文档
├── scripts/                   # 脚本工具
└── docker/                    # Docker 配置
```

### 5.3 验收标准

| 项目 | 验收条件 |
|------|----------|
| Rust 环境 | `cargo build` 成功 |
| Mojo 环境 | `mojo run hello.mojo` 成功 |
| Node 环境 | `npm create svelte@latest` 成功 |
| CI/CD | 推送代码自动触发构建 |
| 监控 | Grafana 能显示基础指标 |

---

## 6. Phase 1: 存储层迁移 (EloqKV)

### 6.1 EloqKV 简介

EloqKV 是一个统一的键值存储系统，支持：
- 多种数据结构（String, Hash, List, Set, SortedSet）
- 持久化存储
- 主从复制
- 事务支持

### 6.2 数据模型映射

#### 6.2.1 MySQL → EloqKV 映射

| MySQL 表 | EloqKV Key 模式 | 数据结构 | 说明 |
|----------|-----------------|----------|------|
| `sys_user` | `user:{id}` | Hash | 用户基础信息 |
| `sys_role` | `role:{id}` | Hash | 角色信息 |
| `agent_config` | `agent:{id}` | Hash | Agent 配置 |
| `device_info` | `device:{mac}` | Hash | 设备信息 |
| `chat_history` | `chat:{device}:{date}` | List | 聊天记录（按天分片） |
| `model_config` | `model:{type}:{name}` | Hash | 模型配置 |

#### 6.2.2 Redis → EloqKV 映射

| Redis Key | EloqKV Key | 数据结构 | 说明 |
|-----------|------------|----------|------|
| `session:{token}` | `session:{token}` | Hash | 会话信息 |
| `cache:config` | `cache:config` | String | 配置缓存 |
| `online:devices` | `online:devices` | Set | 在线设备集合 |

### 6.3 迁移步骤

#### Step 1: EloqKV 部署与评估 (1-2 天)

```bash
# 部署 EloqKV
docker run -d --name eloqkv \
  -p 6379:6379 \
  -v eloqkv-data:/data \
  eloqkv/eloqkv:latest

# 验证连接
redis-cli -h localhost -p 6379 ping
```

**评估检查清单：**
- [ ] 读写性能基准测试
- [ ] 数据持久化验证
- [ ] 内存占用观察
- [ ] 集群模式测试（如需要）

#### Step 2: 数据模型设计 (2-3 天)

```rust
// Rust 数据模型定义
pub mod schema {
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize)]
    pub struct User {
        pub id: u64,
        pub username: String,
        pub password_hash: String,
        pub email: Option<String>,
        pub created_at: i64,
        pub updated_at: i64,
    }

    #[derive(Serialize, Deserialize)]
    pub struct Device {
        pub mac: String,
        pub name: String,
        pub agent_id: Option<u64>,
        pub last_seen: i64,
        pub firmware_version: String,
    }

    #[derive(Serialize, Deserialize)]
    pub struct AgentConfig {
        pub id: u64,
        pub name: String,
        pub asr_config: serde_json::Value,
        pub tts_config: serde_json::Value,
        pub llm_config: serde_json::Value,
    }
}
```

#### Step 3: 存储抽象层实现 (3-4 天)

```rust
// orica-storage/src/lib.rs
use async_trait::async_trait;
use redis::AsyncCommands;

#[async_trait]
pub trait Storage: Send + Sync {
    async fn get_user(&self, id: u64) -> Result<Option<User>>;
    async fn set_user(&self, user: &User) -> Result<()>;
    async fn get_device(&self, mac: &str) -> Result<Option<Device>>;
    async fn set_device(&self, device: &Device) -> Result<()>;
    async fn get_agent(&self, id: u64) -> Result<Option<AgentConfig>>;
    async fn set_agent(&self, agent: &AgentConfig) -> Result<()>;
    // ... 更多方法
}

pub struct EloqKVStorage {
    client: redis::Client,
}

#[async_trait]
impl Storage for EloqKVStorage {
    async fn get_user(&self, id: u64) -> Result<Option<User>> {
        let mut conn = self.client.get_async_connection().await?;
        let data: Option<String> = conn.hgetall(format!("user:{}", id)).await?;
        // 反序列化处理
    }
    // ... 实现其他方法
}
```

#### Step 4: 数据迁移脚本 (2-3 天)

```python
# scripts/migrate_to_eloqkv.py
import mysql.connector
import redis
import json
from tqdm import tqdm

def migrate_users():
    """迁移用户数据"""
    mysql_conn = mysql.connector.connect(...)
    eloqkv = redis.Redis(...)

    cursor = mysql_conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sys_user")

    for row in tqdm(cursor.fetchall(), desc="Migrating users"):
        key = f"user:{row['id']}"
        eloqkv.hset(key, mapping={
            'id': row['id'],
            'username': row['username'],
            'password_hash': row['password'],
            'email': row['email'] or '',
            'created_at': int(row['created_at'].timestamp()),
            'updated_at': int(row['updated_at'].timestamp()),
        })

    print(f"Migrated {cursor.rowcount} users")

def migrate_devices():
    """迁移设备数据"""
    # 类似实现...

def migrate_agents():
    """迁移 Agent 配置"""
    # 类似实现...

def migrate_chat_history():
    """迁移聊天记录（增量方式）"""
    # 按天分片迁移...

if __name__ == "__main__":
    migrate_users()
    migrate_devices()
    migrate_agents()
    migrate_chat_history()
    print("Migration completed!")
```

### 6.4 验收标准

| 检查项 | 验收条件 |
|--------|----------|
| EloqKV 部署 | 服务稳定运行 24 小时无异常 |
| 数据迁移 | 100% 数据完整性校验通过 |
| 读写性能 | 单次读写 < 1ms |
| 存储抽象 | 所有接口单元测试通过 |

---

## 7. Phase 2: Java + Python网络层 → Rust (Axum) 迁移

> **重要**：此阶段不仅迁移 Java manager-api，还包括将 Python xiaozhi-server 中的网络通信层（WebSocket、HTTP）迁移到 Rust。

### 7.1 模块迁移清单

按优先级排序：

| 优先级 | 来源 | Rust 模块 | 复杂度 | 依赖 | 说明 |
|--------|------|-----------|--------|------|------|
| **1** | **Python** | **orica-websocket** | ⭐⭐⭐⭐ | EloqKV, PyO3 | **WebSocket 服务器（从 Python 迁移）** |
| **2** | **Python** | **orica-pyo3-bridge** | ⭐⭐⭐ | - | **PyO3 Python 调用桥接** |
| 3 | Java | orica-auth | ⭐⭐⭐ | EloqKV | 认证模块 |
| 4 | Java | orica-device | ⭐⭐ | orica-auth | 设备管理 |
| 5 | Java | orica-agent | ⭐⭐ | orica-auth | Agent 配置 |
| 6 | Java | orica-model | ⭐⭐ | orica-auth | 模型配置 |
| 7 | Java | orica-user | ⭐⭐ | orica-auth | 用户管理 |
| 8 | Java | orica-chat | ⭐⭐⭐ | orica-auth | 聊天记录 |
| 9 | Java | orica-stats | ⭐⭐⭐⭐ | orica-chat | 统计分析 |

### 7.2 Rust 统一服务器架构

```rust
// orica-server/src/main.rs
use axum::{Router, routing::{get, post, put, delete}};
use axum::extract::ws::WebSocketUpgrade;
use tower_http::cors::CorsLayer;
use pyo3::prelude::*;

mod handlers;
mod middleware;
mod websocket;
mod python_bridge;
mod error;

#[tokio::main]
async fn main() {
    // 初始化日志
    tracing_subscriber::init();

    // 初始化 Python 解释器（PyO3）
    pyo3::prepare_freethreaded_python();

    // 初始化存储
    let storage = EloqKVStorage::new("redis://localhost:6379").await;

    // 初始化 Python AI 引擎
    let ai_engine = python_bridge::AIEngine::new().expect("Failed to init Python AI engine");

    // 构建路由
    let app = Router::new()
        // ===============================
        // WebSocket 路由（设备连接）
        // ===============================
        .route("/xiaozhi/v1/", get(websocket::handler))

        // ===============================
        // RESTful API 路由
        // ===============================
        // 认证路由
        .route("/api/auth/login", post(handlers::auth::login))
        .route("/api/auth/logout", post(handlers::auth::logout))
        .route("/api/auth/refresh", post(handlers::auth::refresh))

        // 设备路由
        .route("/api/devices", get(handlers::device::list))
        .route("/api/devices/:mac", get(handlers::device::get))
        .route("/api/devices/:mac", put(handlers::device::update))

        // Agent 路由
        .route("/api/agents", get(handlers::agent::list))
        .route("/api/agents", post(handlers::agent::create))
        .route("/api/agents/:id", get(handlers::agent::get))
        .route("/api/agents/:id", put(handlers::agent::update))
        .route("/api/agents/:id", delete(handlers::agent::delete))

        // 模型路由
        .route("/api/models", get(handlers::model::list))
        .route("/api/models/:type/:name", get(handlers::model::get))

        // 用户路由
        .route("/api/users", get(handlers::user::list))
        .route("/api/users/:id", get(handlers::user::get))

        // 统计路由
        .route("/api/stats/overview", get(handlers::stats::overview))
        .route("/api/stats/usage", get(handlers::stats::usage))

        // 中间件
        .layer(middleware::auth_layer())
        .layer(CorsLayer::permissive())

        // 共享状态
        .with_state(AppState { storage, ai_engine });

    // 启动统一服务器（WebSocket + HTTP）
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8000").await.unwrap();
    println!("ORica Server running on http://0.0.0.0:8000");
    println!("  WebSocket: ws://0.0.0.0:8000/xiaozhi/v1/");
    println!("  REST API:  http://0.0.0.0:8000/api/");
    axum::serve(listener, app).await.unwrap();
}
```

### 7.3 WebSocket 服务器实现（关键模块）

```rust
// orica-server/src/websocket/handler.rs
use axum::{
    extract::{ws::{Message, WebSocket, WebSocketUpgrade}, State},
    response::IntoResponse,
};
use futures::{SinkExt, StreamExt};
use tokio::sync::mpsc;

/// WebSocket 连接处理器
pub async fn handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(|socket| handle_connection(socket, state))
}

/// 处理单个 WebSocket 连接
async fn handle_connection(socket: WebSocket, state: AppState) {
    let (mut sender, mut receiver) = socket.split();
    let (tx, mut rx) = mpsc::channel::<Message>(32);

    // 会话 ID
    let session_id = uuid::Uuid::new_v4().to_string();

    // 发送任务
    let send_task = tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            if sender.send(msg).await.is_err() {
                break;
            }
        }
    });

    // 接收任务
    let recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Binary(data) => {
                    // 音频数据 - 调用 Python AI 逻辑处理
                    let result = process_audio(&state, &session_id, &data).await;
                    if let Some(response) = result {
                        let _ = tx.send(response).await;
                    }
                }
                Message::Text(text) => {
                    // JSON 控制消息
                    let result = process_control(&state, &session_id, &text).await;
                    if let Some(response) = result {
                        let _ = tx.send(response).await;
                    }
                }
                Message::Close(_) => break,
                _ => {}
            }
        }
    });

    // 等待任务完成
    tokio::select! {
        _ = send_task => {},
        _ = recv_task => {},
    }
}

/// 处理音频数据 - 调用 Python AI 逻辑
async fn process_audio(
    state: &AppState,
    session_id: &str,
    audio_data: &[u8],
) -> Option<Message> {
    // 1. 调用 Mojo 解码 Opus 音频
    let pcm_data = mojo_bridge::decode_opus(audio_data);

    // 2. 通过 PyO3 调用 Python AI 逻辑
    let result = Python::with_gil(|py| {
        let ai_engine = state.ai_engine.as_ref(py);
        ai_engine.call_method1("process_audio", (session_id, &pcm_data[..]))
    });

    match result {
        Ok(response) => {
            // 3. 如果有 TTS 音频响应，编码并返回
            if let Some(tts_audio) = response.get("audio") {
                let opus_data = mojo_bridge::encode_opus(tts_audio);
                Some(Message::Binary(opus_data))
            } else {
                None
            }
        }
        Err(e) => {
            tracing::error!("Python AI error: {}", e);
            None
        }
    }
}
```

### 7.4 PyO3 Python 桥接模块

```rust
// orica-server/src/python_bridge/mod.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyBytes};

/// Python AI 引擎封装
pub struct AIEngine {
    module: Py<PyModule>,
}

impl AIEngine {
    /// 初始化 Python AI 引擎
    pub fn new() -> PyResult<Self> {
        Python::with_gil(|py| {
            // 导入 Python AI 模块
            let module = PyModule::import(py, "orica.ai_engine")?;
            Ok(Self {
                module: module.into(),
            })
        })
    }

    /// 处理音频数据
    pub fn process_audio(
        &self,
        py: Python,
        session_id: &str,
        audio_data: &[u8],
    ) -> PyResult<Py<PyDict>> {
        let module = self.module.as_ref(py);
        let result = module.call_method1(
            "process_audio",
            (session_id, PyBytes::new(py, audio_data)),
        )?;
        Ok(result.extract()?)
    }

    /// 处理文本消息（意图识别）
    pub fn process_text(
        &self,
        py: Python,
        session_id: &str,
        text: &str,
    ) -> PyResult<Py<PyDict>> {
        let module = self.module.as_ref(py);
        let result = module.call_method1(
            "process_text",
            (session_id, text),
        )?;
        Ok(result.extract()?)
    }

    /// 设置会话配置
    pub fn set_config(
        &self,
        py: Python,
        session_id: &str,
        config: &str,  // JSON 字符串
    ) -> PyResult<()> {
        let module = self.module.as_ref(py);
        module.call_method1("set_config", (session_id, config))?;
        Ok(())
    }

    /// 清理会话
    pub fn cleanup_session(
        &self,
        py: Python,
        session_id: &str,
    ) -> PyResult<()> {
        let module = self.module.as_ref(py);
        module.call_method1("cleanup_session", (session_id,))?;
        Ok(())
    }
}
```

### 7.5 核心模块实现

#### 7.5.1 认证模块 (JWT 替代 Shiro)

```rust
// orica-api/src/handlers/auth.rs
use axum::{Json, extract::State};
use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize)]
pub struct LoginResponse {
    token: String,
    expires_in: i64,
    user: UserInfo,
}

#[derive(Serialize, Deserialize)]
pub struct Claims {
    sub: u64,           // user_id
    username: String,
    roles: Vec<String>,
    exp: i64,           // expiration
}

pub async fn login(
    State(state): State<AppState>,
    Json(req): Json<LoginRequest>,
) -> Result<Json<LoginResponse>, ApiError> {
    // 1. 查询用户
    let user = state.storage.get_user_by_username(&req.username).await?
        .ok_or(ApiError::Unauthorized("用户不存在"))?;

    // 2. 验证密码
    if !verify_password(&req.password, &user.password_hash) {
        return Err(ApiError::Unauthorized("密码错误"));
    }

    // 3. 生成 JWT
    let claims = Claims {
        sub: user.id,
        username: user.username.clone(),
        roles: user.roles.clone(),
        exp: chrono::Utc::now().timestamp() + 86400, // 24 小时
    };

    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(JWT_SECRET.as_bytes()),
    )?;

    Ok(Json(LoginResponse {
        token,
        expires_in: 86400,
        user: user.into(),
    }))
}
```

#### 7.3.2 设备管理模块

```rust
// orica-api/src/handlers/device.rs
use axum::{Json, extract::{State, Path, Query}};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct DeviceQuery {
    page: Option<u32>,
    page_size: Option<u32>,
    status: Option<String>,
}

#[derive(Serialize)]
pub struct DeviceListResponse {
    total: u64,
    items: Vec<DeviceInfo>,
}

pub async fn list(
    State(state): State<AppState>,
    Query(query): Query<DeviceQuery>,
) -> Result<Json<DeviceListResponse>, ApiError> {
    let page = query.page.unwrap_or(1);
    let page_size = query.page_size.unwrap_or(20);

    let (total, devices) = state.storage
        .list_devices(page, page_size, query.status.as_deref())
        .await?;

    Ok(Json(DeviceListResponse {
        total,
        items: devices.into_iter().map(Into::into).collect(),
    }))
}

pub async fn get(
    State(state): State<AppState>,
    Path(mac): Path<String>,
) -> Result<Json<DeviceInfo>, ApiError> {
    let device = state.storage.get_device(&mac).await?
        .ok_or(ApiError::NotFound("设备不存在"))?;

    Ok(Json(device.into()))
}

pub async fn update(
    State(state): State<AppState>,
    Path(mac): Path<String>,
    Json(req): Json<UpdateDeviceRequest>,
) -> Result<Json<DeviceInfo>, ApiError> {
    let mut device = state.storage.get_device(&mac).await?
        .ok_or(ApiError::NotFound("设备不存在"))?;

    // 更新字段
    if let Some(name) = req.name {
        device.name = name;
    }
    if let Some(agent_id) = req.agent_id {
        device.agent_id = Some(agent_id);
    }

    state.storage.set_device(&device).await?;

    Ok(Json(device.into()))
}
```

### 7.4 API 对照表

| Java API | Rust API | 方法 | 说明 |
|----------|----------|------|------|
| `/sys/login` | `/api/auth/login` | POST | 用户登录 |
| `/sys/logout` | `/api/auth/logout` | POST | 用户登出 |
| `/device/list` | `/api/devices` | GET | 设备列表 |
| `/device/info/{mac}` | `/api/devices/:mac` | GET | 设备详情 |
| `/device/update` | `/api/devices/:mac` | PUT | 更新设备 |
| `/agent/list` | `/api/agents` | GET | Agent 列表 |
| `/agent/add` | `/api/agents` | POST | 创建 Agent |
| `/agent/info/{id}` | `/api/agents/:id` | GET | Agent 详情 |
| `/agent/update` | `/api/agents/:id` | PUT | 更新 Agent |
| `/agent/delete/{id}` | `/api/agents/:id` | DELETE | 删除 Agent |

### 7.5 迁移步骤

#### Step 1: 核心框架搭建 (3-4 天)

```bash
# 创建 Rust 工作空间
cargo new orica-api
cd orica-api

# 添加依赖
cargo add axum tokio serde serde_json
cargo add tower-http jsonwebtoken redis
cargo add tracing tracing-subscriber
```

**完成内容：**
- [ ] 项目结构搭建
- [ ] 错误处理框架
- [ ] 日志配置
- [ ] CORS 配置
- [ ] 健康检查端点

#### Step 2: 认证模块 (2-3 天)

- [ ] JWT 生成与验证
- [ ] 登录/登出接口
- [ ] Token 刷新
- [ ] 权限中间件

#### Step 3: 业务模块迁移 (5-7 天)

按优先级逐个迁移：
- [ ] 设备管理
- [ ] Agent 配置
- [ ] 模型配置
- [ ] 用户管理
- [ ] 聊天记录
- [ ] 统计分析

#### Step 4: 双写验证 (3-4 天)

```python
# 双写阶段：同时写入 Java 和 Rust
# 读取对比验证数据一致性

def dual_write_middleware(request):
    # 写入 Java
    java_response = forward_to_java(request)

    # 写入 Rust
    rust_response = forward_to_rust(request)

    # 验证一致性
    if java_response != rust_response:
        log_inconsistency(java_response, rust_response)

    return java_response  # 过渡期返回 Java 结果
```

#### Step 5: 流量切换 (3-5 天)

```nginx
# Nginx 灰度配置
upstream java_backend {
    server 127.0.0.1:8002;
}

upstream rust_backend {
    server 127.0.0.1:8003;
}

split_clients "${remote_addr}${uri}" $backend {
    10%  rust_backend;   # 10% 流量到 Rust
    *    java_backend;   # 90% 流量到 Java
}

server {
    location /api/ {
        proxy_pass http://$backend;
    }
}
```

### 7.6 验收标准

| 检查项 | 验收条件 |
|--------|----------|
| API 兼容性 | 100% API 接口行为一致 |
| 性能 | 响应时间 < 10ms (p99) |
| 启动时间 | < 1 秒 |
| 内存占用 | < 50MB |
| 单元测试 | 覆盖率 > 80% |

---

## 8. Phase 3: Python 性能优化 (Mojo + Rust)

### 8.1 性能瓶颈分析

| 模块 | 当前性能 | 目标性能 | 优化手段 |
|------|----------|----------|----------|
| Opus 编解码 | 200-500μs | 20-50μs | Mojo FFI |
| PCM 转换 | 100-200μs | 10-20μs | Mojo SIMD |
| VAD 特征提取 | 300-500μs | 30-50μs | Mojo 向量化 |
| NumPy 操作 | 50-100μs | 5-10μs | Mojo 原生 |

### 8.2 Mojo 模块设计

#### 8.2.1 音频处理模块

```mojo
# mojo/audio/opus_codec.mojo
from python import Python
from memory import memcpy
from sys.ffi import external_call

struct OpusEncoder:
    var encoder_ptr: Pointer[Int8]
    var sample_rate: Int
    var channels: Int

    fn __init__(inout self, sample_rate: Int, channels: Int):
        self.sample_rate = sample_rate
        self.channels = channels
        # 调用 libopus 初始化
        self.encoder_ptr = external_call[
            "opus_encoder_create",
            Pointer[Int8]
        ](sample_rate, channels, 2048)  # OPUS_APPLICATION_AUDIO

    fn encode(self, pcm: Tensor[DType.int16]) -> Tensor[DType.uint8]:
        """编码 PCM 数据为 Opus"""
        let max_packet = 4000
        var output = Tensor[DType.uint8](max_packet)

        let encoded_bytes = external_call[
            "opus_encode",
            Int32
        ](
            self.encoder_ptr,
            pcm.data(),
            pcm.dim(0) // self.channels,
            output.data(),
            max_packet
        )

        return output[:encoded_bytes]


struct OpusDecoder:
    var decoder_ptr: Pointer[Int8]
    var sample_rate: Int
    var channels: Int

    fn __init__(inout self, sample_rate: Int, channels: Int):
        self.sample_rate = sample_rate
        self.channels = channels
        self.decoder_ptr = external_call[
            "opus_decoder_create",
            Pointer[Int8]
        ](sample_rate, channels)

    fn decode(self, opus_data: Tensor[DType.uint8]) -> Tensor[DType.int16]:
        """解码 Opus 数据为 PCM"""
        let frame_size = 960 * self.channels  # 20ms at 48kHz
        var output = Tensor[DType.int16](frame_size)

        let decoded_samples = external_call[
            "opus_decode",
            Int32
        ](
            self.decoder_ptr,
            opus_data.data(),
            opus_data.dim(0),
            output.data(),
            frame_size // self.channels,
            0  # no FEC
        )

        return output[:decoded_samples * self.channels]
```

#### 8.2.2 SIMD 加速模块

```mojo
# mojo/simd/audio_simd.mojo
from algorithm import vectorize
from sys.info import simdwidthof

alias simd_width = simdwidthof[DType.float32]()

fn pcm_to_float_simd(pcm: Tensor[DType.int16]) -> Tensor[DType.float32]:
    """PCM int16 转 float32，SIMD 加速"""
    let n = pcm.dim(0)
    var output = Tensor[DType.float32](n)

    @parameter
    fn convert[width: Int](i: Int):
        let pcm_vec = pcm.load[width](i).cast[DType.float32]()
        let normalized = pcm_vec / 32768.0
        output.store[width](i, normalized)

    vectorize[convert, simd_width](n)
    return output


fn float_to_pcm_simd(audio: Tensor[DType.float32]) -> Tensor[DType.int16]:
    """float32 转 PCM int16，SIMD 加速"""
    let n = audio.dim(0)
    var output = Tensor[DType.int16](n)

    @parameter
    fn convert[width: Int](i: Int):
        let float_vec = audio.load[width](i)
        let scaled = (float_vec * 32767.0).cast[DType.int16]()
        output.store[width](i, scaled)

    vectorize[convert, simd_width](n)
    return output


fn compute_rms_simd(audio: Tensor[DType.float32]) -> Float32:
    """计算 RMS 能量，SIMD 加速"""
    let n = audio.dim(0)
    var sum_squares: Float32 = 0.0

    @parameter
    fn accumulate[width: Int](i: Int):
        let vec = audio.load[width](i)
        sum_squares += (vec * vec).reduce_add()

    vectorize[accumulate, simd_width](n)
    return math.sqrt(sum_squares / n)
```

#### 8.2.3 VAD 特征提取

```mojo
# mojo/vad/features.mojo
from algorithm import vectorize, parallelize
from math import exp, log

fn extract_mfcc_features(
    audio: Tensor[DType.float32],
    sample_rate: Int = 16000,
    n_mfcc: Int = 13,
    frame_length: Int = 400,  # 25ms
    frame_shift: Int = 160,   # 10ms
) -> Tensor[DType.float32]:
    """提取 MFCC 特征，用于 VAD"""
    let n_frames = (audio.dim(0) - frame_length) // frame_shift + 1
    var features = Tensor[DType.float32](n_frames, n_mfcc)

    @parameter
    fn process_frame(frame_idx: Int):
        let start = frame_idx * frame_shift
        let frame = audio[start:start + frame_length]

        # 1. 预加重
        let preemphasized = preemphasis(frame, 0.97)

        # 2. 加窗
        let windowed = apply_hamming_window(preemphasized)

        # 3. FFT
        let spectrum = fft_magnitude(windowed)

        # 4. Mel 滤波器组
        let mel_spectrum = apply_mel_filterbank(spectrum, sample_rate)

        # 5. 对数
        let log_mel = log_safe(mel_spectrum)

        # 6. DCT
        let mfcc = dct(log_mel)[:n_mfcc]

        features[frame_idx] = mfcc

    parallelize[process_frame](n_frames)
    return features
```

### 8.3 Python 集成

```python
# python/orica/audio/mojo_bridge.py
import ctypes
from pathlib import Path

# 加载 Mojo 编译的 .so 文件
_lib_path = Path(__file__).parent / "libmojo_audio.so"
_lib = ctypes.CDLL(str(_lib_path))

# 定义接口
_lib.opus_encode_batch.argtypes = [
    ctypes.c_void_p,  # pcm_data
    ctypes.c_int,     # num_samples
    ctypes.c_void_p,  # output_buffer
    ctypes.c_int,     # max_output_size
]
_lib.opus_encode_batch.restype = ctypes.c_int

def encode_opus_fast(pcm_data: np.ndarray) -> bytes:
    """使用 Mojo 加速的 Opus 编码"""
    output_buffer = ctypes.create_string_buffer(4000)

    encoded_size = _lib.opus_encode_batch(
        pcm_data.ctypes.data,
        pcm_data.shape[0],
        output_buffer,
        4000,
    )

    return output_buffer.raw[:encoded_size]

def decode_opus_fast(opus_data: bytes) -> np.ndarray:
    """使用 Mojo 加速的 Opus 解码"""
    # 类似实现...

def extract_vad_features_fast(audio: np.ndarray) -> np.ndarray:
    """使用 Mojo 加速的 VAD 特征提取"""
    # 类似实现...
```

### 8.4 Python 职责边界

**Python 保留（AI 逻辑层）：**
- Provider 调度与编排
- 对话状态管理
- 插件执行
- LLM 调用
- 配置管理

**迁移到 Mojo（性能层）：**
- Opus 编解码
- PCM 格式转换
- VAD 特征提取
- 音频重采样
- SIMD 向量运算

**迁移到 Rust（基础设施层）：**
- WebSocket 服务器
- HTTP API
- 存储操作
- 设备管理

### 8.5 迁移步骤

#### Step 1: Mojo 环境搭建 (1-2 天)

```bash
# 安装 Mojo SDK
curl -ssL https://get.modular.com | sh
modular auth
modular install mojo

# 验证安装
mojo --version
```

#### Step 2: 核心音频模块实现 (1-2 周)

- [ ] Opus 编解码器封装
- [ ] PCM/Float 转换（SIMD）
- [ ] 音频重采样
- [ ] 编译为 .so 文件

#### Step 3: VAD 特征提取实现 (1 周)

- [ ] MFCC 特征提取
- [ ] 能量计算
- [ ] 过零率计算
- [ ] 批量处理优化

#### Step 4: Python 集成与测试 (1 周)

- [ ] ctypes 接口封装
- [ ] 性能基准测试
- [ ] 与现有代码集成
- [ ] 回归测试

### 8.6 验收标准

| 检查项 | 验收条件 |
|--------|----------|
| Opus 编码 | 延迟 < 50μs (10x 提升) |
| PCM 转换 | 延迟 < 20μs (10x 提升) |
| VAD 特征 | 延迟 < 50μs (10x 提升) |
| 兼容性 | 与原有接口 100% 兼容 |
| 准确性 | 音频质量无损失 |

---

## 9. Phase 4: 前端重构 (Vue → Svelte)

### 9.1 技术选型

| 项目 | 选型 | 说明 |
|------|------|------|
| 框架 | SvelteKit | 全栈框架，支持 SSR |
| UI 库 | shadcn-svelte | 无头组件，高度可定制 |
| 样式 | Tailwind CSS | 原子化 CSS |
| 状态 | Svelte Store | 内置响应式状态 |
| 图表 | ECharts | 保持与现有一致 |
| 构建 | Vite | 极速 HMR |

### 9.2 目录结构

```
web/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn-svelte 基础组件
│   │   │   │   ├── button/
│   │   │   │   ├── card/
│   │   │   │   ├── dialog/
│   │   │   │   └── ...
│   │   │   ├── business/        # 业务组件
│   │   │   │   ├── DeviceList.svelte
│   │   │   │   ├── AgentConfig.svelte
│   │   │   │   └── ...
│   │   │   └── layout/          # 布局组件
│   │   │       ├── Sidebar.svelte
│   │   │       ├── Header.svelte
│   │   │       └── Footer.svelte
│   │   ├── stores/              # 状态管理
│   │   │   ├── auth.ts
│   │   │   ├── device.ts
│   │   │   └── agent.ts
│   │   ├── api/                 # API 调用
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   └── device.ts
│   │   └── utils/               # 工具函数
│   │
│   ├── routes/                  # 页面路由
│   │   ├── +layout.svelte
│   │   ├── +page.svelte         # 首页/仪表盘
│   │   ├── login/
│   │   │   └── +page.svelte
│   │   ├── devices/
│   │   │   ├── +page.svelte     # 设备列表
│   │   │   └── [mac]/
│   │   │       └── +page.svelte # 设备详情
│   │   ├── agents/
│   │   │   ├── +page.svelte     # Agent 列表
│   │   │   └── [id]/
│   │   │       └── +page.svelte # Agent 配置
│   │   ├── models/
│   │   │   └── +page.svelte     # 模型配置
│   │   ├── users/
│   │   │   └── +page.svelte     # 用户管理
│   │   └── settings/
│   │       └── +page.svelte     # 系统设置
│   │
│   ├── app.html
│   ├── app.css                  # 全局样式
│   └── hooks.server.ts          # 服务端钩子
│
├── static/
├── svelte.config.js
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

### 9.3 页面迁移对照表

| Vue 页面 | Svelte 路由 | 复杂度 | 优先级 |
|----------|-------------|--------|--------|
| Login.vue | /login | ⭐ | P0 |
| Dashboard.vue | / | ⭐⭐⭐ | P0 |
| DeviceList.vue | /devices | ⭐⭐ | P0 |
| DeviceDetail.vue | /devices/[mac] | ⭐⭐ | P1 |
| AgentList.vue | /agents | ⭐⭐ | P1 |
| AgentEdit.vue | /agents/[id] | ⭐⭐⭐ | P1 |
| ModelConfig.vue | /models | ⭐⭐ | P2 |
| UserManage.vue | /users | ⭐⭐ | P2 |
| Settings.vue | /settings | ⭐⭐ | P2 |

### 9.4 核心组件示例

#### 9.4.1 设备列表页面

```svelte
<!-- src/routes/devices/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { devices, fetchDevices } from '$lib/stores/device';
  import { DataTable } from '$lib/components/ui/data-table';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Search, RefreshCw } from 'lucide-svelte';

  let searchQuery = '';
  let loading = false;

  onMount(() => {
    fetchDevices();
  });

  $: filteredDevices = $devices.filter(d =>
    d.name.includes(searchQuery) || d.mac.includes(searchQuery)
  );

  async function refresh() {
    loading = true;
    await fetchDevices();
    loading = false;
  }
</script>

<div class="container mx-auto py-6">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">设备管理</h1>
    <div class="flex gap-4">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="搜索设备..."
          bind:value={searchQuery}
          class="pl-10 pr-4 py-2 border rounded-md"
        />
      </div>
      <Button on:click={refresh} disabled={loading}>
        <RefreshCw class="h-4 w-4 mr-2" class:animate-spin={loading} />
        刷新
      </Button>
    </div>
  </div>

  <DataTable data={filteredDevices} columns={[
    { key: 'name', label: '设备名称' },
    { key: 'mac', label: 'MAC 地址' },
    {
      key: 'status',
      label: '状态',
      render: (value) => `<Badge variant="${value === 'online' ? 'success' : 'secondary'}">${value}</Badge>`
    },
    { key: 'agent', label: '绑定 Agent' },
    { key: 'lastSeen', label: '最后在线' },
    { key: 'actions', label: '操作' },
  ]} />
</div>
```

#### 9.4.2 状态管理

```typescript
// src/lib/stores/device.ts
import { writable, derived } from 'svelte/store';
import { api } from '$lib/api/client';

export interface Device {
  mac: string;
  name: string;
  status: 'online' | 'offline';
  agentId?: number;
  agentName?: string;
  lastSeen: string;
  firmwareVersion: string;
}

export const devices = writable<Device[]>([]);
export const selectedDevice = writable<Device | null>(null);

export const onlineDevices = derived(devices, $devices =>
  $devices.filter(d => d.status === 'online')
);

export async function fetchDevices() {
  const response = await api.get('/api/devices');
  devices.set(response.items);
}

export async function updateDevice(mac: string, data: Partial<Device>) {
  const response = await api.put(`/api/devices/${mac}`, data);
  devices.update(list =>
    list.map(d => d.mac === mac ? { ...d, ...response } : d)
  );
}

export async function bindAgent(mac: string, agentId: number) {
  await updateDevice(mac, { agentId });
}
```

### 9.5 迁移步骤

#### Step 1: 项目初始化 (1-2 天)

```bash
# 创建 SvelteKit 项目
npm create svelte@latest web
cd web

# 安装依赖
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 安装 shadcn-svelte
npx shadcn-svelte@latest init

# 安装其他依赖
npm install echarts lucide-svelte
```

#### Step 2: 基础框架搭建 (2-3 天)

- [ ] 布局组件（Sidebar, Header）
- [ ] 路由守卫
- [ ] API 客户端封装
- [ ] 主题配置

#### Step 3: 核心页面迁移 (1-2 周)

按优先级逐个迁移：
- [ ] 登录页面
- [ ] 仪表盘
- [ ] 设备管理
- [ ] Agent 配置
- [ ] 模型配置
- [ ] 用户管理
- [ ] 系统设置

#### Step 4: 组件库完善 (3-5 天)

- [ ] 表格组件（排序、分页、筛选）
- [ ] 表单组件（验证、联动）
- [ ] 图表组件（ECharts 封装）
- [ ] 通知组件（Toast、Alert）

#### Step 5: 测试与优化 (3-5 天)

- [ ] 功能测试
- [ ] 性能测试
- [ ] 响应式适配
- [ ] 浏览器兼容性

### 9.6 验收标准

| 检查项 | 验收条件 |
|--------|----------|
| 功能完整性 | 100% 功能与 Vue 版本一致 |
| 构建速度 | < 5 秒 |
| 首屏加载 | < 1 秒 |
| Lighthouse 评分 | > 90 |
| 浏览器兼容 | Chrome, Firefox, Safari, Edge |

---

## 10. Phase 5: API 统一与文档化

### 10.1 OpenAPI 规范

```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: ORica API
  version: 1.0.0
  description: ORica Framework RESTful API

servers:
  - url: http://localhost:8002
    description: Development server

paths:
  /api/auth/login:
    post:
      summary: 用户登录
      tags: [认证]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: 登录成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: 认证失败

  /api/devices:
    get:
      summary: 获取设备列表
      tags: [设备管理]
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
        - name: status
          in: query
          schema:
            type: string
            enum: [online, offline]
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeviceListResponse'

  /api/devices/{mac}:
    get:
      summary: 获取设备详情
      tags: [设备管理]
      security:
        - bearerAuth: []
      parameters:
        - name: mac
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Device'
        '404':
          description: 设备不存在

    put:
      summary: 更新设备信息
      tags: [设备管理]
      security:
        - bearerAuth: []
      parameters:
        - name: mac
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateDeviceRequest'
      responses:
        '200':
          description: 成功

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    LoginRequest:
      type: object
      required: [username, password]
      properties:
        username:
          type: string
        password:
          type: string

    LoginResponse:
      type: object
      properties:
        token:
          type: string
        expires_in:
          type: integer
        user:
          $ref: '#/components/schemas/UserInfo'

    Device:
      type: object
      properties:
        mac:
          type: string
        name:
          type: string
        status:
          type: string
          enum: [online, offline]
        agentId:
          type: integer
          nullable: true
        lastSeen:
          type: string
          format: date-time
        firmwareVersion:
          type: string

    DeviceListResponse:
      type: object
      properties:
        total:
          type: integer
        items:
          type: array
          items:
            $ref: '#/components/schemas/Device'
```

### 10.2 WebSocket 协议规范

```typescript
// WebSocket 消息类型定义
interface WebSocketMessage {
  type: MessageType;
  payload: unknown;
  timestamp: number;
  session_id?: string;
}

enum MessageType {
  // 控制消息
  HELLO = 'hello',           // 握手
  HELLO_ACK = 'hello_ack',   // 握手响应
  GOODBYE = 'goodbye',       // 断开连接
  HEARTBEAT = 'heartbeat',   // 心跳

  // 音频消息
  AUDIO_START = 'audio_start',   // 开始录音
  AUDIO_DATA = 'audio_data',     // 音频数据（二进制）
  AUDIO_END = 'audio_end',       // 结束录音

  // 对话消息
  ASR_RESULT = 'asr_result',     // ASR 结果
  LLM_RESPONSE = 'llm_response', // LLM 响应
  TTS_START = 'tts_start',       // TTS 开始
  TTS_DATA = 'tts_data',         // TTS 音频（二进制）
  TTS_END = 'tts_end',           // TTS 结束

  // 功能消息
  FUNCTION_CALL = 'function_call',     // 函数调用
  FUNCTION_RESULT = 'function_result', // 函数结果

  // 状态消息
  STATE_CHANGE = 'state_change', // 状态变化
  ERROR = 'error',               // 错误
}

// Hello 消息
interface HelloPayload {
  device_mac: string;
  firmware_version: string;
  capabilities: string[];
}

// Hello ACK 消息
interface HelloAckPayload {
  session_id: string;
  agent_config: AgentConfig;
  server_capabilities: string[];
}

// ASR 结果
interface AsrResultPayload {
  text: string;
  is_final: boolean;
  confidence: number;
}

// LLM 响应
interface LlmResponsePayload {
  text: string;
  is_final: boolean;
  function_calls?: FunctionCall[];
}
```

### 10.3 SDK 自动生成

```bash
# 从 OpenAPI 生成 TypeScript SDK
npx openapi-typescript-codegen \
  --input ./openapi.yaml \
  --output ./web/src/lib/api/generated \
  --client axios

# 从 OpenAPI 生成 Python SDK
openapi-python-client generate \
  --path ./openapi.yaml \
  --output ./python/orica/api/generated
```

### 10.4 验收标准

| 检查项 | 验收条件 |
|--------|----------|
| OpenAPI 规范 | 覆盖 100% API 端点 |
| 文档生成 | Swagger UI 可正常访问 |
| SDK 生成 | TypeScript/Python SDK 可正常使用 |
| WebSocket 协议 | 文档完整，示例清晰 |

---

## 11. Phase 6: 集成测试与灰度发布

### 11.1 测试策略

```
┌─────────────────────────────────────────────────────────────────┐
│                        测试金字塔                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                        ┌─────────┐                              │
│                        │  E2E    │  10%                         │
│                        │  Tests  │  (Playwright)                │
│                       ─┴─────────┴─                             │
│                    ┌─────────────────┐                          │
│                    │  Integration    │  20%                     │
│                    │     Tests       │  (pytest + jest)         │
│                   ─┴─────────────────┴─                         │
│                ┌───────────────────────────┐                    │
│                │      Unit Tests           │  70%               │
│                │  (cargo test + pytest)    │                    │
│               ─┴───────────────────────────┴─                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 端到端测试场景

```typescript
// tests/e2e/device-management.spec.ts
import { test, expect } from '@playwright/test';

test.describe('设备管理', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[name="username"]', 'admin');
    await page.fill('[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('查看设备列表', async ({ page }) => {
    await page.goto('/devices');
    await expect(page.locator('h1')).toContainText('设备管理');
    await expect(page.locator('table tbody tr')).toHaveCount.greaterThan(0);
  });

  test('搜索设备', async ({ page }) => {
    await page.goto('/devices');
    await page.fill('[placeholder="搜索设备..."]', 'test-device');
    await expect(page.locator('table tbody tr')).toHaveCount(1);
  });

  test('编辑设备名称', async ({ page }) => {
    await page.goto('/devices');
    await page.click('table tbody tr:first-child [data-action="edit"]');
    await page.fill('[name="name"]', 'New Device Name');
    await page.click('button[type="submit"]');
    await expect(page.locator('.toast')).toContainText('保存成功');
  });
});
```

### 11.3 灰度发布策略

#### 11.3.1 阶段一：内部测试 (1 周)

```yaml
# 仅内部测试用户
canary:
  enabled: true
  percentage: 0%
  whitelist:
    - user_id: 1      # 管理员
    - user_id: 2      # 开发者
    - ip: 192.168.1.0/24  # 办公网络
```

#### 11.3.2 阶段二：小规模灰度 (1 周)

```yaml
# 5% 流量
canary:
  enabled: true
  percentage: 5%
  metrics:
    error_rate_threshold: 1%
    latency_p99_threshold: 500ms
  rollback:
    auto: true
    trigger: error_rate > 5%
```

#### 11.3.3 阶段三：扩大灰度 (1 周)

```yaml
# 逐步扩大：10% → 25% → 50%
canary:
  enabled: true
  percentage: 50%
  schedule:
    - percentage: 10%
      duration: 2d
    - percentage: 25%
      duration: 2d
    - percentage: 50%
      duration: 3d
```

#### 11.3.4 阶段四：全量发布

```yaml
# 100% 流量切换
canary:
  enabled: false
  percentage: 100%

# 保留旧版本 7 天以便回滚
legacy:
  enabled: true
  retention: 7d
```

### 11.4 监控指标

| 指标 | 阈值 | 告警级别 |
|------|------|----------|
| 错误率 | > 1% | P1 |
| P99 延迟 | > 500ms | P2 |
| P50 延迟 | > 100ms | P3 |
| CPU 使用率 | > 80% | P2 |
| 内存使用率 | > 80% | P2 |
| WebSocket 连接数 | > 10000 | P3 |

### 11.5 回滚方案

```bash
# 快速回滚脚本
#!/bin/bash

# 1. 切换流量到旧版本
kubectl set image deployment/orica-api \
  orica-api=orica/api:v1.0.0-legacy

# 2. 验证服务健康
kubectl rollout status deployment/orica-api

# 3. 通知相关人员
curl -X POST $SLACK_WEBHOOK \
  -d '{"text": "ORica API 已回滚到 v1.0.0-legacy"}'
```

---

## 12. 风险评估与缓解措施

### 12.1 风险矩阵

| 风险 | 可能性 | 影响 | 风险等级 | 缓解措施 |
|------|--------|------|----------|----------|
| Rust 学习曲线 | 高 | 中 | 🟡 中 | 提前培训，渐进式迁移 |
| Mojo 生态不成熟 | 中 | 中 | 🟡 中 | 准备 Cython 后备方案 |
| EloqKV 稳定性 | 低 | 高 | 🟡 中 | 充分测试，保留 MySQL 回滚路径 |
| 数据迁移失败 | 中 | 高 | 🔴 高 | 双写阶段，实时数据校验 |
| 前端迁移遗漏 | 中 | 低 | 🟢 低 | 完整的功能对照表，E2E 测试 |
| 性能回退 | 低 | 高 | 🟡 中 | 完整的性能基准测试 |

### 12.2 缓解措施详情

#### 12.2.1 Rust 学习曲线

**措施：**
1. 组织 2 周 Rust 基础培训
2. 从简单模块（如健康检查 API）开始
3. 代码审查注重 Rust 最佳实践
4. 建立 Rust 代码规范文档

**后备方案：** 如遇严重困难，可考虑使用 Go 作为替代

#### 12.2.2 Mojo 生态不成熟

**措施：**
1. 仅用于音频处理等计算密集型任务
2. 保持模块接口稳定，便于替换
3. 密切关注 Mojo 版本更新

**后备方案：**
- Cython + NumPy 加速
- PyPy 解释器
- Rust + PyO3

#### 12.2.3 数据迁移失败

**措施：**
1. 完整的数据备份
2. 双写阶段实时校验
3. 迁移脚本幂等设计
4. 分批迁移，每批验证

**后备方案：** 保留 MySQL 连接，支持快速回滚

---

## 13. 时间线总览

### 13.1 甘特图

```
2024 Q1                                    Q2
Jan        Feb        Mar        Apr       May
├──────────┼──────────┼──────────┼──────────┼──────────┤

Phase 0: 基础设施准备
████                                       (1月1日 - 1月5日)

Phase 1: EloqKV 存储层
    ████████                               (1月6日 - 1月19日)

Phase 2: Java → Rust
            ████████████████████           (1月20日 - 2月23日)

Phase 3: Python + Mojo (并行)
            ████████████████████████       (1月20日 - 3月2日)

Phase 4: Vue → Svelte
                            ████████████   (2月24日 - 3月23日)

Phase 5: API 统一
                                    ████   (3月24日 - 4月6日)

Phase 6: 集成测试与灰度发布
                                        ██████████
                                           (4月7日 - 4月27日)

█ = 1 周
```

### 13.2 里程碑

| 里程碑 | 日期 | 交付物 |
|--------|------|--------|
| M0: 基础设施就绪 | 1月5日 | CI/CD, 监控, 开发环境 |
| M1: 存储层就绪 | 1月19日 | EloqKV 部署，数据迁移完成 |
| M2: Rust API 就绪 | 2月23日 | Axum API 100% 功能覆盖 |
| M3: 性能层就绪 | 3月2日 | Mojo 音频处理模块上线 |
| M4: 新前端就绪 | 3月23日 | Svelte 管理后台 100% 功能覆盖 |
| M5: API 文档就绪 | 4月6日 | OpenAPI 规范 + SDK |
| M6: 正式发布 | 4月27日 | v2.0.0 全量上线 |

---

## 14. 附录：技术选型速查表

### 14.1 Rust 生态

| 用途 | 推荐库 | 备选 |
|------|--------|------|
| Web 框架 | axum | actix-web |
| 异步运行时 | tokio | async-std |
| 序列化 | serde | - |
| HTTP 客户端 | reqwest | ureq |
| JWT | jsonwebtoken | - |
| Redis 客户端 | redis-rs | fred |
| 日志 | tracing | log |
| 配置 | config | figment |

### 14.2 Python 生态

| 用途 | 推荐库 | 备选 |
|------|--------|------|
| Web 框架 | FastAPI | - |
| 异步 | asyncio | - |
| 配置 | pydantic | - |
| 音频处理 | soundfile | librosa |
| AI 推理 | transformers | - |

### 14.3 Mojo 使用指南

```mojo
# 推荐用法
- SIMD 向量运算
- 数值计算密集型任务
- FFI 调用 C 库

# 不推荐用法
- I/O 密集型任务
- 复杂业务逻辑
- 需要大量库支持的任务
```

### 14.4 Svelte 生态

| 用途 | 推荐库 | 备选 |
|------|--------|------|
| 框架 | SvelteKit | - |
| UI 组件 | shadcn-svelte | skeleton |
| CSS | Tailwind CSS | - |
| 图表 | ECharts | Chart.js |
| 图标 | lucide-svelte | heroicons |
| 表单验证 | superforms | - |
| HTTP | fetch | ky |

---

## 变更记录

| 版本 | 日期 | 作者 | 变更内容 |
|------|------|------|----------|
| v1.0.0 | 2024-01-17 | Claude | 初始版本 |

---

> **提示：** 本文档为重构指导性文件，具体实施过程中请根据实际情况调整。如有疑问，请联系技术负责人。
