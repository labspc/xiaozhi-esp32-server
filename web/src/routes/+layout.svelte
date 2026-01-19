<script>
  console.log("[layout] render");
</script>

<main class="app">
  <header class="app__header">
    <h1>ORica Control</h1>
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
  }
  .app__body {
    padding: 24px;
    flex: 1;
  }
</style>
