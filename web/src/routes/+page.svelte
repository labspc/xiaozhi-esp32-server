<script>
  console.log("[home] render");

  const cards = [
    { title: "设备", desc: "设备列表与状态", path: "/devices" },
    { title: "Agent", desc: "智能体配置与绑定", path: "/agents" },
    { title: "配置", desc: "系统配置与密钥", path: "/config" }
  ];
</script>

<section class="hero">
  <div class="hero__text">
    <p class="eyebrow">ORica 前端重构 · Svelte</p>
    <h2>欢迎使用控制台预览版</h2>
    <p class="sub">遵循简化指南，无复杂 stores/context，日志可追踪。</p>
  </div>
</section>

<section class="grid">
  {#each cards as card}
    <article class="card" on:click={() => console.log("[nav] goto", card.path)}>
      <h3>{card.title}</h3>
      <p>{card.desc}</p>
      <span class="link">即将上线 · {card.path}</span>
    </article>
  {/each}
</section>

<style>
  .hero {
    padding: 24px;
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
  }
  .hero__text h2 {
    margin: 6px 0;
    font-size: 28px;
  }
  .hero__text .eyebrow {
    text-transform: uppercase;
    color: #38bdf8;
    letter-spacing: 0.08em;
    font-size: 12px;
  }
  .hero__text .sub {
    color: #cbd5e1;
  }
  .grid {
    margin-top: 24px;
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  .card {
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 16px;
    background: #0b1220;
    cursor: pointer;
    transition: border-color 0.15s ease;
  }
  .card:hover {
    border-color: #38bdf8;
  }
  .card h3 {
    margin: 0 0 8px 0;
  }
  .card p {
    margin: 0 0 8px 0;
    color: #cbd5e1;
  }
  .link {
    color: #38bdf8;
    font-size: 14px;
  }
</style>
