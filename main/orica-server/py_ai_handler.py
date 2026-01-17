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
    文本处理示例：
    - 空文本返回错误
    - 其他情况：模拟 LLM 回复
    """
    if not text.strip():
        return {"content": None, "error": "empty text"}

    # TODO: 替换为真实 LLM/工具链调用
    reply = f"[AI simulated reply] {text}"
    return {"content": reply, "error": None}


def handle_binary(data: bytes, meta: Optional[dict] = None) -> BinaryResult:
    """
    二进制/音频处理示例：
    - 空数据返回错误
    - 读取 meta（如 sample_rate/format/session_id），可据此调用 ASR/TTS
    - 当前逻辑只返回错误或原始数据
    """
    if not data:
        return {"data": None, "error": "empty binary"}

    # TODO: 替换为真实音频处理：解码/识别/合成
    _ = meta
    return {"data": data, "error": None}
