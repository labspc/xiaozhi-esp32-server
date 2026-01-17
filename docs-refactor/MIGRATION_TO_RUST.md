# xiaozhi-esp32-server 迁移指南：从 Java + MySQL/Redis 到 Rust + EloqKV

## 目录

- [迁移概览](#迁移概览)
- [架构对比](#架构对比)
- [技术栈映射](#技术栈映射)
- [数据迁移方案](#数据迁移方案)
- [API 迁移映射](#api-迁移映射)
- [认证授权改造](#认证授权改造)
- [部署变更](#部署变更)
- [实施路线图](#实施路线图)
- [风险评估与缓解](#风险评估与缓解)
- [验收标准](#验收标准)

---

## 迁移概览

### 迁移目标

将 `manager-api` (Java Spring Boot) 从重量级架构改造为轻量级 Rust 服务，同时将双存储（MySQL + Redis）统一为 EloqKV。

### 核心收益

| 维度 | 现状 | 目标 | 改进 |
|------|------|------|------|
| 启动时间 | ~8-15秒 | <1秒 | **90%+** |
| 内存占用 | ~300-500MB | <50MB | **85%+** |
| 二进制大小 | ~80MB (jar) | ~15MB (静态编译) | **80%+** |
| 存储组件 | MySQL + Redis (2个) | EloqKV (1个) | **50%** 运维成本 |
| 部署复杂度 | JVM + 数据库 + 缓存 | 单二进制 + EloqKV | **极大简化** |

### 迁移范围

**需要迁移的模块：**
- `main/manager-api/` → `main/xiaozhi-config-api/` (Rust)
- MySQL 数据 → EloqKV 数据
- Redis 缓存 → EloqKV 内置缓存

**保持不变的模块：**
- `xiaozhi-server` (Python) - 核心AI引擎
- `manager-web` (Vue 2) - 暂时保留，后续单独迁移
- `manager-mobile` (uni-app) - 暂时保留

---

## 架构对比

### 当前架构（AS-IS）

```
┌─────────────────┐
│  manager-web    │ (Vue 2, port 8001)
│  manager-mobile │ (uni-app)
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────┐
│  manager-api    │ (Java Spring Boot, port 8002)
│  - Spring Web   │
│  - Shiro Auth   │
│  - MyBatis Plus │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌───────┐ ┌───────┐
│ MySQL │ │ Redis │
└───────┘ └───────┘
         ↑
         │ 配置同步
         │
┌─────────────────┐
│ xiaozhi-server  │ (Python, port 8000)
│ WebSocket AI    │
└─────────────────┘
```

### 目标架构（TO-BE）

```
┌─────────────────┐
│  manager-web    │ (保持不变 / 未来迁移Svelte)
│  manager-mobile │
└────────┬────────┘
         │ HTTP REST
         ↓
┌─────────────────┐
│ xiaozhi-cfg-api │ (Rust axum/actix, port 8002)
│ - JWT Auth      │
│ - Async Handler │
│ - EloqKV Client │
└────────┬────────┘
         │
         ↓
    ┌────────┐
    │ EloqKV │ (KV + SQL + Cache)
    └────┬───┘
         ↑
         │ 配置同步
         │
┌─────────────────┐
│ xiaozhi-server  │ (Python, 保持不变)
└─────────────────┘
```

### 关键变化

1. **单体存储**: MySQL + Redis → EloqKV
2. **轻量服务**: Spring Boot → Rust 异步框架
3. **简化认证**: Shiro → JWT + middleware
4. **编译部署**: jar + JVM → 静态链接二进制

---

## 技术栈映射

### 后端框架选型

#### 选项1: **axum** (推荐)

**特点：**
- 基于 tokio 异步运行时
- 类型安全的路由和提取器
- 中间件系统灵活
- Tower 生态集成（限流、日志、追踪）

**适用场景：**
- 需要高性能异步处理
- 需要细粒度控制
- 团队熟悉 Rust 类型系统

**对应关系：**
```
Spring Boot Controller  →  axum Router + Handler
@RestController         →  async fn handler()
@RequestMapping         →  Router::route()
@Autowired Service      →  State<AppState>
```

#### 选项2: **actix-web**

**特点：**
- 成熟稳定，文档丰富
- Actor 模型支持
- 性能基准测试优秀

**适用场景：**
- 需要 Actor 并发模型
- 喜欢宏驱动开发
- 需要成熟生态和案例

**对应关系：**
```
Spring Boot Controller  →  actix_web::web handlers
@RestController         →  #[get("/path")] macro
@Autowired Service      →  web::Data<AppState>
```

### 核心依赖映射

| Java (Spring Boot) | Rust (axum生态) | 用途 |
|-------------------|-----------------|------|
| spring-boot-starter-web | axum | Web框架 |
| jackson | serde + serde_json | JSON序列化 |
| mybatis-plus | sqlx / diesel | 数据库ORM |
| druid | deadpool / bb8 | 连接池 |
| jedis | redis-rs | Redis客户端 → **不需要** |
| shiro | jsonwebtoken + tower-http | 认证授权 |
| lombok | derive宏 (自带) | 代码生成 |
| swagger | utoipa | API文档 |
| slf4j + logback | tracing + tracing-subscriber | 日志 |
| commons-lang3 | 标准库 (String, Vec等) | 工具函数 |

### EloqKV 集成

**官方SDK/库：**
- 查阅 https://www.eloqdata.com/eloqkv/introduction 的客户端文档
- 如果提供 Rust SDK：直接使用
- 如果仅提供 REST API：用 reqwest + serde 封装
- 如果支持 Redis 协议：可用 redis-rs 兼容层

**典型集成模式：**
```
EloqKV Client
├── KV 操作 (类似 Redis)
│   └── GET/SET/DEL/EXPIRE
├── SQL 查询 (类似 MySQL)
│   └── SELECT/INSERT/UPDATE/DELETE
└── 事务支持
    └── MULTI/EXEC 或类似机制
```

---

## 数据迁移方案

### 步骤1：分析现有数据库模式

**工具：** Liquibase changelogs
**位置：** `main/manager-api/src/main/resources/db/changelog/`

**需要提取：**
1. 所有表结构 (CREATE TABLE)
2. 索引定义 (CREATE INDEX)
3. 外键约束 (如有)
4. 初始数据 (INSERT)

### 步骤2：设计 EloqKV 数据模型

#### 策略A: KV 模式（适合简单场景）

**原则：**
- 用 Key 前缀区分不同实体类型
- 用 JSON 存储复杂对象
- 用 Hash 结构存储关系

**示例：**
```
原MySQL表: users (id, username, email, role)
EloqKV设计:
  user:1 → {"id":1,"username":"admin","email":"admin@example.com","role":"admin"}
  user:2 → {"id":2,"username":"demo","email":"demo@example.com","role":"user"}

  索引: username:admin → "1"  (用于按用户名查找)
```

#### 策略B: SQL 模式（如果 EloqKV 支持）

**如果 EloqKV 支持类 SQL 查询：**
- 保持表结构设计
- 使用 EloqKV 的 SQL 接口
- 迁移更简单，改动更小

**验证点：**
- 检查 EloqKV 是否支持 JOIN
- 检查是否支持事务 (ACID)
- 检查索引性能

### 步骤3：编写数据迁移脚本

**工具选择：**
1. **Python脚本** (推荐，因为项目已有Python环境)
   - 连接 MySQL 读取数据
   - 连接 EloqKV 写入数据
   - 使用 `mysql-connector-python` + EloqKV客户端

2. **Rust工具** (性能最优)
   - 使用 `sqlx` 连接 MySQL
   - 并行写入 EloqKV
   - 编译为独立工具

**迁移检查项：**
```
1. 数据完整性验证
   - 行数对比 (MySQL count vs EloqKV count)
   - 关键字段校验和 (checksum)

2. 关系完整性
   - 外键引用检查
   - 索引字段验证

3. 性能测试
   - 批量写入速度
   - 查询响应时间
```

### 步骤4：Redis 数据迁移

**Redis 当前用途分析：**
- Session 存储 (用户登录态)
- 配置热数据缓存
- 临时数据 (验证码等)

**迁移策略：**
1. **Session 数据**：改为 JWT 无状态，无需迁移
2. **配置缓存**：EloqKV 内置缓存，无需显式管理
3. **临时数据**：继续使用 KV 接口，设置 TTL

---

## API 迁移映射

### 模块分析

基于 `manager-api` 的 modules 结构，需要迁移：

```
xiaozhi/modules/
├── user/          # 用户管理
├── device/        # 设备管理
├── config/        # 配置管理
├── log/           # 日志查询
├── system/        # 系统管理
└── security/      # 认证授权
```

### API 端点对照表

#### 示例：用户管理模块

| Spring Boot (原) | Rust axum (新) | 方法 | 说明 |
|-----------------|---------------|------|------|
| `@GetMapping("/user/list")` | `Router::get("/user/list")` | GET | 用户列表 |
| `@PostMapping("/user/save")` | `Router::post("/user/save")` | POST | 新增用户 |
| `@PostMapping("/user/update")` | `Router::put("/user/:id")` | PUT | 更新用户 (REST化) |
| `@PostMapping("/user/delete")` | `Router::delete("/user/:id")` | DELETE | 删除用户 (REST化) |
| `@RequestBody UserDTO` | `Json<UserDto>` | - | 请求体 |
| `@PathVariable Long id` | `Path<i64>` | - | 路径参数 |
| `@RequestParam String name` | `Query<QueryParams>` | - | 查询参数 |

#### 响应格式统一

**原 Java 格式：**
```json
{
  "code": 0,
  "msg": "success",
  "data": {...}
}
```

**保持一致性：** Rust 端继续使用相同格式，确保前端无需改动

**实现方式：**
- 定义统一的 `ApiResponse<T>` 结构体
- 实现 `IntoResponse` trait
- 错误处理中间件自动转换

### 业务逻辑迁移

#### Service 层转换

**Java (Spring Boot):**
```
UserService.java (@Service)
  ├── @Autowired UserDao
  ├── @Autowired RedisTemplate
  └── Business logic methods
```

**Rust (axum):**
```
user_service.rs
  ├── struct UserService { eloqkv: EloqClient }
  ├── impl UserService { async fn get_user(...) }
  └── Handler functions call service methods
```

#### DAO 层转换

**从 MyBatis-Plus 到 EloqKV：**

| MyBatis-Plus | EloqKV 操作 | 示例 |
|--------------|------------|------|
| `selectById(id)` | `eloq.get(key)` 或 `eloq.query_one(sql)` | 按ID查询 |
| `selectList(wrapper)` | `eloq.query(sql)` | 列表查询 |
| `insert(entity)` | `eloq.set(key, json)` 或 `eloq.execute(sql)` | 插入 |
| `updateById(entity)` | `eloq.set(key, json)` | 更新 |
| `deleteById(id)` | `eloq.del(key)` | 删除 |

#### 分页查询处理

**原 MyBatis-Plus 分页：**
```
IPage<User> page = new Page<>(current, size);
userDao.selectPage(page, wrapper);
```

**EloqKV 分页方案：**
- 如果支持 SQL：使用 `LIMIT offset, size`
- 如果仅 KV：需要手动实现游标分页或扫描

### Swagger 文档迁移

**从 Springfox 到 utoipa：**

**原注解：**
```java
@Api(tags = "用户管理")
@ApiOperation("获取用户列表")
@ApiImplicitParam(name = "name", value = "用户名")
```

**新注解：**
```rust
#[utoipa::path(
    get,
    path = "/user/list",
    tag = "用户管理",
    params(
        ("name" = Option<String>, Query, description = "用户名")
    ),
    responses(
        (status = 200, description = "成功", body = ApiResponse<Vec<User>>)
    )
)]
```

**生成文档：**
- utoipa 自动生成 OpenAPI 3.0 规范
- 集成 Swagger UI / Redoc
- 保持与原 API 文档一致性

---

## 认证授权改造

### 从 Shiro 到 JWT

#### Shiro 现状分析

**配置位置：** `manager-api/src/main/java/xiaozhi/modules/security/`

**核心组件：**
- `OAuth2Filter`: 拦截请求验证 token
- `OAuth2Realm`: 用户认证和授权
- `ShiroConfig`: Shiro 配置类

**工作流程：**
1. 前端携带 token (`Authorization: Bearer xxx`)
2. Filter 拦截，调用 Realm 验证
3. 验证通过后，从 Redis/数据库加载用户信息
4. 将用户信息绑定到当前请求上下文

#### JWT 方案设计

**Token 格式：**
```json
{
  "sub": "user_id",
  "username": "admin",
  "role": "admin",
  "exp": 1735200000
}
```

**密钥管理：**
- 使用环境变量 `JWT_SECRET`
- 生产环境建议使用 RSA 非对称加密

**验证流程：**
```
Request → Extract token from header
        → Validate signature & expiration
        → Extract claims (user info)
        → Inject into request extensions
        → Handler accesses user info
```

#### Rust 实现方式

**依赖库：**
- `jsonwebtoken`: JWT 生成和验证
- `tower-http::auth`: Bearer token 中间件
- `axum::middleware`: 自定义认证中间件

**中间件设计：**
1. 全局中间件：验证 token 有效性
2. 路由级中间件：检查用户权限（role-based）
3. 提取器：从 request extensions 获取当前用户

#### 权限模型迁移

**Shiro 权限格式：** `resource:operation` (如 `user:create`)

**JWT 权限方案：**
- 在 token claims 中包含 `permissions: Vec<String>`
- 或简化为 `role: String`，在代码中映射角色到权限
- 使用 `tower-http::validate_request` 进行检查

### 登录流程改造

**原流程 (Shiro):**
```
POST /sys/login
  → 验证用户名密码
  → 生成 token (UUID)
  → 存储到 Redis (token → user info)
  → 返回 token
```

**新流程 (JWT):**
```
POST /sys/login
  → 验证用户名密码
  → 查询 EloqKV 获取用户信息
  → 生成 JWT token (包含用户信息)
  → 返回 token (无需存储)
```

**优势：** 无状态，无需 Redis 存储 session，水平扩展更容易

---

## 部署变更

### 构建产物对比

| 组件 | 现状 | 目标 | 变化 |
|------|------|------|------|
| manager-api | manager-api.jar (~80MB) | xiaozhi-cfg-api (15MB) | **83%↓** |
| JVM | 需要 JDK/JRE | 不需要 | 依赖移除 |
| 配置文件 | application.yml | config.toml / .env | 简化 |

### Docker 镜像优化

**原镜像 (Java):**
```dockerfile
FROM openjdk:21-jdk
COPY target/manager-api.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
# 镜像大小: ~400MB
```

**新镜像 (Rust):**
```dockerfile
# 方案1: 动态链接
FROM debian:bookworm-slim
COPY target/release/xiaozhi-cfg-api /app
ENTRYPOINT ["/app"]
# 镜像大小: ~80MB

# 方案2: 静态编译 (推荐)
FROM scratch
COPY target/x86_64-unknown-linux-musl/release/xiaozhi-cfg-api /app
ENTRYPOINT ["/app"]
# 镜像大小: ~15MB
```

**构建命令：**
- 动态链接: `cargo build --release`
- 静态编译: `cargo build --release --target x86_64-unknown-linux-musl`

### 环境变量配置

**迁移配置项：**

| Java (application.yml) | Rust (环境变量) | 说明 |
|------------------------|----------------|------|
| `spring.datasource.url` | `ELOQKV_URL` | EloqKV 连接地址 |
| `spring.datasource.username` | `ELOQKV_USER` | 用户名 |
| `spring.datasource.password` | `ELOQKV_PASSWORD` | 密码 |
| `spring.redis.*` | 不需要 | Redis 配置移除 |
| `server.port` | `PORT` | 服务端口 (默认8002) |
| `renren.jwt.secret` | `JWT_SECRET` | JWT 签名密钥 |

### 资源需求变化

| 资源 | Java (Spring Boot) | Rust (axum) | 节省 |
|------|-------------------|-------------|------|
| 最小内存 | 512MB | 32MB | **93%** |
| 推荐内存 | 1GB | 64MB | **93%** |
| CPU (空闲) | ~5% | <1% | **80%** |
| 启动时间 | 8-15秒 | 50-200ms | **98%** |

### 服务编排调整

**docker-compose.yml 变化：**

**移除：**
```yaml
  mysql:
    image: mysql:8.0
    # ...

  redis:
    image: redis:7
    # ...
```

**新增：**
```yaml
  eloqkv:
    image: eloqdata/eloqkv:latest  # 根据官方文档调整
    ports:
      - "6379:6379"  # 或其他端口
    volumes:
      - eloqkv_data:/data
    environment:
      - ELOQ_CONFIG=/etc/eloqkv.conf
```

**更新 manager-api 为 xiaozhi-cfg-api：**
```yaml
  xiaozhi-cfg-api:
    build:
      context: ./main/xiaozhi-config-api
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - ELOQKV_URL=eloqkv:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - eloqkv
```

### 健康检查

**原 Spring Boot Actuator:**
```
GET /actuator/health
```

**新 Rust 健康检查端点：**
```
GET /health
  → 检查 EloqKV 连接
  → 返回 JSON {"status": "ok", "timestamp": ...}
```

---

## 实施路线图

### 阶段0：准备阶段 (1-2天)

**任务：**
1. 评估 EloqKV 功能特性
   - 阅读官方文档
   - 本地部署测试实例
   - 验证 KV/SQL 能力
   - 性能基准测试

2. 搭建 Rust 开发环境
   - 安装 Rust toolchain (rustup)
   - 选择 IDE (VS Code + rust-analyzer / IntelliJ IDEA)
   - 熟悉 cargo 工具链

3. 技术选型确认
   - 确定 axum vs actix-web
   - 确定 EloqKV 客户端库
   - 确定 ORM 方案（如需要）

**产出：**
- EloqKV 评估报告
- Rust 项目脚手架
- 技术选型文档

### 阶段1：核心功能迁移 (1周)

**任务：**
1. 创建 Rust 项目结构
   ```
   xiaozhi-config-api/
   ├── Cargo.toml
   ├── src/
   │   ├── main.rs
   │   ├── config.rs          # 配置加载
   │   ├── db/
   │   │   └── eloqkv.rs      # EloqKV 客户端
   │   ├── models/            # 数据模型
   │   ├── handlers/          # API handlers
   │   ├── middleware/        # 认证等中间件
   │   └── error.rs           # 错误处理
   ├── .env.example
   └── Dockerfile
   ```

2. 实现基础设施
   - EloqKV 连接池
   - 日志系统 (tracing)
   - 配置加载 (dotenv/config-rs)
   - 统一错误处理

3. 实现认证系统
   - JWT 生成和验证
   - 登录/登出接口
   - 认证中间件

**产出：**
- 可运行的 Rust 服务骨架
- 认证功能完成

### 阶段2：业务模块迁移 (1-2周)

**优先级排序：**
1. **P0 (核心功能)**: 用户管理、设备管理、配置管理
2. **P1 (重要功能)**: 日志查询、系统管理
3. **P2 (次要功能)**: 统计报表、其他辅助功能

**每个模块迁移步骤：**
1. 分析 Java Service/Controller 代码
2. 设计 EloqKV 数据模型
3. 实现 Rust handlers 和 service 层
4. 编写单元测试
5. API 功能测试

**并行策略：**
- 简单 CRUD 模块可并行开发
- 复杂业务逻辑逐个攻克

**产出：**
- 完整的 API 功能实现
- 单元测试覆盖

### 阶段3：数据迁移 (2-3天)

**任务：**
1. 编写迁移脚本
   - Python 或 Rust 工具
   - 批量读取 MySQL
   - 转换后写入 EloqKV

2. 迁移验证
   - 数据完整性检查
   - 查询性能对比测试
   - 业务逻辑回归测试

3. 双写验证（可选）
   - 同时写入 MySQL 和 EloqKV
   - 对比数据一致性
   - 灰度验证

**产出：**
- 完整数据迁移到 EloqKV
- 验证报告

### 阶段4：集成测试 (3-5天)

**任务：**
1. 前后端联调
   - manager-web 连接新 API
   - manager-mobile 连接新 API
   - 修复兼容性问题

2. xiaozhi-server 集成
   - 验证配置同步功能
   - 测试设备注册流程
   - 测试实时配置推送

3. 压力测试
   - 并发用户测试
   - 设备连接数测试
   - API 响应时间测试

**产出：**
- 集成测试通过
- 性能测试报告

### 阶段5：灰度发布 (1周)

**策略：**
1. **双系统运行**
   - 保持 Java manager-api 运行
   - 部署 Rust xiaozhi-cfg-api 到新端口 (如 8003)
   - 前端配置切换开关

2. **流量切换**
   - 5% 流量 → Rust API (观察1天)
   - 20% 流量 → Rust API (观察2天)
   - 50% 流量 → Rust API (观察2天)
   - 100% 流量 → Rust API

3. **监控指标**
   - API 成功率
   - 响应时间
   - 错误日志
   - 业务指标 (设备在线率等)

**产出：**
- 灰度发布完成
- 问题修复记录

### 阶段6：全量切换与清理 (2-3天)

**任务：**
1. 正式切换
   - 更新所有客户端配置
   - 停止 Java manager-api
   - 下线 MySQL 和 Redis

2. 清理工作
   - 删除旧代码仓库或归档
   - 更新部署文档
   - 更新 API 文档

3. 备份
   - MySQL 数据备份 (保留至少1个月)
   - Redis 快照备份

**产出：**
- 完全迁移到新架构
- 清理完成

---

## 风险评估与缓解

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| EloqKV 功能不满足需求 | 中 | 高 | **提前评估**，准备备选方案 (SQLite + Redis) |
| Rust 学习曲线陡峭 | 高 | 中 | 分阶段学习，参考成熟项目模板 |
| 数据迁移失败或丢失 | 低 | 极高 | **多次测试**，保留 MySQL 备份，双写验证 |
| API 不兼容导致前端报错 | 中 | 高 | 保持响应格式一致，充分联调测试 |
| 性能不如预期 | 低 | 中 | 压力测试验证，优化查询和索引 |

### 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 迁移期间服务中断 | 低 | 极高 | 灰度发布，保持双系统并行运行 |
| 用户体验下降 | 低 | 高 | 充分测试，监控响应时间 |
| 新系统 Bug 导致数据错误 | 中 | 高 | 单元测试 + 集成测试，双写验证 |

### 回滚方案

**触发条件：**
- 关键 API 成功率 < 95%
- 平均响应时间 > 原系统 2倍
- 发现严重数据错误

**回滚步骤：**
1. 流量切回 Java manager-api
2. 停止 Rust API
3. 分析问题根因
4. 修复后重新灰度

**数据同步：**
- 如果使用双写策略：数据已同步，无需处理
- 如果未双写：从备份恢复 MySQL，分析增量数据

---

## 验收标准

### 功能验收

**必须通过：**
- [ ] 所有原有 API 端点功能正常
- [ ] 前端 manager-web 无需修改或仅需配置修改
- [ ] manager-mobile 正常工作
- [ ] xiaozhi-server 配置同步正常
- [ ] 用户登录/权限验证正常
- [ ] 设备注册/管理功能正常

### 性能验收

**目标指标：**
- [ ] API 平均响应时间 < 100ms (原 Java 通常 200-500ms)
- [ ] 服务启动时间 < 1秒 (原 8-15秒)
- [ ] 内存占用 < 64MB (原 300-500MB)
- [ ] 支持并发请求数 >= 原系统 (至少 1000 QPS)

### 稳定性验收

**观察期：** 至少 2 周

**指标：**
- [ ] API 成功率 > 99.9%
- [ ] 无内存泄漏 (长时间运行内存稳定)
- [ ] 无数据丢失或错误
- [ ] 日志无严重错误

### 运维验收

**部署简化：**
- [ ] Docker 镜像大小 < 100MB (原 ~400MB)
- [ ] 部署组件数量减少 (移除 MySQL, Redis)
- [ ] 配置管理简化 (环境变量 vs 复杂 yml)

---

## 参考资源

### Rust 生态

- **axum**: https://github.com/tokio-rs/axum
- **actix-web**: https://github.com/actix/actix-web
- **serde**: https://serde.rs/
- **sqlx**: https://github.com/launchbadge/sqlx (如需 SQL)
- **utoipa**: https://github.com/juhaku/utoipa (OpenAPI)
- **tracing**: https://github.com/tokio-rs/tracing

### EloqKV

- **官方文档**: https://www.eloqdata.com/eloqkv/introduction
- **SDK/客户端**: 查看官网提供的 Rust SDK

### 迁移案例参考

- **Realworld 示例** (各种框架实现同一 API):
  - https://github.com/gothinkster/realworld
  - Rust axum 实现: https://github.com/launchbadge/realworld-axum-sqlx

### 学习资源

- **Rust 官方书**: https://doc.rust-lang.org/book/
- **Async Rust**: https://rust-lang.github.io/async-book/
- **Axum 教程**: https://github.com/tokio-rs/axum/tree/main/examples

---

## 附录

### A. 项目结构对比

**Java (manager-api):**
```
src/main/java/xiaozhi/
├── common/              # 公共组件
├── modules/
│   ├── user/
│   │   ├── controller/
│   │   ├── service/
│   │   ├── dao/
│   │   └── entity/
│   └── device/
│       └── ...
└── XiaozHiApplication.java
```

**Rust (xiaozhi-config-api):**
```
src/
├── main.rs             # 入口
├── config.rs           # 配置
├── error.rs            # 错误处理
├── db/
│   └── eloqkv.rs       # 数据库
├── models/             # 数据模型
│   ├── user.rs
│   └── device.rs
├── handlers/           # API 处理
│   ├── user.rs
│   ├── device.rs
│   └── auth.rs
├── services/           # 业务逻辑 (可选)
│   └── user_service.rs
└── middleware/
    └── auth.rs
```

### B. 配置文件对比

**application.yml (Java):**
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/xiaozhi
    username: root
    password: xxx
  redis:
    host: localhost
    port: 6379
server:
  port: 8002
```

**.env (Rust):**
```bash
ELOQKV_URL=localhost:6379
ELOQKV_USER=default
ELOQKV_PASSWORD=xxx
PORT=8002
JWT_SECRET=your-secret-key
RUST_LOG=info
```

### C. 关键决策记录

**决策1: 选择 axum 而非 actix-web**
- 理由: tokio 生态统一，类型安全更好，社区趋势
- 权衡: actix-web 更成熟，但 Actor 模型不适合本场景

**决策2: JWT 替代 Shiro**
- 理由: 无状态，易于水平扩展，无需 Redis 存储
- 权衡: Token 无法主动失效（可用黑名单缓解）

**决策3: 保留 manager-web (Vue 2)**
- 理由: 减少迁移风险，前后端分离解耦
- 后续: 可单独迁移到 Svelte 5

---

## 结语

本迁移方案旨在将 xiaozhi-esp32-server 从重量级 Java 架构改造为轻量级 Rust 架构，同时统一存储到 EloqKV。

**关键成功要素：**
1. **充分测试**: 数据迁移、功能测试、性能测试
2. **灰度发布**: 逐步切换流量，降低风险
3. **保持备份**: MySQL 数据保留至少 1 个月
4. **监控观察**: 密切关注新系统运行指标

**预期收益：**
- 资源占用降低 85%+
- 启动时间降低 90%+
- 运维复杂度降低 50%+
- 部署更加简单快速

---

**文档版本:** 1.0
**创建日期:** 2026-01-16
**维护者:** Claude Code
**反馈渠道:** 项目 Issues
