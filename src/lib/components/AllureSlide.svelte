<script lang="ts">
	import SlideShell from './SlideShell.svelte';
	import { Counter } from '$lib/useReveal.svelte.ts';
	import { fmtTime, fmtPace, marathonEquiv } from '$lib/data.ts';
	import type { Runner, RaceStats } from '$lib/data.ts';

	const {
		runner,
		stats,
		distKm
	}: {
		runner: Runner;
		stats: RaceStats;
		distKm: number;
	} = $props();

	const paceSec = $derived(runner.temps_sec / distKm);
	const marathon = $derived(fmtTime(marathonEquiv(runner.temps_sec, distKm)));

	const medianSec = $derived(stats.global.medianTime);
	const diffSec = $derived(runner.temps_sec - medianSec);
	const diffSign = $derived(diffSec < 0 ? '−' : '+');
	const diffAbs = $derived(fmtTime(Math.abs(diffSec)));

	const genderMedianSec = $derived(
		runner.genre === 'M' ? stats.byGender.M.medianTime : stats.byGender.F.medianTime
	);
	const gDiffSec = $derived(runner.temps_sec - genderMedianSec);
	const gDiffSign = $derived(gDiffSec < 0 ? '−' : '+');
	const gDiffAbs = $derived(fmtTime(Math.abs(gDiffSec)));

	const paceCounter = new Counter();

	const displayPace = $derived.by(() => {
		const s = Math.round(paceCounter.value);
		const m = Math.floor(s / 60);
		const sec = s % 60;
		return `${m}'${String(sec).padStart(2, '0')}"`;
	});

	function start() {
		paceCounter.run(paceSec, 0);
	}
</script>

<SlideShell onreveal={start}>
	<div class="allure-slide">
		<p class="eyebrow">Allure & comparaison</p>

		<div class="pace-hero">
			<span class="pace-val">{displayPace}</span>
			<span class="pace-unit">/km 🚀</span>
		</div>

		<div class="cards">
			<div class="card">
				<span class="card-val">{marathon}</span>
				<span class="card-lbl">Équivalent marathon</span>
			</div>

			<div class="card delta" class:ahead={diffSec < 0}>
				<span class="card-val">{diffSign}{diffAbs}</span>
				<span class="card-lbl">vs médiane générale ({fmtTime(medianSec)})</span>
			</div>

			<div class="card delta" class:ahead={gDiffSec < 0}>
				<span class="card-val">{gDiffSign}{gDiffAbs}</span>
				<span class="card-lbl">
					vs médiane {runner.genre === 'M' ? 'hommes' : 'femmes'}
					({fmtTime(genderMedianSec)})
				</span>
			</div>
		</div>
	</div>
</SlideShell>

<style>
	.allure-slide { display: flex; flex-direction: column; gap: 24px; }

	.eyebrow {
		font-size: 0.85rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--hot);
		font-weight: 600;
	}

	.pace-hero {
		display: flex;
		align-items: baseline;
		gap: 10px;
	}

	.pace-val {
		font-family: var(--font-display);
		font-size: clamp(64px, 18vw, 160px);
		font-weight: 800;
		font-style: italic;
		line-height: 0.9;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.pace-unit {
		font-size: clamp(20px, 4vw, 36px);
		color: var(--ink-3);
		font-weight: 600;
	}

	.cards { display: flex; gap: 12px; flex-wrap: wrap; }

	.card {
		display: flex;
		flex-direction: column;
		gap: 4px;
		background: var(--bg-2);
		border: 1px solid var(--line-2);
		border-radius: 12px;
		padding: 14px 20px;
		min-width: 140px;
	}

	.card-val {
		font-family: var(--font-display);
		font-size: clamp(22px, 4vw, 36px);
		font-weight: 800;
		color: var(--ink);
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	.card.delta .card-val { color: var(--ink-3); }
	.card.delta.ahead .card-val { color: var(--hot); }

	.card-lbl { font-size: 0.78rem; color: var(--ink-4); }
</style>
