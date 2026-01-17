# Benchmark 设计方案

## 目标

验证 Rust + Python 新架构相比 Python + Java 当前架构在以下方面的改进：

1. **响应速度/延迟** ⚡ (用户最关心)
2. **并发处理能力** 🚀
3. **资源使用效率** 💾
4. **稳定性与可靠性** 🛡️
5. **可扩展性** 📈

---

## 测试环境

### 硬件配置
```yaml
# 标准测试机器
CPU: 4 核 @ 2.5GHz
内存: 8GB RAM
网络: 千兆以太网
存储: SSD

# 说明：使用中等配置更能体现性能差异
```

### 软件环境
```yaml
# 当前架构
Python: 3.10
Java: 21
MySQL: 8.0
Redis: 7.0

# 新架构
Rust: 1.85+
Python: 3.10 (仅 AI 服务)
PostgreSQL: 16
Redis: 7.0
```

### 网络拓扑
```
[测试客户端] ──(100 Mbps)──> [服务器] ──(内网)──> [数据库/Redis]
```

---

## 测试维度与指标

### 1. 🎯 响应速度测试（核心指标）

#### 1.1 端到端语音交互延迟
**场景**：模拟真实用户使用 ESP32 设备进行语音对话

```python
# 测试脚本：benchmark/e2e_latency_test.py
import websocket
import time
import numpy as np

def test_voice_interaction():
    """
    测试流程：
    1. 发送 3 秒音频（PCM 16kHz）
    2. VAD 检测结束
    3. ASR 识别
    4. LLM 生成回复
    5. TTS 合成
    6. 接收第一个音频包
    """
    metrics = {
        'vad_latency': [],        # VAD 响应时间
        'asr_latency': [],        # ASR 完成时间
        'llm_first_token': [],    # LLM 首字延迟
        'tts_first_audio': [],    # TTS 首包延迟
        'total_latency': []       # 总延迟（发送音频 → 收到回复音频）
    }

    for i in range(100):  # 100 次测试
        ws = connect_websocket()

        # 发送音频
        audio_data = load_test_audio("你好小智.pcm")
        t0 = time.time()
        ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)

        # 等待 VAD 结束
        vad_end_time = wait_for_vad_end(ws)
        metrics['vad_latency'].append(vad_end_time - t0)

        # 等待 ASR 结果
        asr_result, asr_time = wait_for_asr(ws)
        metrics['asr_latency'].append(asr_time - t0)

        # 等待 LLM 首字
        first_token_time = wait_for_llm_first_token(ws)
        metrics['llm_first_token'].append(first_token_time - t0)

        # 等待 TTS 首包
        first_audio_time = wait_for_audio(ws)
        metrics['tts_first_audio'].append(first_audio_time - t0)

        total = first_audio_time - t0
        metrics['total_latency'].append(total)

        ws.close()

    return calculate_statistics(metrics)

def calculate_statistics(metrics):
    """计算 P50, P90, P99, 平均值"""
    results = {}
    for key, values in metrics.items():
        results[key] = {
            'mean': np.mean(values),
            'p50': np.percentile(values, 50),
            'p90': np.percentile(values, 90),
            'p99': np.percentile(values, 99),
            'min': np.min(values),
            'max': np.max(values)
        }
    return results
```

**预期改进**：
| 指标 | 当前架构 (ms) | 新架构 (ms) | 改进 |
|------|--------------|------------|------|
| VAD 延迟 | 50 | 20 | **-60%** |
| ASR 延迟 | 800 | 800 | 0% (依赖 AI 模型) |
| LLM 首字 | 1500 | 1200 | **-20%** (减少中间层) |
| TTS 首包 | 2200 | 1800 | **-18%** |
| **总延迟 P90** | **3500** | **2300** | **✅ -34%** |

---

#### 1.2 WebSocket 消息往返延迟 (RTT)
**测试工具**：自定义 Python 脚本

```python
# benchmark/ws_rtt_test.py
async def test_ping_pong_latency():
    """测试 ping/pong 往返时间"""
    async with websockets.connect(WS_URL) as ws:
        latencies = []

        for _ in range(1000):
            t0 = time.time()
            await ws.send('{"type":"ping"}')
            response = await ws.recv()
            t1 = time.time()

            latencies.append((t1 - t0) * 1000)  # 转换为毫秒

        return {
            'mean': np.mean(latencies),
            'p50': np.percentile(latencies, 50),
            'p99': np.percentile(latencies, 99)
        }
```

**预期改进**：
- 当前：P50 = 15ms, P99 = 45ms
- 新架构：P50 = 3ms, P99 = 8ms (**✅ -80% P50**)

---

#### 1.3 HTTP API 响应时间
**测试工具**：`wrk` (HTTP benchmarking tool)

```bash
# 测试脚本：benchmark/http_api_bench.sh

# 测试 1：查询设备列表（只读操作）
wrk -t4 -c100 -d30s \
    -H "Authorization: Bearer $TOKEN" \
    http://localhost:8002/device/list

# 测试 2：创建 Agent（写操作）
wrk -t4 -c50 -d30s \
    -s create_agent.lua \
    http://localhost:8002/agent/save

# 测试 3：复杂查询（联表查询）
wrk -t4 -c100 -d30s \
    -H "Authorization: Bearer $TOKEN" \
    http://localhost:8002/agent/1/devices

# 测试 4：配置更新（带缓存失效）
wrk -t4 -c50 -d30s \
    -s update_config.lua \
    http://localhost:8002/config/update
```

**预期改进**：
| API 类型 | 当前 QPS | 新架构 QPS | 改进 |
|---------|---------|-----------|------|
| 简单查询 (SELECT) | 2,000 | 12,000 | **✅ 6x** |
| 写操作 (INSERT) | 800 | 4,500 | **✅ 5.6x** |
| 复杂查询 (JOIN) | 500 | 2,500 | **✅ 5x** |
| 缓存更新 | 1,200 | 6,000 | **✅ 5x** |

**延迟改进**：
| 指标 | 当前 (ms) | 新架构 (ms) | 改进 |
|------|----------|-----------|------|
| P50 延迟 | 20 | 4 | **✅ -80%** |
| P90 延迟 | 80 | 15 | **✅ -81%** |
| P99 延迟 | 200 | 35 | **✅ -83%** |

---

### 2. 🚀 并发处理能力测试

#### 2.1 WebSocket 并发连接数
**测试工具**：自定义压测脚本

```python
# benchmark/ws_concurrent_test.py
import asyncio
import websockets

async def test_max_connections():
    """测试最大并发 WebSocket 连接数"""
    connections = []
    successful = 0

    async def create_connection(i):
        try:
            ws = await websockets.connect(WS_URL, timeout=5)
            await ws.send('{"type":"hello","audio_params":{}}')
            response = await ws.recv()
            return ws
        except Exception as e:
            print(f"Connection {i} failed: {e}")
            return None

    # 逐步增加连接数
    for batch in [100, 500, 1000, 2000, 5000]:
        tasks = [create_connection(i) for i in range(batch)]
        results = await asyncio.gather(*tasks)
        successful = sum(1 for r in results if r is not None)

        print(f"尝试 {batch} 连接，成功 {successful}")

        if successful < batch * 0.95:  # 成功率低于 95%
            print(f"达到瓶颈：{successful} 连接")
            break

        connections.extend([r for r in results if r])

    # 清理连接
    for ws in connections:
        await ws.close()

    return successful
```

**预期改进**：
- **当前架构**：~500 连接（Python asyncio GIL 限制 + 内存消耗）
- **新架构**：~10,000 连接（Tokio 零成本异步 + Rust 低内存占用）
- **改进**：**✅ 20x**

---

#### 2.2 混合负载压测
**场景**：同时模拟多种操作

```python
# benchmark/mixed_load_test.py
async def mixed_load_test():
    """
    模拟真实场景：
    - 50% 语音交互（WebSocket 音频流）
    - 30% HTTP API 查询
    - 15% HTTP API 写操作
    - 5% 配置更新
    """
    tasks = []

    # 50 个 WebSocket 语音交互
    for _ in range(50):
        tasks.append(voice_interaction_task())

    # 30 个并发查询
    for _ in range(30):
        tasks.append(http_query_task())

    # 15 个写操作
    for _ in range(15):
        tasks.append(http_write_task())

    # 5 个配置更新
    for _ in range(5):
        tasks.append(config_update_task())

    results = await asyncio.gather(*tasks)
    return analyze_results(results)
```

**预期改进**：
- **当前架构**：处理 100 混合任务需要 ~8 秒
- **新架构**：处理 100 混合任务需要 ~2 秒
- **改进**：**✅ 4x 吞吐量**

---

### 3. 💾 资源使用效率测试

#### 3.1 内存占用
**测试方法**：使用 `prometheus` + `grafana` 监控

```yaml
# benchmark/prometheus.yml
scrape_configs:
  - job_name: 'xiaozhi-old'
    static_configs:
      - targets: ['localhost:9100']  # Python + Java

  - job_name: 'xiaozhi-new'
    static_configs:
      - targets: ['localhost:9101']  # Rust + Python
```

**监控指标**：
```python
# benchmark/memory_test.py
def measure_memory_usage():
    """
    测试场景：
    1. 启动时内存（Baseline）
    2. 100 个空闲连接
    3. 100 个活跃语音交互
    4. 1000 个并发 HTTP 请求
    5. 长时间运行（24 小时）
    """
    scenarios = {
        'idle': measure_idle_memory(),
        'ws_100_idle': measure_with_connections(100, active=False),
        'ws_100_active': measure_with_connections(100, active=True),
        'http_burst': measure_http_burst(1000),
        'long_run': measure_24h_run()
    }
    return scenarios
```

**预期改进**：
| 场景 | 当前架构 (MB) | 新架构 (MB) | 改进 |
|------|-------------|-----------|------|
| 启动时 | 800 | 150 | **✅ -81%** |
| 100 空闲连接 | 1,200 | 250 | **✅ -79%** |
| 100 活跃交互 | 3,500 | 1,200 | **✅ -66%** |
| 1000 HTTP 请求 | 2,800 | 800 | **✅ -71%** |
| 24h 运行 | 6,000 | 2,000 | **✅ -67%** |

---

#### 3.2 CPU 使用率
**测试工具**：`htop`, `perf`

```bash
# benchmark/cpu_bench.sh

# 测试 1：空闲 CPU
measure_idle_cpu() {
    pidstat -p $PID 1 60 | awk '{sum+=$8} END {print sum/60}'
}

# 测试 2：100 并发语音交互
measure_active_cpu() {
    ./ws_concurrent_test.py --connections=100 &
    TEST_PID=$!
    pidstat -p $PID 1 60 | awk '{sum+=$8} END {print sum/60}'
    kill $TEST_PID
}

# 测试 3：火焰图分析
perf record -F 99 -p $PID -g -- sleep 60
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

**预期改进**：
| 负载 | 当前 CPU (%) | 新架构 CPU (%) | 改进 |
|------|------------|--------------|------|
| 空闲 | 5% | 1% | **✅ -80%** |
| 100 并发 WS | 85% | 45% | **✅ -47%** |
| 1000 HTTP QPS | 90% | 50% | **✅ -44%** |

---

### 4. 🛡️ 稳定性测试

#### 4.1 长时间运行测试
```python
# benchmark/stability_test.py
def long_run_test(duration_hours=72):
    """
    持续 72 小时测试：
    1. 监控内存泄漏（每小时记录内存）
    2. 监控连接稳定性（连接意外断开次数）
    3. 监控错误率（成功率应 > 99.9%）
    4. 监控响应时间是否劣化
    """
    metrics = {
        'memory_samples': [],
        'connection_drops': 0,
        'total_requests': 0,
        'failed_requests': 0,
        'latency_samples': []
    }

    start_time = time.time()

    while time.time() - start_time < duration_hours * 3600:
        # 每小时记录一次内存
        if time.time() % 3600 < 60:
            metrics['memory_samples'].append(get_memory_usage())

        # 持续发送请求
        success, latency = send_test_request()
        metrics['total_requests'] += 1
        if not success:
            metrics['failed_requests'] += 1
        metrics['latency_samples'].append(latency)

        time.sleep(1)

    # 检查内存泄漏
    memory_trend = np.polyfit(
        range(len(metrics['memory_samples'])),
        metrics['memory_samples'],
        1
    )

    return {
        'memory_leak_rate_mb_per_hour': memory_trend[0],
        'success_rate': 1 - metrics['failed_requests'] / metrics['total_requests'],
        'avg_latency': np.mean(metrics['latency_samples'])
    }
```

**预期结果**：
| 指标 | 当前架构 | 新架构 | 改进 |
|------|---------|-------|------|
| 内存泄漏率 | +50 MB/h | +5 MB/h | **✅ -90%** |
| 成功率 (72h) | 99.5% | 99.95% | **✅ +0.45%** |
| 延迟劣化 | +15% (72h 后) | +2% | **✅ 更稳定** |

---

#### 4.2 故障恢复测试
```bash
# benchmark/fault_recovery_test.sh

# 测试 1：数据库连接断开恢复
test_db_reconnect() {
    # 1. 建立 100 个活跃连接
    # 2. 关闭数据库
    docker stop postgres
    # 3. 等待 10 秒
    sleep 10
    # 4. 重启数据库
    docker start postgres
    # 5. 检查服务是否自动恢复
}

# 测试 2：Redis 连接断开恢复
test_redis_reconnect() {
    docker stop redis
    sleep 10
    docker start redis
}

# 测试 3：Python AI 服务重启恢复
test_ai_service_restart() {
    # 1. 模拟 AI 服务崩溃
    kill -9 $AI_SERVICE_PID
    # 2. 检查 Rust 服务是否优雅降级
    # 3. 重启 AI 服务
    # 4. 检查是否自动重连
}
```

**预期改进**：
- **当前架构**：数据库重连需要重启服务
- **新架构**：自动重连，最多 5 秒恢复
- **改进**：**✅ 零停机恢复**

---

### 5. 📈 可扩展性测试

#### 5.1 水平扩展能力
```yaml
# benchmark/k8s_scaling_test.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xiaozhi-rust
spec:
  replicas: 1  # 从 1 逐步扩展到 10
  template:
    spec:
      containers:
      - name: xiaozhi
        image: xiaozhi-rust:latest
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
```

**测试流程**：
1. 1 个实例承载 1000 连接
2. 扩展到 5 个实例承载 5000 连接
3. 扩展到 10 个实例承载 10000 连接

**预期结果**：
- **当前架构**：线性扩展，但单实例上限低 (~300 连接/实例)
- **新架构**：近似线性扩展，单实例上限高 (~2000 连接/实例)
- **改进**：**✅ 6.7x 单实例容量**

---

#### 5.2 单机极限测试
```python
# benchmark/stress_test.py
def stress_test_to_failure():
    """
    压测直到服务崩溃，找到极限：
    1. 逐步增加并发连接
    2. 每增加 100 连接等待 30 秒稳定
    3. 监控成功率，低于 95% 则认为达到极限
    """
    connections = 0
    step = 100

    while True:
        connections += step
        print(f"Testing {connections} connections...")

        success_rate = test_connections(connections)

        if success_rate < 0.95:
            print(f"极限：{connections - step} 连接")
            return connections - step

        if connections > 20000:  # 安全上限
            break

    return connections
```

**预期极限**：
- **当前架构**：~800 并发连接（4 核 8GB）
- **新架构**：~8000 并发连接（4 核 8GB）
- **改进**：**✅ 10x**

---

## 测试工具清单

### 开源工具
```bash
# HTTP 压测
brew install wrk
brew install hey

# WebSocket 压测
pip install websockets asyncio

# 监控
docker run -d -p 9090:9090 prom/prometheus
docker run -d -p 3000:3000 grafana/grafana

# 性能分析
brew install perf  # Linux
cargo install flamegraph
```

### 自定义脚本
```
benchmark/
├── e2e_latency_test.py       # 端到端延迟测试
├── ws_rtt_test.py            # WebSocket RTT 测试
├── ws_concurrent_test.py     # 并发连接测试
├── http_api_bench.sh         # HTTP API 压测
├── mixed_load_test.py        # 混合负载测试
├── memory_test.py            # 内存测试
├── cpu_bench.sh              # CPU 测试
├── stability_test.py         # 稳定性测试
├── fault_recovery_test.sh    # 故障恢复测试
├── stress_test.py            # 极限压测
└── report_generator.py       # 生成 HTML 报告
```

---

## 自动化测试流程

```bash
# benchmark/run_all_tests.sh
#!/bin/bash

set -e

echo "=== 小智 ESP32 服务器 Benchmark 测试套件 ==="
echo "开始时间：$(date)"

# 1. 环境检查
echo "[1/10] 检查测试环境..."
./check_environment.sh

# 2. 启动当前架构
echo "[2/10] 启动当前架构（Python + Java）..."
docker-compose -f docker-compose.old.yml up -d
sleep 30  # 等待服务启动

# 3. 运行当前架构测试
echo "[3/10] 测试当前架构..."
python e2e_latency_test.py --output=old_latency.json
python ws_concurrent_test.py --output=old_concurrent.json
./http_api_bench.sh --output=old_http.json
python memory_test.py --output=old_memory.json

# 4. 停止当前架构
echo "[4/10] 停止当前架构..."
docker-compose -f docker-compose.old.yml down

# 5. 启动新架构
echo "[5/10] 启动新架构（Rust + Python）..."
docker-compose -f docker-compose.new.yml up -d
sleep 30

# 6. 运行新架构测试
echo "[6/10] 测试新架构..."
python e2e_latency_test.py --output=new_latency.json
python ws_concurrent_test.py --output=new_concurrent.json
./http_api_bench.sh --output=new_http.json
python memory_test.py --output=new_memory.json

# 7. 稳定性测试（72 小时）
echo "[7/10] 开始稳定性测试（预计 72 小时）..."
python stability_test.py --duration=72 --output=stability.json

# 8. 故障恢复测试
echo "[8/10] 故障恢复测试..."
./fault_recovery_test.sh --output=recovery.json

# 9. 极限压测
echo "[9/10] 极限压测..."
python stress_test.py --output=stress.json

# 10. 生成报告
echo "[10/10] 生成测试报告..."
python report_generator.py \
    --old-latency=old_latency.json \
    --new-latency=new_latency.json \
    --old-concurrent=old_concurrent.json \
    --new-concurrent=new_concurrent.json \
    --old-http=old_http.json \
    --new-http=new_http.json \
    --old-memory=old_memory.json \
    --new-memory=new_memory.json \
    --stability=stability.json \
    --recovery=recovery.json \
    --stress=stress.json \
    --output=benchmark_report.html

echo "=== 测试完成 ==="
echo "结束时间：$(date)"
echo "报告：benchmark_report.html"
```

---

## 报告格式

```python
# benchmark/report_generator.py
def generate_html_report(data):
    """
    生成包含以下内容的 HTML 报告：

    1. 执行摘要（Executive Summary）
       - 总体改进百分比
       - 关键指标对比（表格）
       - 推荐结论

    2. 详细测试结果
       - 每个测试维度的图表（折线图、柱状图）
       - P50/P90/P99 分位数对比
       - 资源使用曲线图

    3. 性能火焰图
       - 当前架构 vs 新架构 CPU 热点对比

    4. 原始数据
       - 所有 JSON 测试数据
       - 可导出 CSV
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>小智服务器架构 Benchmark 报告</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .improvement {{ color: green; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>小智 ESP32 服务器性能 Benchmark 报告</h1>

        <div class="summary">
            <h2>执行摘要</h2>
            <p>测试日期：{data['test_date']}</p>
            <p>测试环境：4 核 8GB</p>

            <h3>关键改进</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>当前架构</th>
                    <th>新架构</th>
                    <th>改进</th>
                </tr>
                <tr>
                    <td>端到端延迟 (P90)</td>
                    <td>{data['old_e2e_p90']} ms</td>
                    <td>{data['new_e2e_p90']} ms</td>
                    <td class="improvement">{data['e2e_improvement']}%</td>
                </tr>
                <!-- 更多行... -->
            </table>
        </div>

        <h2>详细测试结果</h2>

        <h3>1. 响应延迟对比</h3>
        <div id="latency-chart"></div>
        <script>
            var trace1 = {{
                x: ['VAD', 'ASR', 'LLM', 'TTS', 'Total'],
                y: {data['old_latencies']},
                name: '当前架构',
                type: 'bar'
            }};
            var trace2 = {{
                x: ['VAD', 'ASR', 'LLM', 'TTS', 'Total'],
                y: {data['new_latencies']},
                name: '新架构',
                type: 'bar'
            }};
            Plotly.newPlot('latency-chart', [trace1, trace2]);
        </script>

        <!-- 更多图表... -->

        <h2>原始数据</h2>
        <details>
            <summary>点击查看 JSON 数据</summary>
            <pre>{json.dumps(data, indent=2)}</pre>
        </details>
    </body>
    </html>
    """
    return html
```

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/xinnan-tech/xiaozhi-esp32-server.git
cd xiaozhi-esp32-server

# 2. 安装测试依赖
pip install -r benchmark/requirements.txt

# 3. 运行快速测试（5 分钟）
./benchmark/quick_test.sh

# 4. 运行完整测试（包含 72 小时稳定性测试）
./benchmark/run_all_tests.sh

# 5. 查看报告
open benchmark_report.html
```

---

## 预期总结

基于以上测试，新架构（Rust + Python）相比当前架构（Python + Java）的**总体改进**：

| 维度 | 改进幅度 | 关键指标 |
|------|---------|---------|
| 🎯 **响应速度** | **-34%** | 端到端延迟 P90：3500ms → 2300ms |
| 🚀 **并发能力** | **20x** | WebSocket 连接：500 → 10,000 |
| 💾 **内存效率** | **-67%** | 24h 运行：6GB → 2GB |
| ⚡ **CPU 效率** | **-44%** | 高负载 CPU：90% → 50% |
| 📈 **吞吐量** | **5-6x** | HTTP QPS：2,000 → 12,000 |
| 🛡️ **稳定性** | **10x** | 内存泄漏率：50 MB/h → 5 MB/h |

**结论**：新架构在所有关键维度均有显著改进，特别是在**响应速度**（-34%）、**并发能力**（20x）和**资源效率**（CPU -44%, 内存 -67%）方面。

---

## 附录：测试数据示例

```json
{
  "test_date": "2026-01-16",
  "environment": {
    "cpu": "4 cores @ 2.5GHz",
    "memory": "8GB",
    "network": "1Gbps"
  },
  "e2e_latency": {
    "old": {
      "vad_ms": {"p50": 45, "p90": 70, "p99": 120},
      "asr_ms": {"p50": 750, "p90": 950, "p99": 1200},
      "llm_first_token_ms": {"p50": 1400, "p90": 1800, "p99": 2500},
      "tts_first_audio_ms": {"p50": 2000, "p90": 2500, "p99": 3200},
      "total_ms": {"p50": 2800, "p90": 3500, "p99": 4500}
    },
    "new": {
      "vad_ms": {"p50": 15, "p90": 25, "p99": 40},
      "asr_ms": {"p50": 750, "p90": 950, "p99": 1200},
      "llm_first_token_ms": {"p50": 1100, "p90": 1400, "p99": 1900},
      "tts_first_audio_ms": {"p50": 1600, "p90": 2000, "p99": 2600},
      "total_ms": {"p50": 1800, "p90": 2300, "p99": 3000}
    },
    "improvement": {
      "total_p90": "-34%"
    }
  },
  "concurrent_websockets": {
    "old_max": 500,
    "new_max": 10000,
    "improvement": "20x"
  },
  "http_api": {
    "old_qps": 2000,
    "new_qps": 12000,
    "improvement": "6x"
  },
  "memory_mb": {
    "old_24h": 6000,
    "new_24h": 2000,
    "improvement": "-67%"
  }
}
```

---

## 贡献者

欢迎提交 Issue 或 PR 改进 Benchmark 测试方案！
