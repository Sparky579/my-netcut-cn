import axios from 'axios'
import router from './router'

const http = axios.create()

// 优先使用环境变量直连后端（例如 http://host:23456），否则走相对路径让 Vite 代理
const envBase = (import.meta as any).env?.VITE_BACKEND_URL || ''
if (envBase) {
	http.defaults.baseURL = envBase
}

http.interceptors.request.use((config) => {
	const mk = localStorage.getItem('MASTER_KEY') || ''
	if (!config.headers) config.headers = {}
	config.headers['x-master-key'] = mk
	return config
})

http.interceptors.response.use(
	(resp) => resp,
	(err) => {
		const status = err?.response?.status
		if (status === 401) {
			router.push('/')
		} else if (status === 403) {
			try {
				const url = new URL(err.config.url!, window.location.origin)
				const parts = url.pathname.split('/')
				const channel = parts[3] || parts[2]
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
