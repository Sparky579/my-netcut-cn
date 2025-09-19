<template>
  <div class="app-wrap">
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style>
:root {
  --bg: #f6f8fb;
  --card: #ffffff;
  --text: #0b1a2b;
  --muted: #5b687a;
  --primary: #2563eb;
  --accent: #7c3aed;
}
* { box-sizing: border-box; }
html, body, #app { height: 100%; margin: 0; background: var(--bg); color: var(--text); }
.app-wrap { min-height: 100%; display: flex; align-items: center; justify-content: center; padding: 24px; }
.card { background: var(--card); border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px; width: 100%; max-width: 960px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); }
.row { display: flex; gap: 12px; }
.btn { background: var(--primary); color: #fff; padding: 8px 14px; border-radius: 10px; border: none; cursor: pointer; font-weight: 600; }
.btn.secondary { background: #e5e7eb; color: var(--text); }
.input, textarea { width: 100%; background: #ffffff; color: var(--text); border: 1px solid #cfd7e6; padding: 10px 12px; border-radius: 10px; }
.badge { background:#eef2ff; color: var(--primary); padding: 4px 8px; border-radius: 999px; font-size: 12px; }
.label { color: var(--muted); font-size: 12px; }
hr { border: none; height: 1px; background: #e5e7eb; margin: 16px 0; }
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: 8px 10px; border-bottom: 1px solid #e5e7eb; text-align: left; }
</style>
