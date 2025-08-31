<template>
  <div class="about">
    <!-- Hero -->
    <section class="hero header-intro">
      <v-container class="hero-inner">
        <v-row align="center" class="ga-4">
          <v-col cols="12">
            <PageTitle>
              <div class="d-flex flex-column flex-md-row align-center ga-6">
                <div class="d-flex justify-center">
                  <div class="avatar-wrap">
                    <div class="ring" />
                    <v-img src="/src/assets/avatar.png" alt="Albert Anguera" width="200" height="200" cover class="avatar" position="50% 10%"/>
                  </div>
                </div>
                <div class="flex-1">
                  <div class="eyebrow">About</div>
                  <h1 class="headline">Albert Anguera Sempere</h1>
                  <div class="role mt-1">Data Scientist · Food Packaging Forum</div>
                  <div class="chips d-flex ga-2 mt-3 flex-wrap">
                    <v-chip size="small" color="primary" variant="tonal">Physics</v-chip>
                    <v-chip size="small" color="secondary" variant="tonal">Chemistry</v-chip>
                    <v-chip size="small" color="primary" variant="tonal">Informatics</v-chip>
                    <v-chip size="small" color="secondary" variant="tonal">ML & RAG</v-chip>
                    <v-chip size="small" color="primary" variant="tonal">Data Platforms</v-chip>
                  </div>
                  <div class="mt-4 op-85">
                    I’m building this GenAI portfolio as part of Codecademy’s AI Bootcamp — a hands-on space to explore
                    practical patterns like retrieval, code generation, and intelligent data interfaces.
                  </div>
                  <div class="links d-flex ga-2 mt-4">
                    <v-btn :href="links.linkedin" target="_blank" rel="noopener" prepend-icon="mdi-linkedin" variant="tonal">LinkedIn</v-btn>
                    <v-btn :href="links.github" target="_blank" rel="noopener" prepend-icon="mdi-github" variant="tonal">GitHub</v-btn>
                  </div>
                </div>
              </div>
            </PageTitle>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- Sections -->
  <section class="sections mt-4">
      <v-container>
        <v-row>
          <!-- Who I am -->
          <v-col cols="12" md="6">
            <v-card class="glass hover-raise h-100">
              <v-card-item>
                <div class="d-flex align-center ga-2 mb-2">
                  <v-icon color="primary" icon="mdi-account-badge-outline" />
                  <div class="text-subtitle-1 font-weight-600">Who I am</div>
                </div>
                <div class="op-85">
                  I work at the Food Packaging Forum where I focus on turning messy, real-world data into reliable
                  insights and systems. My day-to-day spans data engineering, analytics, and applied AI.
                </div>
              </v-card-item>
            </v-card>
          </v-col>

          <!-- Why this portfolio -->
          <v-col cols="12" md="6">
            <v-card class="glass hover-raise h-100">
              <v-card-item>
                <div class="d-flex align-center ga-2 mb-2">
                  <v-icon color="secondary" icon="mdi-rocket-launch-outline" />
                  <div class="text-subtitle-1 font-weight-600">Why this portfolio</div>
                </div>
                <div class="op-85">
                  This portfolio is a living lab created during Codecademy’s AI Bootcamp. It showcases opinionated
                  implementations of GenAI capabilities — from LLM-assisted coding to RAG question answering — with a
                  focus on clarity and real-world usefulness.
                </div>
              </v-card-item>
            </v-card>
          </v-col>

          <!-- Background -->
          <v-col cols="12" md="6">
            <v-card class="glass hover-raise h-100">
              <v-card-item>
                <div class="d-flex align-center ga-2 mb-2">
                  <v-icon color="primary" icon="mdi-school-outline" />
                  <div class="text-subtitle-1 font-weight-600">Background</div>
                </div>
                <div class="op-85">
                  I bring together physics, chemistry, and computer science: BSc in Physics and BSc in Chemistry from
                  Universitat Autònoma de Barcelona, plus a Master in Informatics from the University of Zurich.
                </div>
              </v-card-item>
            </v-card>
          </v-col>

          <!-- Selected work -->
          <v-col cols="12" md="6">
            <v-card class="glass hover-raise h-100">
              <v-card-item>
                <div class="d-flex align-center ga-2 mb-2">
                  <v-icon color="secondary" icon="mdi-briefcase-outline" />
                  <div class="text-subtitle-1 font-weight-600">Selected work</div>
                </div>
                <ul class="list op-85">
                  <li>Built ML models to forecast bioreactor cell growth, inform harvest timing, and predict half-lives.</li>
                  <li>Developed and maintained <strong>enviPath</strong>, a biodegradation database and prediction system for chemicals.</li>
                  <li>Data infrastructure and dashboards: from pipelines to polished visualizations.</li>
                </ul>
              </v-card-item>
            </v-card>
          </v-col>

          <!-- What I do at FPF -->
          <v-col cols="12" md="6">
            <v-card class="glass hover-raise h-100">
              <v-card-item>
                <div class="d-flex align-center ga-2 mb-2">
                  <v-icon color="primary" icon="mdi-database-cog-outline" />
                  <div class="text-subtitle-1 font-weight-600">What I do at FPF</div>
                </div>
                <ul class="list op-85">
                  <li>Process, clean, and structure data for analysis and research.</li>
                  <li>Design and maintain datasets, databases, and supporting infrastructure.</li>
                  <li>Maintain existing dashboards and build new ones to answer evolving questions.</li>
                </ul>
              </v-card-item>
            </v-card>
          </v-col>

          <!-- Purpose -->
          <v-col cols="12" md="6">
            <v-card class="glass hover-raise h-100">
              <v-card-item>
                <div class="d-flex align-center ga-2 mb-2">
                  <v-icon color="secondary" icon="mdi-heart-pulse" />
                  <div class="text-subtitle-1 font-weight-600">Purpose</div>
                </div>
                <div class="op-85">
                  I care about how materials interact with people and the environment. My goal is to help clarify how
                  chemicals in food packaging relate to health, support safer regulations, and make sure people have
                  access to choices that align with long-term well-being.
                </div>
              </v-card-item>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>
  </div>
</template>

<script setup lang="ts">
import PageTitle from '../../components/PageTitle.vue'

const links = {
  linkedin: 'https://www.linkedin.com/in/albert-anguera-sempere/',
  github: 'https://github.com/anguera5'
}
</script>

<style scoped>
.about { position: relative; }
.op-85 { opacity: 0.85; }
.glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(8px) saturate(160%); border: 1px solid rgba(148,163,184,0.18); }
.hover-raise { transition: transform .2s ease, box-shadow .2s ease; }
.hover-raise:hover { transform: translateY(-2px); box-shadow: 0 10px 26px -10px rgba(0,0,0,.45); }

/* Header */
.hero.header-intro { position: relative; padding: 80px 0 32px; }
.hero-inner { position: relative; z-index: 1; max-width: 1080px; margin: 0 auto; }
.eyebrow { letter-spacing: 1px; font-size: 0.8rem; text-transform: uppercase; opacity: 0.7; margin-bottom: 6px; }
.headline { font-size: clamp(1.8rem, 5vw, 2.6rem); font-weight: 800; line-height: 1.05; }
.role { opacity: 0.85; margin-top: 2px; }
.avatar-wrap { position: relative; width: 220px; height: 220px; display: grid; place-items: center; }
.avatar { border-radius: 50%; box-shadow: 0 8px 24px rgba(0,0,0,.35); }
.ring { position: absolute; width: 210px; height: 210px; border-radius: 50%; background: conic-gradient(from 0deg, #9a5fff, #38d6ee, #9a5fff); filter: blur(10px); opacity: .55; animation: spin 12s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }

/* per-page hero visuals removed in favor of global background */

/* Sections */
.sections { padding: 16px 0 40px; }
.list { padding-left: 18px; }
.list li { margin-bottom: 6px; }
</style>