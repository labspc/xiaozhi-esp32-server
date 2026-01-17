# Python-Mojo 共同语法参考与 AI 友好编码规范

## 文档目标

本文档为 **AI 代码生成工具**（如 Claude、GitHub Copilot）提供明确的编码规范，确保生成的代码：
1. ✅ **可读性第一** - 人类和AI都能轻松理解
2. ✅ **简单直接** - 不使用高深语法和复杂操作
3. ✅ **跨语言兼容** - 优先使用 Python 和 Mojo 共同支持的语法
4. ✅ **便于维护** - 避免语言特有的"魔法"特性

---

## 第一部分：当前代码实际使用的 Python 语法分析

### 1.1 基于实际代码库的语法使用统计

**数据来源**：xiaozhi-server 核心模块 (connection.py 1286行, handle/ 模块 500+ 行, providers/ 模块 2000+ 行)

| 语法特性 | 使用频率 | 典型场景 | Mojo 兼容性 |
|---------|---------|---------|------------|
| **if/elif/else** | ⭐⭐⭐⭐⭐ 极高 | VAD 双阈值判断、消息路由 | ✅ 完全兼容 |
| **for 循环** | ⭐⭐⭐⭐⭐ 极高 | 流式响应处理、音频帧遍历 | ✅ 完全兼容 |
| **while 循环** | ⭐⭐⭐⭐ 高 | 音频缓冲区连续处理 | ✅ 完全兼容 |
| **字符串操作** (.startswith/.strip) | ⭐⭐⭐⭐ 高 | JSON 格式检测、工具调用标记 | ✅ 完全兼容 |
| **列表/字典操作** | ⭐⭐⭐⭐ 高 | 配置管理、消息存储 | ✅ 完全兼容 |
| **try/except** | ⭐⭐⭐⭐ 高 | JSON 解析、音频解码错误 | ✅ 完全兼容 |
| **字节数组切片** | ⭐⭐⭐ 中 | 音频帧提取 (buffer[:512*2]) | ✅ 完全兼容 |
| **元组解包** | ⭐⭐⭐ 中 | (content, tools) = response | ✅ 完全兼容 |
| **async/await** | ⭐⭐⭐⭐⭐ 极高 | 整个异步架构 | ⚠️ **部分兼容** (Mojo 有限) |
| **生成器/yield** | ⭐⭐⭐ 中 | LLM 流式输出 | ⚠️ **部分兼容** |
| **hasattr/getattr** | ⭐⭐⭐ 中 | 动态属性检查 | ❌ **不兼容** (Mojo 静态) |
| **列表推导式** | ⭐⭐ 低 | 数据转换 | ⚠️ **部分兼容** (Mojo 简化版) |
| **装饰器** | ⭐⭐ 低 | 日志绑定 | ⚠️ **部分兼容** |
| **with 上下文管理** | ⭐⭐ 低 | torch.no_grad() | ✅ 完全兼容 |
| **递归 + 深度控制** | ⭐ 极低 | 工具链调用 (depth=5) | ✅ 完全兼容 |

---

### 1.2 实际代码片段示例（已使用的语法）

#### **示例1：双阈值 VAD 状态机（实际代码）**

```python
# 来自 core/providers/vad/silero.py:75-85
if speech_prob >= self.vad_threshold:
    is_voice = True
elif speech_prob <= self.vad_threshold_low:
    is_voice = False
else:
    is_voice = conn.last_is_voice  # 保持上一状态（滞后特性）

conn.last_is_voice = is_voice
```

**使用的语法**：
- ✅ `if/elif/else` - Python 和 Mojo 都支持
- ✅ 简单变量赋值 - 通用
- ✅ 对象属性访问 `.last_is_voice` - 通用

**AI 友好性**：⭐⭐⭐⭐⭐ 极佳（逻辑清晰，无隐藏行为）

---

#### **示例2：流式响应处理（实际代码）**

```python
# 来自 core/connection.py:850-870
content_arguments = ""
tool_call_flag = False

for response in llm_responses:  # 生成器迭代
    if self.client_abort:
        break

    content, tools_call = response  # 元组解包

    if content is not None and len(content) > 0:
        content_arguments += content  # 字符串连接

    # 字符串搜索（工具调用检测）
    if not tool_call_flag and content_arguments.startswith("<tool_call>"):
        tool_call_flag = True
```

**使用的语法**：
- ✅ `for` 循环 - 通用
- ⚠️ 生成器迭代 (`llm_responses`) - Mojo 部分支持
- ✅ 元组解包 `content, tools_call = response` - Mojo 支持
- ✅ 字符串操作 `.startswith()` - Mojo 支持
- ✅ `break` 语句 - 通用

**AI 友好性**：⭐⭐⭐⭐ 良好（逻辑清晰，但生成器需要注意）

---

#### **示例3：音频缓冲区处理（实际代码）**

```python
# 来自 core/providers/vad/silero.py:55-65
while len(conn.client_audio_buffer) >= 512 * 2:  # 512 样本 * 2 字节
    # 字节数组切片
    chunk = conn.client_audio_buffer[: 512 * 2]
    conn.client_audio_buffer = conn.client_audio_buffer[512 * 2 :]

    # NumPy 格式转换链
    audio_int16 = np.frombuffer(chunk, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    audio_tensor = torch.from_numpy(audio_float32)
```

**使用的语法**：
- ✅ `while` 循环 - 通用
- ✅ `len()` 函数 - 通用
- ✅ 切片操作 `[:512*2]` - Mojo 支持
- ⚠️ NumPy 操作 - Mojo 需重新实现（但可用 SIMD）

**AI 友好性**：⭐⭐⭐⭐ 良好（数值操作清晰）

---

#### **示例4：JSON 解析（实际代码）**

```python
# 来自 core/handle/receiveAudioHandle.py:45-60
try:
    # 字符串检查
    if text.strip().startswith("{") and text.strip().endswith("}"):
        data = json.loads(text)

        # 字典键检查
        if "speaker" in data and "content" in data:
            speaker_name = data["speaker"]
            actual_text = data["content"]

except (json.JSONDecodeError, KeyError):
    pass  # 回退到原始文本
```

**使用的语法**：
- ✅ `try/except` - Mojo 支持
- ✅ 字符串方法 `.strip()`, `.startswith()`, `.endswith()` - Mojo 支持
- ✅ 字典操作 `in`, `data["key"]` - Mojo 支持
- ⚠️ `json.loads()` - Mojo 需要自己实现或用 FFI

**AI 友好性**：⭐⭐⭐⭐ 良好（防御性编程）

---

## 第二部分：Python-Mojo 共同语法对照表

### 2.1 完全兼容的基础语法（优先使用）

| 语法特性 | Python 示例 | Mojo 示例 | 说明 |
|---------|------------|----------|------|
| **if 条件判断** | `if x > 0:` | `if x > 0:` | 完全一致 |
| **for 循环** | `for i in range(10):` | `for i in range(10):` | 完全一致 |
| **while 循环** | `while x > 0:` | `while x > 0:` | 完全一致 |
| **变量赋值** | `x = 10` | `var x: Int = 10` | Mojo 需要类型注解 |
| **字符串操作** | `s.startswith("x")` | `s.startswith("x")` | 完全一致 |
| **列表索引** | `arr[0]` | `arr[0]` | 完全一致 |
| **切片** | `arr[1:5]` | `arr[1:5]` | 完全一致 |
| **break/continue** | `break`, `continue` | `break`, `continue` | 完全一致 |
| **return** | `return result` | `return result` | 完全一致 |
| **函数定义** | `def foo(x):` | `fn foo(x: Int):` | Mojo 用 `fn` 且强制类型 |
| **注释** | `# 注释` | `# 注释` | 完全一致 |
| **布尔值** | `True`, `False` | `True`, `False` | 完全一致 |
| **比较运算** | `==`, `!=`, `<`, `>` | `==`, `!=`, `<`, `>` | 完全一致 |
| **逻辑运算** | `and`, `or`, `not` | `and`, `or`, `not` | 完全一致 |
| **数学运算** | `+`, `-`, `*`, `/`, `%` | `+`, `-`, `*`, `/`, `%` | 完全一致 |

---

### 2.2 部分兼容的中级语法（需要改造）

| 语法特性 | Python 示例 | Mojo 等价写法 | 注意事项 |
|---------|------------|--------------|---------|
| **元组解包** | `a, b = (1, 2)` | `let (a, b) = (1, 2)` | Mojo 需要 `let` 或 `var` |
| **try/except** | `try: ... except E: ...` | `try: ... except E: ...` | Mojo 语法一致，但异常类型有限 |
| **with 上下文** | `with open(f): ...` | `with open(f): ...` | Mojo 需要实现 `__enter__/__exit__` |
| **字典操作** | `d = {"a": 1}` | `var d = Dict[String, Int]()` | Mojo 需要显式类型 |
| **列表操作** | `arr = [1, 2, 3]` | `var arr = List[Int](1, 2, 3)` | Mojo 需要显式类型 |
| **字符串格式化** | `f"{x} is {y}"` | `String("{} is {}").format(x, y)` | Mojo 不支持 f-string |
| **类型转换** | `int(x)`, `float(x)` | `Int(x)`, `Float64(x)` | Mojo 类型名称大写 |
| **None 检查** | `if x is None:` | `if x is None:` | Mojo 用 `Optional[T]` |

---

### 2.3 不兼容的高级语法（避免使用）

| Python 特性 | 为什么不兼容 | 替代方案 |
|-----------|-----------|---------|
| **hasattr/getattr** | Mojo 是静态类型，不支持运行时反射 | 使用明确的属性检查 |
| **列表推导式** | Mojo 支持简化版，但功能有限 | 改用显式 for 循环 |
| **生成器/yield** | Mojo 支持有限，复杂生成器不可用 | 改用迭代器或显式循环 |
| **装饰器** | Mojo 支持基础装饰器，但功能有限 | 简化使用，避免闭包 |
| **lambda 函数** | Mojo 不支持 lambda | 改用命名函数 |
| **动态类型** | Mojo 是静态类型语言 | 始终使用类型注解 |
| **多重继承** | Mojo 不支持 | 使用 trait 组合 |
| **元类** | Mojo 无元类 | 避免元编程 |
| **async/await** | Mojo 异步支持还在开发中 | Python 处理异步，Mojo 处理同步计算 |

---

## 第三部分：AI 友好编码规范（简化版）

### 3.1 核心原则

```
🎯 目标：让 AI 和人类都能快速理解代码

1. ✅ 简单 > 复杂
2. ✅ 显式 > 隐式
3. ✅ 重复 > 抽象（如果抽象不明显）
4. ✅ 类型明确 > 类型推断
5. ✅ 逐步计算 > 链式调用
```

---

### 3.2 变量命名规范

**✅ 推荐（清晰、描述性）**
```python
# Python / Mojo 通用
audio_buffer_size = 512 * 2  # 512 samples * 2 bytes
speech_probability = 0.85
is_voice_detected = True
max_recursion_depth = 5
```

**❌ 避免（简写、不清晰）**
```python
buf_sz = 1024      # 简写不清晰
sp = 0.85          # 含义模糊
flag = True        # 太通用
d = 5              # 单字母
```

---

### 3.3 函数定义规范

**✅ 推荐（类型明确、注释清晰）**

**Python 版本：**
```python
def check_voice_activity(
    audio_data: bytes,
    threshold: float,
    sample_rate: int
) -> bool:
    """检测音频中是否有语音活动

    Args:
        audio_data: 原始音频字节数据
        threshold: VAD 阈值 (0.0-1.0)
        sample_rate: 采样率 (Hz)

    Returns:
        True 表示检测到语音，False 表示静音
    """
    # 实现逻辑...
    return is_voice
```

**Mojo 版本：**
```mojo
fn check_voice_activity(
    audio_data: DTypePointer[DType.uint8],
    audio_len: Int,
    threshold: Float32,
    sample_rate: Int
) -> Bool:
    """检测音频中是否有语音活动

    Args:
        audio_data: 音频数据指针
        audio_len: 音频长度（字节）
        threshold: VAD 阈值 (0.0-1.0)
        sample_rate: 采样率 (Hz)

    Returns:
        True 表示检测到语音，False 表示静音
    """
    # 实现逻辑...
    return is_voice
```

**❌ 避免（无类型、无注释）**
```python
def check(d, t, s):  # 函数名不清晰，参数名简写，无类型
    # 没有文档字符串
    return True
```

---

### 3.4 条件判断规范

**✅ 推荐（显式、分步骤）**
```python
# 方式1：多层 if（逻辑清晰）
if speech_probability >= high_threshold:
    is_voice = True
elif speech_probability <= low_threshold:
    is_voice = False
else:
    is_voice = previous_state  # 保持上一状态

# 方式2：分步判断（易于调试）
is_above_high = speech_probability >= high_threshold
is_below_low = speech_probability <= low_threshold

if is_above_high:
    is_voice = True
elif is_below_low:
    is_voice = False
else:
    is_voice = previous_state
```

**❌ 避免（三元表达式、复杂嵌套）**
```python
# 三元表达式（不够清晰）
is_voice = True if speech_probability >= high_threshold else (
    False if speech_probability <= low_threshold else previous_state
)

# 过度嵌套（难以理解）
if a:
    if b:
        if c:
            if d:
                result = True
```

---

### 3.5 循环规范

**✅ 推荐（简单、直接）**
```python
# 方式1：基础 for 循环
for i in range(buffer_length):
    sample = audio_buffer[i]
    if sample > threshold:
        voice_count += 1

# 方式2：while 循环（有明确退出条件）
while len(audio_buffer) >= frame_size:
    frame = audio_buffer[:frame_size]
    audio_buffer = audio_buffer[frame_size:]  # 移除已处理的帧
    process_frame(frame)
```

**❌ 避免（列表推导式、复杂迭代器）**
```python
# 列表推导式（Mojo 支持有限）
voice_samples = [s for s in audio_buffer if s > threshold]

# 复杂生成器表达式
results = (process(x) for x in data if condition(x) and x > 0)

# 嵌套推导式（难以理解）
matrix = [[row[i] * col[i] for i in range(n)] for row, col in zip(rows, cols)]
```

---

### 3.6 错误处理规范

**✅ 推荐（显式、分层）**
```python
# 方式1：单一异常类型
try:
    data = json.loads(text)
except json.JSONDecodeError:
    # 回退到默认值
    data = {"content": text}

# 方式2：分层错误处理
try:
    audio_data = decode_opus(opus_bytes)
except OpusDecodeError as e:
    logger.error(f"Opus 解码失败: {e}")
    # 返回空数据或重试
    audio_data = b""
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise  # 重新抛出
```

**❌ 避免（通用 except、忽略错误）**
```python
# 捕获所有异常（过于宽泛）
try:
    do_something()
except:  # 不指定异常类型
    pass  # 忽略所有错误

# 多异常合并（不够精确）
try:
    complex_operation()
except (ValueError, KeyError, TypeError, AttributeError):
    # 无法区分具体错误类型
    handle_error()
```

---

### 3.7 字符串处理规范

**✅ 推荐（显式方法调用）**
```python
# 方式1：显式字符串操作
text = text.strip()  # 去除首尾空格
if text.startswith("{"):
    is_json = True

# 方式2：分步构建字符串
result = "用户："
result += username
result += " 说："
result += message
```

**❌ 避免（f-string、复杂格式化）**
```python
# f-string（Mojo 不支持）
result = f"用户：{username} 说：{message}"

# 复杂格式化
result = "用户：{name}，年龄：{age}，时间：{time:%Y-%m-%d}".format(
    name=username, age=user_age, time=datetime.now()
)
```

---

### 3.8 数据结构规范

**✅ 推荐（显式类型、简单结构）**
```python
# Python 版本
audio_buffer: list[int] = []
config: dict[str, str] = {}

# Mojo 版本
var audio_buffer = List[Int]()
var config = Dict[String, String]()

# 访问操作（显式检查）
if "key" in config:
    value = config["key"]
else:
    value = "default"
```

**❌ 避免（复杂嵌套、隐式类型）**
```python
# 过度嵌套（难以追踪）
data = {
    "users": [
        {"name": "Alice", "tags": [1, 2, {"nested": True}]},
        {"name": "Bob", "tags": [3, 4]}
    ]
}

# 无类型注解（AI 难以推断）
config = {}  # 类型不明确
buffer = []  # 元素类型未知
```

---

## 第四部分：代码对比示例（复杂 vs 简单）

### 4.1 示例1：VAD 检测逻辑

**❌ 复杂版本（不推荐）**
```python
is_voice = (
    True if sp >= th_h else
    False if sp <= th_l else
    conn.last_is_voice
) and conn.listen_mode != "manual"

conn.last_is_voice = is_voice if conn.listen_mode != "manual" else True
```
**问题**：
- 三元嵌套表达式（难以理解）
- 逻辑和状态更新混在一起
- 变量名简写（sp, th_h）

---

**✅ 简单版本（推荐）**
```python
# 步骤1：检查手动模式
if client_listen_mode == "manual":
    is_voice = True
    return is_voice

# 步骤2：双阈值判断
speech_probability = model_output
high_threshold = 0.7
low_threshold = 0.3

if speech_probability >= high_threshold:
    is_voice = True
elif speech_probability <= low_threshold:
    is_voice = False
else:
    # 保持上一状态（滞后特性）
    is_voice = connection.last_voice_state

# 步骤3：更新状态
connection.last_voice_state = is_voice
return is_voice
```
**优点**：
- 逻辑分步骤（易于理解和调试）
- 变量名清晰
- 有注释说明意图

---

### 4.2 示例2：流式响应处理

**❌ 复杂版本（不推荐）**
```python
resp_msg = [c for r in llm_resp if (c := r[0] if isinstance(r, tuple) else r) and not (tcf := "<tool_call>" in (ca := ca + c)) and len(c) > 0]
```
**问题**：
- 列表推导式嵌套海象运算符
- 多个副作用（ca 被修改）
- 一行代码做太多事情

---

**✅ 简单版本（推荐）**
```python
response_message = []
content_arguments = ""
tool_call_flag = False

for response in llm_responses:
    # 步骤1：中断检查
    if client_abort:
        break

    # 步骤2：提取内容
    if isinstance(response, tuple):
        content = response[0]
    else:
        content = response

    # 步骤3：累积内容
    if content is not None and len(content) > 0:
        content_arguments += content

        # 步骤4：检测工具调用标记
        if not tool_call_flag:
            if "<tool_call>" in content_arguments:
                tool_call_flag = True

        # 步骤5：添加到响应列表
        if not tool_call_flag:
            response_message.append(content)

return response_message, tool_call_flag
```
**优点**：
- 每个步骤独立，易于调试
- 变量名清晰
- 逻辑分支明确

---

### 4.3 示例3：JSON 解析

**❌ 复杂版本（不推荐）**
```python
speaker = (data := json.loads(text) if text.strip()[0] == "{" and text.strip()[-1] == "}" else {}).get("speaker", None) if (hasattr(text, "strip") and text.strip()) else None
```
**问题**：
- 链式调用 + 海象运算符 + 三元表达式
- 一行完成所有逻辑
- 错误处理隐藏

---

**✅ 简单版本（推荐）**
```python
# 步骤1：初始化默认值
speaker_name = None
actual_text = text

# 步骤2：检查是否为 JSON 格式
text = text.strip()
is_json_format = text.startswith("{") and text.endswith("}")

if not is_json_format:
    return actual_text, speaker_name

# 步骤3：尝试解析 JSON
try:
    data = json.loads(text)
except json.JSONDecodeError:
    # 解析失败，保持默认值
    return actual_text, speaker_name

# 步骤4：提取字段
if "speaker" in data:
    speaker_name = data["speaker"]

if "content" in data:
    actual_text = data["content"]

return actual_text, speaker_name
```
**优点**：
- 防御性编程（提前返回）
- 错误处理显式
- 逻辑分步骤

---

### 4.4 示例4：音频缓冲区处理

**❌ 复杂版本（不推荐）**
```python
chunks = [buf[i:i+fs] for i in range(0, len(buf), fs) if len(buf[i:i+fs]) == fs]
energies = [sum(x**2 for x in np.frombuffer(c, dtype=np.int16))/len(c) for c in chunks]
```
**问题**：
- 列表推导式嵌套生成器表达式
- 多次切片操作
- NumPy 转换隐藏在表达式中

---

**✅ 简单版本（推荐）**
```python
# 步骤1：定义常量
frame_size = 512 * 2  # 512 samples * 2 bytes
chunks = []
energies = []

# 步骤2：提取完整帧
offset = 0
while offset + frame_size <= len(audio_buffer):
    chunk = audio_buffer[offset : offset + frame_size]
    chunks.append(chunk)
    offset += frame_size

# 步骤3：计算每帧能量
for chunk in chunks:
    # 转换为 NumPy 数组
    audio_int16 = np.frombuffer(chunk, dtype=np.int16)

    # 计算能量
    total_energy = 0.0
    for sample in audio_int16:
        total_energy += sample * sample

    average_energy = total_energy / len(audio_int16)
    energies.append(average_energy)

return energies
```
**优点**：
- 逐步处理（易于调试）
- 常量命名清晰
- 每个操作独立

---

## 第五部分：AI 代码生成提示词模板

### 5.1 通用提示词

当你请求 AI 生成代码时，附加这个提示：

```
请生成代码时遵循以下规范：

1. **语法限制**：
   - 仅使用 Python 和 Mojo 都支持的基础语法
   - 避免：列表推导式、lambda、生成器、装饰器
   - 优先：for/while 循环、if/else、显式函数

2. **可读性优先**：
   - 变量名完整描述性（不用简写）
   - 函数名动词开头（如 check_voice, process_audio）
   - 逻辑分步骤，不要一行做多件事

3. **类型明确**：
   - 所有函数参数和返回值使用类型注解
   - 所有变量声明时注明类型

4. **注释要求**：
   - 每个函数必须有文档字符串
   - 复杂逻辑前加注释说明意图
   - 魔法数字必须用常量表示

5. **错误处理**：
   - 使用 try/except，指定具体异常类型
   - 不要用通用的 except:
   - 提供回退逻辑或重新抛出

请按照这些规范生成代码。
```

---

### 5.2 特定任务提示词

**任务1：VAD 音频检测**
```
任务：实现 VAD（语音活动检测）函数

要求：
1. 输入：音频数据（字节数组）、高阈值、低阈值、上一状态
2. 输出：布尔值（是否检测到语音）
3. 逻辑：
   - 如果概率 >= 高阈值 → True
   - 如果概率 <= 低阈值 → False
   - 否则 → 保持上一状态
4. 遵循 AI 友好编码规范（见上方）
5. 使用显式 if/elif/else，不要三元表达式

生成 Python 和 Mojo 两个版本。
```

---

**任务2：流式响应处理**
```
任务：实现流式 LLM 响应处理函数

要求：
1. 输入：生成器（产生响应块）
2. 输出：完整响应文本、是否包含工具调用
3. 逻辑：
   - 遍历响应块
   - 累积文本内容
   - 检测 "<tool_call>" 标记
   - 支持中断（abort 标志）
4. 使用显式 for 循环，不要推导式
5. 分步骤处理，每步加注释

生成 Python 版本。
```

---

## 第六部分：检查清单

### 6.1 代码审查清单（AI 生成后检查）

**语法检查：**
- [ ] 是否使用了列表推导式？（改为 for 循环）
- [ ] 是否使用了 lambda 函数？（改为命名函数）
- [ ] 是否使用了 f-string？（改为 .format() 或拼接）
- [ ] 是否使用了海象运算符 `:=`？（拆分为独立语句）
- [ ] 是否使用了链式三元表达式？（改为 if/elif/else）

**可读性检查：**
- [ ] 变量名是否清晰？（不用 a, b, x, y）
- [ ] 是否有魔法数字？（提取为常量）
- [ ] 是否一行代码做多件事？（拆分为多步）
- [ ] 是否有深度嵌套（>3层）？（提前返回或提取函数）

**类型检查：**
- [ ] 所有函数参数是否有类型注解？
- [ ] 所有返回值是否有类型注解？
- [ ] 重要变量是否声明了类型？

**注释检查：**
- [ ] 每个函数是否有文档字符串？
- [ ] 复杂逻辑是否有注释说明？
- [ ] 常量是否有注释说明用途？

---

### 6.2 Mojo 移植检查清单

**从 Python 移植到 Mojo 时检查：**
- [ ] 是否所有变量都用 `var` 或 `let` 声明？
- [ ] 是否所有类型都明确标注？
- [ ] 是否避免使用 `hasattr` / `getattr`？
- [ ] 是否避免使用动态类型？
- [ ] 是否替换了 f-string？
- [ ] 是否替换了列表推导式？
- [ ] 是否所有指针操作都有边界检查？
- [ ] 是否所有分配的内存都有释放？

---

## 第七部分：总结

### 7.1 核心要点

1. **优先使用共同语法**
   - if/for/while/try/except
   - 字符串操作、列表、字典
   - 显式类型注解

2. **避免语言特有特性**
   - Python：列表推导式、lambda、f-string
   - Mojo：unsafe、复杂泛型
   - 两者都避免：过度抽象、魔法特性

3. **可读性第一**
   - 清晰的命名
   - 分步骤的逻辑
   - 充分的注释
   - 简单的控制流

4. **AI 友好设计**
   - 避免高深语法
   - 避免隐式行为
   - 提供明确的类型信息
   - 使用常见的设计模式

---

### 7.2 快速参考卡片

```
✅ 推荐使用：
- if/elif/else
- for/while 循环
- 显式变量赋值
- try/except (具体异常)
- 字符串 .startswith() / .endswith()
- 列表/字典显式操作
- 类型注解
- 文档字符串

❌ 避免使用：
- 列表推导式
- lambda 函数
- f-string
- 海象运算符 :=
- hasattr/getattr
- 链式三元表达式
- 过度嵌套
- 魔法数字
```

---

**文档版本**: 1.0
**创建日期**: 2026-01-16
**维护者**: Claude Code
**适用对象**: AI 代码生成工具、人类开发者
**配套文档**:
- `PYTHON_SYNTAX_FRAMEWORK_ANALYSIS.md`
- `MOJO_REWRITE_CANDIDATES.md`
- `PYTHON_MOJO_HYBRID_STRATEGY.md`
