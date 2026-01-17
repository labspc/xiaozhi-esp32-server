# Axum Web 框架简化指南 - AI 友好版

## 写给 AI 的话

这是 Axum web 框架的简化使用指南，必须严格遵守：

1. **只用 Axum 的基础功能**
2. **不用高级特性（提取器、中间件层、泛型路由等）**
3. **代码要简单直接**
4. **每个 Handler 都打印日志**
5. **所有代码都遵循相同模板**
6. **配合 RUST_SIMPLE_GUIDE.md 一起使用**

目标：让不懂 Rust 的人也能看懂 Web API 代码，出错了能快速定位。

---

## 第一章：Axum 禁止使用的特性

### 1. 禁止使用复杂的提取器组合

```rust
// 禁止 - 不要用复杂的提取器
async fn handler(
    Path((user_id, post_id)): Path<(i64, i64)>,
    Query(params): Query<HashMap<String, String>>,
    Json(payload): Json<CreateUser>,
) -> Response {
    // ...
}

// 推荐 - 分步骤手动提取
async fn handler(req: Request<Body>) -> Response<Body> {
    println!("[handler] 开始处理请求");

    // 步骤1：手动解析路径参数
    // 步骤2：手动解析查询参数
    // 步骤3：手动解析 JSON body

    // 返回响应
}
```

### 2. 禁止使用自定义提取器

```rust
// 禁止 - 不要实现 FromRequest trait
#[async_trait]
impl<S> FromRequest<S> for MyExtractor {
    // ...
}

// 推荐 - 用普通函数手动解析
fn parse_user_from_request(req: &Request<Body>) -> Result<User, String> {
    // 手动解析逻辑
}
```

### 3. 禁止使用 Tower 中间件层

```rust
// 禁止 - 不要用 tower 的复杂中间件
let app = Router::new()
    .route("/", get(handler))
    .layer(TraceLayer::new_for_http())
    .layer(TimeoutLayer::new(Duration::from_secs(10)));

// 推荐 - 在 Handler 内部手动实现需要的功能
async fn handler(req: Request<Body>) -> Response<Body> {
    // 手动记录日志
    // 手动检查超时
    // 手动实现业务逻辑
}
```

### 4. 禁止使用泛型路由

```rust
// 禁止 - 不要用泛型
fn generic_handler<T>() -> impl Handler { ... }

// 推荐 - 每个路由写一个具体的 Handler
async fn user_handler(req: Request<Body>) -> Response<Body> { ... }
async fn device_handler(req: Request<Body>) -> Response<Body> { ... }
```

### 5. 禁止使用 State 共享

```rust
// 禁止 - 不要用 State 提取器
#[derive(Clone)]
struct AppState {
    db: Database,
}

async fn handler(State(state): State<AppState>) -> Response {
    // ...
}

// 推荐 - 用全局变量或者在 main 中传递
// 如果需要共享数据，用简单的方式（见后面的模板）
```

---

## 第二章：基础 Cargo.toml

```toml
[package]
name = "xiaozhi-cfg-api"
version = "0.1.0"
edition = "2021"

[dependencies]
# Web 框架（只用基础功能）
axum = "0.7"
tokio = { version = "1", features = ["full"] }

# HTTP 类型
http = "1.0"
http-body-util = "0.1"

# 序列化（手动使用，不用 Json 提取器）
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# 可选：环境变量
dotenv = "0.15"
```

注意：
- 不需要 tower、tower-http（避免复杂中间件）
- 不需要 tracing（用简单的 println!）
- 不需要 async-trait（不实现自定义 trait）

---

## 第三章：标准项目结构

```
xiaozhi-cfg-api/
├── Cargo.toml
├── .env                    # 环境变量配置
├── src/
│   ├── main.rs            # 程序入口，路由定义
│   ├── models.rs          # 数据结构
│   ├── handlers/          # API 处理器
│   │   ├── mod.rs
│   │   ├── user.rs        # 用户相关 API
│   │   ├── device.rs      # 设备相关 API
│   │   └── auth.rs        # 认证相关 API
│   ├── services/          # 业务逻辑
│   │   ├── mod.rs
│   │   ├── user_service.rs
│   │   └── device_service.rs
│   ├── db.rs              # 数据库/EloqKV 连接
│   ├── response.rs        # 统一响应格式
│   └── utils.rs           # 工具函数
└── data/
    └── users.json         # 数据文件
```

---

## 第四章：核心模板

### 模板1：main.rs（程序入口）

```rust
// 文件：main.rs
// 说明：程序入口，定义所有路由
// 创建时间：2026-01-16

// 导入模块
mod models;
mod handlers;
mod services;
mod response;

// 导入依赖
use axum::{
    routing::{get, post},
    Router,
    http::{Request, Response, StatusCode},
    body::Body,
};
use std::net::SocketAddr;

// 主函数
#[tokio::main]
async fn main() {
    println!("========== xiaozhi-cfg-api 启动 ==========\n");

    // 步骤1：加载配置
    println!("[main] 步骤1：加载配置");
    load_config();

    // 步骤2：初始化数据库连接
    println!("[main] 步骤2：初始化数据库");
    // TODO: 初始化 EloqKV 连接

    // 步骤3：创建路由
    println!("[main] 步骤3：创建路由");
    let app = create_router();

    // 步骤4：启动服务器
    println!("[main] 步骤4：启动服务器");
    let addr = SocketAddr::from(([0, 0, 0, 0], 8002));
    println!("[main] 服务器监听地址: {}", addr);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("无法绑定端口");

    println!("[main] 服务器启动成功！");
    println!("========================================\n");

    axum::serve(listener, app)
        .await
        .expect("服务器运行失败");
}

// 创建路由
// 返回：配置好的 Router
fn create_router() -> Router {
    println!("[create_router] 创建路由");

    Router::new()
        // 健康检查
        .route("/health", get(handlers::health::health_check))

        // 用户管理
        .route("/api/user/list", get(handlers::user::list_users))
        .route("/api/user/get/:id", get(handlers::user::get_user))
        .route("/api/user/create", post(handlers::user::create_user))
        .route("/api/user/update", post(handlers::user::update_user))
        .route("/api/user/delete/:id", post(handlers::user::delete_user))

        // 设备管理
        .route("/api/device/list", get(handlers::device::list_devices))
        .route("/api/device/get/:mac", get(handlers::device::get_device))

        // 认证
        .route("/api/auth/login", post(handlers::auth::login))
}

// 加载配置
fn load_config() {
    println!("[load_config] 加载环境变量");

    // 加载 .env 文件
    if let Err(e) = dotenv::dotenv() {
        println!("[load_config] 警告：无法加载 .env 文件: {}", e);
    }

    println!("[load_config] 配置加载完成");
}
```

### 模板2：统一响应格式（response.rs）

```rust
// 文件：response.rs
// 说明：定义统一的 API 响应格式
// 创建时间：2026-01-16

use axum::{
    response::{Response, IntoResponse},
    body::Body,
    http::StatusCode,
};
use serde::Serialize;

// API 响应结构
// 说明：所有 API 返回的统一格式
pub struct ApiResponse<T> {
    pub code: i32,      // 状态码：0表示成功，非0表示失败
    pub msg: String,    // 消息
    pub data: Option<T>, // 数据
}

impl<T> ApiResponse<T> {
    // 创建成功响应
    // 参数：data - 返回的数据
    // 返回：ApiResponse 实例
    pub fn success(data: T) -> Self {
        Self {
            code: 0,
            msg: String::from("success"),
            data: Some(data),
        }
    }

    // 创建失败响应
    // 参数：msg - 错误消息
    // 返回：ApiResponse 实例
    pub fn error(msg: String) -> ApiResponse<()> {
        ApiResponse {
            code: 1,
            msg: msg,
            data: None,
        }
    }
}

// 实现 IntoResponse（让它可以作为 Handler 返回值）
impl<T: Serialize> IntoResponse for ApiResponse<T> {
    fn into_response(self) -> Response {
        println!("[ApiResponse] 转换为 HTTP 响应");
        println!("[ApiResponse] code: {}, msg: {}", self.code, self.msg);

        // 手动序列化为 JSON
        let json_string = match serde_json::to_string(&self) {
            Ok(s) => {
                println!("[ApiResponse] JSON 序列化成功");
                s
            }
            Err(e) => {
                println!("[ApiResponse] JSON 序列化失败: {}", e);
                format!(r#"{{"code":1,"msg":"序列化失败: {}","data":null}}"#, e)
            }
        };

        // 创建响应
        Response::builder()
            .status(StatusCode::OK)
            .header("Content-Type", "application/json")
            .body(Body::from(json_string))
            .unwrap()
    }
}

// 为了能序列化，手动实现 Serialize
impl<T: Serialize> Serialize for ApiResponse<T> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("ApiResponse", 3)?;
        state.serialize_field("code", &self.code)?;
        state.serialize_field("msg", &self.msg)?;
        state.serialize_field("data", &self.data)?;
        state.end()
    }
}
```

### 模板3：Handler 函数（handlers/user.rs）

```rust
// 文件：handlers/user.rs
// 说明：用户相关的 API 处理器
// 创建时间：2026-01-16

use axum::{
    response::Response,
    http::{Request, StatusCode},
    body::Body,
};
use crate::response::ApiResponse;
use crate::models::User;

// Handler：获取用户列表
// 路由：GET /api/user/list
// 返回：用户列表
pub async fn list_users(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：获取用户列表 ==========");
    println!("[list_users] 请求方法: {}", req.method());
    println!("[list_users] 请求路径: {}", req.uri());

    // 步骤1：查询用户列表（这里模拟）
    println!("[list_users] 步骤1：查询用户列表");
    let users = vec![
        User {
            id: 1,
            username: String::from("admin"),
            email: String::from("admin@example.com"),
        },
        User {
            id: 2,
            username: String::from("test"),
            email: String::from("test@example.com"),
        },
    ];
    println!("[list_users] 查询到 {} 个用户", users.len());

    // 步骤2：返回响应
    println!("[list_users] 步骤2：返回响应");
    let response = ApiResponse::success(users);

    println!("[list_users] 处理完成");
    println!("==========================================\n");

    response.into_response()
}

// Handler：获取单个用户
// 路由：GET /api/user/get/:id
// 返回：用户信息
pub async fn get_user(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：获取用户 ==========");
    println!("[get_user] 请求路径: {}", req.uri());

    // 步骤1：提取路径参数
    println!("[get_user] 步骤1：提取用户ID");
    let uri_path = req.uri().path();
    let id_str = match extract_id_from_path(uri_path) {
        Ok(s) => {
            println!("[get_user] 提取到ID字符串: {}", s);
            s
        }
        Err(e) => {
            println!("[get_user] 提取ID失败: {}", e);
            let response = ApiResponse::<()>::error(e);
            return response.into_response();
        }
    };

    // 步骤2：转换为数字
    println!("[get_user] 步骤2：转换ID为数字");
    let user_id = match id_str.parse::<i64>() {
        Ok(id) => {
            println!("[get_user] 转换成功，ID: {}", id);
            id
        }
        Err(e) => {
            let error_msg = format!("ID格式错误: {}", e);
            println!("[get_user] {}", error_msg);
            let response = ApiResponse::<()>::error(error_msg);
            return response.into_response();
        }
    };

    // 步骤3：查询用户（模拟）
    println!("[get_user] 步骤3：查询用户");
    let user = User {
        id: user_id,
        username: String::from("test_user"),
        email: String::from("test@example.com"),
    };
    println!("[get_user] 查询成功: {:?}", user);

    // 步骤4：返回响应
    println!("[get_user] 步骤4：返回响应");
    let response = ApiResponse::success(user);

    println!("[get_user] 处理完成");
    println!("======================================\n");

    response.into_response()
}

// Handler：创建用户
// 路由：POST /api/user/create
// 请求体：JSON格式的用户信息
// 返回：创建结果
pub async fn create_user(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：创建用户 ==========");

    // 步骤1：读取请求体
    println!("[create_user] 步骤1：读取请求体");
    let body_bytes = match read_body_bytes(req).await {
        Ok(bytes) => {
            println!("[create_user] 读取到 {} 字节", bytes.len());
            bytes
        }
        Err(e) => {
            println!("[create_user] 读取请求体失败: {}", e);
            let response = ApiResponse::<()>::error(e);
            return response.into_response();
        }
    };

    // 步骤2：解析 JSON
    println!("[create_user] 步骤2：解析 JSON");
    let user: User = match serde_json::from_slice(&body_bytes) {
        Ok(u) => {
            println!("[create_user] 解析成功: {:?}", u);
            u
        }
        Err(e) => {
            let error_msg = format!("JSON 解析失败: {}", e);
            println!("[create_user] {}", error_msg);
            let response = ApiResponse::<()>::error(error_msg);
            return response.into_response();
        }
    };

    // 步骤3：保存用户（模拟）
    println!("[create_user] 步骤3：保存用户");
    // TODO: 实际保存到数据库
    println!("[create_user] 保存成功");

    // 步骤4：返回响应
    println!("[create_user] 步骤4：返回响应");
    let result = CreateUserResult {
        success: true,
        user_id: user.id,
    };
    let response = ApiResponse::success(result);

    println!("[create_user] 处理完成");
    println!("======================================\n");

    response.into_response()
}

// Handler：更新用户
// 路由：POST /api/user/update
pub async fn update_user(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：更新用户 ==========");

    // 类似 create_user，步骤相同
    // 1. 读取请求体
    // 2. 解析 JSON
    // 3. 更新数据库
    // 4. 返回响应

    let response = ApiResponse::success(UpdateResult {
        success: true,
        message: String::from("更新成功"),
    });

    println!("[update_user] 处理完成");
    println!("======================================\n");

    response.into_response()
}

// Handler：删除用户
// 路由：POST /api/user/delete/:id
pub async fn delete_user(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：删除用户 ==========");

    // 步骤1：提取用户ID（同 get_user）
    // 步骤2：删除用户
    // 步骤3：返回响应

    let response = ApiResponse::success(DeleteResult {
        success: true,
        message: String::from("删除成功"),
    });

    println!("[delete_user] 处理完成");
    println!("======================================\n");

    response.into_response()
}

// ==================== 辅助函数 ====================

// 从路径中提取ID
// 参数：path - 请求路径，如 "/api/user/get/123"
// 返回：成功返回 ID 字符串，失败返回错误信息
fn extract_id_from_path(path: &str) -> Result<String, String> {
    println!("[extract_id_from_path] 解析路径: {}", path);

    // 按 / 分割
    let parts: Vec<&str> = path.split('/').collect();
    println!("[extract_id_from_path] 路径部分数量: {}", parts.len());

    // 最后一部分应该是ID
    if parts.len() > 0 {
        let id_part = parts[parts.len() - 1];
        println!("[extract_id_from_path] 提取到: {}", id_part);
        Ok(String::from(id_part))
    } else {
        let error = String::from("路径格式错误");
        println!("[extract_id_from_path] 错误: {}", error);
        Err(error)
    }
}

// 读取请求体的字节数据
// 参数：req - HTTP 请求
// 返回：成功返回字节数组，失败返回错误信息
async fn read_body_bytes(req: Request<Body>) -> Result<Vec<u8>, String> {
    println!("[read_body_bytes] 开始读取请求体");

    use http_body_util::BodyExt;

    let body = req.into_body();
    let collected = match body.collect().await {
        Ok(c) => {
            println!("[read_body_bytes] 收集完成");
            c
        }
        Err(e) => {
            let error = format!("读取请求体失败: {}", e);
            println!("[read_body_bytes] 错误: {}", error);
            return Err(error);
        }
    };

    let bytes = collected.to_bytes();
    println!("[read_body_bytes] 读取到 {} 字节", bytes.len());
    Ok(bytes.to_vec())
}

// ==================== 返回数据结构 ====================

use serde::Serialize;

#[derive(Serialize)]
struct CreateUserResult {
    success: bool,
    user_id: i64,
}

#[derive(Serialize)]
struct UpdateResult {
    success: bool,
    message: String,
}

#[derive(Serialize)]
struct DeleteResult {
    success: bool,
    message: String,
}
```

### 模板4：数据模型（models.rs）

```rust
// 文件：models.rs
// 说明：定义所有数据结构
// 创建时间：2026-01-16

use serde::{Serialize, Deserialize};

// ==================== User ====================

// 数据结构：用户
pub struct User {
    pub id: i64,
    pub username: String,
    pub email: String,
}

// 实现 Debug（用于打印）
impl std::fmt::Debug for User {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "User{{ id:{}, username:{}, email:{} }}",
               self.id, self.username, self.email)
    }
}

// 实现 Clone（用于复制）
impl Clone for User {
    fn clone(&self) -> Self {
        User {
            id: self.id,
            username: self.username.clone(),
            email: self.email.clone(),
        }
    }
}

// 实现 Serialize（用于转 JSON）
impl Serialize for User {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("User", 3)?;
        state.serialize_field("id", &self.id)?;
        state.serialize_field("username", &self.username)?;
        state.serialize_field("email", &self.email)?;
        state.end()
    }
}

// 实现 Deserialize（用于从 JSON 解析）
impl<'de> Deserialize<'de> for User {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        use serde::de::{self, MapAccess, Visitor};
        use std::fmt;

        struct UserVisitor;

        impl<'de> Visitor<'de> for UserVisitor {
            type Value = User;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct User")
            }

            fn visit_map<V>(self, mut map: V) -> Result<User, V::Error>
            where
                V: MapAccess<'de>,
            {
                let mut id = None;
                let mut username = None;
                let mut email = None;

                while let Some(key) = map.next_key::<String>()? {
                    match key.as_str() {
                        "id" => {
                            id = Some(map.next_value()?);
                        }
                        "username" => {
                            username = Some(map.next_value()?);
                        }
                        "email" => {
                            email = Some(map.next_value()?);
                        }
                        _ => {
                            let _ = map.next_value::<serde::de::IgnoredAny>()?;
                        }
                    }
                }

                let id = id.ok_or_else(|| de::Error::missing_field("id"))?;
                let username = username.ok_or_else(|| de::Error::missing_field("username"))?;
                let email = email.ok_or_else(|| de::Error::missing_field("email"))?;

                Ok(User { id, username, email })
            }
        }

        deserializer.deserialize_struct("User", &["id", "username", "email"], UserVisitor)
    }
}

// ==================== Device ====================

// 数据结构：设备
pub struct Device {
    pub id: String,
    pub mac_address: String,
    pub user_id: i64,
}

// 类似 User，实现 Debug、Clone、Serialize、Deserialize
// ... （为了简洁省略，但实际要写）
```

### 模板5：健康检查（handlers/health.rs）

```rust
// 文件：handlers/health.rs
// 说明：健康检查接口
// 创建时间：2026-01-16

use axum::{
    response::Response,
    http::Request,
    body::Body,
};
use crate::response::ApiResponse;
use serde::Serialize;

// Handler：健康检查
// 路由：GET /health
// 返回：服务状态
pub async fn health_check(_req: Request<Body>) -> Response {
    println!("[health_check] 健康检查");

    let health = HealthStatus {
        status: String::from("ok"),
        timestamp: get_current_timestamp(),
    };

    let response = ApiResponse::success(health);
    response.into_response()
}

#[derive(Serialize)]
struct HealthStatus {
    status: String,
    timestamp: String,
}

// 获取当前时间戳（简化版）
fn get_current_timestamp() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};

    let now = SystemTime::now();
    let since_epoch = now.duration_since(UNIX_EPOCH).unwrap();
    let seconds = since_epoch.as_secs();

    format!("{}", seconds)
}
```

---

## 第五章：认证处理（简化版 JWT）

### 认证 Handler（handlers/auth.rs）

```rust
// 文件：handlers/auth.rs
// 说明：认证相关接口
// 创建时间：2026-01-16

use axum::{
    response::Response,
    http::Request,
    body::Body,
};
use crate::response::ApiResponse;
use serde::{Serialize, Deserialize};

// Handler：用户登录
// 路由：POST /api/auth/login
// 请求体：{"username": "admin", "password": "123456"}
// 返回：{"token": "xxx"}
pub async fn login(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：用户登录 ==========");

    // 步骤1：读取请求体
    println!("[login] 步骤1：读取请求体");
    let body_bytes = match read_body_bytes(req).await {
        Ok(bytes) => bytes,
        Err(e) => {
            let response = ApiResponse::<()>::error(e);
            return response.into_response();
        }
    };

    // 步骤2：解析登录请求
    println!("[login] 步骤2：解析登录请求");
    let login_req: LoginRequest = match serde_json::from_slice(&body_bytes) {
        Ok(req) => {
            println!("[login] 用户名: {}", req.username);
            req
        }
        Err(e) => {
            let error = format!("JSON 解析失败: {}", e);
            let response = ApiResponse::<()>::error(error);
            return response.into_response();
        }
    };

    // 步骤3：验证用户名密码（模拟）
    println!("[login] 步骤3：验证用户名密码");
    if login_req.username != "admin" || login_req.password != "123456" {
        println!("[login] 用户名或密码错误");
        let response = ApiResponse::<()>::error(String::from("用户名或密码错误"));
        return response.into_response();
    }
    println!("[login] 验证成功");

    // 步骤4：生成 token（简化版，实际应该用 JWT 库）
    println!("[login] 步骤4：生成 token");
    let token = generate_simple_token(&login_req.username);
    println!("[login] token: {}", token);

    // 步骤5：返回响应
    println!("[login] 步骤5：返回响应");
    let result = LoginResponse { token };
    let response = ApiResponse::success(result);

    println!("[login] 处理完成");
    println!("====================================\n");

    response.into_response()
}

// 验证 token 的辅助函数
// 在需要认证的 Handler 中调用
// 参数：req - HTTP 请求
// 返回：成功返回 user_id，失败返回错误信息
pub fn verify_token(req: &Request<Body>) -> Result<i64, String> {
    println!("[verify_token] 开始验证 token");

    // 步骤1：从 Header 中获取 Authorization
    let auth_header = match req.headers().get("Authorization") {
        Some(h) => {
            match h.to_str() {
                Ok(s) => {
                    println!("[verify_token] 获取到 Authorization: {}", s);
                    s
                }
                Err(e) => {
                    let error = format!("Authorization 格式错误: {}", e);
                    println!("[verify_token] 错误: {}", error);
                    return Err(error);
                }
            }
        }
        None => {
            let error = String::from("缺少 Authorization header");
            println!("[verify_token] 错误: {}", error);
            return Err(error);
        }
    };

    // 步骤2：提取 token（格式：Bearer xxx）
    let token = if auth_header.starts_with("Bearer ") {
        let t = &auth_header[7..];
        println!("[verify_token] 提取到 token: {}", t);
        t
    } else {
        let error = String::from("Authorization 格式错误，应为 Bearer token");
        println!("[verify_token] 错误: {}", error);
        return Err(error);
    };

    // 步骤3：验证 token（简化版，实际应该解析 JWT）
    println!("[verify_token] 步骤3：验证 token");
    if token.len() < 10 {
        let error = String::from("token 无效");
        println!("[verify_token] 错误: {}", error);
        return Err(error);
    }

    // 步骤4：返回用户ID（模拟）
    println!("[verify_token] 验证成功");
    Ok(1)  // 返回用户ID
}

// ==================== 辅助函数 ====================

// 读取请求体
async fn read_body_bytes(req: Request<Body>) -> Result<Vec<u8>, String> {
    use http_body_util::BodyExt;

    let body = req.into_body();
    let collected = body.collect().await
        .map_err(|e| format!("读取请求体失败: {}", e))?;

    Ok(collected.to_bytes().to_vec())
}

// 生成简单 token（实际应该用 JWT）
fn generate_simple_token(username: &str) -> String {
    use std::time::{SystemTime, UNIX_EPOCH};

    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();

    format!("{}_{}", username, timestamp)
}

// ==================== 数据结构 ====================

#[derive(Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize)]
struct LoginResponse {
    token: String,
}
```

### 在受保护的 Handler 中使用认证

```rust
// 示例：需要认证的接口
pub async fn protected_handler(req: Request<Body>) -> Response {
    println!("[protected_handler] 需要认证的接口");

    // 步骤1：验证 token
    println!("[protected_handler] 步骤1：验证 token");
    let user_id = match crate::handlers::auth::verify_token(&req) {
        Ok(id) => {
            println!("[protected_handler] 认证成功，用户ID: {}", id);
            id
        }
        Err(e) => {
            println!("[protected_handler] 认证失败: {}", e);
            let response = ApiResponse::<()>::error(String::from("未授权"));
            return response.into_response();
        }
    };

    // 步骤2：执行业务逻辑
    println!("[protected_handler] 步骤2：执行业务逻辑");
    // ... 业务代码

    // 步骤3：返回响应
    let response = ApiResponse::success("处理成功");
    response.into_response()
}
```

---

## 第六章：调试和错误排查

### 1. 启动服务

```bash
# 开发模式运行（有详细日志）
cargo run

# 看到输出：
========== xiaozhi-cfg-api 启动 ==========

[main] 步骤1：加载配置
[load_config] 加载环境变量
[load_config] 配置加载完成
[main] 步骤2：初始化数据库
[main] 步骤3：创建路由
[create_router] 创建路由
[main] 步骤4：启动服务器
[main] 服务器监听地址: 0.0.0.0:8002
[main] 服务器启动成功！
========================================
```

### 2. 测试接口

```bash
# 健康检查
curl http://localhost:8002/health

# 看到日志：
[health_check] 健康检查

# 返回：
{"code":0,"msg":"success","data":{"status":"ok","timestamp":"1705401234"}}
```

### 3. 测试登录

```bash
# 登录
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'

# 看到日志：
========== 处理请求：用户登录 ==========
[login] 步骤1：读取请求体
[login] 步骤2：解析登录请求
[login] 用户名: admin
[login] 步骤3：验证用户名密码
[login] 验证成功
[login] 步骤4：生成 token
[login] token: admin_1705401234
[login] 步骤5：返回响应
[login] 处理完成
====================================

# 返回：
{"code":0,"msg":"success","data":{"token":"admin_1705401234"}}
```

### 4. 测试用户查询

```bash
# 获取用户
curl http://localhost:8002/api/user/get/123

# 看到日志：
========== 处理请求：获取用户 ==========
[get_user] 请求路径: /api/user/get/123
[get_user] 步骤1：提取用户ID
[extract_id_from_path] 解析路径: /api/user/get/123
[extract_id_from_path] 路径部分数量: 5
[extract_id_from_path] 提取到: 123
[get_user] 提取到ID字符串: 123
[get_user] 步骤2：转换ID为数字
[get_user] 转换成功，ID: 123
[get_user] 步骤3：查询用户
[get_user] 查询成功: User{ id:123, username:test_user, email:test@example.com }
[get_user] 步骤4：返回响应
[get_user] 处理完成
======================================
```

### 5. 常见错误和日志输出

**错误1：路径参数错误**
```
[get_user] 请求路径: /api/user/get/abc
[get_user] 步骤2：转换ID为数字
[get_user] ID格式错误: invalid digit found in string
[get_user] 处理完成
```

**错误2：JSON 解析失败**
```
[create_user] 步骤2：解析 JSON
[create_user] JSON 解析失败: expected value at line 1 column 1
```

**错误3：认证失败**
```
[verify_token] 开始验证 token
[verify_token] 错误: 缺少 Authorization header
```

---

## 第七章：给 AI 的具体指令

### 生成 Axum 代码时必须遵守：

1. **所有 Handler 函数签名统一**
```rust
pub async fn handler_name(req: Request<Body>) -> Response {
    // 实现
}
```

2. **不要用提取器（Path、Query、Json）**
```rust
// 禁止
async fn handler(Path(id): Path<i64>) -> Response { }

// 推荐
async fn handler(req: Request<Body>) -> Response {
    // 手动解析
}
```

3. **每个 Handler 都要打印日志**
```rust
pub async fn handler(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：XXX ==========");
    println!("[handler] 步骤1：...");
    // ...
    println!("[handler] 处理完成");
    println!("======================================\n");
}
```

4. **所有响应都用统一格式**
```rust
let response = ApiResponse::success(data);
// 或
let response = ApiResponse::<()>::error(String::from("错误信息"));

return response.into_response();
```

5. **手动解析请求数据**
```rust
// 解析路径参数
let id = extract_id_from_path(req.uri().path())?;

// 解析请求体
let body_bytes = read_body_bytes(req).await?;
let data: MyStruct = serde_json::from_slice(&body_bytes)?;

// 解析查询参数
let query = req.uri().query().unwrap_or("");
// 手动解析 query 字符串
```

6. **不要用 State 共享状态**
```rust
// 如果需要共享数据，用简单的全局变量
use std::sync::Mutex;
use lazy_static::lazy_static;

lazy_static! {
    static ref SHARED_DATA: Mutex<MyData> = Mutex::new(MyData::new());
}

// 在 Handler 中使用
let data = SHARED_DATA.lock().unwrap();
```

7. **路由定义要清晰**
```rust
// 在 main.rs 的 create_router 中
Router::new()
    .route("/api/user/list", get(handlers::user::list_users))
    .route("/api/user/get/:id", get(handlers::user::get_user))
    .route("/api/user/create", post(handlers::user::create_user))
```

8. **错误处理要详细**
```rust
// 每个可能出错的地方都要 match
match some_operation() {
    Ok(result) => {
        println!("成功");
        result
    }
    Err(e) => {
        let error = format!("操作失败: {}", e);
        println!("错误: {}", error);
        let response = ApiResponse::<()>::error(error);
        return response.into_response();
    }
}
```

---

## 第八章：完整示例项目

### 项目文件清单

```
xiaozhi-cfg-api/
├── Cargo.toml
├── .env
├── src/
│   ├── main.rs              # 已提供
│   ├── response.rs          # 已提供
│   ├── models.rs            # 已提供
│   └── handlers/
│       ├── mod.rs           # 见下文
│       ├── health.rs        # 已提供
│       ├── user.rs          # 已提供
│       └── auth.rs          # 已提供
```

### handlers/mod.rs

```rust
// 文件：handlers/mod.rs
// 说明：handlers 模块入口
// 创建时间：2026-01-16

pub mod health;
pub mod user;
pub mod auth;
pub mod device;
```

### .env 文件

```bash
# 服务器配置
PORT=8002

# EloqKV 配置
ELOQKV_URL=localhost:6379
ELOQKV_USER=default
ELOQKV_PASSWORD=your_password

# JWT 配置（如果使用真正的 JWT）
JWT_SECRET=your-secret-key
```

### 启动和测试

```bash
# 1. 编译
cargo build

# 2. 运行
cargo run

# 3. 测试健康检查
curl http://localhost:8002/health

# 4. 测试登录
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'

# 5. 测试用户查询（带认证）
TOKEN="admin_1705401234"
curl http://localhost:8002/api/user/list \
  -H "Authorization: Bearer $TOKEN"
```

---

## 第九章：与 EloqKV 集成

### db.rs（EloqKV 客户端）

```rust
// 文件：db.rs
// 说明：EloqKV 数据库客户端
// 创建时间：2026-01-16

use std::env;

// EloqKV 客户端结构
pub struct EloqClient {
    url: String,
    user: String,
    password: String,
}

impl EloqClient {
    // 创建客户端
    pub fn new() -> Self {
        println!("[EloqClient::new] 创建 EloqKV 客户端");

        let url = env::var("ELOQKV_URL").unwrap_or(String::from("localhost:6379"));
        let user = env::var("ELOQKV_USER").unwrap_or(String::from("default"));
        let password = env::var("ELOQKV_PASSWORD").unwrap_or(String::from(""));

        println!("[EloqClient::new] 连接地址: {}", url);

        Self { url, user, password }
    }

    // 获取值
    // 参数：key - 键
    // 返回：成功返回值，失败返回错误信息
    pub fn get(&self, key: &str) -> Result<String, String> {
        println!("[EloqClient::get] 获取 key: {}", key);

        // TODO: 实现真正的 EloqKV GET 操作
        // 这里模拟返回
        let value = format!("value_for_{}", key);

        println!("[EloqClient::get] 返回值: {}", value);
        Ok(value)
    }

    // 设置值
    // 参数：key - 键, value - 值
    // 返回：成功返回 ()，失败返回错误信息
    pub fn set(&self, key: &str, value: &str) -> Result<(), String> {
        println!("[EloqClient::set] 设置 key: {}, value: {}", key, value);

        // TODO: 实现真正的 EloqKV SET 操作

        println!("[EloqClient::set] 设置成功");
        Ok(())
    }

    // 删除值
    pub fn delete(&self, key: &str) -> Result<(), String> {
        println!("[EloqClient::delete] 删除 key: {}", key);

        // TODO: 实现真正的 EloqKV DEL 操作

        println!("[EloqClient::delete] 删除成功");
        Ok(())
    }
}
```

### 在 Handler 中使用 EloqKV

```rust
// 示例：在 user.rs 中使用 EloqKV
pub async fn get_user(req: Request<Body>) -> Response {
    println!("[get_user] 开始处理");

    // 步骤1：提取用户ID
    let user_id = /* ... 提取逻辑 */;

    // 步骤2：从 EloqKV 查询
    println!("[get_user] 步骤2：从数据库查询");
    let client = crate::db::EloqClient::new();
    let key = format!("user:{}", user_id);

    let user_json = match client.get(&key) {
        Ok(json) => {
            println!("[get_user] 查询成功");
            json
        }
        Err(e) => {
            println!("[get_user] 查询失败: {}", e);
            let response = ApiResponse::<()>::error(e);
            return response.into_response();
        }
    };

    // 步骤3：解析 JSON
    let user: User = match serde_json::from_str(&user_json) {
        Ok(u) => u,
        Err(e) => {
            let error = format!("JSON 解析失败: {}", e);
            let response = ApiResponse::<()>::error(error);
            return response.into_response();
        }
    };

    // 步骤4：返回响应
    let response = ApiResponse::success(user);
    response.into_response()
}
```

---

## 第十章：问题排查清单

### 编译错误

**错误1：找不到模块**
```
error[E0583]: file not found for module `handlers`
```
解决：检查文件结构，确保 handlers/mod.rs 存在

**错误2：类型不匹配**
```
expected `Response`, found `()`
```
解决：确保 Handler 返回 `Response`，使用 `.into_response()`

### 运行时错误

**错误1：端口被占用**
```
[main] 服务器运行失败: Address already in use
```
解决：
1. 检查端口 8002 是否被占用：`lsof -i :8002`
2. 杀掉占用进程或换一个端口

**错误2：找不到 .env 文件**
```
[load_config] 警告：无法加载 .env 文件: ...
```
解决：
1. 创建 .env 文件
2. 或者直接设置环境变量：`export PORT=8002`

### API 测试错误

**错误1：404 Not Found**
```
curl http://localhost:8002/api/user/list
# 返回 404
```
解决：
1. 检查路由是否注册：看 create_router() 函数
2. 检查路径是否正确

**错误2：500 Internal Server Error**
看日志输出，找到出错的步骤：
```
[handler] 步骤1：成功
[handler] 步骤2：失败 <-- 在这里出错
```

---

## 总结

### 核心原则

1. **Handler 签名统一**：`async fn(Request<Body>) -> Response`
2. **不用提取器**：手动解析所有数据
3. **不用 State**：用简单的全局变量或在 main 中传递
4. **统一响应格式**：ApiResponse::success / error
5. **详细日志**：每个步骤都打印
6. **简单直接**：不用 Axum 的高级特性

### 代码模板总结

```rust
// Handler 模板
pub async fn handler_name(req: Request<Body>) -> Response {
    println!("\n========== 处理请求：XXX ==========");

    // 步骤1：提取参数
    // 步骤2：验证权限（如需要）
    // 步骤3：业务逻辑
    // 步骤4：返回响应

    let response = ApiResponse::success(data);
    println!("[handler_name] 处理完成\n");
    response.into_response()
}
```

### 开发流程

1. 定义数据结构（models.rs）
2. 实现 Service 层（services/）
3. 创建 Handler（handlers/）
4. 注册路由（main.rs）
5. 测试接口（curl）
6. 查看日志排查问题

记住：**简单、清晰、可追踪**，这样 AI 生成的代码你也能看懂和维护。
