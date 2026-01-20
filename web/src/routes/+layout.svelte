<script>
  console.log("[layout] render");
</script>

<main class="app">
  <header class="app__header">
    <div class="brand">
      <h1>ORica Control</h1>
      <p class="hint">Svelte 预览 · 简化模式</p>
    </div>
    <nav class="nav">
      <a href="/">首页</a>
      <a href="/devices">设备</a>
      <a href="/agents">Agent</a>
      <a href="/login">登录</a>
    </nav>
  </header>
  <section class="app__body">
    <slot />
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: #0f172a;
    color: #e2e8f0;
  }
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .app__header {
    padding: 16px 20px;
    border-bottom: 1px solid #1e293b;
    background: #0b1220;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }
  .brand h1 {
    margin: 0;
    font-size: 18px;
  }
  .brand .hint {
    margin: 2px 0 0 0;
    color: #94a3b8;
    font-size: 12px;
  }
  .nav {
    display: flex;
    gap: 12px;
  }
  .nav a {
    color: #e2e8f0;
    text-decoration: none;
    font-size: 14px;
  }
  .nav a:hover {
    color: #38bdf8;
  }
  .app__body {
    padding: 24px;
    flex: 1;
  }
</style>
