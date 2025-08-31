<template>
  <v-container class="py-0" fluid>
    <div class="section-intro">
      <PageTitle>
        <div class="d-flex flex-column flex-md-row align-center justify-space-between ga-4">
          <div class="flex-1">
            <div class="eyebrow">Chatbot</div>
            <h1 class="headline">Food Packaging Forum RAG <span class="shimmer" /></h1>
            <p class="op-80 mt-1">
              Ask questions about food packaging safety. Replies are grounded on FPF content using
              <strong>text-embedding-3-large</strong> and generated with <strong>gpt-4.1-mini</strong>.
            </p>
          </div>
          <div class="toolbar d-flex ga-3 align-center flex-wrap">
            <v-chip v-if="!apiKeyStore.apiKey" color="warning" variant="tonal" class="pill">Enter API key (top bar)</v-chip>
            <v-chip color="secondary" variant="tonal" class="pill">RAG-enabled</v-chip>
          </div>
        </div>
      </PageTitle>
    </div>

  <div class="py-6"></div>
  <v-card class="chat-shell mb-4 mt-4" elevation="2">
      <div class="messages" ref="messagesEl">
        <div v-for="m in messages" :key="m.id" class="message" :class="m.role">
          <div class="bubble">
            <span class="role" v-if="m.role==='assistant'">Assistant</span>
            <span class="role" v-else>User</span>
            <div class="text">{{ m.text }}</div>
          </div>
        </div>
        <div v-if="loading" class="message assistant pending">
          <div class="bubble"><em>Thinking...</em></div>
        </div>
      </div>
      <v-divider />
      <form @submit.prevent="send" class="composer d-flex align-center pa-2 ga-2">
        <v-textarea
          v-model="draft"
          label="Ask something about food packaging safety..."
          auto-grow
          rows="1"
          max-rows="5"
          class="flex-grow-1"
          density="comfortable"
          hide-details
        />
        <v-btn :disabled="!draft.trim() || loading" type="submit" color="primary" class="send-btn" :loading="loading">Send</v-btn>
      </form>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, nextTick, onMounted } from 'vue'
import http from '../../lib/http'
import { useNotifyStore } from '../../stores/notify'
import { useApiKeyStore } from '../../stores/apiKey'
import PageTitle from '../../components/PageTitle.vue'

interface ChatMessage { id: string; role: 'user' | 'assistant'; text: string }

const apiKeyStore = useApiKeyStore()
const notify = useNotifyStore()
const messages = ref<ChatMessage[]>([])
const draft = ref('')
const loading = ref(false)
const messagesEl = ref<HTMLElement | null>(null)
let chatbotConfigKey: string | undefined

function push(role: ChatMessage['role'], text: string) {
  messages.value.push({ id: `${Date.now()}-${Math.random().toString(36).slice(2)}`, role, text })
  nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  })
}

async function send() {
  const content = draft.value.trim()
  if (!content) return
  push('user', content)
  draft.value = ''
  loading.value = true
  try {
  const res = await http.post('/api/fpf-rag/chat', { prompt: content, api_key: apiKeyStore.apiKey, config_key: chatbotConfigKey })
    push('assistant', res.data.reply)
  } catch (e:any) {
    const msg = e?.response?.data?.detail || 'Error contacting backend'
    push('assistant', msg)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!messages.value.length) {
    chatbotConfigKey = Math.random().toString(16).slice(2, 18)
    console.log(`Chatbot config key: ${chatbotConfigKey}`)
    push(
      'assistant',
      'Hello, this is the Food Packaging Forum chatbot, please ask me anything related to our work and I will happily try to solve your question.'
    )
  }
})
</script>

<style scoped>
.section-intro { position: relative; padding: 48px 16px 8px; max-width: 1200px; margin: 0 auto; }
.headline { position: relative; font-weight: 800; font-size: clamp(1.8rem, 4.6vw, 2.6rem); line-height: 1.1; }
.headline .shimmer { position:absolute; inset:0; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.12), rgba(255,255,255,0)); transform: translateX(-100%); animation: shimmer 5s infinite; pointer-events: none; }
@keyframes shimmer { 0%{ transform: translateX(-100%) } 100%{ transform: translateX(100%) } }
.eyebrow { letter-spacing: 1px; font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; }
.toolbar :deep(.v-field) { background: rgba(255,255,255,0.06); }
.op-80 { opacity: .8; }
.pill { font-weight: 600; }
.chat-shell { display:flex; flex-direction:column; max-width: 980px; margin: 0 auto; height:70vh; min-height:500px; }
.messages { padding: 16px; overflow-y:auto; flex:1; }
.message { margin-bottom: 14px; display:flex; }
.message.user { justify-content:flex-end; }
.message.assistant { justify-content:flex-start; }
.bubble { max-width: 70%; padding: 10px 14px; border-radius: 16px; position:relative; background:rgba(154,95,255,0.18); backdrop-filter: blur(6px); }
.message.user .bubble { background: linear-gradient(135deg,#38d6ee44,#9a5fff55); }
.role { display:block; font-size:0.6rem; opacity:0.6; text-transform:uppercase; margin-bottom:4px; letter-spacing:1px; }
.text { white-space:pre-wrap; font-size:0.85rem; line-height:1.3; }
.pending .bubble { opacity:0.6; font-style:italic; }
.composer .v-textarea { flex:1; }
.send-btn { align-self:flex-end; }
</style>
