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
    文本处理：
    - 空文本返回错误
    - 正常情况：调用 LLM，失败时返回 error
    """
    if not text.strip():
        return {"content": None, "error": "empty text"}
    try:
        reply = run_llm(text)
        return {"content": reply, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"content": None, "error": f"llm_error: {exc}"}


def handle_binary(data: bytes, meta: Optional[dict] = None) -> BinaryResult:
    """
    二进制/音频处理：
    - 空数据返回错误
    - meta 可包含 { "mode": "asr"|"tts", "sample_rate": int, "format": str, "session_id": str }
    - 失败时返回 error
    """
    if not data:
        return {"data": None, "error": "empty binary"}

    try:
        mode = (meta or {}).get("mode", "asr")
        if mode == "asr":
            text = run_asr(data, meta or {})
            return {"data": text.encode("utf-8"), "error": None}
        if mode == "tts":
            audio = run_tts((meta or {}).get("text", ""), meta or {})
            return {"data": audio, "error": None}
        return {"data": data, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"data": None, "error": f"binary_error: {exc}"}


def run_llm(prompt: str) -> str:
    """
    TODO: 替换为真实 LLM 调用。
    当前占位：返回简单回复。
    """
    if not prompt:
        raise ValueError("empty prompt")
    return f"[LLM reply] {prompt}"


def run_asr(data: bytes, meta: Dict[str, Any]) -> str:
    """
    TODO: 替换为真实 ASR 调用。
    当前占位：返回固定提示。
    """
    _ = (data, meta)
    return "[ASR transcript placeholder]"


def run_tts(text: str, meta: Dict[str, Any]) -> bytes:
    """
    TODO: 替换为真实 TTS 调用。
    当前占位：返回空 bytes。
    """
    _ = (text, meta)
    return b""
