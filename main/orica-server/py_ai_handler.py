"""
Python AI Handler 协议（示例实现）

约定：
- 文本消息：handle_text 接收 str，返回 str 作为回复，返回 None 表示回显原文。
- 二进制消息：handle_binary 接收 bytes（可选 meta），返回 bytes 作为处理结果，返回 None 表示不回传。

可根据实际需求扩展 meta（如采样率/格式/会话 ID），并引入真实模型/工具调用。
"""

def handle_text(text: str) -> str | None:
    """
    文本处理示例：前缀回复，替换为真实 LLM/工具链调用。
    """
    # TODO: 接入真实 AI 处理
    return f"[AI] {text}"


def handle_binary(data: bytes, meta: dict | None = None) -> bytes | None:
    """
    二进制处理示例：当前不处理，返回 None。
    可在此添加音频解码、识别或特征提取，并返回处理后的数据。
    """
    _ = (data, meta)
    return None
