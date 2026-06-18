<script lang="ts">
	import SlideShell from './SlideShell.svelte';
	import { Counter } from '$lib/useReveal.svelte.ts';
	import { fasterThanPct, fmtThousands, genderRank } from '$lib/data.ts';
	import type { Runner, RaceStats } from '$lib/data.ts';

	const {
		runner,
		stats
	}: {
		runner: Runner;
		stats: RaceStats;
	} = $props();

	const pct = $derived(fasterThanPct(runner.pos, stats.global.n));
	const gPos = $derived(genderRank(stats.genderRankCurve[runner.genre], runner.temps_sec));
	const gTotal = $derived(stats.genderRankCurve[runner.genre].size);
	const gPct = $derived(fasterThanPct(gPos, gTotal));

	const counter = new Counter();
	const pctCounter = new Counter();

	function start() {
		counter.run(runner.pos, 1);
		pctCounter.run(pct, 0);
	}
</script>

<SlideShell onreveal={start}>
	<div class="rang-slide">
		<p class="label">Classement général</p>
		<h2 class="rank-big">
			<span class="hash">#</span>{fmtThousands(counter.value)}
		</h2>
		<p class="sub">sur {fmtThousands(stats.global.n)} coureurs</p>

		<div class="pct-bar-wrap">
			<div class="pct-bar">
				<div class="pct-fill" style="width: {Math.round(pctCounter.value)}%"></div>
			</div>
			<p class="pct-label">
				Mieux que <strong>{Math.round(pctCounter.value)} %</strong> des coureurs
			</p>
		</div>

		<div class="gender-rank">
			<div class="gr-item">
				<span class="gr-val">#{fmtThousands(gPos)} / {fmtThousands(gTotal)}</span>
				<span class="gr-lbl">parmi les {runner.genre === 'M' ? 'hommes' : 'femmes'} · {gPct} % derrière vous</span>
			</div>
		</div>
	</div>
</SlideShell>

<style>
	.rang-slide { display: flex; flex-direction: column; gap: 20px; }

	.label {
		font-size: 0.85rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--hot);
		font-weight: 600;
	}

	.rank-big {
		font-family: var(--font-display);
		font-size: clamp(80px, 22vw, 220px);
		font-weight: 800;
		line-height: 0.9;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.hash { color: var(--ink-3); margin-right: 0.05em; }

	.sub { color: var(--ink-3); font-size: clamp(1rem, 2vw, 1.25rem); }

	.pct-bar-wrap { display: flex; flex-direction: column; gap: 10px; max-width: 480px; }

	.pct-bar {
		height: 8px;
		border-radius: 100px;
		background: var(--line-2);
		overflow: hidden;
	}

	.pct-fill {
		height: 100%;
		background: var(--hot);
		border-radius: 100px;
		transition: width 1.6s cubic-bezier(0.16, 1, 0.3, 1);
	}

	.pct-label { font-size: 1rem; color: var(--ink-2); }
	.pct-label strong { color: var(--hot); }

	.gender-rank { display: flex; gap: 16px; }
	.gr-item { display: flex; flex-direction: column; gap: 2px; }
	.gr-val { font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; color: var(--ink); }
	.gr-lbl { font-size: 0.8rem; color: var(--ink-3); }
</style>
