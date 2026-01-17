# 自定义组件化存储方案设计

## 核心理念

**将复杂的数据访问场景拆分为独立的小组件，每个组件专注解决一个问题。**

```
┌─────────────────────────────────────────────────────┐
│           xiaozhi-config-api (Rust)                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Device Mgr   │  │ Agent Mgr    │  │ User Mgr  │ │
│  │ (简单 KV)    │  │ (简单 KV)    │  │ (简单 KV) │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         自定义组件层                            │ │
│  ├────────────────────────────────────────────────┤ │
│  │ 📦 ChatArchiver      - 聊天历史归档组件         │ │
│  │ 📊 StatsCalculator   - 统计预计算组件           │ │
│  │ 🔍 ChatSearcher      - 聊天记录搜索组件         │ │
│  │ 📈 ReportGenerator   - 报表生成组件             │ │
│  │ 🗃️  ColdDataManager   - 冷数据管理组件          │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
   ┌─────────┐          ┌──────────┐
   │ EloqKV  │          │ 对象存储  │
   │ (热数据)│          │ (冷数据)  │
   └─────────┘          └──────────┘
```

---

## 需要的小组件清单

### 1. 📦 ChatArchiver - 聊天历史归档组件

**解决问题：** 聊天记录持续增长，KV 存储压力大

#### 功能设计

```rust
pub struct ChatArchiver {
    eloq: EloqClient,
    oss: ObjectStorage,  // MinIO/S3/阿里云OSS
    config: ArchiverConfig,
}

pub struct ArchiverConfig {
    hot_data_days: i32,        // 热数据保留天数（如 7 天）
    archive_format: String,    // "json" 或 "parquet"
    compression: bool,          // 是否压缩
    schedule: String,           // Cron 表达式，如 "0 2 * * *"（每天凌晨2点）
}

impl ChatArchiver {
    /// 归档指定日期之前的聊天记录
    pub async fn archive_before(&self, date: Date) -> Result<ArchiveResult> {
        // 1. 从 EloqKV 扫描旧数据
        let old_messages = self.scan_old_messages(date).await?;

        // 2. 按会话分组
        let grouped = self.group_by_session(old_messages);

        // 3. 生成归档文件
        for (session_id, messages) in grouped {
            let filename = format!("archive/{}/session-{}.json.gz",
                                   date.format("%Y-%m"), session_id);

            // 压缩并上传到 OSS
            let compressed = self.compress_messages(messages)?;
            self.oss.put_object(&filename, compressed).await?;
        }

        // 4. 从 EloqKV 删除已归档数据
        self.delete_archived_messages(old_messages).await?;

        Ok(ArchiveResult {
            archived_count: old_messages.len(),
            files_created: grouped.len()
        })
    }

    /// 查询归档数据（冷数据查询）
    pub async fn query_archived(&self, session_id: &str, date_range: (Date, Date))
        -> Result<Vec<ChatMessage>>
    {
        let mut messages = Vec::new();

        // 遍历日期范围内的归档文件
        for date in date_range.0..=date_range.1 {
            let filename = format!("archive/{}/session-{}.json.gz",
                                   date.format("%Y-%m"), session_id);

            if let Ok(data) = self.oss.get_object(&filename).await {
                let decompressed = self.decompress(data)?;
                let archived_msgs: Vec<ChatMessage> = serde_json::from_slice(&decompressed)?;
                messages.extend(archived_msgs);
            }
        }

        Ok(messages)
    }
}
```

#### 使用方式

```rust
// 定时任务（每天凌晨2点执行）
#[tokio::main]
async fn archive_task() {
    let archiver = ChatArchiver::new(config);
    let cutoff_date = Utc::now() - Duration::days(7);

    match archiver.archive_before(cutoff_date).await {
        Ok(result) => info!("归档完成: {} 条记录", result.archived_count),
        Err(e) => error!("归档失败: {}", e),
    }
}

// API 查询（自动合并热数据+冷数据）
async fn get_chat_history(session_id: &str, days: i32) -> Vec<ChatMessage> {
    let mut messages = Vec::new();

    // 1. 查询热数据（EloqKV）
    let hot_messages = eloq.get(format!("session:{}:messages", session_id))?;
    messages.extend(hot_messages);

    // 2. 查询冷数据（OSS）
    if days > 7 {
        let date_range = (Utc::now() - Duration::days(days), Utc::now() - Duration::days(7));
        let cold_messages = archiver.query_archived(session_id, date_range).await?;
        messages.extend(cold_messages);
    }

    // 3. 排序并返回
    messages.sort_by_key(|m| m.report_time);
    messages
}
```

#### 配置示例

```toml
[chat_archiver]
hot_data_days = 7
archive_format = "json"
compression = true
schedule = "0 2 * * *"  # 每天凌晨2点
oss_bucket = "xiaozhi-archive"
oss_endpoint = "https://oss-cn-hangzhou.aliyuncs.com"
```

---

### 2. 📊 StatsCalculator - 统计预计算组件

**解决问题：** KV 无法高效实现 GROUP BY / COUNT 等聚合查询

#### 功能设计

```rust
pub struct StatsCalculator {
    eloq: EloqClient,
    metrics: MetricsStore,  // 存储预计算结果
}

#[derive(Serialize, Deserialize)]
pub struct DailyStats {
    date: String,
    user_id: i64,
    total_messages: i64,
    user_messages: i64,
    assistant_messages: i64,
    total_devices: i64,
    active_devices: Vec<String>,
}

impl StatsCalculator {
    /// 计算每日统计数据
    pub async fn calculate_daily_stats(&self, date: Date) -> Result<()> {
        // 1. 扫描当天所有聊天记录
        let messages = self.scan_messages_by_date(date).await?;

        // 2. 按用户分组统计
        let mut user_stats: HashMap<i64, DailyStats> = HashMap::new();

        for msg in messages {
            let stats = user_stats.entry(msg.user_id).or_insert(DailyStats {
                date: date.to_string(),
                user_id: msg.user_id,
                ..Default::default()
            });

            stats.total_messages += 1;
            match msg.chat_type {
                0 => stats.user_messages += 1,
                1 => stats.assistant_messages += 1,
                _ => {}
            }

            if !stats.active_devices.contains(&msg.mac_address) {
                stats.active_devices.push(msg.mac_address);
            }
        }

        // 3. 存储统计结果到 EloqKV
        for (user_id, stats) in user_stats {
            let key = format!("stats:daily:{}:{}", user_id, date.format("%Y-%m-%d"));
            self.eloq.set(&key, serde_json::to_string(&stats)?)?;

            // 设置 30 天过期（更久的数据归档）
            self.eloq.expire(&key, 30 * 24 * 3600)?;
        }

        Ok(())
    }

    /// 获取用户统计数据（快速查询）
    pub async fn get_user_stats(&self, user_id: i64, date_range: (Date, Date))
        -> Result<Vec<DailyStats>>
    {
        let mut stats = Vec::new();

        for date in date_range.0..=date_range.1 {
            let key = format!("stats:daily:{}:{}", user_id, date.format("%Y-%m-%d"));

            if let Ok(data) = self.eloq.get(&key) {
                let daily_stat: DailyStats = serde_json::from_str(&data)?;
                stats.push(daily_stat);
            }
        }

        Ok(stats)
    }

    /// 实时统计（用于仪表盘）
    pub async fn get_realtime_stats(&self) -> Result<RealtimeStats> {
        // 从预计算结果快速聚合
        let today = Utc::now().date_naive();
        let today_key = format!("stats:daily:*:{}", today.format("%Y-%m-%d"));

        let daily_stats = self.eloq.scan(&today_key)?;

        let realtime = RealtimeStats {
            total_users: daily_stats.len(),
            total_messages: daily_stats.iter().map(|s| s.total_messages).sum(),
            active_devices: daily_stats.iter()
                .flat_map(|s| s.active_devices.clone())
                .collect::<HashSet<_>>()
                .len(),
        };

        Ok(realtime)
    }
}
```

#### 定时任务

```rust
// 每小时计算一次当天统计
#[tokio::cron("0 * * * *")]
async fn hourly_stats_task() {
    let calculator = StatsCalculator::new(eloq);
    let today = Utc::now().date_naive();

    calculator.calculate_daily_stats(today).await?;
}

// 每天凌晨计算昨天的完整统计
#[tokio::cron("0 1 * * *")]
async fn daily_stats_task() {
    let yesterday = Utc::now().date_naive() - Duration::days(1);
    calculator.calculate_daily_stats(yesterday).await?;
}
```

#### API 使用

```rust
// GET /api/stats/user/{user_id}?from=2026-01-01&to=2026-01-31
async fn get_user_stats_handler(
    user_id: Path<i64>,
    query: Query<DateRangeQuery>,
) -> Result<Json<Vec<DailyStats>>> {
    let stats = calculator.get_user_stats(*user_id, (query.from, query.to)).await?;
    Ok(Json(stats))
}

// 前端可直接渲染图表，无需复杂 SQL 查询
```

---

### 3. 🔍 ChatSearcher - 聊天记录搜索组件

**解决问题：** KV 无法实现全文搜索

#### 方案选择

**方案A：轻量级 - 简单关键词索引**

```rust
pub struct SimpleChatSearcher {
    eloq: EloqClient,
}

impl SimpleChatSearcher {
    /// 写入消息时建立关键词索引
    pub async fn index_message(&self, msg: &ChatMessage) -> Result<()> {
        // 提取关键词（简单分词）
        let keywords = self.extract_keywords(&msg.content);

        for keyword in keywords {
            let index_key = format!("search:keyword:{}:{}",
                                    keyword, msg.session_id);

            // 存储消息ID列表
            self.eloq.sadd(&index_key, &msg.id)?;
        }

        Ok(())
    }

    /// 搜索包含关键词的消息
    pub async fn search(&self, keyword: &str, session_id: &str)
        -> Result<Vec<ChatMessage>>
    {
        let index_key = format!("search:keyword:{}:{}", keyword, session_id);
        let msg_ids = self.eloq.smembers(&index_key)?;

        // 批量获取消息内容
        let messages = self.eloq.mget(
            msg_ids.iter().map(|id| format!("chat:{}", id))
        )?;

        Ok(messages)
    }

    fn extract_keywords(&self, text: &str) -> Vec<String> {
        // 简单实现：分词 + 去停用词
        text.split_whitespace()
            .filter(|w| w.len() > 1 && !self.is_stopword(w))
            .map(|w| w.to_lowercase())
            .collect()
    }
}
```

**方案B：进阶 - 集成 MeiliSearch / Typesense**

```rust
pub struct AdvancedChatSearcher {
    eloq: EloqClient,
    meilisearch: MeiliClient,  // 专用搜索引擎
}

impl AdvancedChatSearcher {
    /// 写入消息时同步到搜索引擎
    pub async fn index_message(&self, msg: &ChatMessage) -> Result<()> {
        // 1. 存储到 EloqKV
        self.eloq.set(&format!("chat:{}", msg.id), serde_json::to_string(msg)?)?;

        // 2. 同步到 MeiliSearch
        self.meilisearch.index("chat_messages")
            .add_documents(&[msg], Some("id"))
            .await?;

        Ok(())
    }

    /// 全文搜索
    pub async fn search(&self, query: &str, filters: SearchFilters)
        -> Result<Vec<ChatMessage>>
    {
        let search_result = self.meilisearch
            .index("chat_messages")
            .search()
            .with_query(query)
            .with_filter(&format!("session_id = {} AND report_time > {}",
                                 filters.session_id, filters.after))
            .execute::<ChatMessage>()
            .await?;

        Ok(search_result.hits.into_iter().map(|h| h.result).collect())
    }
}
```

**推荐：**
- 用户量 < 10000：方案A（简单关键词索引）
- 用户量 > 10000：方案B（MeiliSearch，Docker 部署很简单）

---

### 4. 📈 ReportGenerator - 报表生成组件

**解决问题：** 复杂报表需要多表 JOIN 和聚合

```rust
pub struct ReportGenerator {
    eloq: EloqClient,
    cache: ReportCache,
}

#[derive(Serialize)]
pub struct UserActivityReport {
    user_id: i64,
    username: String,
    total_devices: i64,
    total_chats: i64,
    last_active: DateTime<Utc>,
    favorite_agent: String,
    daily_breakdown: Vec<DailyActivity>,
}

impl ReportGenerator {
    /// 生成用户活跃度报表（每日缓存）
    pub async fn generate_user_activity_report(&self, date: Date)
        -> Result<Vec<UserActivityReport>>
    {
        // 1. 检查缓存
        let cache_key = format!("report:user_activity:{}", date.format("%Y-%m-%d"));
        if let Ok(cached) = self.eloq.get(&cache_key) {
            return Ok(serde_json::from_str(&cached)?);
        }

        // 2. 从预计算统计数据生成报表
        let mut reports = Vec::new();

        // 获取所有用户
        let user_ids = self.get_all_user_ids().await?;

        for user_id in user_ids {
            // 从预计算的统计数据构建报表
            let stats = self.eloq.get(&format!("stats:daily:{}:{}", user_id, date))?;
            let devices = self.eloq.smembers(&format!("user_devices:{}", user_id))?;
            let user = self.eloq.get(&format!("user:id:{}", user_id))?;

            let report = UserActivityReport {
                user_id,
                username: user.username,
                total_devices: devices.len() as i64,
                total_chats: stats.total_messages,
                last_active: stats.last_message_time,
                favorite_agent: self.get_favorite_agent(user_id).await?,
                daily_breakdown: vec![],
            };

            reports.push(report);
        }

        // 3. 缓存结果（24小时）
        self.eloq.set(&cache_key, serde_json::to_string(&reports)?)?;
        self.eloq.expire(&cache_key, 24 * 3600)?;

        Ok(reports)
    }

    /// 导出 CSV 格式
    pub async fn export_csv(&self, date: Date) -> Result<String> {
        let reports = self.generate_user_activity_report(date).await?;

        let mut csv = String::from("用户ID,用户名,设备数,聊天数,最后活跃时间\n");
        for report in reports {
            csv.push_str(&format!("{},{},{},{},{}\n",
                report.user_id,
                report.username,
                report.total_devices,
                report.total_chats,
                report.last_active.format("%Y-%m-%d %H:%M:%S")
            ));
        }

        Ok(csv)
    }
}
```

---

### 5. 🗃️ ColdDataManager - 冷数据管理组件

**解决问题：** 统一管理归档数据的生命周期

```rust
pub struct ColdDataManager {
    oss: ObjectStorage,
    policy: RetentionPolicy,
}

pub struct RetentionPolicy {
    hot_days: i32,      // 热数据：7 天
    warm_days: i32,     // 温数据：30 天（压缩存储）
    cold_days: i32,     // 冷数据：365 天（归档存储）
    delete_after: i32,  // 超过 2 年删除
}

impl ColdDataManager {
    /// 数据分层存储
    pub async fn tier_data(&self) -> Result<()> {
        let now = Utc::now();

        // 1. 热 → 温（7-30天）：从 EloqKV 移到 OSS 标准存储
        let warm_cutoff = now - Duration::days(self.policy.hot_days);
        self.move_to_warm_storage(warm_cutoff).await?;

        // 2. 温 → 冷（30-365天）：转换为归档存储类型
        let cold_cutoff = now - Duration::days(self.policy.warm_days);
        self.move_to_cold_storage(cold_cutoff).await?;

        // 3. 冷 → 删除（>2年）
        let delete_cutoff = now - Duration::days(self.policy.delete_after);
        self.delete_old_data(delete_cutoff).await?;

        Ok(())
    }

    /// 查询时自动选择存储层
    pub async fn get_data(&self, key: &str, date: Date) -> Result<Vec<u8>> {
        let age = (Utc::now().date_naive() - date).num_days();

        match age {
            0..=7 => {
                // 热数据：从 EloqKV 读取
                self.eloq.get(key)
            }
            8..=30 => {
                // 温数据：从 OSS 标准存储读取
                self.oss.get_object(&format!("warm/{}", key)).await
            }
            31.. => {
                // 冷数据：从 OSS 归档存储读取（可能需要解冻）
                self.oss.restore_and_get(&format!("cold/{}", key)).await
            }
            _ => Err(anyhow::anyhow!("Invalid date range")),
        }
    }
}
```

---

## 组件集成架构

### API 层集成

```rust
// src/main.rs
use axum::{Router, routing::get};

#[tokio::main]
async fn main() {
    // 初始化组件
    let eloq = EloqClient::new(config.eloq_url);
    let oss = ObjectStorage::new(config.oss_config);

    let chat_archiver = Arc::new(ChatArchiver::new(eloq.clone(), oss.clone()));
    let stats_calculator = Arc::new(StatsCalculator::new(eloq.clone()));
    let chat_searcher = Arc::new(ChatSearcher::new(eloq.clone()));
    let report_generator = Arc::new(ReportGenerator::new(eloq.clone()));

    // 注册到 AppState
    let state = AppState {
        eloq,
        chat_archiver,
        stats_calculator,
        chat_searcher,
        report_generator,
    };

    // 路由
    let app = Router::new()
        .route("/api/chat/history/:session_id", get(get_chat_history))
        .route("/api/chat/search", get(search_chat))
        .route("/api/stats/user/:user_id", get(get_user_stats))
        .route("/api/reports/activity", get(get_activity_report))
        .with_state(state);

    // 启动后台任务
    tokio::spawn(start_background_tasks(state.clone()));

    axum::Server::bind(&"0.0.0.0:8002".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}

// 后台任务
async fn start_background_tasks(state: AppState) {
    // 归档任务：每天凌晨2点
    let archiver = state.chat_archiver.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::hours(24));
        loop {
            interval.tick().await;
            if Utc::now().hour() == 2 {
                archiver.archive_old_data().await.ok();
            }
        }
    });

    // 统计任务：每小时
    let calculator = state.stats_calculator.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::hours(1));
        loop {
            interval.tick().await;
            calculator.calculate_daily_stats(Utc::now().date_naive()).await.ok();
        }
    });
}
```

---

## 开发清单

### 基础组件（必需）

- [ ] **ChatArchiver** - 聊天历史归档
  - [ ] 定时归档任务
  - [ ] 冷数据查询接口
  - [ ] 归档文件压缩
  - [ ] OSS 上传下载

- [ ] **StatsCalculator** - 统计预计算
  - [ ] 每日统计计算
  - [ ] 预计算结果存储
  - [ ] 快速查询接口

### 进阶组件（可选）

- [ ] **ChatSearcher** - 聊天搜索
  - [ ] 简单关键词索引（方案A）
  - [ ] 或集成 MeiliSearch（方案B）

- [ ] **ReportGenerator** - 报表生成
  - [ ] 用户活跃度报表
  - [ ] CSV 导出

- [ ] **ColdDataManager** - 冷数据管理
  - [ ] 数据分层策略
  - [ ] 自动迁移任务

---

## 技术选型建议

### 对象存储选择

| 方案 | 成本 | 易用性 | 推荐场景 |
|------|------|--------|---------|
| **MinIO** (自托管) | 免费（服务器成本） | ⭐⭐⭐⭐ | 私有部署，完全控制 |
| **阿里云OSS** | 按量付费 | ⭐⭐⭐⭐⭐ | 生产环境，高可用 |
| **AWS S3** | 按量付费 | ⭐⭐⭐⭐⭐ | 海外用户 |
| **本地文件系统** | 免费 | ⭐⭐⭐ | 测试环境 |

**推荐：MinIO**（开源，S3 兼容，Docker 一键部署）

```yaml
# docker-compose.yml
services:
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
```

### 搜索引擎选择

| 方案 | 复杂度 | 性能 | 推荐场景 |
|------|--------|------|---------|
| 自实现关键词索引 | ⭐ | ⭐⭐⭐ | 用户 < 1000 |
| **MeiliSearch** | ⭐⭐ | ⭐⭐⭐⭐⭐ | **推荐**，开箱即用 |
| Elasticsearch | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 大规模场景 |
| Typesense | ⭐⭐ | ⭐⭐⭐⭐ | 备选方案 |

**推荐：MeiliSearch**（Rust 编写，性能优秀，部署简单）

```bash
# Docker 部署
docker run -d \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest
```

### 定时任务框架

```rust
// Cargo.toml
[dependencies]
tokio-cron-scheduler = "0.9"

// 使用示例
use tokio_cron_scheduler::{JobScheduler, Job};

#[tokio::main]
async fn main() {
    let scheduler = JobScheduler::new().await.unwrap();

    // 每天凌晨2点归档
    scheduler.add(Job::new_async("0 0 2 * * *", |_uuid, _l| {
        Box::pin(async move {
            chat_archiver.archive_old_data().await.ok();
        })
    }).unwrap()).await.unwrap();

    scheduler.start().await.unwrap();
}
```

---

## 优劣势分析

### ✅ 优势

1. **灵活性高**
   - 每个组件独立开发，可随时替换
   - 不受 EloqKV 功能限制

2. **性能可控**
   - 热数据 KV 访问极快
   - 冷数据按需加载
   - 统计预计算避免实时聚合

3. **成本优化**
   - 冷数据归档到便宜的对象存储
   - EloqKV 只存储热数据，压力小

4. **易于维护**
   - 组件职责清晰
   - 问题隔离，不影响主系统

5. **扩展性好**
   - 需要新功能？加个组件即可
   - 未来可轻松迁移到专用数据库

### ⚠️ 劣势

1. **开发工作量**
   - 需要自己实现归档、统计等逻辑
   - 需要测试和维护

2. **架构复杂度**
   - 从单一数据库变为多组件协作
   - 需要处理数据一致性

3. **运维成本**
   - 多了 MinIO、MeiliSearch 等组件
   - 需要监控和备份

### 💡 缓解措施

**针对开发工作量：**
- 使用成熟的 Rust crate（如 `object_store`, `meilisearch-sdk`）
- 参考开源项目（如 Plausible Analytics 的归档方案）
- 先实现核心功能，其他可选

**针对架构复杂度：**
- 良好的文档和注释
- 单元测试覆盖关键逻辑
- 使用 tracing 做好链路追踪

**针对运维成本：**
- Docker Compose 一键部署
- 使用 Grafana + Prometheus 监控
- 自动化备份脚本

---

## 实施路线

### 阶段1: MVP（1-2周）

**目标：** 验证方案可行性

```yaml
必须完成:
  - [x] EloqKV 基础 KV 操作
  - [x] 设备/Agent/模型配置迁移到 KV
  - [x] ChatArchiver 基础功能（手动触发）
  - [x] MinIO 集成

可选:
  - [ ] 简单统计（直接查询，不预计算）
  - [ ] 搜索功能（暂时不做）
```

### 阶段2: 生产就绪（2-3周）

**目标：** 完善功能，准备上线

```yaml
必须完成:
  - [ ] ChatArchiver 定时任务
  - [ ] StatsCalculator 预计算
  - [ ] 冷热数据自动切换
  - [ ] 错误处理和重试逻辑
  - [ ] 监控和日志

可选:
  - [ ] MeiliSearch 搜索
  - [ ] 报表生成
```

### 阶段3: 优化增强（持续）

```yaml
  - [ ] 性能调优
  - [ ] 更多统计维度
  - [ ] 高级搜索功能
  - [ ] 数据导出工具
```

---

## 示例代码仓库结构

```
xiaozhi-config-api/
├── src/
│   ├── main.rs
│   ├── components/
│   │   ├── mod.rs
│   │   ├── chat_archiver.rs       # 📦 聊天归档组件
│   │   ├── stats_calculator.rs    # 📊 统计组件
│   │   ├── chat_searcher.rs       # 🔍 搜索组件
│   │   ├── report_generator.rs    # 📈 报表组件
│   │   └── cold_data_manager.rs   # 🗃️  冷数据管理
│   ├── handlers/
│   │   ├── chat.rs                # 聊天相关 API
│   │   ├── stats.rs               # 统计相关 API
│   │   └── report.rs              # 报表相关 API
│   ├── models/
│   │   ├── chat.rs
│   │   └── stats.rs
│   ├── storage/
│   │   ├── eloqkv.rs
│   │   └── object_storage.rs
│   └── tasks/
│       ├── archive_task.rs        # 归档定时任务
│       └── stats_task.rs          # 统计定时任务
├── Cargo.toml
└── docker-compose.yml
```

---

## 总结

**你的思路完全可行！** 🎉

自己写小组件处理复杂场景是**最佳实践**：

1. ✅ **热数据 KV** → 性能极致
2. ✅ **冷数据归档** → 成本优化
3. ✅ **统计预计算** → 避免复杂查询
4. ✅ **组件化设计** → 灵活可扩展

### 核心组件优先级

```
P0（必须）: ChatArchiver（归档）
P1（重要）: StatsCalculator（统计）
P2（可选）: ChatSearcher（搜索）
P3（未来）: ReportGenerator（报表）
```

### 技术栈建议

- **对象存储**: MinIO（免费，S3 兼容）
- **搜索引擎**: MeiliSearch（简单，高性能）
- **定时任务**: tokio-cron-scheduler
- **监控**: Prometheus + Grafana

**下一步：**
1. 先验证 EloqKV 基础功能
2. 实现 ChatArchiver MVP
3. 逐步添加其他组件

需要我帮你写具体某个组件的完整代码吗？
