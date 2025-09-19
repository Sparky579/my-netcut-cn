<template>
  <div class="card">
    <h2>访问密钥</h2>
    <p class="label">首次初始化会生成一个密钥并仅展示一次。拥有密钥的用户可生成带有效期的访客密钥。</p>

    <div class="row" style="margin: 12px 0; align-items:center;">
      <input class="input" v-model="inputKey" placeholder="输入/粘贴访问密钥" @keyup.enter="saveKey" />
      <button class="btn" @click="saveKey">设置为当前密钥</button>
      <button class="btn secondary" @click="goRandom">随机频道</button>
      <router-link to="/dash" class="btn secondary">仪表盘</router-link>
    </div>

    <div class="row" style="gap:20px;">
      <div style="flex:1;">
        <h3>当前密钥状态</h3>
        <div class="label" v-if="me">
          <div>创建时间：{{ ts(me.created_at) }}</div>
          <div>到期时间：{{ me.expires_at ? ts(me.expires_at) : '永久' }}</div>
          <div>类型：{{ me.is_permanent ? '主密钥' : '访客密钥' }}</div>
        </div>
        <div class="row" style="margin-top:8px;">
          <button class="btn secondary" @click="refreshMe">刷新状态</button>
          <button class="btn secondary" @click="changeCurrentKey">更改当前密钥</button>
        </div>
      </div>
      <div style="flex:1;">
        <h3>生成访客密钥</h3>
        <div class="label">仅主密钥可生成</div>
        <div class="row" style="margin-top:6px;">
          <select class="input" v-model.number="minutes">
            <option :value="60">1小时</option>
            <option :value="1440">1天</option>
            <option :value="10080">7天</option>
          </select>
          <button class="btn" :disabled="!me?.can_rotate" @click="rotateKey">生成</button>
        </div>
        <div v-if="generatedKey" style="margin-top:12px; padding:12px; background:#f0f9ff; border:1px solid #bae6fd; border-radius:8px;">
          <div class="label">新生成的访客密钥：</div>
          <div style="word-break:break-all; font-family:monospace; margin:4px 0;">{{ generatedKey.key }}</div>
          <div class="label">到期时间：{{ ts(generatedKey.expires_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import http from '../http'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const inputKey = ref(localStorage.getItem('MASTER_KEY') || '')
const me = ref<any | null>(null)
const minutes = ref<number>(60)
const generatedKey = ref<{key: string, expires_at: number} | null>(null)

async function refreshMe() {
  try {
    const resp = await http.get('/api/master/me')
    me.value = resp.data
  } catch (e) {
    me.value = null
  }
}

function saveKey() {
  if (!inputKey.value) return
  localStorage.setItem('MASTER_KEY', inputKey.value)
  generatedKey.value = null
  refreshMe()
}

function goRandom() {
  if (!localStorage.getItem('MASTER_KEY')) {
    alert('请先设置访问密钥')
    return
  }
  const id = Math.random().toString(36).slice(2, 8)
  router.push('/' + id)
}

async function rotateKey() {
  const resp = await http.post('/api/master/rotate', { minutes: minutes.value })
  generatedKey.value = {
    key: resp.data.master_key,
    expires_at: resp.data.expires_at
  }
}

function changeCurrentKey() {
  const v = prompt('请输入新的当前密钥：')
  if (!v) return
  localStorage.setItem('MASTER_KEY', v)
  inputKey.value = v
  generatedKey.value = null
  refreshMe()
}

function ts(t: number) {
  return new Date(t * 1000).toLocaleString()
}

onMounted(refreshMe)
</script>

<style scoped>
.card { background: #ffffff; border: 1px solid #e5e7eb; color: #0b1a2b; }
.input { background: #ffffff; border: 1px solid #cfd7e6; }
.btn { background: #2563eb; color: #fff; }
.btn.secondary { background: #e5e7eb; color: #0b1a2b; }
.label { color:#5b687a; }
</style>
