<template>
	<div class="global-bg" aria-hidden="true">
		<div class="layer base" />
		<div class="layer swirl" />
		<div class="blob purple" />
		<div class="blob teal" />
		<div class="grid" />
	</div>
  
</template>

<script setup lang="ts">
// purely presentational
</script>

<style scoped>
.global-bg {
	position: fixed;
	inset: 0;
	z-index: 0;
	pointer-events: none;
	overflow: hidden;
}

/* Base subtle radial vignette */
.layer.base {
	position: absolute; inset: -10%;
	background:
		radial-gradient(1200px 800px at 50% 0%, rgba(154,95,255,0.12), transparent 50%),
		radial-gradient(1000px 800px at 50% 100%, rgba(56,214,238,0.10), transparent 55%),
		radial-gradient(1600px 1200px at 50% 50%, #0f1020, #0b0d16);
}

/* Slow conic swirl for depth */
.layer.swirl {
	position: absolute; inset: -30%; opacity: .08; mix-blend-mode: screen;
	background:
		conic-gradient(from 0deg at 50% 50%,
			rgba(154,95,255,0.8), rgba(56,214,238,0.8), rgba(154,95,255,0.8));
	filter: blur(60px);
	animation: swirl-rotate 60s linear infinite;
}
@keyframes swirl-rotate { to { transform: rotate(360deg) } }

/* Signature glowing blobs */
.blob { position: absolute; border-radius: 50%; filter: blur(40px); opacity: .35; mix-blend-mode: screen; }
.blob.purple { width: 680px; height: 680px; left: -140px; top: -140px; background: radial-gradient(circle at 40% 40%, rgba(154,95,255,.45), transparent 60%); animation: float-a 18s ease-in-out infinite; }
.blob.teal { width: 720px; height: 720px; right: -180px; bottom: -180px; background: radial-gradient(circle at 60% 60%, rgba(56,214,238,.42), transparent 60%); animation: float-b 22s ease-in-out infinite; }
@keyframes float-a { 0%,100%{ transform: translate(0,0)} 50%{ transform: translate(24px,18px)} }
@keyframes float-b { 0%,100%{ transform: translate(0,0)} 50%{ transform: translate(-28px,-20px)} }

/* Subtle grid for texture */
.grid { position:absolute; inset:0; opacity:.12; mask-image: radial-gradient(circle at 50% 10%, #000 40%, transparent 85%);
	background-image:
		linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
		linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
	background-size: 48px 48px, 48px 48px;
}
</style>
