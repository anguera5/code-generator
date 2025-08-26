<template>
  <v-snackbar
    v-model="store.visible"
    :timeout="store.active?.timeout ?? 4000"
    :color="mapColor(store.active?.type)"
    location="top right"
    variant="elevated"
    rounded="lg"
    :multi-line="true"
    @update:modelValue="val => { if (!val) store.onHidden() }"
  >
    <div class="d-flex align-center ga-2">
      <v-icon size="18" :icon="mapIcon(store.active?.type)" />
      <span>{{ store.active?.text }}</span>
    </div>
    <template #actions>
      <v-btn variant="text" size="small" @click="store.close()">Close</v-btn>
    </template>
  </v-snackbar>
  <!-- support stacked queue by mounting multiple but we keep one and rotate -->
</template>

<script lang="ts" setup>
import { useNotifyStore } from '../stores/notify'
const store = useNotifyStore()

function mapColor(t?: 'info'|'success'|'warning'|'error') {
  switch (t) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'info'
  }
}
function mapIcon(t?: 'info'|'success'|'warning'|'error') {
  switch (t) {
    case 'success': return 'mdi-check-circle-outline'
    case 'warning': return 'mdi-alert-outline'
    case 'error': return 'mdi-alert-circle-outline'
    default: return 'mdi-information-outline'
  }
}
</script>

<style scoped>
</style>
