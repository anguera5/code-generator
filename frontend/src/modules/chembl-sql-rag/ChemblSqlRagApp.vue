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
        <v-btn class="ml-2" color="secondary" :disabled="!sql.trim()" :loading="execLoading" @click="execSql">
          Run
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

    <v-card v-if="rows.length" class="pa-4 mt-6" elevation="2" max-width="980">
      <div class="d-flex align-center">
        <div class="text-subtitle-2">Results ({{ rows.length }} rows)</div>
        <v-spacer />
        <v-text-field v-model.number="limit" type="number" label="Limit" min="1" max="10000" density="compact" hide-details style="max-width: 120px" />
      </div>
      <v-divider class="my-2" />
      <div class="table-wrapper">
        <table class="result-table">
          <thead>
            <tr>
              <th v-for="c in columns" :key="c">{{ c }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, idx) in rows" :key="idx">
              <td v-for="(c, j) in r" :key="j">{{ c }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import http from '../../lib/http'
import { useNotifyStore } from '../../stores/notify'
import { useApiKeyStore } from '../../stores/apiKey'

const apiKeyStore = useApiKeyStore()
const notify = useNotifyStore()
const loading = ref(false)
const question = ref('')
const sql = ref('')
const related = ref<string[]>([])
const execLoading = ref(false)
const columns = ref<string[]>([])
const rows = ref<any[][]>([])
const limit = ref(100)

async function planSql() {
  loading.value = true
  sql.value = ''
  related.value = []
  try {
  const res = await http.post('/api/chembl/plan-sql', { prompt: question.value, api_key: apiKeyStore.apiKey })
    sql.value = res.data.sql
    related.value = res.data.related_tables || []
  } catch (e:any) {
    const msg = e?.response?.data?.detail || e?.message || 'Failed to plan SQL'
    sql.value = msg
  } finally {
    loading.value = false
  }
}

async function execSql() {
  execLoading.value = true
  columns.value = []
  rows.value = []
  try {
  const res = await http.post('/api/chembl/execute-sql', { sql: sql.value, limit: limit.value })
    columns.value = res.data.columns
    rows.value = res.data.rows
  } catch (e:any) {
    columns.value = []
    rows.value = []
    const msg = e?.response?.data?.detail || e?.message || 'Failed to execute SQL'
  } finally {
    execLoading.value = false
  }
}
</script>

<style scoped>
.result-box { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; white-space: pre-wrap; min-height: 48px; }
.result-box.sql { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.chip-list { display:flex; flex-wrap: wrap; align-items: flex-start; }
.table-wrapper { overflow:auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); }
.result-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.result-table th, .result-table td { padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.08); white-space: nowrap; }
.result-table thead th { position: sticky; top: 0; background: rgba(255,255,255,0.06); text-align: left; }
</style>
