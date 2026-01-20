<script lang="ts">
  export let label: string = "按钮";
  export let variant: "primary" | "ghost" = "primary";
  export let disabled: boolean = false;

  function onClick(event: MouseEvent) {
    if (disabled) {
      event.preventDefault();
      return;
    }
    console.log("[ui/Button] click", { label, variant });
  }
</script>

<button class={`btn ${variant}`} {disabled} on:click|preventDefault={onClick}>
  {label}
</button>

<style>
  .btn {
    padding: 10px 14px;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    color: #0b1220;
    background: #38bdf8;
    transition: transform 0.1s ease, background 0.1s ease, border-color 0.1s ease;
  }
  .btn:hover {
    transform: translateY(-1px);
    background: #0ea5e9;
  }
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .btn.ghost {
    background: transparent;
    color: #e2e8f0;
    border: 1px solid #1f2937;
  }
  .btn.ghost:hover {
    border-color: #38bdf8;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.05);
  }
</style>
