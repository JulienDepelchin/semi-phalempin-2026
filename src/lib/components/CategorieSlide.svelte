<script lang="ts">
	import SlideShell from './SlideShell.svelte';
	import { Counter } from '$lib/useReveal.svelte.ts';
	import { getCategory, fasterThanPct, fmtThousands } from '$lib/data.ts';
	import type { Runner, RaceStats } from '$lib/data.ts';

	const {
		runner,
		stats
	}: {
		runner: Runner;
		stats: RaceStats;
	} = $props();

	const cat = $derived(getCategory(runner.annee, runner.genre));

	// Display code with gender prefix: SE→HSE, M1→HM1, F0→FM0, FSE→FSE
	const displayCatCode = $derived.by(() => {
		if (!cat.startsWith('F')) return 'H' + cat;
		const rest = cat.slice(1);
		return /^\d+$/.test(rest) ? 'FM' + rest : cat;
	});

	const catRunners = $derived(
		stats.runners
			.filter((r) => getCategory(r.annee, r.genre) === cat)
			.sort((a, b) => a.temps_sec - b.temps_sec)
	);

	const catPos = $derived(catRunners.findIndex((r) => r.dossard === runner.dossard) + 1);
	const catTotal = $derived(catRunners.length);
	const catPct = $derived(fasterThanPct(catPos, catTotal));

	const genderRunners = $derived(
		stats.runners
			.filter((r) => r.genre === runner.genre)
			.sort((a, b) => a.temps_sec - b.temps_sec)
	);
	const genderPos = $derived(genderRunners.findIndex((r) => r.dossard === runner.dossard) + 1);
	const genderTotal = $derived(genderRunners.length);

	const catCounter = new Counter();
	const genderCounter = new Counter();

	function start() {
		catCounter.run(catPos, 1);
		genderCounter.run(genderPos, 1);
	}
</script>

<SlideShell onreveal={start}>
	<div class="cat-slide">
		<p class="eyebrow">Catégorie</p>

		<h2 class="place-big">
			<span class="hash">#</span>{fmtThousands(catCounter.value)}
		</h2>
		<p class="cat-label"><span class="cat-code">{displayCatCode}</span></p>
		<p class="cat-sub">sur {fmtThousands(catTotal)} · {catPct} % derrière vous</p>

		<div class="divider"></div>

		<div class="rank-block">
			<span class="rank-num">#{fmtThousands(genderCounter.value)}</span>
			<span class="rank-lbl">
				sur {fmtThousands(genderTotal)} {runner.genre === 'M' ? 'hommes' : 'femmes'}
			</span>
		</div>
	</div>
</SlideShell>

<style>
	.cat-slide { display: flex; flex-direction: column; gap: 10px; }

	.eyebrow {
		font-size: 0.85rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--hot);
		font-weight: 600;
		margin-bottom: 4px;
	}

	.place-big {
		font-family: var(--font-display);
		font-size: clamp(80px, 22vw, 200px);
		font-weight: 800;
		line-height: 0.9;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.hash { color: var(--ink-3); margin-right: 0.05em; }

	.cat-label {
		font-family: var(--font-display);
		font-size: clamp(20px, 4vw, 32px);
		font-weight: 700;
		color: var(--ink-2);
	}

	.cat-code { color: var(--hot); }

	.cat-sub { font-size: 0.9rem; color: var(--ink-3); }

	.divider { height: 1px; background: var(--line); margin: 16px 0 12px; max-width: 400px; }

	.rank-block { display: flex; flex-direction: column; gap: 4px; }

	.rank-num {
		font-family: var(--font-display);
		font-size: clamp(36px, 8vw, 64px);
		font-weight: 800;
		color: var(--hot);
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	.rank-lbl { font-size: 0.9rem; color: var(--ink-2); }
</style>
