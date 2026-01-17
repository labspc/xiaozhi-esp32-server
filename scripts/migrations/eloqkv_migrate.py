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
from typing import Any, Dict, List

MYSQL_DSN = "mysql://user:password@host:3306/db"  # TODO: 覆盖
ELOQKV_DSN = "redis://host:6379"  # TODO: 覆盖


def get_mysql_conn():
    """TODO: 返回真实 MySQL 连接。"""
    # import mysql.connector
    # return mysql.connector.connect(MYSQL_DSN)
    raise NotImplementedError("Replace with real MySQL connector and DSN")


def get_eloqkv_client():
    """TODO: 返回真实 EloqKV 客户端。"""
    # import redis
    # return redis.Redis.from_url(ELOQKV_DSN, decode_responses=True)
    raise NotImplementedError("Replace with real EloqKV client and DSN")


def hash_dict(d: Dict[str, Any]) -> str:
    """稳定哈希，用于迁移后校验."""
    m = hashlib.sha256()
    for k in sorted(d.keys()):
        m.update(str(k).encode())
        m.update(str(d[k]).encode())
    return m.hexdigest()


def migrate_users() -> List[str]:
    """示例：迁移用户表，返回校验哈希列表."""
    # TODO: 用 SQL 查询 sys_user
    rows: List[Dict[str, Any]] = []
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"user:{row['id']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_devices() -> List[str]:
    """示例：迁移设备表，返回校验哈希列表."""
    # TODO: SQL 查询 ai_device
    rows: List[Dict[str, Any]] = []
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"device:{row['mac_address']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def migrate_agents() -> List[str]:
    """示例：迁移 agent 配置."""
    rows: List[Dict[str, Any]] = []
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
    args = parser.parse_args()

    if args.mode == "full":
        migrate_users()
        migrate_devices()
        migrate_agents()
        # TODO: 增补会话/聊天分片
    else:
        # TODO: 增量逻辑
        pass

    print("Migration skeleton completed (fill TODOs before production run).")


if __name__ == "__main__":
    main()
