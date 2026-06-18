<script lang="ts">
	import SlideShell from './SlideShell.svelte';
	import { Counter } from '$lib/useReveal.svelte.ts';
	import { fmtTime, linScale } from '$lib/data.ts';
	import type { Runner, FinishHist } from '$lib/data.ts';

	const {
		runner,
		hist
	}: {
		runner: Runner;
		hist: FinishHist;
	} = $props();

	const VB_W = 1000;
	const VB_H = 480;
	const PAD = { top: 40, right: 24, bottom: 64, left: 40 };
	const innerW = VB_W - PAD.left - PAD.right;
	const innerH = VB_H - PAD.top - PAD.bottom;

	const growth = new Counter();

	const nbins = $derived(hist.men.length);
	const yMax = $derived(Math.max(...hist.men, ...hist.women) || 1);

	const xScale = $derived(linScale([0, nbins], [0, innerW]));
	const yScale = $derived(linScale([0, yMax], [innerH, 0]));

	const binW = $derived(innerW / nbins);

	const runnerBin = $derived(
		hist.domain
			? Math.floor((runner.temps_sec - hist.domain[0]) / hist.binSec)
			: -1
	);
	const runnerX = $derived(
		runnerBin >= 0 && runnerBin < nbins
			? PAD.left + xScale(runnerBin + 0.5)
			: -1
	);

	const tickCount = 6;
	const xTicks = $derived(
		Array.from({ length: tickCount }, (_, i) =>
			Math.round((i / (tickCount - 1)) * (nbins - 1))
		)
	);

	const menMedianBin = $derived(
		hist.domain
			? Math.floor((hist.menMedian - hist.domain[0]) / hist.binSec)
			: -1
	);
	const womenMedianBin = $derived(
		hist.domain
			? Math.floor((hist.womenMedian - hist.domain[0]) / hist.binSec)
			: -1
	);

	function start() {
		growth.run(1, 0);
	}
</script>

<SlideShell onreveal={start}>
	<div class="distrib-slide">
		<p class="eyebrow">Distribution des temps</p>
		<p class="name">{runner.nom.split(',')[0]}</p>

		<div class="svg-wrap">
			<svg
				viewBox="0 0 {VB_W} {VB_H}"
				preserveAspectRatio="xMidYMid meet"
				role="img"
				aria-label="Histogramme des temps de course"
			>
				<g transform="translate({PAD.left},{PAD.top})">
					<!-- Men bars -->
					{#each hist.men as count, i}
						{@const h = (count / yMax) * innerH * growth.value}
						<rect
							x={xScale(i)}
							y={innerH - h}
							width={binW - 1}
							height={h}
							fill="var(--men-color)"
							opacity="0.45"
						/>
					{/each}

					<!-- Women bars -->
					{#each hist.women as count, i}
						{@const h = (count / yMax) * innerH * growth.value}
						<rect
							x={xScale(i)}
							y={innerH - h}
							width={binW - 1}
							height={h}
							fill="var(--women-color)"
							opacity="0.55"
						/>
					{/each}

					<!-- Median lines -->
					{#if menMedianBin >= 0}
						<line
							x1={xScale(menMedianBin + 0.5)}
							y1={0}
							x2={xScale(menMedianBin + 0.5)}
							y2={innerH}
							stroke="var(--men-color)"
							stroke-width="1.5"
							stroke-dasharray="4 4"
							opacity="0.7"
						/>
					{/if}
					{#if womenMedianBin >= 0}
						<line
							x1={xScale(womenMedianBin + 0.5)}
							y1={0}
							x2={xScale(womenMedianBin + 0.5)}
							y2={innerH}
							stroke="var(--women-color)"
							stroke-width="1.5"
							stroke-dasharray="4 4"
							opacity="0.7"
						/>
					{/if}

					<!-- Runner line -->
					{#if runnerBin >= 0}
						{@const rx = xScale(runnerBin + 0.5)}
						<line
							x1={rx} y1={-12}
							x2={rx} y2={innerH}
							stroke="var(--hot)"
							stroke-width="2.5"
						/>
						<rect
							x={rx - 22} y={-28}
							width={44} height={20}
							rx={4}
							fill="var(--hot)"
						/>
						<text
							x={rx} y={-14}
							text-anchor="middle"
							font-size="13"
							font-weight="700"
							fill="var(--bg)"
						>TOI</text>
					{/if}

					<!-- X axis -->
					<line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="var(--line-2)" stroke-width="1" />

					{#each xTicks as bin}
						{@const sec = hist.domain[0] + bin * hist.binSec}
						<text
							x={xScale(bin + 0.5)}
							y={innerH + 20}
							text-anchor="middle"
							font-size="13"
							fill="var(--ink-4)"
						>{fmtTime(sec)}</text>
					{/each}
				</g>
			</svg>
		</div>

		<div class="legend">
			<span class="leg men">Hommes</span>
			<span class="leg women">Femmes</span>
			<span class="leg you">Vous</span>
		</div>
	</div>
</SlideShell>

<style>
	.distrib-slide {
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

	.name {
		font-family: var(--font-display);
		font-size: clamp(28px, 6vw, 52px);
		font-weight: 800;
		font-style: italic;
		color: var(--ink);
	}

	.svg-wrap {
		width: 100%;
		border-radius: 12px;
		overflow: hidden;
		background: var(--bg-2);
		padding: 8px;
	}

	svg {
		width: 100%;
		height: auto;
		display: block;
	}

	.legend {
		display: flex;
		gap: 20px;
		flex-wrap: wrap;
	}

	.leg {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 0.8rem;
		color: var(--ink-3);
	}

	.leg::before {
		content: '';
		display: block;
		width: 12px;
		height: 12px;
		border-radius: 2px;
	}

	.leg.men::before { background: var(--men-color); opacity: 0.7; }
	.leg.women::before { background: var(--women-color); opacity: 0.8; }
	.leg.you::before { background: var(--hot); }
</style>
