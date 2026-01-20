<script lang="ts">
  import type { Device } from "$lib/api/types";
  import { apiGet } from "$lib/api/client";

  console.log("[devices] render");

  let devices: Device[] = [
    { mac: "11:22:33:44:55:66", name: "示例设备 A", status: "online" },
    { mac: "aa:bb:cc:dd:ee:ff", name: "示例设备 B", status: "offline" }
  ];

  async function loadDevices() {
    const data = await apiGet<Device[]>("/devices");
    if (data && Array.isArray(data)) {
      devices = data;
    } else {
      console.log("[devices] using demo list");
    }
  }

  loadDevices();
</script>

<section>
  <header class="section-head">
    <div>
      <p class="eyebrow">设备列表</p>
      <h2>已注册设备</h2>
      <p class="hint">展示示例数据，点击“刷新”尝试调用后端。</p>
    </div>
    <button class="ghost" on:click={loadDevices}>刷新</button>
  </header>

  <div class="table">
    <div class="row header">
      <span>名称</span>
      <span>MAC</span>
      <span>状态</span>
    </div>
    {#each devices as d}
      <div class="row">
        <span>{d.name}</span>
        <span class="mono">{d.mac}</span>
        <span class={d.status === "online" ? "status online" : "status offline"}>{d.status}</span>
      </div>
    {/each}
  </div>
</section>

<style>
  .section-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .eyebrow {
    text-transform: uppercase;
    color: #38bdf8;
    letter-spacing: 0.08em;
    font-size: 12px;
  }
  .hint {
    color: #cbd5e1;
    margin: 0;
  }
  .table {
    margin-top: 16px;
    border: 1px solid #1f2937;
    border-radius: 12px;
    overflow: hidden;
  }
  .row {
    display: grid;
    grid-template-columns: 1.4fr 1fr 0.6fr;
    padding: 12px 14px;
    gap: 8px;
    background: #0b1220;
    border-bottom: 1px solid #1f2937;
  }
  .row.header {
    background: #0f172a;
    font-weight: 600;
  }
  .row:last-child {
    border-bottom: none;
  }
  .mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
      monospace;
  }
  .status {
    text-transform: uppercase;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 999px;
    width: fit-content;
  }
  .status.online {
    background: #0f766e;
    color: #ecfeff;
  }
  .status.offline {
    background: #4b5563;
    color: #e5e7eb;
  }
  .ghost {
    background: transparent;
    color: #e2e8f0;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 8px 12px;
    cursor: pointer;
  }
  .ghost:hover {
    border-color: #38bdf8;
    color: #38bdf8;
  }
</style>
