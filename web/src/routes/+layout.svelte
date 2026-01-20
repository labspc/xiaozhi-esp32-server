<script>
  import Sidebar from "$lib/components/layout/Sidebar.svelte";
  console.log("[layout] render");
</script>

<main class="app">
  <div class="layout">
    <Sidebar />
    <div class="content">
      <header class="app__header">
        <div class="brand">
          <h1>ORica Control</h1>
          <p class="hint">Svelte 预览 · 简化模式</p>
        </div>
      </header>
      <section class="app__body">
        <slot />
      </section>
    </div>
  </div>
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
    background: #0f172a;
  }
  .layout {
    display: flex;
    min-height: 100vh;
  }
  .content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  .app__header {
    padding: 16px 20px;
    border-bottom: 1px solid #1e293b;
    background: #0b1220;
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
  .app__body {
    padding: 24px;
    flex: 1;
  }
</style>
