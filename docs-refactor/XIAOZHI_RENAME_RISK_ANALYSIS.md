# xiaozhi 字样全局替换风险分析

## 执行摘要

**结论**：❌ **不建议简单全局替换 "xiaozhi"**

如果要重命名项目，需要**分层策略**，有些地方可以安全替换，有些地方会破坏外部兼容性。

---

## 风险等级分类

### 🔴 高风险（禁止替换）- 外部协议/固件依赖

| 位置 | 风险描述 | 影响范围 |
|------|---------|---------|
| **WebSocket 路径** `/xiaozhi/v1/` | ESP32 固件硬编码此路径 | ⚠️ **所有 ESP32 设备无法连接** |
| **API context-path** `/xiaozhi` | 前端/移动端/第三方集成硬编码 | ⚠️ **所有 API 调用失败** |
| **文档协议** 飞书文档中定义的协议 | 社区开发者参考的标准 | ⚠️ **生态兼容性破坏** |

**具体位置：**
```yaml
# main/xiaozhi-server/config.yaml:20
websocket: ws://你的ip或者域名:端口号/xiaozhi/v1/

# main/manager-api/src/main/resources/application.yml:10
server:
  servlet:
    context-path: /xiaozhi

# main/xiaozhi-server/app.py:110
logger.info("Websocket地址是\tws://{}:{}/xiaozhi/v1/", ...)

# main/xiaozhi-server/core/http_server.py:33
return f"ws://{local_ip}:{port}/xiaozhi/v1/"
```

**影响：**
- ❌ 现有的 ESP32 固件无法连接（需要重新烧录固件）
- ❌ 移动端 APP 无法调用 API（需要重新发布 APP）
- ❌ Web 前端 API 请求全部失败（需要重新部署前端）
- ❌ 社区基于飞书协议文档开发的第三方集成全部失效

---

### 🟡 中风险（需谨慎替换）- 内部硬编码但无外部依赖

| 位置 | 风险描述 | 替换策略 |
|------|---------|---------|
| **Java package 名称** `xiaozhi.*` | 所有 Java 类的包名 | 可替换，但需全量重新编译测试 |
| **Maven groupId/artifactId** | 构建配置标识 | 可替换，影响依赖引用 |
| **Docker 容器名** | 容器和镜像命名 | 可替换，但需更新所有部署脚本 |
| **配置 typeAliasesPackage** | MyBatis 扫描路径 | 必须与 package 名保持一致 |

**具体位置：**
```xml
<!-- main/manager-api/pom.xml -->
<groupId>xiaozhi</groupId>
<artifactId>xiaozhi-esp32-api</artifactId>

<!-- main/manager-api/src/main/resources/application.yml -->
typeAliasesPackage: xiaozhi.modules.*.entity

<!-- 所有 Java 文件 -->
package xiaozhi.modules.device.service;
package xiaozhi.modules.model.controller;
package xiaozhi.common.convert;
...（300+ 个文件）
```

**替换工作量：**
- 300+ Java 文件的 package 声明需要修改
- 所有 import 语句需要更新
- pom.xml 的 groupId/artifactId 需要修改
- application.yml 的 typeAliasesPackage 需要修改
- 所有 Dockerfile 和 docker-compose.yml 需要修改

---

### 🟢 低风险（可安全替换）- 文档/注释/显示文本

| 位置 | 风险描述 | 替换策略 |
|------|---------|---------|
| **README 文档** | 项目说明文档 | ✅ 可安全替换 |
| **代码注释** | Java/Python 注释 | ✅ 可安全替换 |
| **国际化文件** | i18n 显示文本 | ✅ 可安全替换（仅显示层） |
| **日志输出** | logger.info() 中的描述 | ✅ 可安全替换 |

**具体位置：**
```javascript
// main/manager-web/src/i18n/zh_CN.js
"小智" 相关的显示文本

// 各种 README.md
项目描述、教程、部署文档
```

---

## 详细风险分析

### 1. WebSocket 协议路径风险（最高优先级）

**位置：**
```python
# main/xiaozhi-server/app.py:110
ws://{}:{}/xiaozhi/v1/

# main/xiaozhi-server/core/http_server.py:33
f"ws://{local_ip}:{port}/xiaozhi/v1/"

# main/xiaozhi-server/core/api/ota_handler.py:141
f"ws://{local_ip}:{port}/xiaozhi/v1/"
```

**问题：**
1. ESP32 固件使用硬编码路径 `ws://server:8000/xiaozhi/v1/` 连接服务器
2. 如果修改服务器路径，**所有已部署的 ESP32 设备无法连接**
3. 需要重新编译并烧录固件到每一个设备

**协议文档：**
根据 CLAUDE.md:27，通信协议文档在飞书：
```
https://ccnphfhqs21z.feishu.cn/wiki/M0XiwldO9iJwHikpXD5cEx71nKh
```

**解决方案：**
- **方案 A（推荐）**：保留 `/xiaozhi/v1/` 作为兼容端点，同时添加新的 `/orica/v1/` 端点
- **方案 B（激进）**：完全替换路径，但需要：
  1. 更新飞书协议文档
  2. 发布新版 ESP32 固件
  3. 通知所有用户更新固件
  4. 提供迁移工具或脚本

---

### 2. API Context Path 风险

**位置：**
```yaml
# main/manager-api/src/main/resources/application.yml:10
server:
  servlet:
    context-path: /xiaozhi
```

**影响：**
- 所有 API 路径从 `http://server:8002/xiaozhi/device/list` 变为 `http://server:8002/newname/device/list`
- 前端（Vue/uni-app）的 API_BASE_URL 需要更新
- 移动端 APP 需要重新发布
- API 文档地址变更：`http://server:8002/xiaozhi/doc.html`

**依赖位置：**
```env
# main/manager-web/.env.production
VUE_APP_API_BASE_URL=/xiaozhi

# main/manager-mobile/env/.env
VITE_API_BASE_URL=https://2662r3426b.vicp.fun/xiaozhi
```

**解决方案：**
- 使用 Nginx 反向代理同时支持新旧路径（过渡期）
- 前端使用环境变量配置，便于切换

---

### 3. Java Package 名称风险

**位置：**
所有 Java 文件（300+ 文件）：
```java
package xiaozhi.modules.device.service;
package xiaozhi.modules.model.controller;
package xiaozhi.common.convert;
...
```

**问题：**
1. **编译破坏性**：修改 package 名后，所有 import 语句失效
2. **Maven 构建**：groupId 和 artifactId 变更影响依赖管理
3. **MyBatis 扫描**：`typeAliasesPackage: xiaozhi.modules.*.entity` 必须同步修改
4. **Spring 组件扫描**：`@ComponentScan` 可能需要调整

**工作量估算：**
- 自动替换：300+ 文件的 package 声明和 import 语句
- 手动检查：pom.xml、application.yml、Spring 配置类
- 全量测试：所有功能模块需要重新测试
- 工作量：**2-3 天**（使用 IDE 批量重构工具）

**推荐工具：**
- IntelliJ IDEA 的 "Refactor → Rename Package"
- 可自动更新所有引用，但仍需人工验证

---

### 4. Docker 镜像/容器名风险

**位置：**
```bash
# docker-compose.yml
xiaozhi-esp32-server
xiaozhi-mysql
xiaozhi-redis

# Dockerfile
FROM xiaozhi-server-base

# 镜像名
xinnan-tech/xiaozhi-esp32-server
```

**影响：**
- CI/CD 流水线需要更新镜像名
- 已部署的容器需要重新创建
- 旧镜像和新镜像共存可能导致混淆

**解决方案：**
- 使用 tag 区分版本：`xiaozhi:v1` vs `orica:v2`
- 更新 GitHub Actions 工作流

---

## 替换策略建议

### 推荐方案：渐进式重命名（最小破坏性）

#### 第 1 阶段：品牌层重命名（无风险）
**时间：1-2 天**

✅ 可安全替换：
- [ ] 所有 README 文档（中英文）
- [ ] 代码注释中的 "小智"
- [ ] 国际化文件中的显示文本
- [ ] 网页标题、图标
- [ ] 文档、教程、FAQ

**影响：** 无，纯展示层修改

---

#### 第 2 阶段：内部代码重命名（中风险）
**时间：3-5 天**

⚠️ 需谨慎替换：
- [ ] Java package 名：`xiaozhi.*` → `orica.*`（使用 IDE 自动重构）
- [ ] Maven 配置：groupId/artifactId
- [ ] MyBatis typeAliasesPackage
- [ ] Docker 镜像/容器名

**前置条件：**
1. 完整的单元测试覆盖
2. 完整的集成测试
3. 备份数据库
4. 版本控制打 tag

**验证清单：**
- [ ] 所有 JUnit 测试通过
- [ ] 启动不报错
- [ ] API 接口调用正常
- [ ] 数据库操作正常
- [ ] Redis 缓存正常

---

#### 第 3 阶段：外部协议重命名（高风险，需生态支持）
**时间：4-6 周（包括社区通知期）**

🔴 高风险替换：
- [ ] WebSocket 路径：`/xiaozhi/v1/` → `/orica/v1/`
- [ ] API context-path：`/xiaozhi` → `/orica`

**必须同步完成：**
1. **固件更新**：
   - 发布新版 ESP32 固件（修改 WebSocket 路径）
   - 提供 OTA 升级机制
   - 保留旧路径兼容至少 3 个月
2. **前端更新**：
   - 更新 manager-web（Vue）的 API_BASE_URL
   - 更新 manager-mobile（uni-app）的 API_BASE_URL
   - 重新构建并部署
3. **文档更新**：
   - 更新飞书协议文档
   - 通知社区开发者
   - 提供迁移指南
4. **服务器兼容**：
   - Nginx 同时支持 `/xiaozhi/v1/` 和 `/orica/v1/`（过渡期）
   - 设置 HTTP 301/302 重定向提示用户升级

**回退计划：**
- 保留旧路径支持至少 6 个月
- 提供开关可快速切回旧路径

---

### 替代方案：仅品牌重命名（最保守）

**策略：**
- ✅ 修改所有面向用户的文本（README、UI、文档）
- ❌ 保留所有内部代码和协议路径不变

**优点：**
- 零破坏性
- 无需更新固件/前端
- 工作量最小（1-2 天）

**缺点：**
- 代码和品牌不一致（内部仍是 xiaozhi）
- 技术债务（未来可能需要重构）

---

## 自动化替换脚本（危险！需人工验证）

**⚠️ 警告：不要直接运行！仅供参考！**

```bash
#!/bin/bash
# 此脚本仅用于演示，实际使用需要人工审查每一处修改

NEW_NAME="orica"  # 新名称

# 阶段 1：低风险文档替换
find . -type f -name "*.md" -exec sed -i '' "s/xiaozhi/$NEW_NAME/g" {} \;
find . -type f -name "*.md" -exec sed -i '' "s/小智/ORica/g" {} \;

# 阶段 2：中风险代码替换（需要 IDE 辅助）
# ❌ 不建议用 sed 替换 Java package，应使用 IDE 的 "Refactor → Rename"
# find . -name "*.java" -exec sed -i '' "s/package xiaozhi/package $NEW_NAME/g" {} \;

# 阶段 3：高风险协议替换（禁止自动化！）
# ❌ 绝对不要自动替换 WebSocket 路径和 API context-path
# 需要配合固件更新和前端更新
```

---

## 测试清单

### 功能测试
- [ ] ESP32 设备能连接到 WebSocket
- [ ] Web 前端登录正常
- [ ] 移动端 APP 登录正常
- [ ] 设备列表显示正常
- [ ] 语音交互正常
- [ ] OTA 升级正常
- [ ] 权限控制正常
- [ ] 多语言切换正常

### 性能测试
- [ ] WebSocket 并发连接数（1000+）
- [ ] API 响应时间（<200ms）
- [ ] 数据库查询性能

### 兼容性测试
- [ ] 旧固件仍能连接（如果保留兼容性）
- [ ] 旧 API 路径重定向正常

---

## 最终建议

### 如果是新项目/ORica 独立版本
✅ **可以完全重命名**，但需要：
1. 同步更新所有组件（服务器、固件、前端）
2. 更新所有文档和协议定义
3. 不考虑向后兼容

### 如果是在现有 xiaozhi 基础上演进
⚠️ **建议仅重命名品牌层**：
1. README、UI、文档使用 ORica
2. 内部代码保持 xiaozhi（技术债务可接受）
3. 逐步迁移，保留兼容性

### 如果必须完全重命名
🔴 **需要完整的迁移计划**：
1. 第 1 个月：品牌层 + 内部代码重命名
2. 第 2-3 个月：发布新固件，前后端更新，保留双路径兼容
3. 第 4-6 个月：逐步废弃旧路径，监控迁移进度
4. 6 个月后：完全移除旧路径

---

## 总结

| 方案 | 工作量 | 风险 | 破坏性 | 推荐场景 |
|------|--------|------|--------|---------|
| **仅品牌重命名** | 1-2 天 | 🟢 低 | 无 | 快速更名，保持兼容 |
| **品牌+内部代码** | 5-7 天 | 🟡 中 | 需完整测试 | 技术债务清理 |
| **完全重命名** | 4-6 周 | 🔴 高 | 需生态配合 | 新版本/独立项目 |

**最终建议：**
根据你的实际需求选择方案。如果只是为了品牌独立性，**方案 1 即可**。如果是长期维护的独立项目，建议采用**渐进式重命名（3 阶段）**。

**关键原则：**
- WebSocket 路径和 API context-path 是最敏感的，**必须保留兼容性或同步更新所有客户端**
- Java package 名可以安全重构（使用 IDE 工具）
- 文档和显示文本随时可改
