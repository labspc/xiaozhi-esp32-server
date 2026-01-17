# Mojo FFI 占位
- 目标：加载编译后的 Mojo 共享库（如 `libmojo_audio.so`），供 Python 调用。
- 状态：未实现，等待 Mojo 侧导出稳定 ABI。
- 提醒：在实现前请定义清晰的 C ABI（函数签名、返回长度、错误码）。
