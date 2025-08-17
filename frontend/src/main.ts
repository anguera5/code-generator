import { createApp } from 'vue'
import App from './App.vue'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import './styles.css'
import { router } from './router'
import '@mdi/font/css/materialdesignicons.css'


const vuetify = createVuetify({
	components,
	directives,
	theme: {
		defaultTheme: 'customDark',
		themes: {
			customDark: {
				dark: true,
				colors: {
					background: '#0f1115',
						surface: '#111318',
						primary: '#9a5fff',
						secondary: '#38d6ee',
						accent: '#38d6ee',
						info: '#38d6ee',
						success: '#10b981',
						warning: '#f59e0b',
						error: '#ef4444',
						'on-background': '#e2e8f0',
						'on-surface': '#e2e8f0'
				}
			}
		}
	}
})

createApp(App).use(router).use(vuetify).mount('#app')
