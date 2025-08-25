<template>
  <v-container class="py-6" fluid>
    <h1 class="mb-4">ChEMBL SQL RAG</h1>
    <v-card class="pa-4 mb-6" elevation="2" max-width="980">
      <div class="d-flex align-center ga-3">
        <v-textarea
          v-model="question"
          label="Ask a question (e.g., 'Top 10 compounds active against a given target')"
          auto-grow
          rows="2"
          max-rows="6"
          hide-details
          class="flex-1"
          density="comfortable"
        />
      </div>
      <div class="d-flex align-center mt-3">
        <v-spacer />
        <v-btn color="primary" :loading="loading" :disabled="!apiKeyStore.apiKey || !question.trim()" @click="planSql">
          Plan SQL
        </v-btn>
      </div>
    </v-card>

    <v-card v-if="sql || related.length" class="pa-4" elevation="2" max-width="980">
      <div class="d-flex ga-4 flex-column flex-sm-row">
        <div class="flex-1">
          <div class="text-subtitle-2 mb-2">Proposed SQL</div>
          <pre class="result-box sql">{{ sql || '(no result yet)' }}</pre>
        </div>
        <div class="flex-1">
          <div class="text-subtitle-2 mb-2">Related tables</div>
          <div class="chip-list">
            <v-chip v-for="t in related" :key="t" class="ma-1" variant="tonal" color="secondary">{{ t }}</v-chip>
            <div v-if="!related.length" class="text-disabled">(none)</div>
          </div>
        </div>
      </div>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import axios from 'axios'
import { useApiKeyStore } from '../../stores/apiKey'

const apiKeyStore = useApiKeyStore()
const loading = ref(false)
const question = ref('')
const sql = ref('')
const related = ref<string[]>([])

async function planSql() {
  loading.value = true
  sql.value = ''
  related.value = []
  try {
    const res = await axios.post('/api/chembl/plan-sql', { prompt: question.value, api_key: apiKeyStore.apiKey })
    sql.value = res.data.sql
    related.value = res.data.related_tables || []
  } catch (e:any) {
    sql.value = e?.response?.data?.detail || e?.message || 'Failed to plan SQL'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.result-box { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; white-space: pre-wrap; min-height: 48px; }
.result-box.sql { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.chip-list { display:flex; flex-wrap: wrap; align-items: flex-start; }
</style>
