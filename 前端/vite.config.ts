import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
	const fileEnv = loadEnv(mode, process.cwd(), '')
	const target = process.env.VITE_BACKEND_URL || fileEnv.VITE_BACKEND_URL || 'http://localhost:23456'
	return {
		plugins: [vue()],
		server: {
			port: 5173,
			proxy: {
				'/api': {
					target,
					changeOrigin: true,
				}
			}
		}
	}
})
