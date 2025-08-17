import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import HomePage from './pages/HomePage.vue'

const CodeGeneratorApp = () => import('./modules/code-generator/CodeGeneratorApp.vue')
const CodeReviewApp = () => import('./modules/code-review/CodeReviewApp.vue')
const AboutPage = () => import('./modules/about/AboutMe.vue')

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/code-generator', name: 'code-generator', component: CodeGeneratorApp },
  { path: '/about', name: 'about', component: AboutPage }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
