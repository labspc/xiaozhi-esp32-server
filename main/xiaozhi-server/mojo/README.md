# Mojo Audio Accelerators (Stub)

目标：为音频关键路径提供 Opus/PCM/VAD 加速模块，并通过 FFI 暴露给 Python。

当前状态：占位目录，尚未实现。

建议结构：
```
mojo/
  audio/
    opus_decode.mojo
    pcm_convert.mojo
    vad_features.mojo
  ffi/
    lib.mojo         # 导出 C ABI 接口
```

FFI 约定（示例）：
- `opus_decode(input_ptr: Pointer[UInt8], len: Int32, sample_rate: Int32, channels: Int32) -> Pointer[Int16]`
- `pcm_to_float(input_ptr: Pointer[Int16], len: Int32) -> Pointer[Float32]`
- `vad_energy(input_ptr: Pointer[Float32], len: Int32) -> Float32`

Python 侧：使用 `ctypes`/`cffi` 调用，提供回退开关。
