<template>
  <v-container class="py-6" fluid>
    <h1 class="mb-4">Food Packaging Forum RAG</h1>
    <v-card class="chat-shell mb-4" elevation="2">
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
