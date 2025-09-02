<template>
  <v-container class="py-0 animate-in" fluid>
    <!-- Intro block mirroring chembl style -->
    <div class="section-intro">
      <PageTitle>
        <div class="d-flex flex-column flex-md-row align-center justify-space-between ga-4">
          <div class="flex-1">
            <div class="eyebrow">Code Review</div>
            <h1 class="headline">AI PR Review via GitHub Webhook</h1>
            <p class="op-80 mt-1">
              Automate PR reviews with an LLM. Comments on your PRs will be posted by <strong>@anguera5</strong>.
              This workflow currently targets <strong>public repositories</strong>.
            </p>
            <!-- Mini flow strip -->
            <div class="flow-strip mt-4">
              <div class="step"><v-icon icon="mdi-source-pull" size="22" /><div class="label">PR opened</div></div>
              <div class="arrow"><v-icon icon="mdi-arrow-right" /></div>
              <div class="step"><v-icon icon="mdi-brain" size="22" /><div class="label">LLM review</div></div>
              <div class="arrow"><v-icon icon="mdi-arrow-right" /></div>
              <div class="step"><v-icon icon="mdi-comment-quote-outline" size="22" /><div class="label">Review posted</div></div>
            </div>
          </div>
          <div class="toolbar d-flex ga-3 align-center flex-wrap">
            <v-chip color="secondary" variant="tonal" class="pill">Public repos</v-chip>
          </div>
        </div>
      </PageTitle>
    </div>

    <div class="py-4"></div>

    <!-- CTA: moved directly under title block -->
    <div class="content-wrap">
      <v-row class="mt-2 cta-row" align="stretch">
        <v-col cols="12" md="6">
          <v-card class="cta-card h-100">
            <v-card-text class="d-flex align-center ga-3">
              <v-icon icon="mdi-rocket-launch-outline" size="26" />
              <div>
                <div class="cta-title">Ready to see it in action?</div>
                <div class="cta-sub">Open a Pull Request and watch the AI review appear from <strong>@anguera5</strong>.</div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="6">
          <v-card class="cta-card h-100">
            <v-card-text>
              <div class="d-flex align-center ga-3 mb-2">
                <v-icon icon="mdi-open-in-new" size="24" />
                <div class="cta-title">Or try it out directly with your Pull Request URL</div>
              </div>
              <div class="try-row">
                <v-text-field
                  v-model="prUrl"
                  label="https://github.com/owner/repo/pull/123"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  class="try-input"
                />
                <v-btn color="primary" class="try-btn" @click="submitPrUrl">
                  <v-icon icon="mdi-send" size="18" class="mr-1" />
                  Send
                </v-btn>
              </div>
              <div class="hint mt-2 op-80">We’ll verify it’s a PR URL and trigger the same review flow as the webhook.</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

  <!-- Feature strip aligned with cards -->
    <div class="content-wrap">
      <div class="feature-strip">
        <div class="feature">
          <v-icon icon="mdi-lightbulb-on-outline" color="primary" size="24" />
          <div class="t">LLM summary</div>
          <div class="s">High-signal, concise feedback</div>
        </div>
        <div class="feature">
          <v-icon icon="mdi-format-line-style" color="secondary" size="24" />
          <div class="t">Inline comments</div>
          <div class="s">On added lines when applicable</div>
        </div>
        <div class="feature">
          <v-icon icon="mdi-account-badge-outline" color="primary" size="24" />
          <div class="t">Identity</div>
          <div class="s">Comments by @anguera5</div>
        </div>
      </div>
    </div>

    <v-row class="mt-2" justify="center">
      <v-col cols="12">
        <div class="content-wrap">
          <v-row class="dense-cards" align="stretch">
            <v-col cols="12" md="4">
              <!-- Requirements Card -->
              <v-card class="pretty-card compact h-100">
                <div class="accent accent-1" />
                <v-card-title class="card-title">
                  <v-icon icon="mdi-check-decagram-outline" size="20" class="mr-2" />
                  <span>Requirements</span>
                </v-card-title>
                <v-card-text>
                  <ul class="checklist mb-0 small">
                    <li><v-icon icon="mdi-check-circle-outline" size="16" /> GitHub account.</li>
                    <li><v-icon icon="mdi-check-circle-outline" size="16" /> Public repository.</li>
                  </ul>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="12" md="4">
              <!-- Webhook Setup Card -->
              <v-card class="pretty-card compact h-100">
                <div class="accent accent-2" />
                <v-card-title class="card-title">
                  <v-icon icon="mdi-webhook" size="20" class="mr-2" />
                  <span>GitHub Webhook Setup</span>
                </v-card-title>
                <v-card-text>
                  <ul class="mini-list op-90 mb-0">
                    <li><span class="num-badge">1</span><div class="li-text">Repo → Settings → Webhooks → <strong>Add webhook</strong>.</div></li>
                    <li><span class="num-badge">2</span><div class="li-text">Payload URL: <code>{{ baseUrl }}/api/code-review/webhook</code></div></li>
                    <li><span class="num-badge">3</span><div class="li-text">Content type: <code>application/json</code></div></li>
                    <li><span class="num-badge">4</span><div class="li-text">Secret: <strong>leave it empty</strong>.</div></li>
                    <li><span class="num-badge">5</span><div class="li-text">Events: choose <em>Let me select individual events</em> → check <strong>Pull requests ONLY</strong>.</div></li>
                    <li><span class="num-badge">6</span><div class="li-text">Save webhook.</div></li>
                  </ul>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="12" md="4">
              <!-- What to expect Card -->
              <v-card class="pretty-card compact h-100">
                <div class="accent accent-3" />
                <v-card-title class="card-title">
                  <v-icon icon="mdi-eye-check-outline" size="20" class="mr-2" />
                  <span>What to expect</span>
                </v-card-title>
                <v-card-text>
                  <ul class="checklist mb-0 small">
                    <li><v-icon icon="mdi-check-circle-outline" size="16" /> Triggers on PR <code>opened</code> or <code>reopened</code>.</li>
                    <li><v-icon icon="mdi-check-circle-outline" size="16" /> Summary review plus inline comments on added lines when possible.</li>
                    <li><v-icon icon="mdi-account-circle-outline" size="16" /> Reviewer identity: <strong>@anguera5</strong>.</li>
                  </ul>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- CTA row moved above under title block -->
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import http from '../../lib/http'
import { useNotifyStore } from '../../stores/notify'
import PageTitle from '../../components/PageTitle.vue'

const prUrl = ref('')
const notify = useNotifyStore()

async function submitPrUrl() {
  const url = prUrl.value.trim()
  const re = /^https:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+(?:\/.*)?$/
  if (!re.test(url)) {
    notify.warning('Enter a valid GitHub PR URL like https://github.com/owner/repo/pull/123')
    return
  }
  try {
    const { data } = await http.post('/api/code-review/by-url', { url })
    notify.success('Review triggered: ' + (data?.review || 'queued'))
    prUrl.value = ''
  } catch (e) {
    // interceptor will show error; no-op
  }
}
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

/* Simple flow and feature strip styles to mirror chembl module */
.flow-strip { display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap; max-width: 1200px; margin: 0 auto; }
.flow-strip .step { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 10px; background: rgba(255,255,255,0.04); }
.flow-strip .label { font-size: 0.8rem; opacity: 0.9; }
.feature-strip { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px; max-width: 1200px; margin: 0 auto 16px; padding: 0 8px; }
.feature { display:flex; flex-direction:column; align-items:center; text-align:center; gap: 4px; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); }
.feature .t { font-weight: 700; font-size: 0.95rem; }
.feature .s { font-size: 0.8rem; opacity: .8; }
@media (max-width: 1024px) { .feature-strip { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 560px) { .feature-strip { grid-template-columns: 1fr; } }

/* Elegant cards */
.pretty-card { position: relative; overflow: hidden; border-radius: 14px; background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 6px 24px rgba(0,0,0,0.25); transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
.pretty-card:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,0,0,0.32); border-color: rgba(255,255,255,0.12); }
.pretty-card .accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.accent-1 { background: linear-gradient(90deg, #6dd5ed, #2193b0); }
.accent-2 { background: linear-gradient(90deg, #a18cd1, #fbc2eb); }
.accent-3 { background: linear-gradient(90deg, #f6d365, #fda085); }
.card-title { display: flex; align-items: center; gap: 8px; font-weight: 700; letter-spacing: 0.2px; }
.pill.step { text-transform: uppercase; font-weight: 700; letter-spacing: .6px; }

/* Lists */
.checklist { list-style: none; padding-left: 0; }
.checklist li { display: flex; align-items: center; gap: 8px; margin: 8px 0; padding: 6px 10px; border-radius: 10px; background: rgba(255,255,255,0.04); }
/* Numbered mini list (like how-it-works) */
.mini-list { list-style: none; padding-left: 0; font-size: 0.9rem; }
.mini-list li { margin: 10px 0; display:flex; align-items:flex-start; gap: 10px; }
.mini-list .li-text { flex: 1 1 auto; min-width: 0; }
.num-badge { flex: 0 0 auto; display:inline-flex; align-items:center; justify-content:center; width: 22px; height: 22px; border-radius: 50%; font-size: 0.78rem; font-weight: 800; color:#fff; background: rgba(154,95,255,0.38); border: 1px solid rgba(255,255,255,0.18); box-sizing: border-box; }

/* CTA */
.cta-card { border-radius: 14px; background: linear-gradient(90deg, rgba(98,0,234,0.2), rgba(3,169,244,0.2)); border: 1px solid rgba(255,255,255,0.12); box-shadow: 0 10px 30px rgba(0,0,0,0.32); }
.cta-title { font-weight: 800; font-size: 1rem; }
.cta-sub { opacity: 0.9; }

/* Layout wrap to match title width */
.content-wrap { max-width: 1200px; margin: 0 auto; padding: 0 8px; }
/* Extra spacing beneath the PR URL CTA row */
.cta-row { margin-bottom: 24px; }

/* Try PR URL row */
.try-row { display:flex; gap:10px; align-items:center; }
.try-input { flex: 1 1 auto; }
.try-btn { white-space: nowrap; }
</style>
