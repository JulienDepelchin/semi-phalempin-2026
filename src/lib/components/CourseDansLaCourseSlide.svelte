<script lang="ts">
	import { onMount } from 'svelte';
	import SlideShell from './SlideShell.svelte';
	import { Counter } from '$lib/useReveal.svelte.ts';
	import { fmtThousands } from '$lib/data.ts';
	import type { Runner, RaceStats } from '$lib/data.ts';

	const {
		runner,
		stats
	}: {
		runner: Runner;
		stats: RaceStats;
	} = $props();

	// Desktop (vertical bars)
	const VB_W = 900;
	const VB_H = 308;
	const PAD = { top: 28, right: 16, bottom: 64, left: 44 };
	const innerW = VB_W - PAD.left - PAD.right;
	const innerH = VB_H - PAD.top - PAD.bottom;

	// Mobile (horizontal bars)
	const VB_W_M = 400;
	const VB_H_M = 300;
	const PAD_M = { top: 8, bottom: 8, left: 64, right: 12 };
	const innerW_M = VB_W_M - PAD_M.left - PAD_M.right; // 324
	const innerH_M = VB_H_M - PAD_M.top - PAD_M.bottom; // 284

	let isMobile = $state(false);

	onMount(() => {
		const mq = window.matchMedia('(max-width: 767px)');
		isMobile = mq.matches;
		const handler = (e: MediaQueryListEvent) => { isMobile = e.matches; };
		mq.addEventListener('change', handler);
		return () => mq.removeEventListener('change', handler);
	});

	// Age groups by decade (age ≈ 2026 − birth year)
	// Sub labels are approximate FFA category hints.
	interface AgeGroupDef { label: string; sub: string; minYear: number; maxYear: number; }

	const AGE_GROUPS: AgeGroupDef[] = [
		{ label: '≃<19',   sub: '(JU)',    minYear: 2007, maxYear: 9999 },
		{ label: '≃20-22', sub: '(ES)',    minYear: 2004, maxYear: 2006 },
		{ label: '≃23-34', sub: '(SE)',    minYear: 1992, maxYear: 2003 },
		{ label: '≃35-39', sub: '(M0)',    minYear: 1987, maxYear: 1991 },
		{ label: '≃40-49', sub: '(M1-M2)', minYear: 1977, maxYear: 1986 },
		{ label: '≃50-59', sub: '(M3-M4)', minYear: 1967, maxYear: 1976 },
		{ label: '≃60-69', sub: '(M5-M6)', minYear: 1957, maxYear: 1966 },
		{ label: '≃70+',   sub: '(M7+)',   minYear: 0,    maxYear: 1956 },
	];

	const myAgeLabel = $derived.by(() => {
		const b = parseInt(runner.annee);
		if (isNaN(b)) return '';
		return AGE_GROUPS.find(g => b >= g.minYear && b <= g.maxYear)?.label ?? '';
	});

	const groupData = $derived.by(() =>
		AGE_GROUPS.map(g => {
			const gr = stats.runners.filter(r => {
				const b = parseInt(r.annee);
				return !isNaN(b) && b >= g.minYear && b <= g.maxYear;
			});
			const mCount = gr.filter(r => r.genre === 'M').length;
			const fCount = gr.filter(r => r.genre === 'F').length;
			return { label: g.label, sub: g.sub, mCount, fCount, total: mCount + fCount };
		}).filter(g => g.total > 0)
	);

	const maxTotal = $derived(Math.max(...groupData.map(g => g.total), 1));

	// Desktop bar geometry
	const barStep = $derived(innerW / groupData.length);
	const barW = $derived(Math.max(20, barStep * 0.75));

	// Mobile bar geometry
	const barStepM = $derived(innerH_M / groupData.length);
	const barH_M = $derived(Math.max(14, barStepM * 0.65));

	const myGroupData = $derived(groupData.find(g => g.label === myAgeLabel));
	const myAgeSub = $derived(myGroupData?.sub ?? '');
	const myPct = $derived(
		myGroupData ? Math.round(myGroupData.total / stats.global.n * 100) : 0
	);

	const growth = new Counter();
	function start() { growth.run(1, 0); }
</script>

<SlideShell onreveal={start}>
	<div class="cdc-slide">
		<p class="eyebrow">La course dans la course.</p>

		{#if myGroupData}
			<p class="context-phrase">
				Vous étiez parmi les <strong>{fmtThousands(myGroupData.total)}</strong> coureurs
				de la tranche <strong>{myAgeLabel} ans</strong> <span class="cat-hint">{myAgeSub}</span>,
				soit <strong>{myPct}%</strong> de tous les finishers.
			</p>
		{/if}

		<div class="svg-wrap">
			{#if isMobile}
				<!-- Mobile: horizontal bars (age groups on Y, count on X) -->
				<svg
					viewBox="0 0 {VB_W_M} {VB_H_M}"
					preserveAspectRatio="xMidYMid meet"
					role="img"
					aria-label="Histogramme horizontal par tranche d'âge"
				>
					<!-- X gridlines (vertical) -->
					{#each [0.25, 0.5, 0.75, 1.0] as frac}
						{@const gx = PAD_M.left + frac * innerW_M}
						<line
							x1={gx} y1={PAD_M.top}
							x2={gx} y2={PAD_M.top + innerH_M}
							stroke="rgba(255,255,255,0.06)" stroke-width="1"
						/>
					{/each}

					<!-- Y axis baseline -->
					<line
						x1={PAD_M.left} y1={PAD_M.top}
						x2={PAD_M.left} y2={PAD_M.top + innerH_M}
						stroke="rgba(255,255,255,0.2)" stroke-width="1"
					/>

					<!-- Horizontal stacked bars (M=left teal, F=right pink) -->
					{#each groupData as g, i}
						{@const by = PAD_M.top + i * barStepM + (barStepM - barH_M) / 2}
						{@const isMe = g.label === myAgeLabel}
						{@const mW = (g.mCount / maxTotal) * innerW_M * growth.value}
						{@const fW = (g.fCount / maxTotal) * innerW_M * growth.value}
						{@const totalW = mW + fW}
						{@const cy = by + barH_M / 2}

						<!-- M bar (teal, left) -->
						<rect
							x={PAD_M.left} y={by}
							width={mW} height={barH_M}
							fill="#00eabd" opacity={isMe ? 1 : 0.45}
						/>
						<!-- F bar (pink, right of M) -->
						<rect
							x={PAD_M.left + mW} y={by}
							width={fW} height={barH_M}
							fill="#e1135e" opacity={isMe ? 1 : 0.45}
						/>

						<!-- White border for runner's group -->
						{#if isMe}
							<rect
								x={PAD_M.left - 2} y={by - 2}
								width={totalW + 2} height={barH_M + 4}
								fill="none" stroke="white" stroke-width="2" rx={2}
							/>
						{/if}

						<!-- Total count to the right of bar -->
						{#if growth.value > 0.6}
							<text
								x={PAD_M.left + totalW + 5} y={cy + 4}
								text-anchor="start" font-size="11"
								fill={isMe ? 'white' : 'rgba(255,255,255,0.5)'}
								font-weight={isMe ? '700' : '400'}
							>{g.total}</text>
						{/if}

						<!-- Age group label (two lines) on the left -->
						<text
							x={PAD_M.left - 4} y={cy - 3}
							text-anchor="end" font-size="9"
							fill={isMe ? '#00eabd' : 'rgba(255,255,255,0.55)'}
							font-weight={isMe ? '700' : '400'}
						>{g.label}</text>
						<text
							x={PAD_M.left - 4} y={cy + 9}
							text-anchor="end" font-size="8"
							fill={isMe ? 'rgba(0,234,189,0.65)' : 'rgba(255,255,255,0.28)'}
						>{g.sub}</text>
					{/each}
				</svg>
			{:else}
				<!-- Desktop: vertical bars -->
				<svg
					viewBox="0 0 {VB_W} {VB_H}"
					preserveAspectRatio="xMidYMid meet"
					role="img"
					aria-label="Histogramme par tranche d'âge"
				>
					<!-- Y gridlines -->
					{#each [0.25, 0.5, 0.75, 1.0] as frac}
						{@const tickVal = Math.round(frac * maxTotal)}
						{@const gy = PAD.top + innerH - frac * innerH}
						<line
							x1={PAD.left} y1={gy}
							x2={PAD.left + innerW} y2={gy}
							stroke="rgba(255,255,255,0.06)" stroke-width="1"
						/>
						<text x={PAD.left - 4} y={gy + 4} text-anchor="end" font-size="10"
							fill="rgba(255,255,255,0.3)">{tickVal}</text>
					{/each}

					<!-- X axis baseline -->
					<line
						x1={PAD.left} y1={PAD.top + innerH}
						x2={PAD.left + innerW} y2={PAD.top + innerH}
						stroke="rgba(255,255,255,0.2)" stroke-width="1"
					/>

					<!-- Stacked bars (M=bottom teal, F=top pink) -->
					{#each groupData as g, i}
						{@const bx = PAD.left + i * barStep + (barStep - barW) / 2}
						{@const isMe = g.label === myAgeLabel}
						{@const mH = (g.mCount / maxTotal) * innerH * growth.value}
						{@const fH = (g.fCount / maxTotal) * innerH * growth.value}
						{@const totalH = mH + fH}
						{@const barTop = PAD.top + innerH - totalH}
						{@const cx = bx + barW / 2}

						<!-- M bar bottom -->
						<rect
							x={bx} y={barTop + fH}
							width={barW} height={mH}
							fill="#00eabd" opacity={isMe ? 1 : 0.45}
						/>
						<!-- F bar top -->
						<rect
							x={bx} y={barTop}
							width={barW} height={fH}
							fill="#e1135e" opacity={isMe ? 1 : 0.45}
						/>

						<!-- White border for runner's group -->
						{#if isMe}
							<rect
								x={bx - 2} y={barTop - 2}
								width={barW + 4} height={totalH + 2}
								fill="none" stroke="white" stroke-width="2" rx={2}
							/>
						{/if}

						<!-- Total above bar -->
						{#if growth.value > 0.6}
							<text
								x={cx} y={barTop - 6}
								text-anchor="middle" font-size="11"
								fill={isMe ? 'white' : 'rgba(255,255,255,0.5)'}
								font-weight={isMe ? '700' : '400'}
							>{g.total}</text>
						{/if}

						<!-- Decade label (line 1) -->
						<text
							x={cx} y={PAD.top + innerH + 17}
							text-anchor="middle" font-size="11"
							fill={isMe ? '#00eabd' : 'rgba(255,255,255,0.55)'}
							font-weight={isMe ? '700' : '400'}
						>{g.label}</text>
						<!-- FFA hint (line 2) -->
						<text
							x={cx} y={PAD.top + innerH + 31}
							text-anchor="middle" font-size="9"
							fill={isMe ? 'rgba(0,234,189,0.65)' : 'rgba(255,255,255,0.28)'}
						>{g.sub}</text>
					{/each}
				</svg>
			{/if}
		</div>

		<div class="legend">
			<span class="legend-item">
				<span class="legend-swatch" style="background:#e1135e"></span>
				Femmes
			</span>
			<span class="legend-item">
				<span class="legend-swatch" style="background:#00eabd"></span>
				Hommes
			</span>
			<span class="legend-item">
				<span class="legend-swatch legend-border"></span>
				Votre tranche
			</span>
		</div>
	</div>
</SlideShell>

<style>
	.cdc-slide { display: flex; flex-direction: column; gap: 10px; }

	.eyebrow {
		font-family: var(--font-display);
		font-size: clamp(22px, 5vw, 40px);
		font-weight: 800;
		font-style: italic;
		color: var(--ink);
	}

	.context-phrase {
		font-size: 0.9rem;
		color: rgba(255,255,255,0.75);
		font-style: italic;
		font-weight: 600;
		line-height: 1.5;
		max-width: 520px;
	}

	.context-phrase strong {
		color: #00eabd;
		font-style: normal;
	}

	.cat-hint {
		font-style: normal;
		font-weight: 400;
		color: rgba(255,255,255,0.4);
		font-size: 0.85em;
	}

	.svg-wrap {
		width: 100%;
		border-radius: 12px;
		background: var(--bg-2);
		padding: 8px;
	}

	svg { width: 100%; height: auto; display: block; }

	.legend {
		display: flex;
		gap: 16px;
		flex-wrap: wrap;
		font-size: 0.75rem;
		color: rgba(255,255,255,0.55);
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.legend-swatch {
		display: inline-block;
		width: 12px;
		height: 12px;
		border-radius: 2px;
		flex-shrink: 0;
	}

	.legend-border {
		background: transparent;
		box-shadow: 0 0 0 2px rgba(255,255,255,0.65);
	}
</style>
