<template>
  <div class="card">
    <div class="row" style="align-items:center; justify-content: space-between;">
      <h2>仪表盘</h2>
      <router-link class="btn secondary" to="/">返回</router-link>
    </div>
    <table class="table" style="margin-top: 10px;">
      <thead>
        <tr><th>频道</th><th>占用大小</th></tr>
      </thead>
      <tbody>
        <tr v-for="c in channels" :key="c.channel">
          <td><router-link :to="'/' + c.channel">{{ c.channel }}</router-link></td>
          <td>{{ formatSize(c.total) }}</td>
        </tr>
      </tbody>
    </table>
    <div style="margin-top: 10px;">总占用：<strong>{{ formatSize(total) }}</strong></div>
  </div>
</template>

<script setup lang="ts">
import http from '../http'
import { ref, onMounted } from 'vue'

const channels = ref<{channel:string,total:number}[]>([])
const total = ref(0)

async function load() {
  const resp = await http.get('/api/dashboard')
  channels.value = resp.data.channels
  total.value = resp.data.total_size
}

function formatSize(n: number) {
  if (n < 1024) return n + ' B'
  if (n < 1024*1024) return (n/1024).toFixed(1) + ' KB'
  if (n < 1024*1024*1024) return (n/1024/1024).toFixed(1) + ' MB'
  return (n/1024/1024/1024).toFixed(1) + ' GB'
}

onMounted(load)
</script>
