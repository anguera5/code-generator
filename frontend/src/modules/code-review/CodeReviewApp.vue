<template>
  <v-container class="py-0 animate-in" fluid>
    <!-- Hero (standalone, not a card) -->
    <section class="cg-hero">
      <div class="hero-bg">
        <div class="blob b1" />
        <div class="blob b2" />
        <div class="grid-overlay" />
      </div>
      <div class="cg-hero-inner">
        <div class="d-flex flex-column flex-md-row align-center justify-space-between ga-4">
          <div class="flex-1">
            <div class="eyebrow">Reviews</div>
            <h1 class="headline">Code Review (LLM) <span class="shimmer" /></h1>
            <p class="op-80 mt-1">
              Automate pull request reviews via a simple webhook. The backend uses OpenAI’s
              <strong>gpt-4.1-mini</strong> to generate clear, structured feedback.
            </p>
          </div>
          <div class="toolbar d-flex ga-3 align-center flex-wrap">
            <v-chip color="secondary" variant="tonal" class="pill">Webhook-based</v-chip>
            <v-chip color="primary" variant="tonal" class="pill">Powered by OpenAI</v-chip>
          </div>
        </div>
      </div>
    </section>

    <div class="py-6"></div>

    <v-alert type="info" variant="tonal" class="mb-6">
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
const baseUrl = window.location.origin
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
.code-block { white-space: pre-wrap; font-size: 0.75rem; line-height: 1.15rem; }
ol.small, ul.small { font-size: 0.85rem; }
code { background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 6px; }
pre { background: rgba(255,255,255,0.04); padding: 12px; border-radius: 10px; }
</style>
