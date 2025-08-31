<template>
  <v-container class="py-0 animate-in" fluid>
    <div class="section-intro">
      <PageTitle>
        <div>
          <div class="eyebrow">Code Review</div>
          <h1 class="headline">AI Pull Request Review <span class="shimmer" /></h1>
          <p class="op-80 mt-1">
            Paste a diff or a PR URL. The assistant will summarize, spot issues, and suggest improvements.
          </p>
        </div>
      </PageTitle>
    </div>

  <div class="py-6"></div>

  <v-alert type="info" variant="tonal" class="mb-6 mt-2">
      Configure a repository webhook that posts pull request events here for automated LLM review.
    </v-alert>

    <h2 class="text-h6 mb-2">1. Overview</h2>
    <p class="mb-4">
      Add a webhook on your repository: <code>{{ baseUrl }}/api/code-review/webhook</code> listening to
      <code>pull_request</code> events. The backend summarizes metadata (optionally diff) and generates a structured review.
    </p>

    <h2 class="text-h6 mb-2">2. GitHub Webhook Setup</h2>
    <ol class="mb-4 small">
      <li>Go to Repo &gt; Settings &gt; Webhooks &gt; <strong>Add webhook</strong>.</li>
      <li>Payload URL: <code>{{ baseUrl }}/api/code-review/webhook</code></li>
      <li>Content type: <code>application/json</code></li>
      <li>Secret: optional (add signature verification in backend before production).</li>
      <li>Events: choose <code>Let me select individual events</code> &gt; check <code>Pull requests</code>.</li>
      <li>Save webhook.</li>
    </ol>

    <h2 class="text-h6 mb-2">3. Sample Test (cURL)</h2>
    <v-card variant="outlined" class="mb-6">
      <v-card-text>
        <pre class="code-block">curl -X POST "{{ baseUrl }}/api/code-review/webhook" \
  -H "X-GitHub-Event: pull_request" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "pull_request": {
      "title": "Add authentication middleware",
      "body": "Implements JWT auth; refactors session handling.",
      "base": { "ref": "main" },
      "head": { "ref": "feature/auth-middleware" },
      "diff_url": "https://github.com/org/repo/pull/42.diff"
    },
    "repository": { "full_name": "org/repo" }
  }'</pre>
      </v-card-text>
    </v-card>

    <h2 class="text-h6 mb-2">4. Response</h2>
    <p class="mb-4">The API returns JSON: <code>{ "review": "...structured feedback..." }</code></p>

<!--    <h2 class="text-h6 mb-2">5. Recommendations</h2>
    <ul class="mb-6 small">
      <li>Add HMAC signature validation (e.g., <code>X-Hub-Signature-256</code>).</li>
      <li>Persist reviews (database) for audit history.</li>
      <li>Fetch &amp; chunk actual diffs and include truncated sections.</li>
      <li>Post inline comments back via provider API for deeper integration.</li>
    </ul>

    <v-alert type="warning" variant="tonal">
      This is an MVP; do not expose publicly without authentication and validation hardening.
    </v-alert>-->
  </v-container>
</template>

<script setup lang="ts">
import PageTitle from '../../components/PageTitle.vue'

const baseUrl = window.location.origin
</script>

<style scoped>
.section-intro { position: relative; padding: 48px 16px 8px; max-width: 1200px; margin: 0 auto; }
.headline { position: relative; font-weight: 800; font-size: clamp(1.8rem, 4.6vw, 2.6rem); line-height: 1.1; }
.headline .shimmer { position:absolute; inset:0; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.12), rgba(255,255,255,0)); transform: translateX(-100%); animation: shimmer 5s infinite; pointer-events: none; }
@keyframes shimmer { 0%{ transform: translateX(-100%) } 100%{ transform: translateX(100%) } }
.eyebrow { letter-spacing: 1px; font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; }
.op-80 { opacity: .8; }
.pill { font-weight: 600; }
.code-block { white-space: pre-wrap; font-size: 0.75rem; line-height: 1.15rem; }
ol.small, ul.small { font-size: 0.85rem; }
code { background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 6px; }
pre { background: rgba(255,255,255,0.04); padding: 12px; border-radius: 10px; }
</style>
