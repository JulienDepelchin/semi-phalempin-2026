<script lang="ts">
	import { onMount } from 'svelte';
	import { loadStats, type Runner, type Race, type RaceStats, type StatsJson } from '$lib/data.ts';
	import WrappedPips from '$lib/components/WrappedPips.svelte';
	import CoverSlide from '$lib/components/CoverSlide.svelte';
	import TempsSlide from '$lib/components/TempsSlide.svelte';
	import RangSlide from '$lib/components/RangSlide.svelte';
	import PelotanSlide from '$lib/components/PelotanSlide.svelte';
	import CategorieSlide from '$lib/components/CategorieSlide.svelte';
	import CourseDansLaCourseSlide from '$lib/components/CourseDansLaCourseSlide.svelte';
	import AllureSlide from '$lib/components/AllureSlide.svelte';
	import PartageSlide from '$lib/components/PartageSlide.svelte';

	const TOTAL_SLIDES = 8; // 0-7
	const DIST: Record<Race, number> = { '10km': 10, '6km': 6 };

	let stats = $state<StatsJson | null>(null);
	let runner = $state<Runner | null>(null);
	let race = $state<Race>('10km');
	let activeSlide = $state(0);
	let scrollEl = $state<HTMLElement | null>(null);

	const raceStats = $derived<RaceStats | null>(stats ? stats[race] : null);

	onMount(async () => {
		stats = await loadStats();

		const params = new URLSearchParams(window.location.search);
		const dossard = params.get('dossard');
		const epreuve = params.get('epreuve') as Race | null;
		if (dossard && epreuve && stats[epreuve]) {
			const found = stats[epreuve].runners.find((r) => r.dossard === dossard);
			if (found) {
				race = epreuve;
				runner = found;
				setTimeout(() => gotoSlide(1), 120);
			}
		}

	});

	$effect(() => {
		void runner; // re-run when runner changes so newly created slides are observed
		if (!scrollEl) return;
		const slides = scrollEl.querySelectorAll('[data-slide]');
		const observer = new IntersectionObserver(
			(entries) => {
				let best = -1, bestRatio = -1;
				for (const entry of entries) {
					if (entry.intersectionRatio > bestRatio) {
						bestRatio = entry.intersectionRatio;
						best = Number((entry.target as HTMLElement).dataset.slide);
					}
				}
				if (best >= 0) activeSlide = best;
			},
			{ threshold: [0, 0.1, 0.5, 0.9, 1] }
		);
		slides.forEach((el) => observer.observe(el));
		return () => observer.disconnect();
	});

	function gotoSlide(idx: number) {
		scrollEl?.querySelector(`[data-slide="${idx}"]`)?.scrollIntoView({ behavior: 'smooth' });
	}

	function handleSelect(r: Runner, selectedRace: Race) {
		runner = r;
		race = selectedRace;
		setTimeout(() => gotoSlide(1), 50);
	}

	function handleRestart() {
		runner = null;
		gotoSlide(0);
	}

	function tryStep(dir: 1 | -1) {
		const max = runner ? TOTAL_SLIDES - 1 : 0;
		gotoSlide(Math.max(0, Math.min(max, activeSlide + dir)));
	}

	function onKeydown(e: KeyboardEvent) {
		if ((e.target as HTMLElement).tagName === 'INPUT') return;
		if (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') {
			e.preventDefault(); tryStep(1);
		} else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
			e.preventDefault(); tryStep(-1);
		}
	}
</script>

<svelte:window onkeydown={onKeydown} />

<main class="scroll-root" bind:this={scrollEl}>
	<WrappedPips total={runner ? TOTAL_SLIDES : 1} active={activeSlide} />

	<!-- Slide 0: Cover -->
	<div data-slide="0" class="slide-wrapper">
		{#if stats}
			<CoverSlide
				runners10={stats['10km'].runners}
				runners6={stats['6km'].runners}
				onselect={handleSelect}
			/>
		{:else}
			<div class="loading">
				<div class="spinner"></div>
				<p>Chargement des résultats…</p>
			</div>
		{/if}
	</div>

	{#if runner && raceStats}
		{#key runner.dossard}
			<!-- Slide 1: Temps -->
			<div data-slide="1" class="slide-wrapper">
				<TempsSlide {runner} stats={raceStats} {race} />
			</div>

			<!-- Slide 2: Rang -->
			<div data-slide="2" class="slide-wrapper">
				<RangSlide {runner} stats={raceStats} />
			</div>

			<!-- Slide 3: Peloton -->
			<div data-slide="3" class="slide-wrapper">
				<PelotanSlide {runner} stats={raceStats} />
			</div>

			<!-- Slide 4: Catégorie -->
			<div data-slide="4" class="slide-wrapper">
				<CategorieSlide {runner} stats={raceStats} />
			</div>

			<!-- Slide 5: La course dans la course -->
			<div data-slide="5" class="slide-wrapper">
				<CourseDansLaCourseSlide {runner} stats={raceStats} />
			</div>

			<!-- Slide 6: Allure -->
			<div data-slide="6" class="slide-wrapper">
				<AllureSlide {runner} stats={raceStats} {race} distKm={DIST[race]} />
			</div>

			<!-- Slide 7: Partage -->
			<div data-slide="7" class="slide-wrapper">
				<PartageSlide
					{runner}
					stats={raceStats}
					{race}
					distKm={DIST[race]}
					onrestart={handleRestart}
				/>
			</div>
		{/key}
	{/if}
</main>

<style>
	.scroll-root {
		height: 100dvh;
		overflow-y: scroll;
		scroll-snap-type: y mandatory;
		overscroll-behavior: none;
	}

	.slide-wrapper {
		scroll-snap-align: start;
		scroll-snap-stop: always;
		min-height: 100dvh;
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100dvh;
		gap: 16px;
		color: var(--ink-3);
	}

	.spinner {
		width: 36px;
		height: 36px;
		border: 3px solid var(--line-2);
		border-top-color: var(--hot);
		border-radius: 50%;
		animation: spin 0.75s linear infinite;
	}

	@keyframes spin { to { transform: rotate(360deg); } }
</style>
