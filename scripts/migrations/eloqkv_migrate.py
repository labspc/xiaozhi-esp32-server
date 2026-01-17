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

# TODO: 替换为真实依赖/连接
def get_mysql_conn():
    raise NotImplementedError("Replace with real MySQL connector")


def get_eloqkv_client():
    raise NotImplementedError("Replace with real EloqKV client")


def hash_dict(d: Dict[str, Any]) -> str:
    """稳定哈希，用于迁移后校验."""
    m = hashlib.sha256()
    for k in sorted(d.keys()):
        m.update(str(k).encode())
        m.update(str(d[k]).encode())
    return m.hexdigest()


def migrate_users() -> List[str]:
    """示例：迁移用户表，返回校验哈希列表."""
    # TODO: 填写查询
    rows: List[Dict[str, Any]] = []
    client = get_eloqkv_client()
    hashes: List[str] = []
    for row in rows:
        key = f"user:{row['id']}"
        client.hset(key, mapping=row)  # type: ignore[attr-defined]
        hashes.append(hash_dict(row))
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(description="EloqKV migration (skeleton)")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()

    if args.mode == "full":
        migrate_users()
        # TODO: 增补设备/agent/会话/聊天分片
    else:
        # TODO: 增量逻辑
        pass

    print("Migration skeleton completed (fill TODOs before production run).")


if __name__ == "__main__":
    main()
