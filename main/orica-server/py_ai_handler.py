"""
Python AI Handler 示例
- handle_text: 处理文本消息，返回字符串（或 None 表示不替换）
- handle_binary: 处理二进制消息（音频等），可添加实际逻辑
"""

def handle_text(text: str) -> str | None:
    # TODO: 替换为实际 AI 处理
    return f"py_response: {text}"


def handle_binary(data: bytes) -> None:
    # TODO: 处理音频帧或二进制消息
    _ = data
    return None
