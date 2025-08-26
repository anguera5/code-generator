import type { App } from 'vue'
import GlobalNotifier from '../components/GlobalNotifier.vue'

export const GlobalNotifierPlugin = {
  install(app: App) {
    app.component('GlobalNotifier', GlobalNotifier)
  }
}

export default GlobalNotifierPlugin
