<template>
  <v-app>
    <v-main>
      <v-container class="py-6 animate-in" fluid>
        <v-row class="mb-4" align="center" justify="space-between">
          <v-col cols="12" md="6">
            <h1>Code Generation</h1>
          </v-col>
          <v-col cols="12" md="6" class="text-right">
            <v-select
              v-model="language"
              :items="languages"
              label="Language"
              class="mr-4"
              style="max-width: 220px"
            />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" md="6">
            <div class="glass-panel p-4 hover-raise" style="height: 100%">
            <v-textarea
              v-model="prompt"
              label="Describe what to generate"
              auto-grow
              rows="8"
              clearable
            />
            <div class="d-flex gap-2 mb-6">
              <v-btn class="bg-primary" @click="generate" :loading="loading">Generate!</v-btn>
              <v-btn class="bg-secondary" @click="genDocs" :disabled="!codeText" :loading="loadingDocs">Add Documentation</v-btn>
              <v-btn class="bg-secondary" @click="genTests" :disabled="!codeText" :loading="loadingTests">Add Unit Tests</v-btn>
            </div>
            </div>
          </v-col>

          <v-col cols="12" md="6">
            <div class="glass-panel p-4 hover-raise" style="height: 100%">
            <div class="mb-2 d-flex align-center justify-space-between">
              <v-tabs v-model="activeTab" density="comfortable" color="primary" bg-color="transparent">
                <v-tab value="code">Code</v-tab>
                <v-tab value="tests">Tests</v-tab>
              </v-tabs>
              <div>
                <v-btn size="small" variant="text" @click="copyCurrent" :disabled="!currentText">Copy</v-btn>
                <v-btn size="small" variant="text" @click="downloadCurrent" :disabled="!currentText">Download</v-btn>
              </div>
            </div>
            <div class="editor">
        <div ref="editorEl" style="height: 520px;"></div>
            </div>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import './monaco-setup'
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as monaco from 'monaco-editor'
import axios from 'axios'

const prompt = ref('')
const codeText = ref('')
const testsText = ref('')

const languageMap = {
  python: 'py',
  java: 'java',
  javascript: 'js',
  R: 'r',
  matlab: 'm',
  node: 'js'
} as const;

type Language = keyof typeof languageMap;
const languages = Object.keys(languageMap);
const language = ref<Language>('python');
let outputLanguage = ''

const activeTab = ref<'code' | 'tests'>('code')

const loading = ref(false)
const loadingTests = ref(false)
const loadingDocs = ref(false)

let editor: monaco.editor.IStandaloneCodeEditor | null = null
let codeModel: monaco.editor.ITextModel | null = null
let testsModel: monaco.editor.ITextModel | null = null
const editorEl = ref<HTMLDivElement | null>(null)

onMounted(() => {
  codeModel = monaco.editor.createModel(codeText.value, language.value)
  testsModel = monaco.editor.createModel(testsText.value, language.value)
  editor = monaco.editor.create(editorEl.value!, {
    model: codeModel,
    theme: 'vs-dark',
    minimap: { enabled: false },
    wordWrap: 'on',
    automaticLayout: true,
  })
  editor.onDidChangeModelContent(() => {
    const m = editor!.getModel()
    if (m === codeModel) codeText.value = m.getValue()
    else if (m === testsModel) testsText.value = m.getValue()
  })
})

watch(codeText, (val) => {
  if (codeModel && val !== codeModel.getValue()) codeModel.setValue(val)
})
watch(testsText, (val) => {
  if (testsModel && val !== testsModel.getValue()) testsModel.setValue(val)
})

watch(language, (lang) => {
  if (codeModel) monaco.editor.setModelLanguage(codeModel, lang)
  if (testsModel) monaco.editor.setModelLanguage(testsModel, lang)
})

watch(activeTab, (tab) => {
  if (!editor) return
  if (tab === 'code' && codeModel) editor.setModel(codeModel)
  if (tab === 'tests' && testsModel) editor.setModel(testsModel)
})

async function generate() {
  loading.value = true
  try {
    const res = await axios.post('/api/generate', { prompt: prompt.value, language: language.value })
    codeText.value = res.data.code
    activeTab.value = 'code'
    outputLanguage = language.value
  } catch (e: any) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function genTests() {
  loadingTests.value = true
  try {
    const res = await axios.post('/api/tests', { code: codeText.value})
    testsText.value = res.data.code
    activeTab.value = 'tests'
  } catch (e: any) {
    console.error(e)
  } finally {
    loadingTests.value = false
  }
}

async function genDocs() {
  loadingDocs.value = true
  try {
    const res = await axios.post('/api/docs', { code: codeText.value})
    codeText.value = res.data.code
    activeTab.value = 'code'
  } catch (e: any) {
    console.error(e)
  } finally {
    loadingDocs.value = false
  }
}

const currentText = computed(() => activeTab.value === 'code' ? codeText.value : testsText.value)

async function copyCurrent() {
  if (!currentText.value) return
  await navigator.clipboard.writeText(currentText.value)
}

function downloadCurrent() {
  if (!currentText.value) return
  const blob = new Blob([currentText.value], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  const baseExt = languageMap[outputLanguage]
  const suffix = activeTab.value === 'tests' ? '.test' : ''
  const ext = `${suffix}.${baseExt}`
  a.href = URL.createObjectURL(blob)
  a.download = `generated${ext}`
  a.click()
  URL.revokeObjectURL(a.href)
}

onBeforeUnmount(() => {
  editor?.dispose()
  codeModel?.dispose()
  testsModel?.dispose()
})
</script>

<style>
html, body, #app {
  height: 100%;
}
.gap-2 > * + * { margin-left: 8px; }
</style>
