<template>
  <div class="card">
    <h2>输入频道密码</h2>
    <p class="label">此频道已设置访问密码，请输入以继续。</p>
    <div class="row" style="margin-top:12px; align-items:center;">
      <input class="input" v-model="pwd" type="password" placeholder="频道密码" @keyup.enter="submit" />
      <button class="btn" @click="submit">确认</button>
      <router-link class="btn secondary" to="/">取消</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const channel = route.params.channel as string
const cb = (route.query.cb as string) || `/${channel}`
const pwd = ref('')

function submit() {
  if (!pwd.value) return
  localStorage.setItem(`PWD_${channel}`, pwd.value)
  router.replace(cb)
}
</script>

<style scoped>
.card { background: #ffffff; border: 1px solid #e5e7eb; color: #0b1a2b; }
.input { background: #ffffff; border: 1px solid #cfd7e6; }
.btn { background: #2563eb; color: #fff; }
.btn.secondary { background: #e5e7eb; color: #0b1a2b; }
.label { color:#5b687a; }
</style>
