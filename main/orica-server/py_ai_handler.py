"""
Python AI Handler 协议（简易实现示例）

文本消息：
- 输入：str
- 输出：
  - None：服务器回显原文
  - str：服务器发送该字符串
  - dict：{ "content": str, "error": str|None }

二进制消息（音频等）：
- 输入：bytes，meta 可包含 { "sample_rate": int, "format": str, "session_id": str }
- 输出：
  - None：不回传
  - bytes：处理后的数据
  - dict：{ "data": bytes, "error": str|None }
"""
from typing import Any, Dict, Optional, Union

TextResult = Union[str, Dict[str, Any], None]
BinaryResult = Union[bytes, Dict[str, Any], None]


def handle_text(text: str) -> TextResult:
    """
    简单逻辑示例：
    - 如果输入为空，返回错误
    - 否则返回大写内容作为“AI 回复”
    """
    if not text.strip():
        return {"content": None, "error": "empty text"}
    return {"content": f"[AI] {text.upper()}", "error": None}


def handle_binary(data: bytes, meta: Optional[dict] = None) -> BinaryResult:
    """
    简单逻辑示例：
    - 如果二进制为空，返回错误
    - 否则直接回传数据（可替换为音频处理）
    """
    if not data:
        return {"data": None, "error": "empty binary"}
    # 可在此做解码/特征提取/推理
    return {"data": data, "error": None}
