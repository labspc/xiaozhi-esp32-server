<script lang="ts">
  import type { Agent } from "$lib/api/types";
  import { apiGet } from "$lib/api/client";

  console.log("[agents] render");

  let agents: Agent[] = [
    { id: "ag-1", name: "示例 Agent A", model: "gpt-4o-mini" },
    { id: "ag-2", name: "示例 Agent B", model: "llama-3" }
  ];

  async function loadAgents() {
    const data = await apiGet<Agent[]>("/agents");
    if (data && Array.isArray(data)) {
      agents = data;
    } else {
      console.log("[agents] using demo list");
    }
  }

  loadAgents();
</script>

<section>
  <header class="section-head">
    <div>
      <p class="eyebrow">Agent 列表</p>
      <h2>已配置智能体</h2>
      <p class="hint">示例数据占位，点击“刷新”尝试调用后端。</p>
    </div>
    <button class="ghost" on:click={loadAgents}>刷新</button>
  </header>

  <div class="table">
    <div class="row header">
      <span>ID</span>
      <span>名称</span>
      <span>模型</span>
    </div>
    {#each agents as a}
      <div class="row">
        <span class="mono">{a.id}</span>
        <span>{a.name}</span>
        <span>{a.model}</span>
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
    grid-template-columns: 0.9fr 1.1fr 1fr;
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
