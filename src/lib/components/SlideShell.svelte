<script lang="ts">
	import { reveal } from '$lib/useReveal.svelte.ts';
	import type { Snippet } from 'svelte';

	const {
		tone = 'dark',
		children,
		onreveal
	}: {
		tone?: 'dark' | 'hot';
		children: Snippet;
		onreveal?: () => void;
	} = $props();
</script>

<section class="slide tone-{tone}">
	<div class="grid-bg" aria-hidden="true"></div>
	<div class="content" use:reveal={{ onReveal: onreveal }}>
		{@render children()}
	</div>
</section>

<style>
	.slide {
		position: relative;
		min-height: 100dvh;
		scroll-snap-align: start;
		scroll-snap-stop: always;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.tone-hot {
		background: var(--bg-3);
	}

	.grid-bg {
		position: absolute;
		inset: 0;
		pointer-events: none;
		background-image:
			linear-gradient(rgba(0, 234, 189, 0.04) 1px, transparent 1px),
			linear-gradient(90deg, rgba(0, 234, 189, 0.04) 1px, transparent 1px),
			radial-gradient(ellipse 80% 50% at 50% 0%, rgba(0, 234, 189, 0.07) 0%, transparent 60%);
		background-size: 44px 44px, 44px 44px, 100% 100%;
		-webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 30%, black 30%, transparent 80%);
		mask-image: radial-gradient(ellipse 100% 100% at 50% 30%, black 30%, transparent 80%);
	}

	.content {
		position: relative;
		z-index: 1;
		width: 100%;
		max-width: 900px;
		padding: 48px var(--slide-pad);
		opacity: 0;
		transform: translateY(20px);
		transition: opacity 0.55s ease, transform 0.55s ease;
	}

	:global(.content[data-revealed='true']) {
		opacity: 1;
		transform: none;
	}
</style>
