<script lang="ts">
  const links = [
    { label: "首页", href: "/" },
    { label: "设备", href: "/devices" },
    { label: "Agent", href: "/agents" },
    { label: "登录", href: "/login" }
  ];
  console.log("[layout/Sidebar] render");
</script>

<aside class="sidebar">
  <div class="sidebar__brand">
    <h2>ORica</h2>
    <p>预览 · 简化版</p>
  </div>
  <nav class="sidebar__nav">
    {#each links as link}
      <a href={link.href} on:click={() => console.log("[nav]", link.href)}>
        {link.label}
      </a>
    {/each}
  </nav>
</aside>

<style>
  .sidebar {
    width: 200px;
    min-height: 100vh;
    border-right: 1px solid #1e293b;
    background: #0b1220;
    padding: 16px;
    box-sizing: border-box;
  }
  .sidebar__brand h2 {
    margin: 0;
    font-size: 18px;
  }
  .sidebar__brand p {
    margin: 4px 0 0 0;
    color: #94a3b8;
    font-size: 12px;
  }
  .sidebar__nav {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .sidebar__nav a {
    color: #e2e8f0;
    text-decoration: none;
    font-size: 14px;
    padding: 8px 10px;
    border-radius: 8px;
  }
  .sidebar__nav a:hover {
    background: rgba(56, 189, 248, 0.08);
    color: #38bdf8;
  }
</style>
