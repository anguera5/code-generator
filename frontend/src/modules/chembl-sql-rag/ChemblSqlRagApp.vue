<template>
  <v-container class="py-0" fluid>
    <!-- Hero (standalone) -->
    <section class="cg-hero">
      <div class="hero-bg">
        <div class="blob b1" />
        <div class="blob b2" />
        <div class="grid-overlay" />
      </div>
      <div class="cg-hero-inner">
        <div class="d-flex flex-column flex-md-row align-center justify-space-between ga-4">
          <div class="flex-1">
            <div class="eyebrow">RAG + SQL</div>
            <h1 class="headline">ChEMBL SQL RAG <span class="shimmer" /></h1>
            <p class="op-80 mt-1">
              Plan SQL queries against the local ChEMBL snapshot using natural language. We embed context with
              <strong>text-embedding-3-large</strong> and generate SQL with <strong>gpt-4.1-mini</strong>.
            </p>
          </div>
          <div class="toolbar d-flex ga-3 align-center flex-wrap">
            <v-chip v-if="!apiKeyStore.apiKey" color="warning" variant="tonal" class="pill">Enter API key (top bar)</v-chip>
            <v-chip color="secondary" variant="tonal" class="pill">Local SQLite</v-chip>
          </div>
        </div>
      </div>
    </section>

    <div class="py-6"></div>
    <!-- Flow diagram for first impression -->
    <div class="flow-strip" ref="flowEl">
      <div class="step reveal">
        <v-icon icon="mdi-comment-question-outline" size="26" />
        <div class="label">Question</div>
      </div>
      <div class="arrow reveal"><v-icon icon="mdi-arrow-right" /></div>
      <div class="step reveal">
        <v-icon icon="mdi-brain" size="26" />
        <div class="label">LLM plan</div>
      </div>
      <div class="arrow reveal"><v-icon icon="mdi-arrow-right" /></div>
      <div class="step reveal">
        <v-icon icon="mdi-code-tags" size="26" />
        <div class="label">SQL</div>
      </div>
      <div class="arrow reveal"><v-icon icon="mdi-arrow-right" /></div>
      <div class="step reveal">
        <v-icon icon="mdi-database" size="26" />
        <div class="label">SQLite</div>
      </div>
      <div class="arrow reveal"><v-icon icon="mdi-arrow-right" /></div>
      <div class="step reveal">
        <v-icon icon="mdi-table" size="26" />
        <div class="label">Results</div>
      </div>
    </div>

    <!-- Feature strip for first impression -->
    <div class="feature-strip">
      <div class="feature">
        <v-icon icon="mdi-lightbulb-on-outline" color="primary" size="24" />
        <div class="t">Plan with LLM</div>
        <div class="s">Translate your question into optimized SQL</div>
      </div>
      <div class="feature">
        <v-icon icon="mdi-code-tags" color="secondary" size="24" />
        <div class="t">Elegant SQL</div>
        <div class="s">Syntax highlighted and lightly linted</div>
      </div>
      <div class="feature">
        <v-icon icon="mdi-table-column" color="primary" size="24" />
        <div class="t">Smart schema</div>
        <div class="s">Columns and meanings at a glance</div>
      </div>
      <div class="feature">
        <v-icon icon="mdi-database" color="secondary" size="24" />
        <div class="t">ChEMBL 35</div>
        <div class="s">Local SQLite snapshot for speed</div>
      </div>
    </div>
    <v-card class="pa-4 mb-6 glass-panel hover-raise mx-auto" elevation="2" max-width="1200">
      <div class="d-flex justify-center">
        <div class="input-wrap">
          <v-textarea
            v-model="question"
            label="Ask a question (e.g., 'Top 10 compounds active against a given target')"
            auto-grow
            rows="2"
            max-rows="6"
            hide-details
            density="comfortable"
          />
        </div>
      </div>
      <div class="d-flex justify-center ga-2 mt-3">
        <v-btn variant="tonal" color="secondary" @click="showExamplesDialog = true">Examples</v-btn>
        <v-btn color="primary" :loading="loading" :disabled="!apiKeyStore.apiKey || !question.trim()" @click="planSql">
          Plan SQL
        </v-btn>
        <v-btn color="secondary" :disabled="!sql.trim()" :loading="execLoading" @click="execSql">
          Run
        </v-btn>
      </div>
    </v-card>

    <!-- Examples Modal -->
    <v-dialog v-model="showExamplesDialog" max-width="900">
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <span>Typical ChEMBL questions</span>
          <v-btn icon="mdi-close" variant="text" @click="showExamplesDialog=false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div class="examples-grid">
            <v-sheet
              v-for="ex in examples"
              :key="ex.title"
              class="example-block"
              rounded
              border
              :elevation="1"
            >
              <div class="ex-title">{{ ex.title }}</div>
              <div class="ex-desc">{{ ex.description }}</div>
              <div class="d-flex ga-2 mt-3">
                <v-btn size="small" color="primary" variant="tonal" @click="useExample(ex, false)">Use</v-btn>
                <v-btn size="small" color="primary" @click="useExample(ex, true)">Use & Plan</v-btn>
              </div>
            </v-sheet>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-card v-if="sql || related.length" class="pa-4 glass-panel hover-raise mx-auto" elevation="2" max-width="1200">
      <v-row class="ga-4" align="stretch">
        <!-- SQL preview (full width) -->
        <v-col cols="12" md="12">
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="text-subtitle-2">Proposed SQL</div>
            <div>
              <v-btn size="small" variant="text" @click="copySql" :disabled="!sql">Copy</v-btn>
              <v-btn size="small" variant="text" @click="downloadSql" :disabled="!sql">Download</v-btn>
            </div>
          </div>
          <div class="editor" ref="sqlEditorEl" style="height: 460px;"></div>
          <div v-if="sqlMarkers.length" class="mt-2 small op-80">
            <v-chip v-for="(m, i) in sqlMarkers" :key="i" size="x-small" :color="m.severity==='error' ? 'error' : (m.severity==='warning' ? 'warning' : 'info')" class="ma-1" variant="tonal">
              {{ m.message }}
            </v-chip>
          </div>
        </v-col>

        <!-- Related tables + schema details (stacked below) -->
        <v-col cols="12" md="12" class="schema-panel">
          <div class="text-subtitle-2 mb-2 d-flex align-center ga-2">
            <span>Related tables</span>
            <v-spacer />
            <v-chip v-if="!tableCards.length" size="small" variant="tonal">(none)</v-chip>
          </div>
          <div class="chip-list mb-2">
            <v-chip v-for="t in tableCards" :key="t.name" class="ma-1 reveal" variant="tonal" color="secondary" @click="scrollToTable(t.name)">{{ t.name }}</v-chip>
          </div>
          <div class="schema-scroll">
            <v-expansion-panels variant="accordion" multiple>
              <v-expansion-panel v-for="t in tableCards" :key="t.name" :ref="setTableRef(t.name)" class="schema-card reveal">
                <v-expansion-panel-title>
                  <div class="d-flex align-center w-100">
                    <strong>{{ t.name }}</strong>
                    <v-spacer />
                    <v-btn size="x-small" variant="text" @click.stop="copySchema(t)">Copy schema</v-btn>
                  </div>
                  <template #subtitle>
                    <span v-if="t.description" class="small op-80">{{ t.description }}</span>
                  </template>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div v-if="t.columns && t.columns.length" class="kv-list">
                    <div v-for="col in t.columns" :key="col.name + (col.type||'')" class="kv-row">
                      <div class="k">{{ col.name }}</div>
                      <div class="v">
                        <span v-if="col.type" class="tag">{{ col.type }}</span>
                        <span v-if="col.pk" class="tag">PK</span>
                        <span v-if="col.fk" class="tag">FK</span>
                        <span v-if="col.uk" class="tag">UK</span>
                        <span v-if="col.notnull" class="tag">NOT NULL</span>
                        <span v-if="col.description" class="desc">{{ col.description }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-disabled small">No columns detected.</div>
                  <div v-if="t.foreign_keys && t.foreign_keys.length" class="fk-block mt-2">
                    <div class="small op-70 mb-1">Foreign keys</div>
                    <div class="kv-row" v-for="(fk, i) in t.foreign_keys" :key="i">
                      <div class="k">{{ fk.from }}</div>
                      <div class="v">→ {{ fk.table }}.{{ fk.to }} <span class="op-70" v-if="fk.on_delete">(on_delete: {{ fk.on_delete }})</span></div>
                    </div>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </v-col>
      </v-row>
    </v-card>

  <v-card v-if="rows.length" class="pa-4 mt-6 glass-panel hover-raise mx-auto" elevation="2" max-width="1200">
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
import '../../monaco-setup'
import { ref, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import * as monaco from 'monaco-editor'
import http from '../../lib/http'
import { useNotifyStore } from '../../stores/notify'
import { useApiKeyStore } from '../../stores/apiKey'

const apiKeyStore = useApiKeyStore()
const notify = useNotifyStore()
const loading = ref(false)
const question = ref('')
const showExamplesDialog = ref(false)
const examples = [
  { title: 'Top active compounds for a target', description: 'Top 10 compounds by activity against target CHEMBL203 (EGFR).', prompt: 'Top 10 compounds by potency (pChEMBL) against target CHEMBL203 (EGFR).' },
  { title: 'Assays with strong activity', description: 'Assays for DRD2 (CHEMBL240) with IC50 < 100 nM.', prompt: 'List assays for target CHEMBL240 (DRD2) with IC50 < 100 nM.' },
  { title: 'Drug mechanisms of action', description: 'Mechanisms of action for drug imatinib (CHEMBL941).', prompt: 'Show mechanisms of action for CHEMBL941 (imatinib).' },
  { title: 'Targets for a drug', description: 'Targets associated with CHEMBL941.', prompt: 'List all known targets for CHEMBL941 (imatinib).' },
  { title: 'Compound properties', description: 'Compounds with 300 <= MW <= 500 and bioavailability > 0.', prompt: 'Find compounds with molecular weight between 300 and 500 and bioavailability > 0.' },
  { title: 'Top journals', description: 'Top journals publishing ChEMBL assays in the last 5 years.', prompt: 'Top journals by count of assays recorded in the last 5 years.' },
]
const sql = ref('')
const related = ref<any[]>([])
const execLoading = ref(false)
const columns = ref<string[]>([])
const rows = ref<any[][]>([])
const limit = ref(100)


// Monaco editor for SQL preview
let sqlEditor: any = null
let sqlModel: any = null
const sqlEditorEl = ref<HTMLDivElement | null>(null)
const sqlMarkers = ref<Array<{ message: string; severity: 'error' | 'warning' | 'hint'; startLineNumber?: number; startColumn?: number }>>([])

function indexToPosition(text: string, index: number) {
  const lines = text.slice(0, index).split('\n')
  const lineNumber = lines.length
  const startColumn = (lines[lines.length - 1] || '').length + 1
  return { lineNumber, startColumn }
}

function lintSql(text: string) {
  const markers: any[] = []
  const uiMarkers: typeof sqlMarkers.value = []
  const lower = text.toLowerCase()
  const Sev = { Error: 8, Warning: 4, Hint: 1 }
  const addMarker = (msg: string, sev: number, at = 0) => {
    const pos = indexToPosition(text, at)
    markers.push({
      message: msg,
      severity: sev,
      startLineNumber: pos.lineNumber,
      startColumn: pos.startColumn,
      endLineNumber: pos.lineNumber,
      endColumn: pos.startColumn + 1,
    })
    uiMarkers.push({ message: msg, severity: sev === Sev.Error ? 'error' : sev === Sev.Warning ? 'warning' : 'hint', startLineNumber: pos.lineNumber, startColumn: pos.startColumn })
  }
  // Basic rules mirroring backend constraints
  if (!(lower.trim().startsWith('select') || lower.trim().startsWith('with'))) {
    addMarker('Only SELECT or WITH queries are allowed.', Sev.Error, 0)
  }
  const forbidden = ['pragma','attach','detach','vacuum','insert','update','delete','drop','alter','create','replace','begin','commit','rollback']
  for (const tok of forbidden) {
    const idx = lower.indexOf(tok)
    if (idx !== -1) addMarker(`Forbidden token: ${tok}`, Sev.Error, idx)
  }
  if (text.includes(';')) {
    addMarker('Semicolons are not allowed (single statement only).', Sev.Warning, text.indexOf(';'))
  }
  if (!/\blimit\b/i.test(text)) {
    addMarker('LIMIT will be enforced server-side.', Sev.Hint, 0)
  }
  if (sqlModel) monaco.editor.setModelMarkers(sqlModel, 'chembl-sql-lint', markers)
  sqlMarkers.value = uiMarkers
}

function ensureSqlEditor() {
  if (!sqlModel) sqlModel = monaco.editor.createModel(sql.value || '', 'sql')
  if (!sqlEditor && sqlEditorEl.value) {
    sqlEditor = monaco.editor.create(sqlEditorEl.value, {
      model: sqlModel,
      theme: 'vs-dark',
      readOnly: true,
      automaticLayout: true,
      minimap: { enabled: false },
      wordWrap: 'on',
    })
  }
  if (sqlModel) sqlModel.setValue(sql.value || '')
  lintSql(sql.value || '')
}

watch(sql, (val) => {
  if (sqlModel && val !== sqlModel.getValue()) sqlModel.setValue(val)
  lintSql(val || '')
})

onMounted(() => {
  nextTick(() => ensureSqlEditor())
})

onBeforeUnmount(() => {
  sqlEditor?.dispose()
  sqlModel?.dispose()
})

// Table cards derived from related_tables
type TableCard = { name: string; description?: string; columns?: Array<{ name: string; type?: string; pk?: boolean; fk?: boolean; uk?: boolean; notnull?: boolean; default?: string | null; description?: string; keyRaw?: string; nullableRaw?: string }>; foreign_keys?: Array<{ from: string; table: string; to: string; on_delete?: string }>; raw?: string }
const tableCards = ref<TableCard[]>([])
const flowEl = ref<HTMLElement | null>(null)
const tableRefs = new Map<string, HTMLElement | null>()
const setTableRef = (name: string) => (el: HTMLElement | null) => tableRefs.set(name, el)
function scrollToTable(name: string) {
  const el = tableRefs.get(name)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
const collapsedTables = ref<Record<string, boolean>>({})
function toggleTable(name: string) {
  collapsedTables.value[name] = !collapsedTables.value[name]
}

function parseRelatedTables(rt: any): TableCard[] {
  // Expect entries possibly in these shapes:
  // - "table_name"
  // - "table_name: column1 (TYPE) - description; column2 (TYPE) - desc; ..."
  // - JSON-like descriptions are left in raw
  const cards: TableCard[] = []
  // Normalize input to an iterable list of entries
  const dbg = (...args: any[]) => console.info('[CHEMBL][parseRelatedTables]', ...args)
  let list: any[] = []
  if (!rt) list = []
  else if (Array.isArray(rt)) list = rt
  else if (typeof rt === 'object') {
    // Could be a single table dict or a dict-of-tables
    if ((rt as any).table || (rt as any).name) list = [rt]
    else {
      // dict-of-tables: preserve the key as table name if value lacks it
      list = Object.entries(rt as Record<string, any>).map(([k, v]) => {
        if (v && typeof v === 'object' && !('table' in v) && !('name' in v)) {
          return { ...(v as any), table: k }
        }
        return v
      })
    }
  } else {
    list = [rt]
  }
  dbg('input kind =', Array.isArray(rt) ? 'array' : typeof rt, 'len/keys =', Array.isArray(rt) ? (rt as any[]).length : (rt && typeof rt==='object' ? Object.keys(rt).length : 1))

  const tryParseJsonLoose = (txt: string): any | null => {
    try { return JSON.parse(txt) } catch {}
    try {
      let j = txt
      // Python repr -> JSON-ish
      j = j.replace(/\bNone\b/g, 'null').replace(/\bTrue\b/g, 'true').replace(/\bFalse\b/g, 'false')
      // Keys: 'key': -> "key":
      j = j.replace(/(['"])??([A-Za-z0-9_]+)\1?\s*:/g, '"$2":')
      // Single-quoted strings -> JSON strings
      j = j.replace(/'([^']*)'/g, (_m, s) => JSON.stringify(String(s)))
      return JSON.parse(j)
    } catch { return null }
  }

  for (const entry of list) {
    if (!entry) continue
    // Structured dict from backend
    if (typeof entry === 'object' && (entry.table || entry.name)) {
  dbg('entry: structured object with table/name')
      const tname: string = (entry.table || entry.name || '').toString()
      const description: string | undefined = (entry.description || '').toString() || undefined
      const cols: TableCard['columns'] = []
      if (Array.isArray(entry.columns)) {
        for (const c of entry.columns) {
          const keyStr = (c.key || '').toString().toUpperCase()
          const pk = keyStr.includes('PK')
          const fk = keyStr.includes('FK')
          const uk = keyStr.includes('UK')
          const notnull = typeof c.nullable === 'string' ? /NOT\s+NULL/i.test(c.nullable) : !!c.notnull
          cols!.push({
            name: c.name,
            type: c.type,
            pk,
            fk,
            uk,
            notnull,
            description: c.comment || c.description,
            keyRaw: c.key,
            nullableRaw: c.nullable,
          })
        }
      }
    cards.push({ name: tname, description, columns: cols, raw: JSON.stringify(entry) })
    dbg('added card', tname, 'cols=', cols?.length || 0)
      continue
    }
    const txt = String(entry).trim()
    // Try JSON first
    if (txt.startsWith('{') || txt.startsWith('[')) {
    dbg('entry: stringified JSON-ish, attempting parse')
      const obj = tryParseJsonLoose(txt)
      if (obj) {
        if (Array.isArray(obj)) {
      dbg('parsed array JSON with length', obj.length)
          for (const o of obj) {
            const name = (o.name || o.table || '').trim()
            if (!name) continue
            // Map column fields if present
            const mappedCols = Array.isArray(o.columns) ? o.columns.map((c: any) => {
              const keyStr = (c.key || '').toString().toUpperCase()
              return {
                name: c.name,
                type: c.type,
                pk: keyStr.includes('PK'),
                fk: keyStr.includes('FK'),
                uk: keyStr.includes('UK'),
                notnull: typeof c.nullable === 'string' ? /NOT\s+NULL/i.test(c.nullable) : !!c.notnull,
                description: c.comment || c.description,
                keyRaw: c.key,
                nullableRaw: c.nullable,
              }
            }) : (o.columns || o.cols || [])
            cards.push({ name, description: o.description, columns: mappedCols, foreign_keys: o.foreign_keys || o.fk || [], raw: entry })
            dbg('added card (json array)', name, 'cols=', Array.isArray(mappedCols) ? mappedCols.length : 0)
          }
          continue
        } else if (obj && typeof obj === 'object') {
          const name = (obj.name || obj.table || '').trim()
          if (name) {
            const mappedCols = Array.isArray(obj.columns) ? obj.columns.map((c: any) => {
              const keyStr = (c.key || '').toString().toUpperCase()
              return {
                name: c.name,
                type: c.type,
                pk: keyStr.includes('PK'),
                fk: keyStr.includes('FK'),
                uk: keyStr.includes('UK'),
                notnull: typeof c.nullable === 'string' ? /NOT\s+NULL/i.test(c.nullable) : !!c.notnull,
                description: c.comment || c.description,
                keyRaw: c.key,
                nullableRaw: c.nullable,
              }
            }) : (obj.columns || obj.cols || [])
    cards.push({ name, description: obj.description, columns: mappedCols, foreign_keys: obj.foreign_keys || obj.fk || [], raw: entry })
    dbg('added card (json object)', name, 'cols=', Array.isArray(mappedCols) ? mappedCols.length : 0)
            continue
          }
        }
      }
    }
    // Try "- Table: NAME" style with Description and Columns
    if (/Table:\s*/i.test(txt) && /Columns:/i.test(txt)) {
  dbg('entry: Table:/Columns: style')
      const nameMatch = txt.match(/Table:\s*([A-Za-z0-9_]+)/i)
      const name = nameMatch ? nameMatch[1].trim() : undefined
      if (name) {
        const descMatch = txt.match(/Description:\s*([\s\S]*?)(?:\n\s*Columns:|$)/i)
        const description = descMatch ? descMatch[1].trim() : undefined
        const columnsSectionMatch = txt.match(/Columns:\s*([\s\S]*)/i)
        const cols: TableCard['columns'] = []
        if (columnsSectionMatch) {
          const lines = columnsSectionMatch[1].split(/\n+/).map(l => l.trim()).filter(l => l)
          for (const line of lines) {
            // - [PK,UK] COL (TYPE, NOT NULL) — description
            const m = line.match(/^[-*]\s*(?:\[([^\]]+)\]\s*)?([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*(?:—|\-|:)\s*(.*)?$/)
            if (m) {
              const attrsRaw = (m[1] || '').split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
              const colName = m[2]
              const typeRaw = m[3] || ''
              const type = typeRaw.split(',')[0].trim()
              const notnull = /NOT\s+NULL/i.test(typeRaw)
              const descriptionCol = (m[4] || '').trim() || undefined
              cols!.push({
                name: colName,
                type,
                notnull,
                pk: attrsRaw.includes('PK'),
                fk: attrsRaw.includes('FK'),
                uk: attrsRaw.includes('UK'),
                description: descriptionCol,
              })
            }
          }
        }
        const card: TableCard = { name, description, columns: cols, raw: entry }
        cards.push(card)
        dbg('added card (table style)', name, 'cols=', cols.length)
        continue
      }
    }
    const [namePart, details] = txt.split(/:\s*/, 2)
    const name = namePart.trim()
    const card: TableCard = { name, raw: entry }
    if (details) {
      const cols: TableCard['columns'] = []
      for (const chunk of details.split(/;\s*/)) {
        if (!chunk) continue
        // Try to parse "col (TYPE) - description" or "col TYPE - description"
        const m = chunk.match(/^([\w\d_]+)\s*(?:\(([^)]+)\)|\s+([A-Z][A-Z0-9_]+))?\s*(?:-\s*(.*))?$/i)
        if (m) {
          const colName = m[1]
          const type = (m[2] || m[3] || '').trim() || undefined
          const description = (m[4] || '').trim() || undefined
          cols!.push({ name: colName, type, description })
        }
      }
      if (cols && cols.length) card.columns = cols
    }
    cards.push(card)
    dbg('added card (fallback)', name, 'cols=', card.columns?.length || 0)
  }
  // initialize collapsed state (default collapsed to show description first)
  const collapsed: Record<string, boolean> = {}
  for (const c of cards) collapsed[c.name] = true
  collapsedTables.value = collapsed
  dbg('total cards =', cards.length, 'names =', cards.map(c => c.name))
  return cards
}

async function planSql() {
  loading.value = true
  sql.value = ''
  related.value = []
  try {
  const res = await http.post('/api/chembl/plan-sql', { prompt: question.value, api_key: apiKeyStore.apiKey })
    sql.value = res.data.sql
  console.info('[CHEMBL] plan response keys =', Object.keys(res.data || {}))
  console.info('[CHEMBL] related_tables type =', Array.isArray(res.data?.related_tables) ? 'array' : typeof res.data?.related_tables)
  related.value = res.data.related_tables ?? []
  tableCards.value = parseRelatedTables(related.value)
  console.info('[CHEMBL] tableCards count =', tableCards.value.length, 'names =', tableCards.value.map(t => t.name))
  nextTick(() => { ensureSqlEditor(); revealDynamic() })
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

// Utilities
async function copySql() {
  if (!sql.value) return
  await navigator.clipboard.writeText(sql.value)
}

function downloadSql() {
  if (!sql.value) return
  const blob = new Blob([sql.value], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'query.sql'
  a.click()
  URL.revokeObjectURL(a.href)
}

function copySchema(t: TableCard) {
  const payload: any = {
    table: t.name,
    description: t.description,
  columns: (t.columns || []).map(c => ({ name: c.name, type: c.type, description: c.description, pk: c.pk, notnull: c.notnull, default: c.default, key: c.keyRaw, nullable: c.nullableRaw })),
    foreign_keys: t.foreign_keys || [],
  }
  const text = JSON.stringify(payload, null, 2)
  navigator.clipboard.writeText(text)
}

function useExample(ex: { title: string; description: string; prompt: string }, autoPlan = false) {
  question.value = ex.prompt
  showExamplesDialog.value = false
  if (autoPlan) planSql()
}

// Simple scroll-reveal animations
onMounted(() => {
  const observer = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) e.target.classList.add('revealed')
    }
  }, { threshold: 0.1 })
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el))
})

// Mark dynamically added chips/panels as revealed so they are visible
function revealDynamic() {
  const nodes = document.querySelectorAll('.chip-list .reveal, .schema-card.reveal')
  nodes.forEach(el => el.classList.add('revealed'))
}
</script>

<style scoped>
.cg-hero { position: relative; overflow: hidden; padding: 36px 16px 0; }
.cg-hero-inner { position: relative; z-index: 2; max-width: 1200px; margin: 0 auto; padding: 28px 8px 8px; }
.hero-bg { position:absolute; inset:0; z-index:1; overflow:hidden; }
.blob { position:absolute; filter: blur(48px); opacity:.55; border-radius: 50%; mix-blend-mode: screen; }
.b1 { width: 520px; height: 520px; background: radial-gradient(circle at 30% 30%, #9a5fff55, transparent 60%); top: -120px; left: -120px; animation: float1 14s ease-in-out infinite; }
.b2 { width: 560px; height: 560px; background: radial-gradient(circle at 70% 70%, #38d6ee55, transparent 60%); bottom: -160px; right: -160px; animation: float2 18s ease-in-out infinite; }
@keyframes float1 { 0%,100%{ transform: translate(0,0) } 50%{ transform: translate(20px,16px) } }
@keyframes float2 { 0%,100%{ transform: translate(0,0) } 50%{ transform: translate(-24px,-18px) } }
.grid-overlay { position:absolute; inset:0; background-image: linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px); background-size: 36px 36px; mask-image: radial-gradient(circle at 50% 0%, black 20%, transparent 70%); opacity:.45; }
.headline { position: relative; font-weight: 800; font-size: clamp(1.8rem, 4.6vw, 2.6rem); line-height: 1.1; }
.headline .shimmer { position:absolute; inset:0; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.12), rgba(255,255,255,0)); transform: translateX(-100%); animation: shimmer 5s infinite; pointer-events: none; }
@keyframes shimmer { 0%{ transform: translateX(-100%) } 100%{ transform: translateX(100%) } }
.eyebrow { letter-spacing: 1px; font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; }
.toolbar :deep(.v-field) { background: rgba(255,255,255,0.06); }
.op-80 { opacity: .8; }
.pill { font-weight: 600; }
.result-box { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; white-space: pre-wrap; min-height: 48px; }
.result-box.sql { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.chip-list { display:flex; flex-wrap: wrap; align-items: flex-start; }
.table-wrapper { overflow:auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); }
.result-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.result-table th, .result-table td { padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.08); white-space: nowrap; }
.result-table thead th { position: sticky; top: 0; background: rgba(255,255,255,0.06); text-align: left; }

/* Schema panel */
.schema-panel { display:flex; flex-direction:column; }
.schema-scroll { max-height: 420px; overflow:auto; padding-right: 4px; }
.schema-card { border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px; margin-bottom: 10px; background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)); }
.schema-title { font-weight: 700; margin-bottom: 6px; }
.schema-title.clickable { cursor: pointer; }
.kv-list { display:flex; flex-direction:column; gap: 6px; }
.kv-row { display:flex; align-items:center; gap: 8px; }
.kv-row .k { min-width: 160px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.85rem; }
.kv-row .v { display:flex; flex-wrap: wrap; gap: 6px; }
.tag { display:inline-block; background: rgba(56,214,238,0.12); border: 1px solid rgba(56,214,238,0.35); padding: 1px 6px; border-radius: 999px; font-size: 0.72rem; }

/* Centered input width */
.input-wrap { width: 100%; max-width: 900px; }

/* Examples grid */
.examples-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; }
.example-block { padding: 12px; background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); }
.example-block .ex-title { font-weight: 700; margin-bottom: 4px; }
.example-block .ex-desc { font-size: .9rem; opacity: .8; }
@media (max-width: 700px) { .examples-grid { grid-template-columns: 1fr; } }

/* Feature strip */
.feature-strip { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; max-width: 1200px; margin: 0 auto 16px; padding: 0 8px; }
.feature { display:flex; flex-direction:column; align-items:flex-start; gap: 4px; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); }
.feature .t { font-weight: 700; font-size: 0.95rem; }
.feature .s { font-size: 0.8rem; opacity: .8; }
@media (max-width: 900px) { .feature-strip { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 520px) { .feature-strip { grid-template-columns: 1fr; } }

/* Flow strip */
.flow-strip { display:flex; align-items:center; justify-content:center; gap: 10px; max-width: 1200px; margin: 0 auto 12px; padding: 0 8px; }
.flow-strip .step { display:flex; flex-direction:column; align-items:center; gap: 6px; padding: 8px 10px; border-radius: 10px; border: 1px dashed var(--border); background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); min-width: 90px; }
.flow-strip .label { font-size: 0.8rem; opacity: .9; }
.flow-strip .arrow { opacity: .6; }
@media (max-width: 680px) {
  .flow-strip { flex-wrap: wrap; row-gap: 6px; }
  .flow-strip .arrow { display:none; }
}

/* Reveal animations */
.reveal { opacity: 0; transform: translateY(8px); transition: opacity .4s ease, transform .4s ease; }
.reveal.revealed { opacity: 1; transform: translateY(0); }
/* Ensure dynamic schema chips/panels are visible even if reveal didn't trigger */
.schema-scroll .reveal, .chip-list .reveal { opacity: 1 !important; transform: none !important; }
</style>
