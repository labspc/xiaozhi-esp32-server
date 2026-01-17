# EloqKV 迁移运行手册（影子/全量）

## 前提
- 确认 EloqKV 实例可用，连接串已在 `scripts/migrations/eloqkv_migrate.py` DSN 覆盖。
- MySQL/Redis 只读窗口已协商；影子阶段不改写源库。
- 对照 `docs-refactor/ELOQKV_KEYS.md` 完成 Key 形态与索引确认。

## 步骤
1) 配置：
   - 填写 `MYSQL_DSN`、`ELOQKV_DSN`（可用环境变量覆盖），替换连接实现。
   - 补全 SQL 查询（用户/设备/agent/会话/聊天分片）与增量条件。
2) 影子迁移（推荐）：
   - 运行：`python scripts/migrations/eloqkv_migrate.py --mode full`（影子目标）。
   - 校验：输出行数、哈希列表；抽样业务查询对比 MySQL/Redis。
   - 影子读：在新服务只读方式读取 EloqKV，确保业务查询一致。
3) 增量/双写（可选）：
   - 为变更表启用双写或定期增量迁移；记录 offset/timestamp；可用 `--mode incremental --since <ts>`。
4) 切换前校验：
   - 行数/哈希比对通过；关键查询一致；聊天分片数量对齐。
5) 切换：
   - 标记旧库只读（如适用），更新服务配置指向 EloqKV。
6) 回滚预案：
   - 保留旧库数据；如异常，切回旧库配置并停用双写。

## 输出要求
- 迁移报告：行数、哈希摘要、抽样查询结果、异常列表。
- 日志：记录迁移时间、批次、起止 offset/日期。
- 脚本版本：记录使用的脚本 commit 与参数。
