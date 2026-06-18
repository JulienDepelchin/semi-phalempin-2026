<script lang="ts">
	import SlideShell from './SlideShell.svelte';
	import { Counter } from '$lib/useReveal.svelte.ts';
	import { fmtTime, fasterThanPct, formatName } from '$lib/data.ts';
	import type { Runner, RaceStats } from '$lib/data.ts';

	const {
		runner,
		stats,
		race
	}: {
		runner: Runner;
		stats: RaceStats;
		race: string;
	} = $props();

	const pct = $derived(fasterThanPct(runner.pos, stats.global.n));
	const phrase = $derived(
		pct >= 99 ? "Vous faites partie de l'élite." :
		pct >= 90 ? 'Une performance remarquable.' :
		pct >= 75 ? 'Largement au-dessus de la moyenne.' :
		pct >= 50 ? 'Dans la première moitié du peloton.' :
		pct >= 25 ? 'Dans la seconde moitié, mais finisher !' :
		'Chaque finisher est un vainqueur.'
	);

	const timeCounter = new Counter();
	const displayTime = $derived(fmtTime(Math.round(timeCounter.value)));
	let titleVisible = $state(false);

	function start() {
		titleVisible = true;
		timeCounter.run(runner.temps_sec, 0);
	}
</script>

<SlideShell onreveal={start}>
	<div class="temps-slide">
		<p class="eyebrow">{race}</p>
		<p class="runner-name" class:visible={titleVisible}>{formatName(runner.nom)}</p>
		<div class="time-display">
			<span class="time-value">{displayTime}</span>
		</div>
		<p class="phrase">{phrase}</p>
		<div class="sub-stats">
			<div class="stat-chip">
				<span class="chip-val">{pct} %</span>
				<span class="chip-lbl">des coureurs derrière vous</span>
			</div>
			<div class="stat-chip">
				<span class="chip-val">#{runner.pos}</span>
				<span class="chip-lbl">au classement général</span>
			</div>
		</div>
	</div>
</SlideShell>

<style>
	.temps-slide {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.eyebrow {
		font-size: 0.85rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--hot);
		font-weight: 600;
	}

	.runner-name {
		font-family: var(--font-display);
		font-size: clamp(22px, 5vw, 40px);
		font-weight: 800;
		font-style: italic;
		color: var(--ink-2);
		opacity: 0;
		transform: translateY(8px);
		transition: opacity 0.4s ease, transform 0.4s ease;
	}

	.runner-name.visible {
		opacity: 1;
		transform: none;
	}

	.time-value {
		display: block;
		font-family: var(--font-display);
		font-size: clamp(72px, 22vw, 200px);
		font-weight: 800;
		font-style: italic;
		line-height: 1;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.phrase {
		font-size: clamp(1rem, 2.5vw, 1.35rem);
		color: var(--ink-2);
		max-width: 480px;
		line-height: 1.5;
	}

	.sub-stats {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
	}

	.stat-chip {
		display: flex;
		flex-direction: column;
		gap: 2px;
		background: var(--bg-2);
		border: 1px solid var(--line-2);
		border-radius: 10px;
		padding: 12px 18px;
	}

	.chip-val {
		font-family: var(--font-display);
		font-size: 1.8rem;
		font-weight: 800;
		color: var(--hot);
		line-height: 1;
	}

	.chip-lbl { font-size: 0.78rem; color: var(--ink-3); }
</style>
