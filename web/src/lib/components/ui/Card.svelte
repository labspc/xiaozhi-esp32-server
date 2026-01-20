<script lang="ts">
  export let title: string = "";
  export let subtitle: string = "";
  console.log("[ui/Card] render", { title });
</script>

<article class="card">
  {#if title}
    <h3>{title}</h3>
  {/if}
  {#if subtitle}
    <p class="sub">{subtitle}</p>
  {/if}
  <slot />
</article>

<style>
  .card {
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 16px;
    background: #0b1220;
  }
  h3 {
    margin: 0 0 8px 0;
  }
  .sub {
    margin: 0 0 12px 0;
    color: #cbd5e1;
  }
</style>
