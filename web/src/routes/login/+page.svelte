<script lang="ts">
  console.log("[login] render");

  let username = "";
  let password = "";

  function onSubmit(event: Event) {
    event.preventDefault();
    console.log("[login] submit", { username, password: password ? "***" : "" });
    // TODO: 调用后端登录接口，写 cookie/token
  }
</script>

<section class="card">
  <h2>登录</h2>
  <p class="hint">预览版，表单仅做占位。</p>
  <form class="form" on:submit|preventDefault={onSubmit}>
    <label>
      <span>用户名</span>
      <input bind:value={username} placeholder="admin" required />
    </label>
    <label>
      <span>密码</span>
      <input type="password" bind:value={password} placeholder="••••" required />
    </label>
    <button type="submit">登录</button>
  </form>
</section>

<style>
  .card {
    max-width: 360px;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 16px;
    background: #0b1220;
  }
  h2 {
    margin: 0 0 8px 0;
  }
  .hint {
    color: #cbd5e1;
    margin: 0 0 12px 0;
  }
  .form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 14px;
  }
  input {
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #1f2937;
    background: #0f172a;
    color: #e2e8f0;
  }
  button {
    padding: 10px;
    border-radius: 8px;
    border: none;
    background: #38bdf8;
    color: #0b1220;
    cursor: pointer;
    font-weight: 600;
  }
  button:hover {
    background: #0ea5e9;
  }
</style>
