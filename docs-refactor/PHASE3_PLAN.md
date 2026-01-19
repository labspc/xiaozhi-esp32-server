# Phase3 音频性能优化计划（Rust 实现，保留 Mojo 兼容 ABI）

## 目标
- 为音频关键路径提供加速（Opus/PCM/VAD），通过 FFI 暴露给 Python。
- 当前采用 Rust 实现并导出与 Mojo 兼容的 C ABI，保留未来替换为 Mojo 的空间。
- 提供回退开关，保持功能可用。

## 任务建议
1) 定义 C ABI 接口（opus_decode/encode、pcm_to_float、vad_energy）。
2) Mojo 模块实现与测试；导出共享库。
3) Python FFI 封装与配置切换；回退到 Python 实现。
4) 基准测试：延迟/吞吐对比，更新文档。

## 状态
- Rust FFI 已实现并可编译链接系统 `libopus`（`main/xiaozhi-server/mojo/`），导出 `opus_decode`/`opus_encode`/`pcm_to_float`/`vad_energy`（ABI 兼容 Mojo 命名以便后续替换）。
- Python 侧提供 `mojo/ffi/MojoAudioFFI`（ctypes 加载 + Python 回退）。
- 配置开关已接入：`config.yaml` -> `mojo.audio_enabled/audio_lib`（可被环境变量覆盖），启动日志会输出启用/禁用原因。
- 辅助脚本：`scripts/mojo_smoke.sh` 运行 smoke test（需 `opuslib_next`）。
- CI 辅助：`scripts/mojo_smoke_ci.sh` 会自建 venv、安装 `opuslib_next` 并运行 smoke test。
- 已补充 Opus encode FFI + Python 封装（编码路径回退）。
- 基准：`scripts/bench_mojo_audio.py` 对比 Rust FFI/opuslib 编解码耗时（需 `opuslib_next`）。
- 后续可选：补充 VAD 特征/批处理；若未来引入 Mojo，可复用当前 ABI/脚本。
