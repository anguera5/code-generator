<template>
  <div class="glow" :style="glowStyle" aria-hidden="true"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ inset?: number; intensity?: number; speed?: number }>()

const glowStyle = computed(() => ({
  '--spread': `${props.inset ?? 64}px`,        // how far the light spills outside
  '--intensity': String(props.intensity ?? 1.25), // scales opacity/brightness
  '--speed': String(props.speed ?? 1),         // 1 = default speed
}))
</script>

<style scoped>
/* Custom properties for animating the light center and tint */
@property --cx { syntax: '<percentage>'; initial-value: 50%; inherits: false; }
@property --cy { syntax: '<percentage>'; initial-value: 50%; inherits: false; }
@property --rot { syntax: '<angle>'; initial-value: 0deg; inherits: false; }

.glow {
  /* The parent should be position:relative and set a border-radius; we inherit it */
  position: absolute;
  inset: calc(var(--spread, 56px) * -1); /* extend outside so the light spills beyond borders */
  border-radius: inherit;
  pointer-events: none;
  z-index: 0;
  /* Centered, diffusing light with a subtle rotating tint */
  background:
    /* Bright central core (bulb) */
    radial-gradient(46% 36% at var(--cx) var(--cy), rgba(255,255,255,0.66), rgba(154,95,255,0.46) 32%, rgba(56,214,238,0.32) 60%, transparent 86%),
    /* Wide main diffusion */
    radial-gradient(160% 140% at var(--cx) var(--cy), rgba(255,255,255,0.22), rgba(154,95,255,0.26) 18%, rgba(56,214,238,0.20) 46%, rgba(154,95,255,0.12) 68%, transparent 88%),
    /* Irregular lobes to avoid symmetry */
    radial-gradient(95% 70% at 88% 28%, rgba(154,95,255,0.22), transparent 60%),
    radial-gradient(90% 68% at 18% 40%, rgba(56,214,238,0.20), transparent 62%),
    radial-gradient(90% 70% at 40% 90%, rgba(154,95,255,0.18), transparent 64%),
    /* Rotating tint to add life */
    conic-gradient(from var(--rot), rgba(154,95,255,0.14), rgba(56,214,238,0.10), rgba(154,95,255,0.14));
  filter: blur(72px) saturate(165%) brightness(calc(1.12 * var(--intensity, 1)));
  opacity: calc(0.60 * var(--intensity, 1));
  animation:
    rot calc(40s / var(--speed, 1)) linear infinite,
    drift calc(16s / var(--speed, 1)) ease-in-out infinite alternate,
    breathe calc(8s / var(--speed, 1)) ease-in-out infinite;
}

/* Ultra-subtle grain/dither to avoid banding and add elegance */
.glow::after {
  content: "";
  position: absolute; inset: -40px;
  border-radius: inherit;
  pointer-events: none;
  background-image:
    radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1.4px),
    radial-gradient(rgba(0,0,0,0.05) 1px, transparent 1.6px);
  background-size: 3px 3px, 4px 4px;
  background-position: 0 0, 1px 2px;
  mix-blend-mode: soft-light;
  opacity: .06;
  filter: blur(.4px) saturate(120%);
  animation: grainShift calc(14s / var(--speed, 1)) linear infinite alternate;
}

@keyframes rot { to { --rot: 360deg; } }
@keyframes drift {
  0% { --cx: 49%; --cy: 51%; }
  50% { --cx: 52%; --cy: 49%; }
  100% { --cx: 48%; --cy: 50%; }
}
@keyframes breathe {
  0% { opacity: .34; filter: blur(38px) saturate(140%) brightness(1.03); }
  50% { opacity: .50; filter: blur(46px) saturate(165%) brightness(1.10); }
  100% { opacity: .34; filter: blur(38px) saturate(140%) brightness(1.03); }
}

@keyframes grainShift {
  0% { transform: translate3d(0,0,0) rotate(0deg); }
  50% { transform: translate3d(1px,-1px,0) rotate(0.5deg); }
  100% { transform: translate3d(-1px,1px,0) rotate(-0.5deg); }
}

@media (prefers-reduced-motion: reduce) {
  .glow { animation: none; }
}
</style>
