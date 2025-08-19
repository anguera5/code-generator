import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useApiKeyStore = defineStore('apiKey', () => {
  const apiKey = ref('')
  function setKey(val: string) { apiKey.value = val }
  return { apiKey, setKey }
})
