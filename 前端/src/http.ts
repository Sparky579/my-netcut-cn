import axios from 'axios'
import router from './router'

const http = axios.create()

http.interceptors.request.use((config) => {
	const mk = localStorage.getItem('MASTER_KEY') || ''
	if (!config.headers) config.headers = {}
	config.headers['x-master-key'] = mk
	// 若存在频道本地密码，Channel.vue 单独加 header，这里不处理
	return config
})

http.interceptors.response.use(
	(resp) => resp,
	(err) => {
		const status = err?.response?.status
		if (status === 401) {
			router.push('/')
		} else if (status === 403) {
			// 需要频道密码或密码不正确，跳转密码输入页
			try {
				const url = new URL(err.config.url!, window.location.origin)
				const parts = url.pathname.split('/')
				const channel = parts[3] || parts[2] // 兼容相对路径
				if (channel) {
					const cb = router.currentRoute.value.fullPath
					router.push({ path: `/${channel}/password`, query: { cb } })
				}
			} catch {}
		}
		return Promise.reject(err)
	}
)

export default http
