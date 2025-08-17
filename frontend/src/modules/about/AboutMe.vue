<template>
  <v-container class="py-8" fluid>
    <h1>About Me</h1>
    <p class="mt-4">
      Hello — I'm Albert Anguera. This site demonstrates GenAI utilities: a code generator and
      a code-review webhook that uses an LLM to review pull requests. Use the <strong>Code Review</strong>
      module to configure a repository webhook that posts PR events to the backend for automated reviews.
    </p>

    <v-divider class="my-6" />

    <h2 class="text-h6 mb-2">Contact</h2>
    <p>
      Find me on:
    </p>
    <div class="d-flex gap-3 mt-2">
      <v-btn icon :href="links.linkedin" target="_blank" rel="noopener" aria-label="LinkedIn">
        <v-icon>mdi-linkedin</v-icon>
      </v-btn>
      <v-btn icon :href="links.github" target="_blank" rel="noopener" aria-label="GitHub">
        <v-icon>mdi-github</v-icon>
      </v-btn>
    </div>

    <!--<v-alert type="info" class="mt-8" variant="tonal">
      Edit this page in <code>frontend/src/pages/AboutPage.vue</code> to add more personal info,
      links, or a short bio.
    </v-alert>-->
  </v-container>
</template>

<script setup lang="ts">
const links = {
  linkedin: 'https://www.linkedin.com/in/albert-anguera-sempere/',
  github: 'https://github.com/anguera5'
}
</script>

<style scoped>
h1, p, h2 { color: #e2e8f0; }
code { background: rgba(255,255,255,0.04); padding: 2px 6px; border-radius: 6px; }
</style>