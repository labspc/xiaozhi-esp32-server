# Mojo Audio Accelerators (Stub)

目标：为音频关键路径提供 Opus/PCM/VAD 加速模块，并通过 FFI 暴露给 Python。

当前状态：Rust stub 已提供 C ABI（基于 libopus + 简单 PCM/VAD），用于在 Python 中验证接口；后续可替换为 Mojo 实现。

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

本地构建提示：
- 依赖系统 `libopus`（Homebrew: `brew install opus`）。已在 `.cargo/config.toml` 中写入 `PKG_CONFIG_PATH=/opt/homebrew/opt/opus/lib/pkgconfig`，确保优先使用系统包，避免 CMake 重新编译。
- `cargo build` 生成 `target/debug/libmojo_audio.dylib`（或对应 release 版本）。
