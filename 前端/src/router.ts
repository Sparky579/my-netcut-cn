import { createRouter, createWebHistory } from 'vue-router'
import Gate from './pages/Gate.vue'
import Channel from './pages/Channel.vue'
import Dashboard from './pages/Dashboard.vue'
import PasswordPrompt from './pages/PasswordPrompt.vue'

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{ path: '/', component: Gate },
		{ path: '/dash', component: Dashboard },
		{ path: '/:channel', component: Channel },
		{ path: '/:channel/password', component: PasswordPrompt },
	]
})

router.beforeEach((to, from, next) => {
	const mk = localStorage.getItem('MASTER_KEY')
	if (!mk && to.path !== '/') {
		return next('/')
	}
	next()
})

export default router
