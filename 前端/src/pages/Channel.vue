<template>
  <div class="card">
    <div class="row" style="align-items:center; justify-content: space-between;">
      <div>
        <h2>频道：{{ channel }}</h2>
        <span class="badge" v-if="passwordSet">已设置密码</span>
        <div class="label" v-if="expireAt">到期：{{ formatTime(expireAt) }}</div>
      </div>
      <div class="row">
        <select class="input" v-model.number="expireMinutes">
          <option v-for="o in presets" :key="o.v" :value="o.v">{{ o.t }}</option>
        </select>
        <button class="btn" @click="saveText">保存 (Ctrl+S)</button>
        <router-link class="btn secondary" to="/">返回</router-link>
      </div>
    </div>

    <textarea v-model="content" rows="14" @keydown.ctrl.s.prevent="saveText"></textarea>

    <div class="row" style="margin-top: 10px; align-items:center;">
      <input class="input" v-model="passwordInput" type="password" style="max-width: 260px;" placeholder="输入访问密码或留空清除" />
      <button class="btn secondary" @click="applyPassword">设置/清除密码</button>
    </div>

    <hr />
    <h3>文件</h3>
    <div
      class="uploader"
      @dragover.prevent
      @drop.prevent="onDrop"
      style="border: 1px dashed #cfd7e6; padding: 16px; border-radius: 10px; background: #f8fafc; color: #0b1a2b;"
    >
      <p class="label" style="color:#5b687a">拖拽文件到此处，或</p>
      <input type="file" multiple @change="onPick" />
      <div class="row" style="margin-top:8px; align-items:center;">
        <select class="input" v-model.number="expireMinutesUpload" style="width:200px">
          <option :value="-1">跟随页面</option>
          <option v-for="o in presets" :key="o.v" :value="o.v">{{ o.t }}</option>
        </select>
      </div>
    </div>

    <table class="table" style="margin-top: 10px;">
      <thead>
        <tr><th>文件名</th><th>大小</th><th>上传时间</th><th>到期</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="f in files" :key="f.id">
          <td>{{ f.name }}</td>
          <td>{{ formatSize(f.size) }}</td>
          <td>{{ formatTime(f.uploaded_at) }}</td>
          <td>{{ f.expire_at ? formatTime(f.expire_at) : (expireAt ? formatTime(expireAt) : '—') }}</td>
          <td>
            <a class="btn secondary" :href="downloadUrl(f.id)" target="_blank">下载</a>
            <button class="btn secondary" @click="removeFile(f.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import http from '../http'
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const channel = route.params.channel as string
const content = ref('')
const expireMinutes = ref<number>(10)
const expireAt = ref<number | null>(null)
const passwordSet = ref(false)
const passwordInput = ref(localStorage.getItem(`PWD_${channel}`) || '')
const files = ref<any[]>([])
const expireMinutesUpload = ref<number>(-1)

const presets = [
  { t: '10分钟', v: 10 },
  { t: '1小时', v: 60 },
  { t: '12小时', v: 60*12 },
  { t: '1天', v: 60*24 },
  { t: '3天', v: 60*24*3 },
  { t: '7天', v: 60*24*7 },
  { t: '30天', v: 60*24*30 },
  { t: '365天', v: 60*24*365 },
  { t: '3650天', v: 60*24*3650 },
]

function authHeaders(extra: any = {}) {
  return { 'x-channel-password': passwordInput.value || '', ...extra }
}

async function load() {
  const resp = await http.get(`/api/channel/${encodeURIComponent(channel)}`, { headers: authHeaders() })
  content.value = resp.data.content
  passwordSet.value = resp.data.password_set
  expireAt.value = resp.data.expire_at
  await loadFiles()
}

async function saveText() {
  const resp = await http.post(`/api/channel/${encodeURIComponent(channel)}/save`, {
    content: content.value,
    expire_minutes: expireMinutes.value,
    password: passwordInput.value || undefined,
  }, { headers: authHeaders(), })
  expireAt.value = resp.data.expire_at
  if (passwordInput.value) localStorage.setItem(`PWD_${channel}`, passwordInput.value)
  await loadFiles()
}

async function applyPassword() {
  await http.post(`/api/channel/${encodeURIComponent(channel)}/password`, { password: passwordInput.value || null }, { headers: authHeaders() })
  if (passwordInput.value) localStorage.setItem(`PWD_${channel}`, passwordInput.value) 
  else localStorage.removeItem(`PWD_${channel}`)
  await load()
}

async function loadFiles() {
  const resp = await http.get(`/api/channel/${encodeURIComponent(channel)}/files`, { headers: authHeaders() })
  files.value = resp.data.files
}

function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  uploadFiles(input.files)
  input.value = ''
}

function onDrop(e: DragEvent) {
  if (!e.dataTransfer) return
  uploadFiles(e.dataTransfer.files)
}

async function uploadFiles(list: FileList) {
  for (const f of Array.from(list)) {
    const fd = new FormData()
    fd.append('file', f)
    const eff = (expireMinutesUpload.value === -1) ? expireMinutes.value : expireMinutesUpload.value
    fd.append('expire_minutes', String(eff))
    await http.post(`/api/channel/${encodeURIComponent(channel)}/upload`, fd, {
      headers: authHeaders(),
    })
  }
  await loadFiles()
}

function downloadUrl(id: number) {
  return `/api/channel/${encodeURIComponent(channel)}/download/${id}`
}

async function removeFile(id: number) {
  await http.delete(`/api/channel/${encodeURIComponent(channel)}/file/${id}`, { headers: authHeaders() })
  await loadFiles()
}

function formatSize(n: number) {
  if (n < 1024) return n + ' B'
  if (n < 1024*1024) return (n/1024).toFixed(1) + ' KB'
  if (n < 1024*1024*1024) return (n/1024/1024).toFixed(1) + ' MB'
  return (n/1024/1024/1024).toFixed(1) + ' GB'
}
function formatTime(ts: number) {
  const d = new Date(ts * 1000)
  return d.toLocaleString()
}

onMounted(load)
watch(() => passwordInput.value, () => {/* no-op */})
</script>

<style scoped>
/* 亮色样式同前 */
.card { background: #ffffff; border: 1px solid #e5e7eb; color: #0b1a2b; }
.input, textarea { background: #ffffff; color: #0b1a2b; border: 1px solid #cfd7e6; }
.btn { background: #2563eb; color: #fff; }
.btn.secondary { background: #e5e7eb; color: #0b1a2b; }
.badge { background:#eef2ff; color: #3730a3; }
.label { color: #5b687a; }
.table th, .table td { border-bottom: 1px solid #e5e7eb; }
</style>
