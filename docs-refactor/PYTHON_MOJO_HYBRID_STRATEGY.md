# Python-Mojo 混合架构策略

## 文档概述

本文档定义 xiaozhi-server 采用 Python-Mojo 混合架构的编码标准、互操作模式、目录结构和实施指南。

---

## 1. 架构设计原则

### 1.1 核心原则

**"用对的语言做对的事"**

| 语言 | 适用场景 | 不适用场景 |
|------|---------|-----------|
| **Python** | 异步I/O、AI SDK集成、配置管理、WebSocket服务器 | 数值计算、编解码、实时处理 |
| **Mojo** | 音频处理、数值计算、SIMD优化、性能关键路径 | 网络I/O、动态加载、AI SDK调用 |

---

### 1.2 边界划分

```
┌─────────────────────────────────────────────────────────┐
│                    Python 层                            │
│  - WebSocket 服务器 (websockets)                        │
│  - HTTP 客户端 (aiohttp)                                │
│  - AI SDK 集成 (openai, funasr)                         │
│  - 配置管理 (YAML, 环境变量)                             │
│  - 日志系统 (loguru)                                     │
│  - Provider 框架 (动态加载)                              │
└──────────────────┬──────────────────────────────────────┘
                   │ FFI / ctypes / C-API
┌──────────────────┴──────────────────────────────────────┐
│                    Mojo 层                              │
│  - Opus 编解码 (libopus FFI)                            │
│  - 音频数值处理 (SIMD 优化)                              │
│  - VAD 特征提取 (能量、过零率)                           │
│  - PCM 格式转换                                          │
│  - 实时音频流处理                                        │
└─────────────────────────────────────────────────────────┘
```

---

### 1.3 设计哲学

根据项目中的 `RUST_SIMPLE_GUIDE.md` 精神，制定 **Mojo Simple Guide**：

**禁止事项**：
1. ❌ 禁止在Mojo中使用动态类型
2. ❌ 禁止复杂的闭包和函数式编程
3. ❌ 禁止unsafe操作（除非必要且有文档说明）
4. ❌ 禁止过度抽象和泛型编程
5. ❌ 禁止引入非标准库依赖（除libopus等必要库）

**推荐事项**：
1. ✅ 所有函数和变量显式类型注解
2. ✅ 手动实现trait，不使用自动派生
3. ✅ 优先使用SIMD向量化
4. ✅ 显式内存管理，及时释放
5. ✅ 简单、直接、可追溯的代码风格

---

## 2. 项目目录结构

### 2.1 混合架构目录

```
xiaozhi-esp32-server/
├── main/
│   ├── xiaozhi-server/               # Python主项目
│   │   ├── app.py                    # 应用入口（Python）
│   │   ├── core/
│   │   │   ├── websocket_server.py   # WebSocket服务器（Python）
│   │   │   ├── connection.py         # 连接处理（Python）
│   │   │   ├── providers/            # AI Provider（Python）
│   │   │   │   ├── asr/
│   │   │   │   │   ├── base.py       # Python调用Mojo模块
│   │   │   │   │   ├── fun_local.py
│   │   │   │   │   └── openai_api.py
│   │   │   │   └── ...
│   │   │   └── handle/               # 消息处理（Python）
│   │   ├── config/                   # 配置管理（Python）
│   │   ├── plugins_func/             # 插件系统（Python）
│   │   └── requirements.txt
│   │
│   ├── xiaozhi-server-mojo/          # Mojo加速模块（新增）
│   │   ├── __init__.mojo             # Mojo包初始化
│   │   ├── audio/                    # 音频处理模块
│   │   │   ├── opus_codec.mojo       # Opus编解码
│   │   │   ├── processing.mojo       # 音频数值处理
│   │   │   ├── simd_utils.mojo       # SIMD工具函数
│   │   │   └── buffer.mojo           # 音频缓冲区管理
│   │   ├── vad/                      # VAD加速模块
│   │   │   ├── features.mojo         # 特征提取
│   │   │   └── energy.mojo           # 能量计算
│   │   ├── utils/                    # 通用工具
│   │   │   ├── types.mojo            # 通用类型定义
│   │   │   └── ffi_helpers.mojo      # FFI辅助函数
│   │   ├── bindings/                 # Python绑定
│   │   │   ├── audio_bindings.mojo   # 音频模块绑定
│   │   │   └── vad_bindings.mojo     # VAD模块绑定
│   │   ├── tests/                    # Mojo单元测试
│   │   │   ├── test_opus.mojo
│   │   │   └── test_processing.mojo
│   │   └── build.sh                  # 编译脚本
│   │
│   ├── manager-api/                  # Java后端（保持不变）
│   ├── manager-web/                  # Vue前端（保持不变）
│   └── manager-mobile/               # uni-app移动端（保持不变）
│
├── docs/                             # 文档
│   ├── PYTHON_SYNTAX_FRAMEWORK_ANALYSIS.md
│   ├── MOJO_REWRITE_CANDIDATES.md
│   └── PYTHON_MOJO_HYBRID_STRATEGY.md (本文档)
│
└── README.md
```

---

### 2.2 编译产物目录

```
main/xiaozhi-server-mojo/
├── build/                            # 编译中间产物
│   ├── audio.o
│   └── vad.o
├── lib/                              # 编译后的库文件
│   ├── libxiaozhi_audio.so           # Linux
│   ├── libxiaozhi_audio.dylib        # macOS
│   └── xiaozhi_audio.dll             # Windows
└── dist/                             # Python可导入的包
    └── xiaozhi_mojo/
        ├── __init__.py
        ├── audio.py                  # Python绑定
        └── _audio.so                 # 编译后的Mojo库
```

---

## 3. Python-Mojo 互操作规范

### 3.1 数据传递协议

#### 3.1.1 标量类型映射

| Python类型 | Mojo类型 | C类型 | 说明 |
|-----------|---------|-------|------|
| `int` | `Int` | `int64_t` | 64位整数 |
| `float` | `Float64` | `double` | 64位浮点 |
| `bool` | `Bool` | `bool` | 布尔值 |
| `str` | `String` | `char*` | UTF-8字符串 |
| `bytes` | `DTypePointer[DType.uint8]` | `uint8_t*` | 字节数组 |

---

#### 3.1.2 复杂类型映射

**Python bytes → Mojo 音频数据**
```python
# Python侧
import xiaozhi_mojo.audio as mojo_audio

def process_audio(opus_data: bytes) -> bytes:
    """调用Mojo处理音频"""
    # Python bytes自动转为Mojo DTypePointer[DType.uint8]
    pcm_data = mojo_audio.decode_opus(opus_data)
    return pcm_data  # Mojo返回值自动转为Python bytes
```

**Mojo侧实现**（通过C-API导出）
```mojo
from python import Python, PythonObject

fn decode_opus_py(opus_bytes: PythonObject) -> PythonObject:
    """Python可调用的Opus解码函数"""
    # 1. 提取Python bytes为指针
    let opus_ptr = opus_bytes.__bytes__().unsafe_ptr()
    let opus_len = len(opus_bytes)

    # 2. 分配输出buffer
    let pcm_size = opus_len * 4  # 预估PCM大小
    let pcm_buffer = DTypePointer[DType.int16].alloc(pcm_size)

    # 3. 调用Mojo核心函数
    let actual_pcm_len = decode_opus_internal(opus_ptr, opus_len, pcm_buffer)

    # 4. 转换为Python bytes
    let result = Python.bytes(pcm_buffer, actual_pcm_len * 2)

    # 5. 清理
    pcm_buffer.free()

    return result
```

---

#### 3.1.3 零拷贝数据传递（高性能）

**使用 NumPy Array Protocol**
```python
# Python侧（高性能，零拷贝）
import numpy as np
import xiaozhi_mojo.audio as mojo_audio

def process_audio_fast(pcm_int16: np.ndarray) -> np.ndarray:
    """零拷贝处理音频"""
    # NumPy数组直接传递指针给Mojo
    result = mojo_audio.pcm_to_float32_inplace(pcm_int16)
    return result
```

**Mojo侧实现（接收NumPy数组）**
```mojo
fn pcm_to_float32_numpy(array: PythonObject) -> PythonObject:
    """接收NumPy数组，零拷贝处理"""
    let np = Python.import_module("numpy")

    # 1. 获取NumPy数组元信息
    let shape = array.shape
    let dtype = array.dtype
    let data_ptr = array.__array_interface__["data"][0]

    # 2. 转换为Mojo指针（零拷贝）
    let pcm_ptr = DTypePointer[DType.int16](address=data_ptr)
    let length = Int(shape[0])

    # 3. 分配输出buffer
    let float_buffer = DTypePointer[DType.float32].alloc(length)

    # 4. SIMD处理
    pcm_to_float32(pcm_ptr, length, float_buffer)

    # 5. 包装为NumPy数组（使用现有buffer）
    let result = np.frombuffer(float_buffer, dtype=np.float32, count=length)

    return result
```

---

### 3.2 错误处理规范

#### 3.2.1 Mojo错误传递到Python

**Mojo侧**
```mojo
from python import Python

fn decode_opus_safe(opus_data: DTypePointer[DType.uint8],
                    opus_len: Int) raises -> DTypePointer[DType.int16]:
    """可抛出异常的Opus解码"""
    if opus_len <= 0:
        raise Error("Invalid Opus data length")

    # ... 解码逻辑

    if decode_failed:
        raise Error("Opus decoding failed")

    return pcm_buffer
```

**Python侧捕获**
```python
import xiaozhi_mojo.audio as mojo_audio

try:
    pcm_data = mojo_audio.decode_opus(opus_data)
except RuntimeError as e:
    logger.error(f"Mojo解码失败: {e}")
    # 回退到Python实现
    pcm_data = python_opus_decode(opus_data)
```

---

#### 3.2.2 返回值 + 错误码模式（无异常）

**Mojo侧**
```mojo
struct OpusDecodeResult:
    var pcm_data: DTypePointer[DType.int16]
    var length: Int
    var error_code: Int  # 0 = success, -1 = error

fn decode_opus_result(opus_data: DTypePointer[DType.uint8],
                      opus_len: Int) -> OpusDecodeResult:
    """返回结果结构体，不抛异常"""
    if opus_len <= 0:
        return OpusDecodeResult(
            pcm_data=DTypePointer[DType.int16](),
            length=0,
            error_code=-1
        )

    # ... 解码逻辑

    return OpusDecodeResult(
        pcm_data=pcm_buffer,
        length=actual_len,
        error_code=0
    )
```

**Python侧处理**
```python
result = mojo_audio.decode_opus_result(opus_data)
if result.error_code != 0:
    logger.error("解码失败")
    return None
pcm_data = result.pcm_data
```

---

### 3.3 线程安全和GIL

#### 3.3.1 释放GIL（性能关键）

**在耗时操作中释放GIL**
```python
# Python侧
import xiaozhi_mojo.audio as mojo_audio
import threading

def batch_process_audio(audio_list: list[bytes]):
    """并行处理多个音频，Mojo函数会释放GIL"""
    threads = []
    results = [None] * len(audio_list)

    for i, audio in enumerate(audio_list):
        def worker(idx, data):
            # Mojo函数自动释放GIL，允许真正并行
            results[idx] = mojo_audio.decode_opus(data)

        t = threading.Thread(target=worker, args=(i, audio))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results
```

**Mojo侧标记释放GIL**
```mojo
# 使用@parameter注解标记可并行执行
@parameter
fn decode_opus_parallel(opus_data: DTypePointer[DType.uint8],
                        opus_len: Int) -> DTypePointer[DType.int16]:
    """标记为可并行，Python C-API会自动释放GIL"""
    # ... 解码逻辑（不调用Python对象）
    return pcm_buffer
```

---

#### 3.3.2 线程安全的Mojo对象

**使用原子操作保证线程安全**
```mojo
from sys.threading import atomic

struct ThreadSafeAudioQueue:
    """线程安全的音频队列"""
    var buffer: DTypePointer[AudioFrame]
    var capacity: Int
    var head: atomic.Atomic[Int]
    var tail: atomic.Atomic[Int]

    fn push(inout self, frame: AudioFrame) -> Bool:
        """线程安全推入"""
        let current_tail = self.tail.load(atomic.Ordering.Acquire)
        let next_tail = (current_tail + 1) % self.capacity

        if next_tail == self.head.load(atomic.Ordering.Acquire):
            return False  # 队列满

        self.buffer[current_tail] = frame
        self.tail.store(next_tail, atomic.Ordering.Release)
        return True
```

---

## 4. 编码规范

### 4.1 Mojo 编码规范

#### 4.1.1 命名约定

**遵循Rust风格（参考 RUST_SIMPLE_GUIDE.md）**

```mojo
// ✅ 正确命名
fn decode_opus()              // 函数：snake_case
struct AudioBuffer            // 结构体：PascalCase
var sample_rate: Int          // 变量：snake_case
alias BUFFER_SIZE = 4096      // 常量：SCREAMING_SNAKE_CASE

// ❌ 错误命名
fn DecodeOpus()               // 函数不使用PascalCase
struct audioBuffer            // 结构体不使用camelCase
var SampleRate: Int           // 变量不使用PascalCase
```

---

#### 4.1.2 类型注解（强制）

**所有变量和函数必须显式类型注解**

```mojo
// ✅ 正确
fn process_audio(data: DTypePointer[DType.int16],
                 length: Int,
                 sample_rate: Int) -> Float32:
    var total_energy: Float32 = 0.0
    for i in range(length):
        let sample: Float32 = Float32(data[i])
        total_energy += sample * sample
    return total_energy / Float32(length)

// ❌ 错误（缺少类型注解）
fn process_audio(data, length):  // 类型不明确
    var total_energy = 0.0       // 推断类型不够明确
    return total_energy
```

---

#### 4.1.3 内存管理规范

**显式分配和释放**

```mojo
// ✅ 正确
fn process_buffer(size: Int) -> Bool:
    # 1. 分配
    let buffer = DTypePointer[DType.float32].alloc(size)

    # 2. 使用
    for i in range(size):
        buffer[i] = Float32(i)

    # 3. 释放（必须）
    buffer.free()
    return True

// ❌ 错误（内存泄漏）
fn process_buffer_leak(size: Int):
    let buffer = DTypePointer[DType.float32].alloc(size)
    # 使用buffer...
    # 忘记free() - 内存泄漏！
```

**使用RAII模式（推荐）**
```mojo
@value
struct AudioBuffer:
    var data: DTypePointer[DType.float32]
    var size: Int

    fn __init__(inout self, size: Int):
        self.data = DTypePointer[DType.float32].alloc(size)
        self.size = size

    fn __del__(owned self):
        """析构时自动释放"""
        self.data.free()

fn process_audio_safe():
    # AudioBuffer离开作用域时自动调用__del__
    let buffer = AudioBuffer(4096)
    # 使用buffer...
    # 自动释放，无需手动free()
```

---

#### 4.1.4 SIMD使用规范

**优先使用SIMD向量化**

```mojo
from algorithm import vectorize

// ✅ 正确（SIMD加速）
fn multiply_arrays_simd(a: DTypePointer[DType.float32],
                        b: DTypePointer[DType.float32],
                        out: DTypePointer[DType.float32],
                        length: Int):
    """使用SIMD加速数组乘法"""
    alias simd_width = simdbitwidth() // 32

    @parameter
    fn vectorized_multiply[simd_width: Int](idx: Int):
        let vec_a = a.load[width=simd_width](idx)
        let vec_b = b.load[width=simd_width](idx)
        let vec_result = vec_a * vec_b
        out.store[width=simd_width](idx, vec_result)

    vectorize[vectorized_multiply, simd_width](length)

// ❌ 错误（未使用SIMD，性能差）
fn multiply_arrays_slow(a, b, out, length):
    for i in range(length):
        out[i] = a[i] * b[i]  // 逐个元素，无SIMD
```

---

#### 4.1.5 错误处理规范

**使用Result类型或raises**

```mojo
// ✅ 正确（使用raises）
fn load_audio_file(path: String) raises -> AudioBuffer:
    """加载音频文件，失败时抛出异常"""
    if not file_exists(path):
        raise Error("File not found: " + path)

    let file = open_file(path)
    # ... 读取逻辑
    return buffer

// ✅ 正确（使用Optional）
fn find_peak(audio: DTypePointer[DType.float32],
             length: Int) -> Optional[Int]:
    """查找峰值索引，未找到返回None"""
    var max_val: Float32 = -1.0
    var max_idx: Optional[Int] = None

    for i in range(length):
        if audio[i] > max_val:
            max_val = audio[i]
            max_idx = i

    return max_idx
```

---

### 4.2 Python 编码规范（调用Mojo）

#### 4.2.1 导入约定

```python
# ✅ 正确
import xiaozhi_mojo.audio as mojo_audio
from xiaozhi_mojo.vad import extract_features

def process_opus(data: bytes) -> bytes:
    return mojo_audio.decode_opus(data)

# ❌ 错误（不推荐的通配符导入）
from xiaozhi_mojo.audio import *
```

---

#### 4.2.2 错误处理模式

**优雅降级到Python实现**

```python
import xiaozhi_mojo.audio as mojo_audio
from opuslib import Decoder as PythonOpusDecoder

class ASRProvider:
    def __init__(self):
        self.use_mojo = True
        self.python_decoder = None

        try:
            # 尝试使用Mojo加速版本
            mojo_audio.test_opus_available()
        except (ImportError, RuntimeError):
            logger.warning("Mojo模块不可用，降级到Python实现")
            self.use_mojo = False
            self.python_decoder = PythonOpusDecoder(16000, 1)

    def decode_opus(self, opus_data: bytes) -> bytes:
        """解码Opus，自动选择Mojo或Python"""
        try:
            if self.use_mojo:
                return mojo_audio.decode_opus(opus_data)
        except Exception as e:
            logger.error(f"Mojo解码失败: {e}，回退到Python")
            self.use_mojo = False

        # 回退到Python实现
        return self.python_decoder.decode(opus_data, frame_size=320)
```

---

#### 4.2.3 性能基准测试集成

**内置性能对比**

```python
import time
import numpy as np
import xiaozhi_mojo.audio as mojo_audio

def benchmark_and_validate():
    """基准测试并验证正确性"""
    test_audio = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)
    test_bytes = test_audio.tobytes()

    # Python版本
    start = time.perf_counter()
    for _ in range(1000):
        python_result = pcm_to_float32_python(test_bytes)
    python_time = time.perf_counter() - start

    # Mojo版本
    start = time.perf_counter()
    for _ in range(1000):
        mojo_result = mojo_audio.pcm_to_float32(test_bytes)
    mojo_time = time.perf_counter() - start

    # 验证正确性
    assert np.allclose(python_result, mojo_result, atol=1e-5), "结果不匹配！"

    speedup = python_time / mojo_time
    logger.info(f"Mojo加速倍数: {speedup:.2f}x")

    if speedup < 5.0:
        logger.warning("加速效果不理想，检查SIMD优化是否启用")

    return speedup

# 在应用启动时运行
if __name__ == "__main__":
    benchmark_and_validate()
```

---

## 5. 构建和部署

### 5.1 编译脚本

**`main/xiaozhi-server-mojo/build.sh`**
```bash
#!/bin/bash
set -e

echo "编译 Mojo 模块..."

# 1. 编译Mojo模块为共享库
mojo build audio/opus_codec.mojo -o lib/libxiaozhi_audio.so
mojo build vad/features.mojo -o lib/libxiaozhi_vad.so

# 2. 生成Python绑定
mojo package build bindings/ -o dist/xiaozhi_mojo

# 3. 运行测试
mojo test tests/

echo "✅ 编译完成！"
echo "共享库位置: lib/"
echo "Python包位置: dist/xiaozhi_mojo"
```

**使用方法**：
```bash
cd main/xiaozhi-server-mojo
./build.sh
```

---

### 5.2 Python 安装集成

**`main/xiaozhi-server-mojo/setup.py`**
```python
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import subprocess

class MojoBuildExt(build_ext):
    """自定义构建命令，调用Mojo编译器"""

    def run(self):
        # 调用Mojo编译脚本
        subprocess.check_call(['bash', 'build.sh'])
        super().run()

setup(
    name='xiaozhi_mojo',
    version='1.0.0',
    description='Mojo加速模块 for xiaozhi-server',
    packages=['xiaozhi_mojo'],
    package_dir={'xiaozhi_mojo': 'dist/xiaozhi_mojo'},
    cmdclass={'build_ext': MojoBuildExt},
    install_requires=[
        'numpy>=1.26.4',
    ],
)
```

**安装方式**：
```bash
cd main/xiaozhi-server-mojo
pip install -e .  # 开发模式安装
```

---

### 5.3 Docker 集成

**`main/xiaozhi-server/Dockerfile`（更新）**
```dockerfile
FROM python:3.10-slim

# 1. 安装Mojo SDK
RUN curl https://get.modular.com | sh && \
    modular install mojo

# 2. 安装系统依赖
RUN apt-get update && apt-get install -y \
    libopus0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. 拷贝代码
WORKDIR /app
COPY xiaozhi-server/ /app/xiaozhi-server/
COPY xiaozhi-server-mojo/ /app/xiaozhi-server-mojo/

# 4. 编译Mojo模块
WORKDIR /app/xiaozhi-server-mojo
RUN bash build.sh

# 5. 安装Python依赖
WORKDIR /app/xiaozhi-server
RUN pip install -r requirements.txt && \
    pip install -e ../xiaozhi-server-mojo

# 6. 运行应用
CMD ["python", "app.py"]
```

---

### 5.4 CI/CD 集成

**`.github/workflows/mojo-build.yml`**
```yaml
name: Build and Test Mojo Modules

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Install Mojo
        run: |
          curl https://get.modular.com | sh
          modular install mojo

      - name: Build Mojo modules
        run: |
          cd main/xiaozhi-server-mojo
          bash build.sh

      - name: Run Mojo tests
        run: |
          cd main/xiaozhi-server-mojo
          mojo test tests/

      - name: Benchmark performance
        run: |
          cd main/xiaozhi-server
          python benchmark_mojo_modules.py
```

---

## 6. 测试策略

### 6.1 单元测试（Mojo）

**`main/xiaozhi-server-mojo/tests/test_opus.mojo`**
```mojo
from testing import assert_equal, assert_true
from audio.opus_codec import decode_opus

fn test_opus_decode_basic():
    """测试基本Opus解码功能"""
    # 1. 准备测试数据（实际Opus帧）
    let test_opus_data = load_test_opus_file()

    # 2. 解码
    let pcm_buffer = DTypePointer[DType.int16].alloc(320)
    let decoded_len = decode_opus(test_opus_data, 100, pcm_buffer)

    # 3. 验证结果
    assert_true(decoded_len > 0, "解码长度应大于0")
    assert_equal(decoded_len, 320, "解码长度应为320样本")

    # 4. 清理
    pcm_buffer.free()

fn test_opus_decode_invalid_data():
    """测试无效数据处理"""
    let invalid_data = DTypePointer[DType.uint8].alloc(10)
    let pcm_buffer = DTypePointer[DType.int16].alloc(320)

    # 应该返回错误码或抛出异常
    let result = decode_opus(invalid_data, 10, pcm_buffer)
    assert_equal(result, -1, "无效数据应返回错误")

    invalid_data.free()
    pcm_buffer.free()

fn main():
    test_opus_decode_basic()
    test_opus_decode_invalid_data()
    print("✅ 所有测试通过")
```

**运行测试**：
```bash
mojo test main/xiaozhi-server-mojo/tests/test_opus.mojo
```

---

### 6.2 集成测试（Python调用Mojo）

**`main/xiaozhi-server/tests/test_mojo_integration.py`**
```python
import pytest
import numpy as np
import xiaozhi_mojo.audio as mojo_audio

def test_opus_decode_integration():
    """测试Mojo Opus解码的Python集成"""
    # 1. 加载真实Opus文件
    with open("tests/data/test_audio.opus", "rb") as f:
        opus_data = f.read()

    # 2. 调用Mojo解码
    pcm_data = mojo_audio.decode_opus(opus_data)

    # 3. 验证结果
    assert isinstance(pcm_data, bytes)
    assert len(pcm_data) > 0
    assert len(pcm_data) % 2 == 0  # int16是2字节

    # 4. 转换为NumPy数组验证
    pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
    assert pcm_array.dtype == np.int16
    assert len(pcm_array) > 0

def test_pcm_to_float32_accuracy():
    """测试PCM转float32的精度"""
    # 1. 创建测试数据
    test_pcm = np.array([0, 16384, 32767, -16384, -32768], dtype=np.int16)
    expected_float = test_pcm.astype(np.float32) / 32768.0

    # 2. Mojo转换
    mojo_result = mojo_audio.pcm_to_float32(test_pcm.tobytes())
    mojo_array = np.frombuffer(mojo_result, dtype=np.float32)

    # 3. 验证精度
    np.testing.assert_allclose(mojo_array, expected_float, atol=1e-5)

def test_performance_speedup():
    """测试性能提升"""
    import time

    # 生成测试数据
    test_audio = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)
    test_bytes = test_audio.tobytes()

    # Python版本基准
    start = time.perf_counter()
    for _ in range(1000):
        python_result = (test_audio.astype(np.float32) / 32768.0)
    python_time = time.perf_counter() - start

    # Mojo版本
    start = time.perf_counter()
    for _ in range(1000):
        mojo_result = mojo_audio.pcm_to_float32(test_bytes)
    mojo_time = time.perf_counter() - start

    speedup = python_time / mojo_time
    assert speedup >= 5.0, f"加速不足：{speedup:.2f}x，预期>=5x"
    print(f"✅ Mojo加速: {speedup:.2f}x")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

### 6.3 端到端测试

**验证混合架构的完整流程**

```python
# tests/test_e2e_hybrid.py
import asyncio
import xiaozhi_mojo.audio as mojo_audio
from core.providers.asr.fun_local import FunLocalASR

async def test_e2e_asr_with_mojo():
    """端到端测试：Opus解码 + FunASR识别"""
    # 1. 加载真实Opus音频
    with open("tests/data/speech.opus", "rb") as f:
        opus_data = f.read()

    # 2. Mojo解码
    pcm_data = mojo_audio.decode_opus(opus_data)

    # 3. ASR识别（Python + FunASR）
    asr = FunLocalASR({"model": "paraformer-zh"})
    text, _ = await asr.speech_to_text(pcm_data, session_id="test")

    # 4. 验证结果
    assert text is not None
    assert len(text) > 0
    print(f"✅ 识别结果: {text}")

if __name__ == "__main__":
    asyncio.run(test_e2e_asr_with_mojo())
```

---

## 7. 性能监控

### 7.1 运行时性能统计

**在Python侧添加性能埋点**

```python
import time
from functools import wraps

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {
            "opus_decode": [],
            "pcm_to_float32": [],
            "vad_features": [],
        }

    def measure(self, name: str):
        """装饰器：测量函数执行时间"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                self.metrics[name].append(elapsed * 1000)  # 转为毫秒
                return result
            return wrapper
        return decorator

    def report(self):
        """生成性能报告"""
        for name, times in self.metrics.items():
            if not times:
                continue
            avg = sum(times) / len(times)
            p50 = sorted(times)[len(times) // 2]
            p99 = sorted(times)[int(len(times) * 0.99)]
            print(f"{name}:")
            print(f"  平均: {avg:.2f}ms, P50: {p50:.2f}ms, P99: {p99:.2f}ms")

# 全局监控器
perf_monitor = PerformanceMonitor()

# 使用示例
@perf_monitor.measure("opus_decode")
def decode_opus_monitored(data: bytes) -> bytes:
    return mojo_audio.decode_opus(data)
```

---

### 7.2 Prometheus 指标导出

**集成到应用中**

```python
from prometheus_client import Counter, Histogram, start_http_server

# 定义指标
opus_decode_duration = Histogram(
    'opus_decode_duration_seconds',
    'Opus解码耗时',
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05)
)

mojo_calls_total = Counter(
    'mojo_calls_total',
    'Mojo模块调用次数',
    ['module', 'function']
)

# 在函数中记录
def decode_opus_with_metrics(data: bytes) -> bytes:
    with opus_decode_duration.time():
        result = mojo_audio.decode_opus(data)

    mojo_calls_total.labels(module='audio', function='decode_opus').inc()
    return result

# 启动Prometheus HTTP服务器
start_http_server(9090)
```

---

## 8. 故障排查指南

### 8.1 常见问题

#### 问题1：ImportError: cannot import name 'mojo_audio'

**原因**：Mojo模块未正确编译或安装

**解决方案**：
```bash
# 1. 重新编译
cd main/xiaozhi-server-mojo
bash build.sh

# 2. 检查生成的库文件
ls -lh lib/

# 3. 重新安装Python包
pip install -e . --force-reinstall
```

---

#### 问题2：Segmentation Fault 在调用Mojo函数时

**原因**：内存访问越界或指针错误

**调试步骤**：
```bash
# 1. 使用AddressSanitizer编译Mojo
mojo build -D ASAN audio/opus_codec.mojo -o lib/libxiaozhi_audio.so

# 2. 运行Python脚本
export ASAN_OPTIONS=detect_leaks=1
python app.py

# 3. 检查Mojo代码中的指针操作
# - 确保buffer在使用前已分配
# - 确保访问索引在范围内
# - 确保buffer在释放后不再使用
```

---

#### 问题3：性能提升不明显

**排查清单**：
1. ✅ 确认编译时启用了优化：`mojo build --release`
2. ✅ 确认SIMD代码正确向量化：`mojo build --emit-llvm` 检查LLVM IR
3. ✅ 确认没有频繁的Python-Mojo边界跨越
4. ✅ 确认使用零拷贝数据传递（NumPy数组）
5. ✅ 运行性能基准测试对比

**优化示例**：
```python
# ❌ 错误：频繁跨边界
for opus_frame in opus_frames:
    pcm = mojo_audio.decode_opus(opus_frame)  # 每次调用有开销

# ✅ 正确：批量处理
all_pcm = mojo_audio.decode_opus_batch(opus_frames)  # 一次调用
```

---

#### 问题4：Mojo版本和Python版本结果不一致

**验证步骤**：
```python
import numpy as np

# 1. 生成测试数据
test_data = np.random.randint(-32768, 32767, size=1000, dtype=np.int16)

# 2. Python版本
python_result = test_data.astype(np.float32) / 32768.0

# 3. Mojo版本
mojo_result = np.frombuffer(
    mojo_audio.pcm_to_float32(test_data.tobytes()),
    dtype=np.float32
)

# 4. 对比差异
diff = np.abs(python_result - mojo_result)
max_diff = np.max(diff)
print(f"最大差异: {max_diff}")

if max_diff > 1e-5:
    print("⚠️ 精度不足，检查Mojo实现")
    # 打印前10个差异最大的元素
    indices = np.argsort(diff)[-10:]
    for idx in indices:
        print(f"  [{idx}] Python: {python_result[idx]:.6f}, "
              f"Mojo: {mojo_result[idx]:.6f}, "
              f"Diff: {diff[idx]:.6f}")
```

---

## 9. 版本演进路线

### 9.1 Phase 1: 基础架构（当前）

**目标**：建立Python-Mojo混合架构基础

**交付物**：
- [x] Python-Mojo项目结构
- [x] 编译和构建脚本
- [x] Python-Mojo互操作规范
- [x] 编码规范文档
- [x] 测试框架

**时间**：1周

---

### 9.2 Phase 2: 核心音频模块

**目标**：实现高ROI的音频处理加速

**交付物**：
- [ ] Opus编解码（Mojo FFI → libopus）
- [ ] PCM格式转换（SIMD优化）
- [ ] 音频重采样
- [ ] 能量计算
- [ ] 性能基准测试（>=10x加速）

**时间**：2-3周

---

### 9.3 Phase 3: VAD加速

**目标**：VAD特征提取和推理加速

**交付物**：
- [ ] VAD特征提取（Mojo SIMD）
- [ ] ONNX Runtime集成
- [ ] 端到端VAD流程优化
- [ ] 性能基准测试（>=5x加速）

**时间**：1-2周

---

### 9.4 Phase 4: 生产部署

**目标**：稳定运行于生产环境

**交付物**：
- [ ] Docker镜像优化
- [ ] CI/CD集成
- [ ] 性能监控和告警
- [ ] 文档和培训
- [ ] 生产环境压力测试

**时间**：1-2周

---

### 9.5 Phase 5: 高级优化（可选）

**目标**：极限性能优化

**交付物**：
- [ ] PyTorch推理加速
- [ ] 无锁音频队列
- [ ] GPU加速集成
- [ ] 分布式部署优化

**时间**：2-4周

---

## 10. 总结

### 10.1 关键原则回顾

1. **用对的语言做对的事**
   - Python：异步I/O、AI SDK、配置管理
   - Mojo：数值计算、编解码、性能关键路径

2. **不重复造轮子**
   - WebSocket服务器：保持Python (websockets)
   - AI SDK集成：保持Python (openai, funasr)
   - Opus编解码：Mojo FFI调用libopus
   - 音频处理：Mojo SIMD替代NumPy

3. **性能优先，兼顾可维护性**
   - 编码规范：简单、直接、可追溯
   - 显式类型注解：提高可读性
   - 充分测试：保证正确性

---

### 10.2 预期收益

**性能提升**：
- Opus解码：**5-10倍**
- NumPy音频处理：**10-100倍**
- VAD特征提取：**10-20倍**
- 端到端延迟降低：**50-70%**

**资源优化**：
- CPU占用降低：**40-60%**
- 支持并发连接数：**2-3倍**

**开发体验**：
- 编译后的静态库：部署更简单
- 显式类型系统：减少运行时错误
- SIMD加速：接近C++性能

---

### 10.3 风险和缓解

**主要风险**：
1. Mojo生态不成熟 → 限制使用范围，保留Python回退
2. 学习曲线陡峭 → 提供培训和文档
3. 调试困难 → 使用AddressSanitizer和充分测试

---

**文档版本**: 1.0
**创建日期**: 2026-01-16
**维护者**: Claude Code
**参考文档**:
- `PYTHON_SYNTAX_FRAMEWORK_ANALYSIS.md`
- `MOJO_REWRITE_CANDIDATES.md`
- `RUST_SIMPLE_GUIDE.md`
