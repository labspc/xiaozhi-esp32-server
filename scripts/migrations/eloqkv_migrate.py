"""
EloqKV 迁移脚本骨架

目标：
- 从 MySQL/Redis 拉取核心数据（用户/设备/agent/会话/聊天分片）
- 写入 EloqKV，支持全量与增量模式
- 输出校验报告（行数、哈希、抽样业务查询）

注意：
- 填写实际连接字符串和查询语句
- 运行前先影子环境验证；正式迁移前切只读标记
- 对照 docs-refactor/ELOQKV_KEYS.md 的 Key 规范
"""

import argparse
import hashlib
import os
from typing import Any, Dict, List, Optional

MYSQL_DSN = os.getenv("MYSQL_DSN", "mysql://user:password@host:3306/db")
ELOQKV_DSN = os.getenv("ELOQKV_DSN", "redis://host:6379")


def get_mysql_conn():
    """
    返回 MySQL 连接；需要安装 mysql-connector-python 或 pymysql。
    用实际库替换注释。
    """
    try:
        import mysql.connector  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Please install mysql-connector-python") from exc
    # DSN 示例：mysql+mysqlconnector://user:password@host:3306/db 不直接被 mysql.connector 解析
    # 用户需根据环境拆分 DSN；这里简化为使用环境变量各项
    return mysql.connector.connect(option_files=None, option_groups=None, dsn=MYSQL_DSN)


def get_eloqkv_client():
    """
    返回 EloqKV 客户端；可兼容 redis 协议。
    用实际库替换注释。
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
    """示例：迁移用户表，返回校验哈希列表。"""
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
        hashes.append(hash_dict(row))
    return hashes


def migrate_devices(since: Optional[str] = None) -> List[str]:
    """示例：迁移设备表，返回校验哈希列表。"""
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
        key = f"device:{row['mac_address']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_agents(since: Optional[str] = None) -> List[str]:
    """示例：迁移 agent 配置。"""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="EloqKV migration (skeleton)")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--since", help="增量迁移起始时间戳或日期", default=None)
    args = parser.parse_args()

    if args.mode == "full":
        migrate_users()
        migrate_devices()
        migrate_agents()
        # TODO: 增补会话/聊天分片
    else:
        migrate_users(since=args.since)
        migrate_devices(since=args.since)
        migrate_agents(since=args.since)
        # TODO: 增量聊天分片

    print("Migration skeleton completed (fill TODOs before production run).")


if __name__ == "__main__":
    main()
