<template>
  <v-app>
    <GlobalNotifier />
    <HeroBackdrop />
    <v-navigation-drawer v-model="drawer" temporary class="app-drawer">
      <div class="drawer-header d-flex align-center py-3">
        <v-btn class="nav-trigger mr-2" icon variant="text" @click="drawer = false" :aria-label="'Close project drawer'">
          <v-img src="/src/assets/favicon.png" width="26" height="26" alt="Close drawer" />
        </v-btn>
      </div>
      <div class="drawer-header d-flex align-center px-4 py-3">
        <v-icon icon="mdi-cube-outline" size="26" class="mr-2 gradient-icon" />
        <span class="drawer-title">Projects</span>
      </div>
      <v-divider class="mb-2 opacity-divider" />
      <v-list density="compact" nav>
        <v-list-item
          v-for="m in modules"
          :key="m.path"
          :to="m.path"
          link
        >
          <template #prepend>
            <v-icon icon="mdi-rocket-launch-outline" size="18" class="list-bullet" />
          </template>
          <v-list-item-title class="list-title">{{ m.title }}</v-list-item-title>
          <v-list-item-subtitle v-if="m.description">
            {{ m.description }}
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
      <template #append>
        <div class="about-section px-4 pb-4 pt-2">
          <v-divider class="mb-3 opacity-divider" />
          <div class="drawer-header d-flex align-center py-3">
            <v-icon icon="mdi-account" size="26" class="mr-2 gradient-icon" />
            <span class="drawer-title">About me</span>
          </div>
          <div class="d-flex align-center ga-2">
            <v-btn icon variant="tonal" size="small" :to="'/about'">
              <v-icon icon="mdi-information" />
            </v-btn>
            <v-btn icon variant="tonal" size="small" :href="links.linkedin" target="_blank" rel="noopener" aria-label="LinkedIn profile">
              <v-icon icon="mdi-linkedin" />
            </v-btn>
            <v-btn icon variant="tonal" size="small" :href="links.github" target="_blank" rel="noopener" aria-label="GitHub profile">
              <v-icon icon="mdi-github" />
            </v-btn>
          </div>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar flat color="transparent" class="app-bar">
      <v-btn class="nav-trigger mr-2" icon variant="text" @click="drawer = !drawer" :aria-label="drawer ? 'Close project drawer' : 'Open project drawer'">
        <v-img src="/src/assets/favicon.png" width="28" height="28" alt="Projects" class="elevate" />
      </v-btn>
      <v-toolbar-title>
        <router-link to="/" class="brand brand-link">GenAI<span class="accent">Portfolio</span></router-link>
      </v-toolbar-title>
      <v-spacer />
      <!-- Mobile API key button -->
      <v-btn class="api-key-button-mobile mr-2" icon variant="tonal" @click="apiKeyDialog = true" aria-label="Set API Key on mobile">
        <v-icon icon="mdi-key-outline" />
      </v-btn>
      <v-text-field
        v-model="apiKeyStore.apiKey"
        label="API Key"
        type="password"
        variant="outlined"
        density="compact"
        hide-details
        style="max-width:230px"
        class="mr-4 api-key-field"
      />
    </v-app-bar>

    <!-- API Key Dialog (mobile-friendly) -->
    <v-dialog v-model="apiKeyDialog" max-width="420">
      <v-card>
        <v-card-title>Set API Key</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="tempApiKey"
            label="API Key"
            type="password"
            variant="outlined"
            hide-details
            autofocus
          />
          <div class="text-caption mt-2" style="opacity:.7">Your key is stored locally in your browser.</div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="apiKeyDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="saveApiKey">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { modules } from './modules'
import { useApiKeyStore } from './stores/apiKey'
import GlobalNotifier from './components/GlobalNotifier.vue'
import HeroBackdrop from './components/HeroBackdrop.vue'
const drawer = ref(false)
const links = {
  linkedin: 'https://www.linkedin.com/in/albert-anguera-sempere/',
  github: 'https://github.com/anguera5'
}
const apiKeyStore = useApiKeyStore()

// Mobile API key dialog state
const apiKeyDialog = ref(false)
const tempApiKey = ref(apiKeyStore.apiKey)
function saveApiKey() {
  apiKeyStore.apiKey = tempApiKey.value
  apiKeyDialog.value = false
}
</script>

<style>
html, body, #app { height: 100%; }
/* Prevent horizontal scrollbar on mobile */
html, body { overflow-x: hidden; }

.app-bar { backdrop-filter: blur(6px) saturate(140%); background: linear-gradient(90deg, rgba(255,255,255,0.04), rgba(255,255,255,0)); }
.nav-trigger { color: #e2e8f0 !important; }
.nav-trigger .v-img { border-radius: 8px; box-shadow: 0 2px 6px -2px rgba(0,0,0,.6); transition: transform .25s ease, box-shadow .25s ease; }
.nav-trigger .v-img:hover { transform: scale(1.08) rotate(-4deg); box-shadow: 0 6px 18px -4px rgba(0,0,0,.7); }
.nav-icon { color: #e2e8f0 !important; }
.clickable-title { cursor: pointer; user-select: none; }
.brand { font-weight: 700; letter-spacing: 0.5px; font-size: 1.05rem; background: linear-gradient(90deg,#fff,#c7d2fe,#93c5fd,#22d3ee); -webkit-background-clip: text; background-clip: text; color: transparent; }
.brand .accent { color: #9a5fff; -webkit-text-fill-color: #9a5fff; background: none; }
/* Make only the brand text clickable area */
.brand-link { text-decoration: none; display: inline-flex; align-items: center; cursor: pointer; }

.app-drawer { background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)) !important; backdrop-filter: blur(14px) saturate(160%); border-right: 1px solid rgba(148,163,184,0.18) !important; }
.drawer-header { color: #e2e8f0; font-weight: 600; }
.drawer-title { font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }
.gradient-icon { background: linear-gradient(135deg,#9a5fff,#38d6ee); -webkit-background-clip: text; background-clip: text; color: transparent; }
.opacity-divider { opacity: 0.4; }

.v-list { --list-pad: 4px; }
.v-list-item { border-radius: 10px; margin: 2px 8px; transition: background .18s ease, transform .18s ease; }
.v-list-item:hover { background: rgba(154,95,255,0.14) !important; transform: translateX(2px); }
.v-list-item--active { background: linear-gradient(90deg, rgba(154,95,255,0.3), rgba(56,214,238,0.18)) !important; }
.list-bullet { opacity: 0.85; margin-right: 4px; }
.list-title { font-weight: 600; font-size: 0.9rem; }
.v-list-item-title, .v-list-item-subtitle { color: #e2e8f0 !important; }
.v-list-item-subtitle { opacity: 0.55; }


.about-section { color:#e2e8f0; font-size:0.75rem; }
.about-label { font-size:0.65rem; text-transform:uppercase; letter-spacing:1px; opacity:0.55; }
.about-section .v-btn { background: rgba(255,255,255,0.07); }
.about-section .v-btn:hover { background: rgba(154,95,255,0.25); }

/* Ensure landing page text is white by default */
body, .v-main, .v-container, .v-card, .v-alert, p, h2, h3, h4, h5, h6 { color: #e2e8f0; }

/* Ensure content sits above the global background */
.v-main { position: relative; z-index: 1; }

.api-key-field input { font-size: 0.75rem; letter-spacing: 0.5px; }
/* Desktop shows text field; mobile shows key icon */
.api-key-button-mobile { display: none; }

/* Mobile tweaks: prevent title from truncating and free space */
@media (max-width: 600px) {
  /* Hide API key input on small screens to avoid crowding */
  .api-key-field { display: none !important; }
  .api-key-button-mobile { display: inline-flex; }

  /* Let the title breathe and avoid ellipsis */
  .app-bar .v-toolbar-title {
    overflow: visible;
    text-overflow: clip;
    white-space: nowrap;
    max-width: 100%;
    min-width: 0;
  }

  /* Slightly reduce brand size on very small widths */
  .brand { font-size: 0.95rem; }

  /* Make the nav icon a touch smaller to gain a few pixels */
  .nav-trigger .v-img { width: 24px; height: 24px; }
}

</style>
