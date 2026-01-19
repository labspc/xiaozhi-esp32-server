# Audio Accelerators (Rust FFI，兼容 Mojo ABI)

目标：为音频关键路径提供 Opus/PCM/VAD 加速模块，并通过 FFI 暴露给 Python。当前实现基于 Rust（链接系统 libopus），导出与 Mojo 兼容的 C ABI，便于未来替换为 Mojo，同时即刻可用。

当前状态：Rust FFI 已提供 C ABI（基于 libopus，包含 decode/encode/PCM/VAD），Python 已接入；如未来需要 Mojo，只需保持相同 ABI。

FFI 约定（C ABI，与 Mojo 兼容命名）：
- `int opus_decode(const uint8_t* in, int32_t in_len, int32_t sample_rate, int32_t channels, int16_t* out, int32_t out_len);` 返回写入的样本数或负值错误码。
- `int opus_encode(const int16_t* in, int32_t samples, int32_t sample_rate, int32_t channels, uint8_t* out, int32_t out_len);` 返回写入的字节数或负值错误码。
- `int pcm_to_float(const int16_t* in, int32_t len, float* out);` 返回写入元素数。
- `float vad_energy(const float* in, int32_t len);` 返回能量值。
- 错误码：0 或正值表示长度，负值表示失败（-1 decode/encode error, -2 invalid arg）。

本地构建提示（Rust 版）：
- 依赖系统 `libopus`（Homebrew: `brew install opus`）。已在 `.cargo/config.toml` 中写入 `PKG_CONFIG_PATH=/opt/homebrew/opt/opus/lib/pkgconfig`，确保优先使用系统包，避免 CMake 重新编译。
- `cargo build` 生成 `target/debug/libmojo_audio.dylib`（或对应 release 版本）；库名保留以兼容现有 Python 载入逻辑和配置字段。

Python FFI 封装：
- `mojo/ffi/mojo_audio.py` 提供 `MojoAudioFFI`，优先加载 `MOJO_AUDIO_LIB` 指定的共享库，回退到默认 `target/{release,debug}/libmojo_audio.*`。当库不可用时，会自动回退到 `opuslib_next`/纯 Python 实现。
- 示例：
  ```python
  from mojo.ffi import MojoAudioFFI

  mojo = MojoAudioFFI()
  pcm_bytes = mojo.decode_opus(opus_packet)  # bytes or None
  float_bytes = mojo.pcm_to_float(pcm_bytes or b"")
  energy = mojo.vad_energy(float_bytes or b"")
  opus_bytes = mojo.encode_opus(pcm_bytes or b"")
  ```
- 配置开关：`config.yaml` 可设置 `mojo.audio_enabled`、`mojo.audio_lib`；环境变量 `MOJO_AUDIO_ENABLED`/`MOJO_AUDIO_LIB` 优先，启动日志会输出当前状态。
- 快速自检：`scripts/mojo_smoke.sh`（需 `opuslib_next`，可在虚拟环境中执行）；CI 可使用 `scripts/mojo_smoke_ci.sh`。
- 简易基准：`scripts/bench_mojo_audio.py`（需要 `opuslib_next`，对比 Rust FFI/opuslib 编解码耗时）。
