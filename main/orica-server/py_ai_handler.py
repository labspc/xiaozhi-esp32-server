"""
Python AI Handler 协议示例
传输格式（建议）：
- 文本消息：纯文本，返回 None 回显原文，返回 str 替换回复
- 音频/二进制：bytes，内部自定义处理，可返回 None

建议定义：
- handle_text(text: str) -> str | None
- handle_binary(data: bytes, meta: dict | None = None) -> bytes | None
"""

def handle_text(text: str) -> str | None:
    # TODO: 替换为实际 AI 处理（LLM/工具调用）
    return f"py_response: {text}"


def handle_binary(data: bytes, meta: dict | None = None) -> bytes | None:
    # TODO: 处理音频帧或二进制消息，返回处理后的数据或 None
    _ = (data, meta)
    return None
