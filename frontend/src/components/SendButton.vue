<template>
  <v-btn
    :type="type"
    :disabled="disabled"
    :loading="loading"
    class="send-cta"
    height="44"
    rounded="pill"
    variant="flat"
    color="primary"
  >
  <span class="ring" aria-hidden="true" />
    <span class="inner">
      <svg class="icon" viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden>
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2 .01 7z" />
      </svg>
      <span class="label"><slot>Send</slot></span>
    </span>
  </v-btn>
</template>

<script setup lang="ts">
defineProps<{ disabled?: boolean; loading?: boolean; type?: 'button'|'submit'|'reset' }>()
</script>

<style scoped>
.send-cta {
  position: relative;
  padding: 0 18px;
  font-weight: 700;
  letter-spacing: .2px;
  background: linear-gradient(135deg, #7a5cff, #3fd3ec);
  box-shadow: 0 8px 24px -8px rgba(122,92,255,.6), 0 2px 10px -6px rgba(63,211,236,.7);
}
.send-cta .inner { display: inline-flex; align-items: center; gap: 8px; position: relative; z-index: 1; }
.send-cta .icon { filter: drop-shadow(0 1px 0 rgba(255,255,255,.25)); }
.send-cta .label { text-transform: none; }
.send-cta .ring {
  position: absolute; inset: -2px; border-radius: 999px; pointer-events: none;
  background: radial-gradient(60% 140% at 50% 50%, rgba(122,92,255,.9), rgba(63,211,236,.7) 60%, rgba(63,211,236,0) 72%),
              radial-gradient(40% 90% at 20% 30%, rgba(255,255,255,.5), transparent 60%);
  filter: blur(12px) saturate(140%);
  opacity: .55; transition: opacity .2s ease, transform .2s ease;
}
.send-cta:hover .ring { opacity: .85; transform: scale(1.03); }
.send-cta:disabled { background: rgba(255,255,255,.08) !important; color: rgba(255,255,255,.45) !important; box-shadow: none; }
.send-cta:disabled .ring { opacity: 0; }
@media (prefers-reduced-motion: no-preference) {
  .send-cta .ring { animation: breathe 2.8s ease-in-out infinite; }
}
@keyframes breathe { 0%{ opacity:.5; transform: scale(1) } 50%{ opacity:.85; transform: scale(1.06) } 100%{ opacity:.5; transform: scale(1) } }
</style>
