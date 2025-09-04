<template>
  <v-container class="py-8" fluid>
    <div class="section">
      <PageTitle>
        <div class="d-flex align-center ga-3">
          <v-icon icon="mdi-alert-circle-outline" color="warning" size="28" />
          <h1 class="headline">Page not found <span class="shimmer" /></h1>
        </div>
        <p class="op-80 mt-2">We couldn't find the page you were looking for.</p>
      </PageTitle>
      <v-card class="glass-panel mx-auto mt-4" elevation="2" max-width="900">
        <v-card-text>
          <div class="text-body-2 op-80">
            The URL might be incorrect or the page has moved. You can go back home or open one of the available modules.
          </div>
          <div class="d-flex ga-2 mt-3 flex-wrap">
            <v-btn color="primary" :to="{ name: 'home' }" variant="flat">Go to Home</v-btn>
            <v-btn color="secondary" :to="'/code-generator'" variant="tonal">Code Generator</v-btn>
            <v-btn color="secondary" :to="'/code-review'" variant="tonal">Code Review</v-btn>
            <v-btn color="secondary" :to="'/fpf-chatbot'" variant="tonal">FPF Chatbot</v-btn>
            <v-btn color="secondary" :to="'/chembl-agent'" variant="tonal">ChEMBL Agent</v-btn>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </v-container>
  
</template>

<script setup lang="ts">
import PageTitle from '../components/PageTitle.vue'
</script>

<style scoped>
.section { max-width: 1200px; margin: 0 auto; }
.headline { font-size: clamp(1.8rem, 4.6vw, 2.6rem); font-weight: 800; position: relative; }
.headline .shimmer { position:absolute; inset:0; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.12), rgba(255,255,255,0)); transform: translateX(-100%); animation: shimmer 5s infinite; pointer-events: none; }
@keyframes shimmer { 0%{ transform: translateX(-100%) } 100%{ transform: translateX(100%) } }
.op-80 { opacity: .8; }
.glass-panel { background: rgba(255,255,255,0.05); backdrop-filter: blur(8px) saturate(160%); border: 1px solid rgba(148,163,184,0.18); }
</style>
