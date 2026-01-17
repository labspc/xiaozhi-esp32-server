# ORica 兼容层设计方案

## 文档目的

设计一个**零停机、渐进式重构**的兼容层，允许：
- ✅ 旧客户端（xiaozhi 路径）继续正常工作
- ✅ 新客户端（orica 路径）可以立即使用
- ✅ 内部代码逐步从 xiaozhi 迁移到 orica
- ✅ 最终平滑废弃 xiaozhi 路径

**核心理念**：双路径并存 → 渐进迁移 → 优雅废弃

---

## 架构设计

### 整体兼容层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     客户端层（多版本共存）                      │
├─────────────────────────────────────────────────────────────┤
│  旧固件                │  新固件               │  前端/移动端   │
│  ws://.../xiaozhi/v1/ │  ws://.../orica/v1/  │  可配置路径    │
└──────────┬──────────────┴──────────┬────────────────────────┘
           │                         │
           ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  兼容层（路径映射 + 别名）                     │
├─────────────────────────────────────────────────────────────┤
│  WebSocket 路由:                                             │
│    /xiaozhi/v1/  ──┐                                        │
│                    ├──→  统一处理器 (ConnectionHandler)      │
│    /orica/v1/    ──┘                                        │
│                                                             │
│  HTTP API 路由:                                             │
│    /xiaozhi/*    ──┐                                        │
│                    ├──→  Spring Controller                  │
│    /orica/*      ──┘                                        │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│              核心业务层（逐步重构 package 名）                 │
├─────────────────────────────────────────────────────────────┤
│  第一阶段: xiaozhi.modules.*                                 │
│  第二阶段: orica.modules.* + xiaozhi 别名（deprecated）      │
│  第三阶段: 仅 orica.modules.*                                │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                  数据层（无需修改）                           │
│              数据库表名、字段名保持不变                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 第一层：WebSocket 兼容层

### 方案：双路径注册 + 统一处理器

**目标**：让 `/xiaozhi/v1/` 和 `/orica/v1/` 都能连接到同一个处理器

#### 实现代码（Python xiaozhi-server）

```python
# main/xiaozhi-server/core/websocket_server.py

class WebSocketServer:
    def __init__(self, config):
        self.config = config
        self.app = web.Application()

        # 🔥 关键：注册双路径，指向同一个处理器
        self.app.router.add_get('/xiaozhi/v1/', self.websocket_handler)  # 旧路径
        self.app.router.add_get('/orica/v1/', self.websocket_handler)    # 新路径

        logger.info("WebSocket 双路径已启用:")
        logger.info("  旧路径: ws://{}:{}/xiaozhi/v1/")
        logger.info("  新路径: ws://{}:{}/orica/v1/")

    async def websocket_handler(self, request):
        """统一的 WebSocket 处理器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # 从请求路径判断是旧客户端还是新客户端（可选，用于统计）
        path = request.path
        client_type = "legacy" if "xiaozhi" in path else "new"
        logger.info(f"客户端连接: {client_type} from {path}")

        # 创建连接处理器（核心逻辑不变）
        connection_handler = ConnectionHandler(ws, self.config)
        await connection_handler.handle()

        return ws
```

#### 配置兼容性

```yaml
# main/xiaozhi-server/config.yaml

# 保留旧配置向后兼容
websocket: ws://你的ip:8000/xiaozhi/v1/

# 新增 ORica 配置（可选）
websocket_new: ws://你的ip:8000/orica/v1/

# 或者使用数组支持多个地址
websocket_urls:
  - ws://你的ip:8000/xiaozhi/v1/  # 兼容旧固件
  - ws://你的ip:8000/orica/v1/    # 新固件使用
```

#### HTTP 配置返回兼容

```python
# main/xiaozhi-server/core/http_server.py

class HttpServer:
    def get_websocket_url(self):
        """根据客户端请求返回对应的 WebSocket URL"""
        config_ws = self.config.get('websocket')

        if config_ws:
            return config_ws
        else:
            # 默认返回新路径，但旧路径也能用
            local_ip = get_local_ip()
            port = self.config.get('websocket_port', 8000)

            # 🔥 可以根据请求头判断返回哪个路径
            # 例如：User-Agent 包含 "xiaozhi-v1" 返回旧路径
            return f"ws://{local_ip}:{port}/orica/v1/"  # 默认返回新路径
```

---

## 第二层：HTTP API 兼容层

### 方案：Spring Boot 双 Context Path

**目标**：让 `/xiaozhi/*` 和 `/orica/*` 都能访问同一套 API

#### 方案 A：Nginx 反向代理（推荐，零代码修改）

```nginx
# /etc/nginx/conf.d/orica.conf

server {
    listen 80;
    server_name your-domain.com;

    # 新路径：/orica/* → 后端 /xiaozhi/*
    location /orica/ {
        # 🔥 关键：重写路径，将 /orica 替换为 /xiaozhi
        rewrite ^/orica/(.*) /xiaozhi/$1 break;
        proxy_pass http://localhost:8002;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Original-Path "orica";  # 标记原始路径
    }

    # 旧路径：/xiaozhi/* → 后端 /xiaozhi/*（直接透传）
    location /xiaozhi/ {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Original-Path "xiaozhi";  # 标记原始路径
    }

    # WebSocket 支持
    location /orica/v1/ {
        rewrite ^/orica/v1/(.*) /xiaozhi/v1/$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /xiaozhi/v1/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**优点**：
- ✅ 零代码修改，立即生效
- ✅ 性能损耗极小
- ✅ 易于回滚（修改 Nginx 配置即可）

**缺点**：
- ❌ 需要 Nginx（但部署时通常都有）

---

#### 方案 B：Spring Boot Filter（无 Nginx 时使用）

```java
// main/manager-api/src/main/java/xiaozhi/common/filter/PathCompatibilityFilter.java

package xiaozhi.common.filter;

import javax.servlet.*;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletRequestWrapper;
import java.io.IOException;

/**
 * 路径兼容过滤器：将 /orica/* 重写为 /xiaozhi/*
 */
public class PathCompatibilityFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        String requestURI = httpRequest.getRequestURI();

        // 🔥 如果是 /orica 开头，重写为 /xiaozhi
        if (requestURI.startsWith("/orica/")) {
            String newURI = requestURI.replaceFirst("^/orica/", "/xiaozhi/");

            // 包装请求，修改 URI
            HttpServletRequestWrapper wrapper = new HttpServletRequestWrapper(httpRequest) {
                @Override
                public String getRequestURI() {
                    return newURI;
                }

                @Override
                public String getServletPath() {
                    return newURI;
                }
            };

            chain.doFilter(wrapper, response);
        } else {
            chain.doFilter(request, response);
        }
    }
}
```

```java
// main/manager-api/src/main/java/xiaozhi/modules/security/config/FilterConfig.java

@Configuration
public class FilterConfig {

    @Bean
    public FilterRegistrationBean<PathCompatibilityFilter> pathCompatibilityFilter() {
        FilterRegistrationBean<PathCompatibilityFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(new PathCompatibilityFilter());
        registration.addUrlPatterns("/orica/*");  // 仅拦截 /orica 路径
        registration.setOrder(1);  // 最高优先级
        return registration;
    }
}
```

---

#### 方案 C：双 Application Context（完全隔离，不推荐）

```yaml
# main/manager-api/src/main/resources/application.yml

server:
  servlet:
    context-path: /xiaozhi  # 保持旧路径

# 可以启动两个实例（不同端口）
---
spring:
  profiles: orica
server:
  port: 8003
  servlet:
    context-path: /orica
```

**不推荐原因**：
- ❌ 需要运行两个进程
- ❌ 内存占用翻倍
- ❌ 配置复杂

---

## 第三层：Java Package 兼容层

### 方案：Module Alias + Deprecated 标记

**目标**：在 `orica.*` package 创建新代码，同时保留 `xiaozhi.*` 的别名

#### 阶段 1：创建 orica.* package，xiaozhi.* 作为别名

```java
// 新路径：main/manager-api/src/main/java/orica/modules/device/service/DeviceService.java
package orica.modules.device.service;

public interface DeviceService {
    // 新的实现
}
```

```java
// 旧路径：main/manager-api/src/main/java/xiaozhi/modules/device/service/DeviceService.java
package xiaozhi.modules.device.service;

/**
 * @deprecated 请使用 {@link orica.modules.device.service.DeviceService}
 */
@Deprecated
public interface DeviceService extends orica.modules.device.service.DeviceService {
    // 空接口，仅作为别名
}
```

**问题**：工作量太大（300+ 文件）

---

#### 阶段 2：使用 Maven Shade Plugin 重命名（推荐）

```xml
<!-- main/manager-api/pom.xml -->

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-shade-plugin</artifactId>
            <version>3.5.1</version>
            <executions>
                <execution>
                    <phase>package</phase>
                    <goals>
                        <goal>shade</goal>
                    </goals>
                    <configuration>
                        <relocations>
                            <!-- 🔥 将 xiaozhi 包重命名为 orica -->
                            <relocation>
                                <pattern>xiaozhi</pattern>
                                <shadedPattern>orica</shadedPattern>
                            </relocation>
                        </relocations>
                        <createSourcesJar>true</createSourcesJar>
                    </configuration>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

**工作流程**：
1. 开发时仍使用 `xiaozhi.*` package（保持兼容）
2. 构建时自动重命名为 `orica.*`
3. 运行时实际是 `orica.*` package

**优点**：
- ✅ 开发时无需修改代码
- ✅ 自动化重命名
- ✅ 可逐步迁移

**缺点**：
- ❌ 调试时包名可能混淆
- ❌ 增加构建复杂度

---

#### 阶段 3：IntelliJ IDEA 批量重构（最彻底）

**步骤**：

1. **创建新分支**
```bash
git checkout -b refactor/rename-to-orica
```

2. **使用 IDE 重构**
```
IntelliJ IDEA:
  右键 src/main/java/xiaozhi 目录
  → Refactor
  → Rename...
  → 输入 "orica"
  → Refactor in Comments and Strings: 取消勾选（避免修改日志）
  → Search for text occurrences: 取消勾选
  → 点击 "Refactor"
```

3. **手动修改配置**
```yaml
# application.yml
typeAliasesPackage: orica.modules.*.entity  # 从 xiaozhi 改为 orica
```

```xml
<!-- pom.xml -->
<groupId>orica</groupId>
<artifactId>orica-esp32-api</artifactId>
```

4. **全量测试**
```bash
mvn clean test
mvn spring-boot:run
```

5. **提交**
```bash
git add .
git commit -m "refactor: rename package xiaozhi to orica"
```

**时间估算**：
- IDE 自动重构：10 分钟
- 手动修改配置：30 分钟
- 全量测试：2-3 小时
- **总计：1 个工作日**

---

## 第四层：前端/移动端兼容层

### 方案：环境变量 + 配置中心

#### Vue 2 前端（manager-web）

```javascript
// main/manager-web/.env.development
VUE_APP_API_BASE_URL=/xiaozhi  # 开发环境仍用旧路径

// main/manager-web/.env.production
VUE_APP_API_BASE_URL=/orica    # 生产环境用新路径
```

```javascript
// main/manager-web/src/apis/request.js

const BASE_URL = process.env.VUE_APP_API_BASE_URL || '/xiaozhi';

// 🔥 支持运行时切换（从服务器获取配置）
let runtimeBaseUrl = BASE_URL;

export async function initApiConfig() {
    try {
        const response = await fetch('/api/config/frontend');
        const config = await response.json();
        if (config.data.apiBaseUrl) {
            runtimeBaseUrl = config.data.apiBaseUrl;
            console.log('API Base URL updated to:', runtimeBaseUrl);
        }
    } catch (err) {
        console.warn('Failed to load runtime config, using default:', BASE_URL);
    }
}

export function getApiUrl(path) {
    return `${runtimeBaseUrl}${path}`;
}
```

#### uni-app 移动端（manager-mobile）

```javascript
// main/manager-mobile/env/.env
VITE_API_BASE_URL=/orica  # 新版本使用新路径

// 或支持双路径自动探测
VITE_API_URLS=["https://example.com/orica", "https://example.com/xiaozhi"]
```

```javascript
// main/manager-mobile/src/utils/request.js

const API_URLS = import.meta.env.VITE_API_URLS
    ? JSON.parse(import.meta.env.VITE_API_URLS)
    : [import.meta.env.VITE_API_BASE_URL];

// 🔥 自动探测可用的 API 地址
async function detectAvailableApi() {
    for (const url of API_URLS) {
        try {
            const response = await fetch(`${url}/health`);
            if (response.ok) {
                console.log('Using API:', url);
                return url;
            }
        } catch (err) {
            console.warn('API unavailable:', url);
        }
    }

    // 降级到第一个地址
    return API_URLS[0];
}

export const apiBaseUrl = await detectAvailableApi();
```

---

## 第五层：数据库/配置兼容层

### 方案：数据保持不变，仅代码重命名

**重要**：数据库表名、字段名、Redis key **完全不需要修改**

```sql
-- ✅ 保持不变
CREATE TABLE `xiaozhi_device` (
    `id` BIGINT PRIMARY KEY,
    `device_code` VARCHAR(64),
    ...
);

-- ❌ 不需要重命名表
-- ALTER TABLE `xiaozhi_device` RENAME TO `orica_device`;  -- 不需要！
```

**原因**：
1. 表名是实现细节，对外部不可见
2. 修改表名需要数据迁移，风险高
3. 保持表名不变，仅修改代码层，风险最小

**Entity 映射不受影响**：
```java
// orica.modules.device.entity.DeviceEntity.java

@Data
@TableName("xiaozhi_device")  // 🔥 表名保持 xiaozhi_device
public class DeviceEntity {
    // ...
}
```

---

## 完整迁移路线图

### 阶段 0：准备工作（1 天）
- [ ] 创建新分支 `refactor/orica-compatibility`
- [ ] 备份数据库
- [ ] 在测试环境部署
- [ ] 制定回滚计划

### 阶段 1：兼容层部署（2-3 天）

**第 1 天：WebSocket 双路径**
- [ ] 修改 `websocket_server.py`，注册双路径
- [ ] 修改 `http_server.py`，返回配置支持双路径
- [ ] 测试旧固件连接 `/xiaozhi/v1/` 正常
- [ ] 测试新固件连接 `/orica/v1/` 正常

**第 2 天：HTTP API 双路径**
- [ ] 配置 Nginx 反向代理（方案 A）
  - 或者实现 `PathCompatibilityFilter`（方案 B）
- [ ] 测试 `/xiaozhi/device/list` 正常
- [ ] 测试 `/orica/device/list` 正常
- [ ] 验证 API 文档访问（/xiaozhi/doc.html 和 /orica/doc.html）

**第 3 天：前端配置更新**
- [ ] manager-web 增加环境变量配置
- [ ] manager-mobile 增加多路径探测
- [ ] 测试前端切换 API_BASE_URL 正常
- [ ] 发布新版前端（可选择新旧路径）

### 阶段 2：内部代码重构（5-7 天）

**第 4-5 天：Java Package 重命名**
- [ ] 使用 IntelliJ IDEA 批量重构 `xiaozhi` → `orica`
- [ ] 修改 `pom.xml` 的 groupId/artifactId
- [ ] 修改 `application.yml` 的 typeAliasesPackage
- [ ] 全量测试（JUnit + 集成测试）

**第 6 天：Python 项目重命名**
- [ ] 修改项目名称（可选）
- [ ] 修改配置文件中的项目标识
- [ ] 修改日志输出中的项目名

**第 7 天：Docker 镜像重命名**
- [ ] 修改 Dockerfile 中的镜像名
- [ ] 修改 docker-compose.yml 中的服务名
- [ ] 重新构建镜像：`docker build -t orica-server`
- [ ] 更新 CI/CD 流水线

### 阶段 3：客户端迁移（4-8 周）

**第 1-2 周：发布新版固件**
- [ ] 发布使用 `/orica/v1/` 的新固件
- [ ] 提供 OTA 升级机制
- [ ] 监控升级进度

**第 3-4 周：发布新版前端/移动端**
- [ ] 发布使用 `/orica` API 的新版前端
- [ ] 发布新版移动端 APP
- [ ] 更新文档和教程

**第 5-8 周：监控迁移进度**
- [ ] 监控旧路径访问量（通过日志或 Nginx 统计）
- [ ] 当旧路径访问量 < 5% 时，准备废弃
- [ ] 发布废弃公告（提前 2 周）

### 阶段 4：废弃旧路径（1-2 周）

**第 1 周：添加弃用警告**
```python
# websocket_server.py
async def websocket_handler(self, request):
    if "xiaozhi" in request.path:
        logger.warning("⚠️  /xiaozhi/v1/ 已弃用，请升级到 /orica/v1/")
        # 可选：在响应头添加警告
        # response.headers['X-Deprecated-Path'] = 'true'
```

**第 2 周：移除旧路径**
```python
# 仅保留新路径
self.app.router.add_get('/orica/v1/', self.websocket_handler)
# self.app.router.add_get('/xiaozhi/v1/', ...)  # 删除
```

```nginx
# Nginx 返回 410 Gone
location /xiaozhi/ {
    return 410 "This path has been permanently removed. Please use /orica/ instead.";
}
```

---

## 监控和回滚策略

### 监控指标

**关键指标**：
```python
# 添加路径使用统计
from collections import defaultdict

path_stats = defaultdict(int)

async def websocket_handler(self, request):
    path = request.path
    path_stats[path] += 1

    # 定期输出统计
    if sum(path_stats.values()) % 100 == 0:
        total = sum(path_stats.values())
        logger.info("路径使用统计:")
        for p, count in path_stats.items():
            percentage = (count / total) * 100
            logger.info(f"  {p}: {count} ({percentage:.2f}%)")
```

**监控日志示例**：
```
路径使用统计:
  /xiaozhi/v1/: 850 (85.00%)
  /orica/v1/: 150 (15.00%)

# 2周后
路径使用统计:
  /xiaozhi/v1/: 120 (12.00%)
  /orica/v1/: 880 (88.00%)

# 6周后
路径使用统计:
  /xiaozhi/v1/: 15 (1.50%)
  /orica/v1/: 985 (98.50%)
```

### 回滚策略

**紧急回滚（1 小时内）**：
```bash
# 1. 回滚代码
git revert <commit-hash>

# 2. 重启服务
docker-compose down
docker-compose up -d

# 3. 恢复 Nginx 配置
sudo cp /etc/nginx/conf.d/orica.conf.bak /etc/nginx/conf.d/orica.conf
sudo nginx -s reload
```

**数据回滚（如果有数据迁移）**：
```bash
# 恢复数据库备份
mysql -u root -p xiaozhi_db < backup_before_migration.sql

# 恢复 Redis
redis-cli --rdb /path/to/backup.rdb
```

---

## 风险控制清单

### 部署前检查

- [ ] ✅ 在测试环境完整验证双路径
- [ ] ✅ 备份数据库（至少保留 30 天）
- [ ] ✅ 准备回滚脚本和文档
- [ ] ✅ 通知用户即将发布新版本
- [ ] ✅ 选择低峰期部署（如凌晨 2-4 点）

### 部署时监控

- [ ] ✅ 实时监控错误日志
- [ ] ✅ 监控 WebSocket 连接成功率
- [ ] ✅ 监控 API 响应时间和错误率
- [ ] ✅ 监控数据库连接池状态
- [ ] ✅ 准备随时回滚

### 部署后验证

- [ ] ✅ 验证旧固件仍能连接
- [ ] ✅ 验证新固件能连接
- [ ] ✅ 验证前端 API 调用正常
- [ ] ✅ 验证移动端正常
- [ ] ✅ 验证 OTA 升级正常
- [ ] ✅ 验证权限控制正常

---

## 配置示例

### 完整的 Nginx 配置

```nginx
# /etc/nginx/conf.d/orica.conf

upstream orica_backend {
    server localhost:8002;
}

upstream orica_websocket {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 请求日志（记录原始路径）
    log_format path_tracking '$remote_addr - $request_uri - $http_user_agent';
    access_log /var/log/nginx/orica_paths.log path_tracking;

    # ===== HTTP API 双路径 =====

    # 新路径（推荐）
    location /orica/ {
        rewrite ^/orica/(.*) /xiaozhi/$1 break;
        proxy_pass http://orica_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Original-Path "orica";
    }

    # 旧路径（兼容）
    location /xiaozhi/ {
        proxy_pass http://orica_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Original-Path "xiaozhi";

        # 添加弃用警告头（可选）
        add_header X-Deprecated-API "true" always;
        add_header X-Deprecation-Info "Please migrate to /orica/" always;
    }

    # ===== WebSocket 双路径 =====

    # 新路径（推荐）
    location /orica/v1/ {
        rewrite ^/orica/v1/(.*) /xiaozhi/v1/$1 break;
        proxy_pass http://orica_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 旧路径（兼容）
    location /xiaozhi/v1/ {
        proxy_pass http://orica_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # ===== 静态文件（如果有）=====
    location /static/ {
        alias /var/www/orica/static/;
        expires 30d;
    }
}
```

### 完整的 Python WebSocket 服务器

```python
# main/xiaozhi-server/core/websocket_server.py

from aiohttp import web
from loguru import logger
import asyncio
from collections import defaultdict
from datetime import datetime

class WebSocketServer:
    def __init__(self, config):
        self.config = config
        self.app = web.Application()
        self.path_stats = defaultdict(int)
        self.start_time = datetime.now()

        # 🔥 双路径注册
        self.app.router.add_get('/xiaozhi/v1/', self.websocket_handler)
        self.app.router.add_get('/orica/v1/', self.websocket_handler)

        # 添加统计端点
        self.app.router.add_get('/stats', self.stats_handler)

        logger.info("=" * 60)
        logger.info("WebSocket 服务器已启用双路径兼容模式")
        logger.info("  旧路径（兼容）: ws://{}:{}/xiaozhi/v1/")
        logger.info("  新路径（推荐）: ws://{}:{}/orica/v1/")
        logger.info("=" * 60)

    async def websocket_handler(self, request):
        """统一的 WebSocket 处理器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        path = request.path
        self.path_stats[path] += 1

        # 判断客户端类型
        is_legacy = "xiaozhi" in path
        client_type = "legacy" if is_legacy else "new"

        logger.bind(tag="WS").info(
            f"客户端连接: {client_type} | 路径: {path} | IP: {request.remote}"
        )

        # 如果是旧路径，发送弃用警告（可选）
        if is_legacy:
            logger.bind(tag="WS").warning(
                f"⚠️  客户端使用已弃用路径: {path}，建议升级到 /orica/v1/"
            )

        # 创建连接处理器
        try:
            connection_handler = ConnectionHandler(ws, self.config)
            await connection_handler.handle()
        except Exception as e:
            logger.error(f"WebSocket 处理错误: {e}")
        finally:
            await ws.close()

        return ws

    async def stats_handler(self, request):
        """统计端点"""
        total = sum(self.path_stats.values())
        runtime = (datetime.now() - self.start_time).total_seconds()

        stats = {
            "runtime_seconds": runtime,
            "total_connections": total,
            "path_stats": dict(self.path_stats),
            "path_percentages": {
                path: f"{(count / total * 100):.2f}%"
                for path, count in self.path_stats.items()
            } if total > 0 else {}
        }

        return web.json_response(stats)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()

        port = self.config.get('websocket_port', 8000)
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()

        logger.success(f"WebSocket 服务器运行在端口 {port}")
```

---

## 总结

### 核心优势

| 特性 | 传统重构 | 兼容层方案 |
|------|---------|-----------|
| **停机时间** | 需要停机 | ✅ 零停机 |
| **回滚速度** | 数小时 | ✅ 几分钟（修改 Nginx） |
| **旧客户端** | ❌ 立即失效 | ✅ 继续工作 |
| **迁移节奏** | 必须一次性完成 | ✅ 渐进式迁移 |
| **风险** | 🔴 高 | 🟢 低 |

### 关键时间节点

```
第 0 周:   准备工作 + 测试环境部署
第 1 周:   生产环境部署兼容层（双路径上线）
第 2-3 周: 内部代码重构（Java package 重命名）
第 4-6 周: 发布新版固件/前端，监控迁移进度
第 7-8 周: 当旧路径访问量 < 5% 时，发布废弃公告
第 10 周:  完全移除旧路径（可选，也可永久保留）
```

### 最终建议

✅ **推荐使用此方案**，因为：
1. **零风险**：旧客户端继续工作，新客户端立即可用
2. **灵活**：可随时暂停、加速或回滚迁移
3. **可观测**：通过统计数据了解迁移进度
4. **可回滚**：任何阶段都可快速回滚

🔥 **关键成功因素**：
- 使用 Nginx 反向代理（最简单、最可靠）
- 监控路径使用统计（了解迁移进度）
- 渐进式发布（固件 → 前端 → 移动端）
- 保留兼容性至少 2-3 个月（给用户充足时间升级）
