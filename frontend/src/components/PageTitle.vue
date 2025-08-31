<template>
  <div class="title-wrap" :style="wrapStyle">
    <GlowAura />
    <div class="title-block" :class="variantClass">
      <div class="inner">
        <slot />
      </div>
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed } from 'vue'
import GlowAura from './GlowAura.vue'

const props = defineProps<{ variant?: 'primary' | 'secondary'; maxWidth?: number | string; fullBleed?: boolean }>()
const variantClass = computed(() => (props.variant === 'secondary' ? 'secondary' : 'primary'))
const wrapStyle = computed(() => {
  const mw = props.fullBleed ? undefined : (typeof props.maxWidth === 'number' ? `${props.maxWidth}px` : (props.maxWidth || '1200px'))
  const style: Record<string, string | undefined> = { maxWidth: mw, width: '100%', margin: '0 auto' }
  if (mw) style['--title-max-width'] = mw
  return style
})
</script>

<style scoped>
/* Glow handled by GlowAura; this block focuses on the title styling and a soft border ring */
.title-wrap { --title-max-width: 1200px; }
.title-wrap {
  position: relative;
  border-radius: 18px;
  width: 100%;
  margin: 0 auto;
}

.title-block {
  --brand-purple: #9a5fff;
  --brand-teal: #38d6ee;
  position: relative;
  display: block;
  width: min(100%, var(--title-max-width));
  padding: 64px 28px; /* larger, more heroic */
  border-radius: 18px;
  /* Neutral glass background for content readability over the glow */
  background: linear-gradient(180deg, rgba(16,18,34,0.55), rgba(16,18,34,0.35));
  border: 2px solid transparent; /* gradient border handled by ::before */
  outline: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(10px) saturate(160%);
  box-shadow: 0 18px 36px -20px rgba(0,0,0,.6), inset 0 1px 0 rgba(255,255,255,0.05);
  margin: 0 auto 32px; /* separation from the app section */
  overflow: hidden;
}

.title-block::before {
  content: none; /* center-diffused light handled by GlowAura */
}


.inner {
  position: relative;
  z-index: 1;
  margin: 0;
  padding: 0;
}

.inner :deep(h1),
.inner :deep(h2),
.inner :deep(h3) {
  margin: 0 0 4px 0;
}

/* Remove the old horizontal white shimmer on titles inside the block */
.inner :deep(.shimmer) { display: none; }

.title-block.secondary {
  background: linear-gradient(180deg, rgba(56,214,238,0.15), rgba(154,95,255,0.06));
}

@media (prefers-reduced-motion: reduce) {
  .title-block::before { animation: none; opacity: .35; }
}
</style>
