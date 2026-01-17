"""
Python AI Handler 示例
- handle_text: 处理文本消息，返回字符串（或 None 表示不替换）
- handle_binary: 处理二进制消息（音频等），可添加实际逻辑
"""

def handle_text(text: str) -> str | None:
    """
    文本消息处理示例：
    - 返回 None 时，服务器回显原文
    - 返回字符串时，服务器发送此字符串
    """
    return f"py_response: {text}"


def handle_binary(data: bytes) -> None:
    """
    二进制消息处理示例（音频帧等）：
    - 可在此进行解码、分析或调用模型
    - 当前占位不做处理
    """
    _ = data
    return None
