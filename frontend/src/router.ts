import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import HomePage from './pages/HomePage.vue'

const CodeGeneratorApp = () => import('./modules/code-generator/CodeGeneratorApp.vue')
const CodeReviewApp = () => import('./modules/code-review/CodeReviewApp.vue')
const AboutPage = () => import('./modules/about/AboutMe.vue')
const FpfRagApp = () => import('./modules/FPF-rag/FpfRagApp.vue')

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/code-generator', name: 'code-generator', component: CodeGeneratorApp },
  { path: '/code-review', name: 'code-review', component: CodeReviewApp },
  { path: '/about', name: 'about', component: AboutPage }
  ,{ path: '/fpf-rag', name: 'fpf-rag', component: FpfRagApp }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
