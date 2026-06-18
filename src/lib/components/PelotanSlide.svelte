<script lang="ts">
	import { onMount } from 'svelte';
	import SlideShell from './SlideShell.svelte';
	import { fasterThanPct, seededRng, formatName, linScale, fmtTime } from '$lib/data.ts';
	import { forceSimulation, forceX, forceY, forceCollide } from 'd3';
	import type { Runner, RaceStats } from '$lib/data.ts';

	const {
		runner,
		stats
	}: {
		runner: Runner;
		stats: RaceStats;
	} = $props();

	// Desktop layout constants
	const VB_W = 1000;
	const VB_H = 340;
	const Y_CENTER = 155;
	const AX_Y = VB_H - 42;
	const PAD = { left: 40, right: 40 };
	const innerW = VB_W - PAD.left - PAD.right;

	// Mobile vertical beeswarm constants
	const VB_W_M = 400;
	const VB_H_M = 530;
	const PAD_LEFT_M = 45;
	const PAD_RIGHT_M = 90;
	const PAD_TOP_M = 50;
	const PAD_BOT_M = 40;
	const INNER_W_M = VB_W_M - PAD_LEFT_M - PAD_RIGHT_M; // 265
	const innerH_M = VB_H_M - PAD_TOP_M - PAD_BOT_M;    // 440
	const AX_X_M = VB_W_M - PAD_RIGHT_M;                  // 310
	const X_CENTER_M = PAD_LEFT_M + INNER_W_M / 2;        // 177

	const R = 2.5;
	const MAX_NODES = 900;

	let isMobile = $state(false);
	let ready = $state(false);

	onMount(() => {
		const mq = window.matchMedia('(max-width: 767px)');
		isMobile = mq.matches;
		const handler = (e: MediaQueryListEvent) => { isMobile = e.matches; };
		mq.addEventListener('change', handler);
		return () => mq.removeEventListener('change', handler);
	});

	const pct = $derived(fasterThanPct(runner.pos, stats.global.n));

	const timeDomain = $derived.by((): [number, number] => {
		let lo = Infinity, hi = -Infinity;
		for (const r of stats.runners) {
			if (r.temps_sec < lo) lo = r.temps_sec;
			if (r.temps_sec > hi) hi = r.temps_sec;
		}
		return [lo, hi];
	});

	interface BNode {
		x: number; y: number;
		vx?: number; vy?: number;
		targetX: number;
		fill: string;
		isRunner: boolean;
	}

	interface BNodeV {
		x: number; y: number;
		vx?: number; vy?: number;
		targetY: number;
		fill: string;
		isRunner: boolean;
	}

	interface Dot {
		cx: number; cy: number;
		fill: string;
		isRunner: boolean;
	}

	function buildPool() {
		let pool = stats.runners;
		if (pool.length > MAX_NODES) {
			const sorted = pool.slice().sort((a, b) => a.temps_sec - b.temps_sec);
			const step = sorted.length / (MAX_NODES - 1);
			pool = Array.from({ length: MAX_NODES - 1 }, (_, i) => sorted[Math.floor(i * step)]);
			if (!pool.find(r => r.dossard === runner.dossard)) pool.push(runner);
		}
		return pool;
	}

	// Desktop horizontal beeswarm
	const dots = $derived.by((): Dot[] => {
		const rng = seededRng(parseInt(runner.dossard) || 42);
		const [lo, hi] = timeDomain;
		const xFn = linScale([lo, hi], [PAD.left, PAD.left + innerW]);
		const pool = buildPool();

		const simNodes: BNode[] = pool.map(r => ({
			x: xFn(r.temps_sec),
			y: Y_CENTER + (rng() - 0.5) * 4,
			targetX: xFn(r.temps_sec),
			fill: r.genre === 'M' ? '#00eabd' : '#e1135e',
			isRunner: r.dossard === runner.dossard,
		}));

		forceSimulation<BNode>(simNodes)
			.force('x', forceX<BNode>(d => d.targetX).strength(0.9))
			.force('y', forceY<BNode>(Y_CENTER).strength(0.05))
			.force('collide', forceCollide<BNode>(R + 0.5).iterations(2))
			.stop()
			.tick(150);

		return simNodes.map(d => ({
			cx: d.x,
			cy: Math.max(8, Math.min(AX_Y - 4, d.y)),
			fill: d.fill,
			isRunner: d.isRunner,
		}));
	});

	// Mobile vertical beeswarm
	const dotsMobile = $derived.by((): Dot[] => {
		const rng = seededRng(parseInt(runner.dossard) || 42);
		const [lo, hi] = timeDomain;
		const yFn = linScale([lo, hi], [PAD_TOP_M, PAD_TOP_M + innerH_M]);
		const pool = buildPool();

		const simNodes: BNodeV[] = pool.map(r => ({
			x: X_CENTER_M + (rng() - 0.5) * 4,
			y: yFn(r.temps_sec),
			targetY: yFn(r.temps_sec),
			fill: r.genre === 'M' ? '#00eabd' : '#e1135e',
			isRunner: r.dossard === runner.dossard,
		}));

		forceSimulation<BNodeV>(simNodes)
			.force('y', forceY<BNodeV>(d => d.targetY).strength(0.9))
			.force('x', forceX<BNodeV>(X_CENTER_M).strength(0.05))
			.force('collide', forceCollide<BNodeV>(R + 0.5).iterations(2))
			.stop()
			.tick(150);

		return simNodes.map(d => ({
			cx: Math.max(PAD_LEFT_M + R + 5, Math.min(AX_X_M - R - 10, d.x)),
			cy: Math.max(PAD_TOP_M + R, Math.min(PAD_TOP_M + innerH_M - R, d.y)),
			fill: d.fill,
			isRunner: d.isRunner,
		}));
	});

	interface MedianLine {
		label: string;
		strokeColor: string; strokeW: number; dashed: boolean; lineOpacity: number;
		bgFill: string; border: string; badgeW: number;
		time: number; x: number; badgeTop: number;
	}

	const medians = $derived.by((): MedianLine[] => {
		const [lo, hi] = timeDomain;
		const xFn = linScale([lo, hi], [PAD.left, PAD.left + innerW]);
		const raw: MedianLine[] = [
			{
				label: 'médiane',
				strokeColor: 'rgba(255,255,255,0.7)', strokeW: 1.5, dashed: false, lineOpacity: 1,
				bgFill: 'rgba(255,255,255,0.15)', border: 'rgba(255,255,255,0.4)', badgeW: 62,
				time: stats.global.medianTime, x: 0, badgeTop: 6,
			},
			{
				label: 'médiane H',
				strokeColor: '#00eabd', strokeW: 1, dashed: true, lineOpacity: 0.5,
				bgFill: 'rgba(0,234,189,0.2)', border: '#00eabd', badgeW: 68,
				time: stats.byGender.M.medianTime, x: 0, badgeTop: 6,
			},
			{
				label: 'médiane F',
				strokeColor: '#e1135e', strokeW: 1, dashed: true, lineOpacity: 0.5,
				bgFill: 'rgba(225,19,94,0.2)', border: '#e1135e', badgeW: 68,
				time: stats.byGender.F.medianTime, x: 0, badgeTop: 6,
			},
		].map(m => ({ ...m, x: xFn(m.time) }));

		const sorted = raw.slice().sort((a, b) => a.x - b.x);
		const topAlt = [6, 38, 6];
		sorted.forEach((m, i) => { m.badgeTop = topAlt[i]; });

		return raw;
	});

	interface MedianLineMobile {
		label: string;
		strokeColor: string; strokeW: number; dashed: boolean; lineOpacity: number;
		bgFill: string; border: string;
		time: number; y: number;
	}

	const mediansMobile = $derived.by((): MedianLineMobile[] => {
		const [lo, hi] = timeDomain;
		const yFn = linScale([lo, hi], [PAD_TOP_M, PAD_TOP_M + innerH_M]);
		return [
			{
				label: 'médiane',
				strokeColor: 'rgba(255,255,255,0.7)', strokeW: 1.5, dashed: false, lineOpacity: 1,
				bgFill: 'rgba(255,255,255,0.15)', border: 'rgba(255,255,255,0.4)',
				time: stats.global.medianTime, y: yFn(stats.global.medianTime),
			},
			{
				label: 'médiane H',
				strokeColor: '#00eabd', strokeW: 1, dashed: true, lineOpacity: 0.5,
				bgFill: 'rgba(0,234,189,0.2)', border: '#00eabd',
				time: stats.byGender.M.medianTime, y: yFn(stats.byGender.M.medianTime),
			},
			{
				label: 'médiane F',
				strokeColor: '#e1135e', strokeW: 1, dashed: true, lineOpacity: 0.5,
				bgFill: 'rgba(225,19,94,0.2)', border: '#e1135e',
				time: stats.byGender.F.medianTime, y: yFn(stats.byGender.F.medianTime),
			},
		];
	});

	const PROXIMITY_THRESH = 60;
	const medianProximity = $derived.by(() => {
		if (Math.abs(runner.temps_sec - stats.global.medianTime)    < PROXIMITY_THRESH) return 'générale';
		if (Math.abs(runner.temps_sec - stats.byGender.M.medianTime) < PROXIMITY_THRESH) return 'hommes';
		if (Math.abs(runner.temps_sec - stats.byGender.F.medianTime) < PROXIMITY_THRESH) return 'femmes';
		return null;
	});

	const xTickData = $derived.by(() => {
		const [lo, hi] = timeDomain;
		const xFn = linScale([lo, hi], [PAD.left, PAD.left + innerW]);
		const step = Math.ceil((hi - lo) / 6 / 60) * 60;
		const ticks: { t: number; x: number }[] = [];
		for (let t = Math.ceil(lo / step) * step; t <= hi; t += step) {
			ticks.push({ t, x: xFn(t) });
		}
		return ticks;
	});

	const yTickDataMobile = $derived.by(() => {
		const [lo, hi] = timeDomain;
		const yFn = linScale([lo, hi], [PAD_TOP_M, PAD_TOP_M + innerH_M]);
		const step = Math.ceil((hi - lo) / 5 / 60) * 60;
		const ticks: { t: number; y: number }[] = [];
		for (let t = Math.ceil(lo / step) * step; t <= hi; t += step) {
			ticks.push({ t, y: yFn(t) });
		}
		return ticks;
	});
</script>

<SlideShell onreveal={() => (ready = true)}>
	<div class="pelotan-slide">
		<p class="eyebrow">Dans le peloton</p>
		<p class="name">{formatName(runner.nom)}</p>
		<p class="pct-caption">Devant <strong>{pct} %</strong> des coureurs</p>

		{#if medianProximity}
			<p class="proximity-note">Vous êtes proche de la médiane <strong>{medianProximity}</strong>.</p>
		{/if}

		<div class="svg-wrap" class:ready>
			{#if isMobile}
				<!-- Mobile: vertical beeswarm (Y = time, top=fast) -->
				<svg
					viewBox="0 0 {VB_W_M} {VB_H_M}"
					preserveAspectRatio="xMidYMid meet"
					role="img"
					aria-label="Beeswarm vertical des coureurs par temps"
				>
					<defs>
						<filter id="glow-you-m" x="-80%" y="-80%" width="260%" height="260%">
							<feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"/>
							<feMerge>
								<feMergeNode in="blur"/>
								<feMergeNode in="SourceGraphic"/>
							</feMerge>
						</filter>
						<clipPath id="swarm-clip-m">
							<rect x={PAD_LEFT_M} y={PAD_TOP_M} width={INNER_W_M} height={innerH_M}/>
						</clipPath>
					</defs>

					<!-- Crowd dots (clipped) -->
					<g clip-path="url(#swarm-clip-m)">
						{#each dotsMobile as d}
							{#if !d.isRunner}
								<circle cx={d.cx} cy={d.cy} r={R} fill={d.fill} opacity={0.5}/>
							{/if}
						{/each}
					</g>

					<!-- Median horizontal lines -->
					{#each mediansMobile as m}
						<line
							x1={PAD_LEFT_M} y1={m.y}
							x2={AX_X_M} y2={m.y}
							stroke={m.strokeColor}
							stroke-width={m.strokeW}
							stroke-dasharray={m.dashed ? '4 5' : undefined}
							opacity={m.lineOpacity}
						/>
					{/each}
					<!-- Median badges on right -->
					{#each mediansMobile as m}
						<rect
							x={AX_X_M + 4} y={m.y - 10}
							width={82} height={20} rx={4}
							fill={m.bgFill} stroke={m.border} stroke-width="1"
						/>
						<text
							x={AX_X_M + 45} y={m.y + 4}
							text-anchor="middle" font-size="10" font-weight="600"
							fill="white"
						>{m.label}</text>
					{/each}

					<!-- Y axis line -->
					<line
						x1={PAD_LEFT_M} y1={PAD_TOP_M}
						x2={PAD_LEFT_M} y2={PAD_TOP_M + innerH_M}
						stroke="rgba(255,255,255,0.15)" stroke-width="1"
					/>
					<!-- Y ticks -->
					{#each yTickDataMobile as { t, y }}
						<line x1={PAD_LEFT_M - 4} y1={y} x2={PAD_LEFT_M} y2={y}
							stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
						<text x={PAD_LEFT_M - 7} y={y + 4} text-anchor="end"
							font-size="10" fill="rgba(255,255,255,0.4)">{fmtTime(t)}</text>
					{/each}

					<!-- Direction labels -->
					<text x={PAD_LEFT_M} y={PAD_TOP_M - 10} font-size="9"
						fill="rgba(255,255,255,0.2)">↑ rapide</text>
					<text x={PAD_LEFT_M} y={PAD_TOP_M + innerH_M + 18} font-size="9"
						fill="rgba(255,255,255,0.2)">↓ lent</text>

					<!-- Runner dot + VOUS badge (outside clip so badge never gets clipped) -->
					{#each dotsMobile as d}
						{#if d.isRunner}
							{@const badgeY = Math.max(2, d.cy - 36)}
							<g filter="url(#glow-you-m)">
								<circle cx={d.cx} cy={d.cy} r={6} fill="#00eabd"/>
							</g>
							<rect x={d.cx - 22} y={badgeY} width={44} height={20} rx={4} fill="#00eabd"/>
							<text x={d.cx} y={badgeY + 13} text-anchor="middle"
								font-size="12" font-weight="700" fill="#0d0d1a">VOUS</text>
							<line x1={d.cx} y1={badgeY + 20} x2={d.cx} y2={d.cy - 6}
								stroke="#00eabd" stroke-width="1.5"/>
						{/if}
					{/each}
				</svg>
			{:else}
				<!-- Desktop: horizontal beeswarm (X = time, left=fast) -->
				<svg
					viewBox="0 0 {VB_W} {VB_H}"
					preserveAspectRatio="xMidYMid meet"
					role="img"
					aria-label="Beeswarm des coureurs par temps"
				>
					<defs>
						<filter id="glow-you" x="-80%" y="-80%" width="260%" height="260%">
							<feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"/>
							<feMerge>
								<feMergeNode in="blur"/>
								<feMergeNode in="SourceGraphic"/>
							</feMerge>
						</filter>
						<clipPath id="swarm-clip">
							<rect x="0" y="0" width={VB_W} height={AX_Y}/>
						</clipPath>
					</defs>

					<!-- Crowd dots (clipped) -->
					<g clip-path="url(#swarm-clip)">
						{#each dots as d}
							{#if !d.isRunner}
								<circle cx={d.cx} cy={d.cy} r={R} fill={d.fill} opacity={0.5}/>
							{/if}
						{/each}

						<!-- Runner dot — rendered last so it sits on top -->
						{#each dots as d}
							{#if d.isRunner}
								<g filter="url(#glow-you)">
									<circle cx={d.cx} cy={d.cy} r={6} fill="#00eabd"/>
								</g>
								<rect x={d.cx - 22} y={d.cy - 36} width={44} height={20} rx={4} fill="#00eabd"/>
								<text x={d.cx} y={d.cy - 22} text-anchor="middle" font-size="12" font-weight="700" fill="#0d0d1a">VOUS</text>
								<line x1={d.cx} y1={d.cy - 16} x2={d.cx} y2={d.cy - 6} stroke="#00eabd" stroke-width="1.5"/>
							{/if}
						{/each}
					</g>

					<!-- 3 median lines -->
					{#each medians as m}
						<line
							x1={m.x} y1={m.badgeTop + 26}
							x2={m.x} y2={AX_Y}
							stroke={m.strokeColor}
							stroke-width={m.strokeW}
							stroke-dasharray={m.dashed ? '4 5' : undefined}
							opacity={m.lineOpacity}
						/>
					{/each}
					{#each medians as m}
						<line
							x1={m.x} y1={m.badgeTop + 20}
							x2={m.x} y2={m.badgeTop + 26}
							stroke={m.border} stroke-width="1.5"
						/>
						<rect
							x={m.x - m.badgeW / 2} y={m.badgeTop}
							width={m.badgeW} height={20} rx={4}
							fill={m.bgFill} stroke={m.border} stroke-width="1"
						/>
						<text
							x={m.x} y={m.badgeTop + 13}
							text-anchor="middle" font-size="10" font-weight="600"
							fill="white"
						>{m.label}</text>
					{/each}

					<!-- X axis -->
					<line
						x1={PAD.left} y1={AX_Y}
						x2={PAD.left + innerW} y2={AX_Y}
						stroke="rgba(255,255,255,0.15)" stroke-width="1"
					/>
					{#each xTickData as { t, x }}
						<line x1={x} y1={AX_Y} x2={x} y2={AX_Y + 5}
							stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
						<text x={x} y={AX_Y + 18} text-anchor="middle" font-size="11"
							fill="rgba(255,255,255,0.4)">{fmtTime(t)}</text>
					{/each}

					<text x={PAD.left} y={VB_H - 2} font-size="10" fill="rgba(255,255,255,0.2)" text-anchor="start">← plus rapide</text>
					<text x={PAD.left + innerW} y={VB_H - 2} font-size="10" fill="rgba(255,255,255,0.2)" text-anchor="end">plus lent →</text>
				</svg>
			{/if}
		</div>
	</div>
</SlideShell>

<style>
	.pelotan-slide { display: flex; flex-direction: column; gap: 12px; }

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

	.pct-caption { font-size: 1rem; color: var(--ink-2); }
	.pct-caption strong { color: var(--hot); }

	.proximity-note {
		font-size: 0.82rem;
		color: var(--ink-3);
		font-style: italic;
	}

	.proximity-note strong { color: var(--ink-2); font-style: normal; }

	.svg-wrap {
		width: 100%;
		border-radius: 12px;
		overflow: hidden;
		background: var(--bg-2);
		opacity: 0;
		transition: opacity 0.8s ease;
	}

	.svg-wrap.ready { opacity: 1; }

	svg { width: 100%; height: auto; display: block; }
</style>
