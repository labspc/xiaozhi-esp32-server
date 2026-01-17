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
import sys
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple

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


def migrate_users(since: Optional[str] = None, dry_run: bool = False) -> List[str]:
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
        if not dry_run:
            client.hset(key, mapping=row)  # type: ignore[attr-defined]
            if "username" in row:
                client.set(f"user:username:{row['username']}", row["id"])  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_devices(since: Optional[str] = None, dry_run: bool = False) -> List[str]:
    """
    迁移设备：写入 device:{mac}，并建立用户到设备的索引。
    返回校验哈希列表。
    """
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT mac_address, user_id, agent_id, last_connected_at as last_seen, firmware_version, board, alias, update_date FROM ai_device"
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
        if not dry_run:
            client.hset(key, mapping=row)  # type: ignore[attr-defined]
            if row.get("user_id"):
                client.sadd(f"device:user:{row['user_id']}", mac)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_agents(since: Optional[str] = None, dry_run: bool = False) -> List[str]:
    """迁移 agent 配置。"""
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = """
    SELECT id, agent_name as name, asr_model_id, vad_model_id, llm_model_id, update_date
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
        if not dry_run:
            client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_chat_shard(date_str: str, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    示例：迁移某日的聊天分片。
    返回迁移条数，用于统计。
    """
    # TODO: 拉取 chat_history 按日期分片（按实际表字段调整）
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = """
    SELECT device_mac as device, timestamp, role, content, meta_json
    FROM chat_history
    WHERE DATE(timestamp) = %s
    ORDER BY timestamp ASC
    """
    cursor.execute(sql, (date_str,))
    messages: List[Dict[str, Any]] = cursor.fetchall()  # type: ignore
    client = get_eloqkv_client()
    count = 0
    hashes: List[str] = []
    for msg in messages:
        device = msg["device"]
        key = f"chat:{device}:{date_str}"
        if not dry_run:
            client.rpush(key, msg)  # type: ignore[attr-defined]
        count += 1
        hashes.append(hash_dict(msg))
    return count, hashes


def migrate_sessions(since: Optional[str] = None, dry_run: bool = False) -> List[str]:
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
        if not dry_run:
            client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_models(since: Optional[str] = None, dry_run: bool = False) -> List[str]:
    """
    迁移模型配置：按实际表/字段调整。
    """
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id, model_type, model_name, config_json, update_date FROM ai_model_config"
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
        if not dry_run:
            client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(description="EloqKV migration (skeleton)")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", help="增量迁移起始时间戳或日期", default=None)
    parser.add_argument("--chat-date", help="迁移指定日期的聊天分片 (YYYYMMDD)", default=None)
    parser.add_argument("--dry-run", action="store_true", help="仅打印数量，不写入 EloqKV")
    parser.add_argument("--report", help="校验报告输出路径", default=None)
    parser.add_argument("--sample", type=int, default=5, help="抽样哈希条数输出")
    args = parser.parse_args()

    dry_run = args.dry_run
    report: List[Tuple[str, int]] = []
    samples: List[Tuple[str, List[str]]] = []

    if args.mode == "full":
        hashes_users = migrate_users(dry_run=dry_run)
        report.append(("users", len(hashes_users)))
        samples.append(("users", hashes_users[: args.sample]))

        hashes_devices = migrate_devices(dry_run=dry_run)
        report.append(("devices", len(hashes_devices)))
        samples.append(("devices", hashes_devices[: args.sample]))

        hashes_agents = migrate_agents(dry_run=dry_run)
        report.append(("agents", len(hashes_agents)))
        samples.append(("agents", hashes_agents[: args.sample]))

        hashes_sessions = migrate_sessions(dry_run=dry_run)
        report.append(("sessions", len(hashes_sessions)))
        samples.append(("sessions", hashes_sessions[: args.sample]))

        hashes_models = migrate_models(dry_run=dry_run)
        report.append(("models", len(hashes_models)))
        samples.append(("models", hashes_models[: args.sample]))

        if args.chat_date:
            count, hash_chat = migrate_chat_shard(args.chat_date, dry_run=dry_run)
            report.append((f"chat:{args.chat_date}", count))
            samples.append((f"chat:{args.chat_date}", hash_chat[: args.sample]))
        else:
            print("⚠️  chat-date 未指定，聊天分片未迁移", file=sys.stderr)
    else:
        hashes_users = migrate_users(since=args.since, dry_run=dry_run)
        report.append(("users", len(hashes_users)))
        samples.append(("users", hashes_users[: args.sample]))

        hashes_devices = migrate_devices(since=args.since, dry_run=dry_run)
        report.append(("devices", len(hashes_devices)))
        samples.append(("devices", hashes_devices[: args.sample]))

        hashes_agents = migrate_agents(since=args.since, dry_run=dry_run)
        report.append(("agents", len(hashes_agents)))
        samples.append(("agents", hashes_agents[: args.sample]))

        hashes_sessions = migrate_sessions(since=args.since, dry_run=dry_run)
        report.append(("sessions", len(hashes_sessions)))
        samples.append(("sessions", hashes_sessions[: args.sample]))

        hashes_models = migrate_models(since=args.since, dry_run=dry_run)
        report.append(("models", len(hashes_models)))
        samples.append(("models", hashes_models[: args.sample]))

        if args.chat_date:
            count, hash_chat = migrate_chat_shard(args.chat_date, dry_run=dry_run)
            report.append((f"chat:{args.chat_date}", count))
            samples.append((f"chat:{args.chat_date}", hash_chat[: args.sample]))
        else:
            print("⚠️  chat-date 未指定，聊天分片增量未迁移", file=sys.stderr)

    print("Migration skeleton completed (fill TODOs before production run).")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            for name, cnt in report:
                f.write(f"{name},{cnt}\n")
            f.write("samples:\n")
            for name, s in samples:
                f.write(f"{name}:{';'.join(s)}\n")
    else:
        for name, cnt in report:
            print(f"{name}: {cnt}")
        for name, s in samples:
            print(f"sample {name}: {s}")


if __name__ == "__main__":
    main()
