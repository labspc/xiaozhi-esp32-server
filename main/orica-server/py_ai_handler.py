"""
Python AI Handler 协议（示例实现）

文本消息协议：
- 输入：字符串
- 输出：
  - 返回 None：服务器回显原文
  - 返回字符串：服务器发送该字符串
  - 返回 dict：期望字段 { "content": str, "error": str|None }，content 优先

二进制消息协议（音频等）：
- 输入：bytes，meta 可包含 { "sample_rate": int, "format": str, "session_id": str }
- 输出：
  - None：不回传
  - bytes：处理后的数据（例如编码后的音频帧）
  - dict：期望字段 { "data": bytes, "error": str|None }

请替换示例逻辑为真实 AI 调用（ASR/LLM/TTS）。
"""
from typing import Any, Dict, Optional, Union


TextResult = Union[str, Dict[str, Any], None]
BinaryResult = Union[bytes, Dict[str, Any], None]


def handle_text(text: str) -> TextResult:
    # TODO: 接入真实 LLM/工具链，按需返回 dict 或 str
    return {"content": f"[AI reply] {text}"}


def handle_binary(data: bytes, meta: Optional[dict] = None) -> BinaryResult:
    # TODO: 处理音频/二进制，按需返回 dict 或 bytes
    _ = (data, meta)
    return None
