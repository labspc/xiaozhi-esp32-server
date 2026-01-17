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

FFI 约定（草案，C ABI）：
- `int opus_decode(const uint8_t* in, int32_t in_len, int32_t sample_rate, int32_t channels, int16_t* out, int32_t out_len);` 返回写入的样本数或负值错误码。
- `int pcm_to_float(const int16_t* in, int32_t len, float* out);` 返回写入元素数。
- `float vad_energy(const float* in, int32_t len);` 返回能量值。
- 错误码：0 或正值表示长度，负值表示失败（-1 decode error, -2 invalid arg）。

Python 侧：使用 `ctypes`/`cffi`，需提供 out buffer 与检查返回值，失败回退到 Python 实现。
