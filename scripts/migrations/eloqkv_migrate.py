"""
EloqKV 迁移脚本骨架（目标存储为 KV/JSON，迁移后不再依赖 SQL 查询）。

目标：
- 从现有 MySQL/Redis 导出数据（仅作为源），写入 EloqKV（兼容 redis 协议）
- 支持全量与增量（基于时间戳/自增 id）
- 输出校验报告（行数、哈希、抽样查询），并构建必要索引 Key

注意：
- 迁移完成后，服务仅依赖 EloqKV（KV/JSON），不再依赖 SQL 查询能力
- 按 docs-refactor/ELOQKV_KEYS.md 的 Key 规范写入，构建索引 Key（用户名、设备索引等）
- 按 MIGRATION_RUNBOOK 进行影子/增量/切换/回滚
"""

import argparse
import hashlib
import os
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

MYSQL_DSN = os.getenv("MYSQL_DSN", "mysql://user:password@host:3306/db")
ELOQKV_DSN = os.getenv("ELOQKV_DSN", "redis://host:6379")


def get_mysql_conn():
    """
    返回 MySQL 连接；需要安装 mysql-connector-python 或 pymysql。
    """
    try:
        import mysql.connector  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Please install mysql-connector-python") from exc
    parsed = urlparse(MYSQL_DSN)
    if not parsed.hostname or not parsed.path:
        raise RuntimeError("MYSQL_DSN is invalid, expected mysql://user:password@host:port/db")
    return mysql.connector.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
    )


def get_eloqkv_client():
    """
    返回 EloqKV 客户端；服务端兼容 redis 协议。
    生产服务建议用 redis-rs client；本迁移脚本示例使用 redis-py。
    """
    try:
        import redis  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Please install redis-py (pip install redis)") from exc
    return redis.Redis.from_url(ELOQKV_DSN, decode_responses=True)


def hash_dict(d: Dict[str, Any]) -> str:
    """稳定哈希，用于迁移后校验."""
    m = hashlib.sha256()
    for k in sorted(d.keys()):
        m.update(str(k).encode())
        m.update(str(d[k]).encode())
    return m.hexdigest()


def migrate_users(since: Optional[str] = None) -> List[str]:
    """
    迁移用户：写入 user:{id}，并可选建立用户名索引。
    返回校验哈希列表。
    """
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id, username, password, email, create_date as created_at, update_date as updated_at FROM sys_user"
    if since:
        sql += " WHERE update_date >= %s"
        cursor.execute(sql, (since,))
    else:
        cursor.execute(sql)
    rows: List[Dict[str, Any]] = cursor.fetchall()  # type: ignore
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"user:{row['id']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        if "username" in row:
            client.set(f"user:username:{row['username']}", row["id"])  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_devices(since: Optional[str] = None) -> List[str]:
    """
    迁移设备：写入 device:{mac}，并建立用户到设备的索引。
    返回校验哈希列表。
    """
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT mac_address, user_id, agent_id, last_connected_at as last_seen, firmware_version, board, alias FROM ai_device"
    if since:
        sql += " WHERE update_date >= %s"
        cursor.execute(sql, (since,))
    else:
        cursor.execute(sql)
    rows: List[Dict[str, Any]] = cursor.fetchall()  # type: ignore
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        mac = row["mac_address"]
        key = f"device:{mac}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        if row.get("user_id"):
            client.sadd(f"device:user:{row['user_id']}", mac)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_agents(since: Optional[str] = None) -> List[str]:
    """迁移 agent 配置。"""
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = """
    SELECT id, agent_name as name, asr_model_id, vad_model_id, llm_model_id
    FROM ai_agent
    """
    if since:
        sql += " WHERE update_date >= %s"
        cursor.execute(sql, (since,))
    else:
        cursor.execute(sql)
    rows: List[Dict[str, Any]] = cursor.fetchall()  # type: ignore
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"agent:{row['id']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_chat_shard(date_str: str) -> int:
    """
    示例：迁移某日的聊天分片。
    返回迁移条数，用于统计。
    """
    # TODO: 拉取 chat_history 按日期分片
    messages: List[Dict[str, Any]] = []
    client = get_eloqkv_client()
    count = 0
    for msg in messages:
        key = f"chat:{msg['device']}:{date_str}"
        client.rpush(key, msg)  # type: ignore[attr-defined]
        count += 1
    return count


def migrate_sessions(since: Optional[str] = None) -> List[str]:
    """
    迁移会话/token：写入 session:{token}。
    注意：需要按实际表/字段调整查询。
    """
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT user_id, token, expire_date as expire_at, update_date as updated_at FROM sys_user_token"
    if since:
        sql += " WHERE update_date >= %s"
        cursor.execute(sql, (since,))
    else:
        cursor.execute(sql)
    rows: List[Dict[str, Any]] = cursor.fetchall()  # type: ignore
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"session:{row['token']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_models(since: Optional[str] = None) -> List[str]:
    """
    迁移模型配置：按实际表/字段调整。
    """
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id, model_type, model_name, config_json FROM ai_model_config"
    params: tuple = ()
    if since:
        sql += " WHERE update_date >= %s"
        params = (since,)
    cursor.execute(sql, params)
    rows: List[Dict[str, Any]] = cursor.fetchall()  # type: ignore
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"model:{row['model_type']}:{row['model_name']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(description="EloqKV migration (skeleton)")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", help="增量迁移起始时间戳或日期", default=None)
    args = parser.parse_args()

    if args.mode == "full":
        migrate_users()
        migrate_devices()
        migrate_agents()
        migrate_sessions()
        migrate_models()
        # TODO: 聊天分片按日期循环
    else:
        migrate_users(since=args.since)
        migrate_devices(since=args.since)
        migrate_agents(since=args.since)
        migrate_sessions(since=args.since)
        migrate_models(since=args.since)
        # TODO: 增量聊天分片

    print("Migration skeleton completed (fill TODOs before production run).")


if __name__ == "__main__":
    main()
