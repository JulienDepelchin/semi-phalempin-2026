<script lang="ts">
	import SlideShell from './SlideShell.svelte';
	import { base } from '$app/paths';
	import {
		fmtTime, fmtPace, fasterThanPct, genderRank,
		getCategory, getCategoryLabel, marathonEquiv, fmtThousands, formatName
	} from '$lib/data.ts';
	import type { Runner, RaceStats, Race } from '$lib/data.ts';

	const {
		runner,
		stats,
		race,
		distKm,
		onrestart
	}: {
		runner: Runner;
		stats: RaceStats;
		race: Race;
		distKm: number;
		onrestart: () => void;
	} = $props();

	const pct = $derived(fasterThanPct(runner.pos, stats.global.n));
	const cat = $derived(getCategory(runner.annee, runner.genre));
	const pace = $derived(fmtPace(runner.temps_sec, distKm));

	const gCurve = $derived(stats.genderRankCurve[runner.genre]);
	const gPos = $derived(genderRank(gCurve, runner.temps_sec));
	const gTotal = $derived(gCurve.size);

	const catRunners = $derived(
		stats.runners
			.filter((r) => getCategory(r.annee, r.genre) === cat)
			.sort((a, b) => a.temps_sec - b.temps_sec)
	);
	const catPos = $derived(catRunners.findIndex((r) => r.dossard === runner.dossard) + 1);
	const catTotal = $derived(catRunners.length);

	const marathonSec = $derived(marathonEquiv(runner.temps_sec, distKm));

	const shareUrl = $derived(
		typeof window !== 'undefined'
			? `${window.location.origin}${base}/?dossard=${runner.dossard}`
			: ''
	);

	const shareText = $derived(
		`J'ai couru le Semi-Marathon de Phalempin en ${runner.temps_str} ! Devant ${pct}% des coureurs.`
	);

	let copied = $state(false);
	let storyLoading = $state(false);
	let storyToast = $state('');
	let previewUrl = $state('');

	// ── Photo state ───────────────────────────────────────────────────────────
	let photoDataUrl = $state<string | null>(null);

	function onPhotoChosen(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onload = (ev) => {
			photoDataUrl = ev.target?.result as string ?? null;
		};
		reader.readAsDataURL(file);
	}

	function removePhoto() {
		photoDataUrl = null;
	}

	// ── Canvas preview ────────────────────────────────────────────────────────
	let previewCanvasEl = $state<HTMLCanvasElement | null>(null);

	$effect(() => {
		void photoDataUrl;
		const canvas = previewCanvasEl;
		if (!canvas) return;
		let cancelled = false;
		(async () => {
			await document.fonts.ready;
			if (cancelled) return;
			await drawPreview(canvas);
		})();
		return () => { cancelled = true; };
	});

	async function drawPreview(canvas: HTMLCanvasElement) {
		const PW = 200, PH = 356;
		const dpr = window.devicePixelRatio || 1;
		canvas.width = PW * dpr;
		canvas.height = PH * dpr;
		canvas.style.width = PW + 'px';
		canvas.style.height = PH + 'px';
		const ctx = canvas.getContext('2d')!;
		ctx.scale(dpr, dpr);

		// Background
		if (photoDataUrl) {
			const img = await new Promise<HTMLImageElement | null>(resolve => {
				const i = new Image();
				i.onload = () => resolve(i);
				i.onerror = () => resolve(null);
				i.src = photoDataUrl!;
			});
			if (img) {
				const scale = Math.max(PW / img.naturalWidth, PH / img.naturalHeight);
				const sw = PW / scale, sh = PH / scale;
				ctx.drawImage(img, (img.naturalWidth - sw) / 2, (img.naturalHeight - sh) / 2, sw, sh, 0, 0, PW, PH);
			} else {
				ctx.fillStyle = '#0a0a0a'; ctx.fillRect(0, 0, PW, PH);
			}
			ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, PW, PH);
		} else {
			ctx.fillStyle = '#0a0a0a'; ctx.fillRect(0, 0, PW, PH);
			ctx.strokeStyle = 'rgba(255,255,255,0.06)'; ctx.lineWidth = 0.5;
			for (let x = 0; x < PW; x += 15) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,PH); ctx.stroke(); }
			for (let y = 0; y < PH; y += 15) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(PW,y); ctx.stroke(); }
		}

		// Separator
		ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 0.5;
		ctx.beginPath(); ctx.moveTo(12, 46); ctx.lineTo(PW - 12, 46); ctx.stroke();

		// Time
		ctx.font = 'italic 800 36px "Barlow Condensed"';
		ctx.fillStyle = '#00eabd'; ctx.textAlign = 'center';
		ctx.fillText(runner.temps_str, PW / 2, 92);

		// Name
		ctx.font = 'italic 700 13px "Barlow Condensed"';
		ctx.fillStyle = 'rgba(255,255,255,0.88)';
		ctx.fillText(formatName(runner.nom), PW / 2, 110, PW - 20);

		// Race
		ctx.font = '600 7px "Barlow"';
		ctx.fillStyle = 'rgba(255,255,255,0.38)';
		ctx.fillText(race.toUpperCase(), PW / 2, 123);

		ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth = 0.5;
		ctx.beginPath(); ctx.moveTo(12, 132); ctx.lineTo(PW - 12, 132); ctx.stroke();

		// Stats 2×2 grid
		const blocks = [
			{ val: `#${fmtThousands(runner.pos)}`, lbl: 'classement' },
			{ val: `#${fmtThousands(catPos)}`,     lbl: 'catégorie' },
			{ val: `#${fmtThousands(gPos)}`,       lbl: runner.genre === 'M' ? 'hommes' : 'femmes' },
			{ val: pace,                            lbl: 'allure /km' },
		];
		const BW = (PW - 30) / 2, BH = 44;
		const bx0 = 10, by0 = 140;

		for (let i = 0; i < 4; i++) {
			const col = i % 2, row = Math.floor(i / 2);
			const bx = bx0 + col * (BW + 10);
			const by = by0 + row * (BH + 6);
			const bcx = bx + BW / 2;

			ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 0.5;
			ctx.strokeRect(bx, by, BW, BH);

			ctx.font = 'italic 800 16px "Barlow Condensed"';
			ctx.fillStyle = '#00eabd'; ctx.textAlign = 'center';
			ctx.fillText(blocks[i].val, bcx, by + 22, BW - 6);

			ctx.font = '600 7px "Barlow"';
			ctx.fillStyle = 'rgba(255,255,255,0.88)';
			ctx.fillText(blocks[i].lbl, bcx, by + 35, BW - 6);
		}

		ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth = 0.5;
		ctx.beginPath(); ctx.moveTo(12, 248); ctx.lineTo(PW - 12, 248); ctx.stroke();

		// Percentile
		ctx.font = '600 7px "Barlow"';
		ctx.fillStyle = 'rgba(255,255,255,0.4)'; ctx.textAlign = 'center';
		ctx.fillText('DEVANT', PW / 2, 262);

		ctx.font = 'italic 800 28px "Barlow Condensed"';
		ctx.fillStyle = '#00eabd';
		ctx.fillText(`${pct}%`, PW / 2, 286);

		ctx.font = '10px "Barlow"';
		ctx.fillStyle = 'rgba(255,255,255,0.65)';
		ctx.fillText('des coureurs derrière vous', PW / 2, 300);

		// Progress bar
		const barW = PW - 24, barH = 3;
		ctx.fillStyle = 'rgba(255,255,255,0.1)';
		ctx.fillRect(12, 310, barW, barH);
		ctx.fillStyle = '#00eabd';
		ctx.fillRect(12, 310, Math.max(barH, (pct / 100) * barW), barH);
	}

	// ── Share buttons ────────────────────────────────────────────────────────

	function shareX() {
		(window as any).umami?.track('partage', { canal: 'x' });
		window.open(
			`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`,
			'_blank', 'noopener'
		);
	}

	function shareFacebook() {
		(window as any).umami?.track('partage', { canal: 'facebook' });
		window.open(
			`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
			'_blank', 'noopener'
		);
	}

	function shareWhatsApp() {
		(window as any).umami?.track('partage', { canal: 'whatsapp' });
		window.open(
			`https://wa.me/?text=${encodeURIComponent(`${shareText} Retrouvez mes stats 👉 ${shareUrl}`)}`,
			'_blank', 'noopener'
		);
	}

	async function copyLink() {
		(window as any).umami?.track('partage', { canal: 'lien' });
		try {
			await navigator.clipboard.writeText(shareUrl);
			copied = true;
			setTimeout(() => (copied = false), 2200);
		} catch {
			alert(shareUrl);
		}
	}

	// ── Story generation ──────────────────────────────────────────────────────

	function drawRoundRect(
		ctx: CanvasRenderingContext2D,
		x: number, y: number, w: number, h: number, r: number
	) {
		ctx.beginPath();
		ctx.moveTo(x + r, y);
		ctx.lineTo(x + w - r, y);
		ctx.arcTo(x + w, y, x + w, y + r, r);
		ctx.lineTo(x + w, y + h - r);
		ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
		ctx.lineTo(x + r, y + h);
		ctx.arcTo(x, y + h, x, y + h - r, r);
		ctx.lineTo(x, y + r);
		ctx.arcTo(x, y, x + r, y, r);
		ctx.closePath();
	}

	const LOGO_SVG = `<svg id="Calque_1" xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 250 62.82" width="250" height="62.82">
  <defs><style>.st0{fill:#fff}.st1{fill:#00eabd}</style></defs>
  <polygon class="st0" points="71.72 57.43 35.56 57.43 37.47 53.88 73.62 53.88 71.72 57.43"/>
  <polygon class="st0" points="48.27 62.38 33.31 62.38 35.21 58.84 50.17 58.84 48.27 62.38"/>
  <path class="st0" d="M74.83,32.87c-1.01-1.47-2.65-2.64-4.9-3.5s-5.2-1.43-8.85-1.7l-7.35-.61c-1.96-.17-3.31-.49-4.03-.97-.73-.48-1.09-1.08-1.09-1.83,0-1.01.62-1.77,1.85-2.28s2.9-.76,5-.76c1.59,0,2.96.15,4.11.46s2.04.74,2.66,1.29c.63.56,1.01,1.21,1.14,1.95h11.97c-.17-2.54-1.11-4.76-2.81-6.67-1.71-1.91-4.01-3.39-6.9-4.44s-6.2-1.57-9.92-1.57-7.2.48-10.05,1.42-5.06,2.34-6.65,4.18c-.68.79-1.21,1.66-1.59,2.61h0l-.1.26c-.04.11-.09.23-.12.34l-1.22,3.33-11.65,26.98-11.69-26.98H0l17.45,38.05h13.44l7.87-17.17c.1.12.19.25.29.37,1.73,2.01,4.11,3.58,7.16,4.69,3.04,1.12,6.58,1.67,10.6,1.67s7.35-.57,10.27-1.7c2.92-1.13,5.2-2.72,6.82-4.77s2.44-4.42,2.44-7.13c0-2.23-.51-4.08-1.52-5.55h0ZM62.47,42.23c-1.3.54-3.12.81-5.45.81-1.69,0-3.16-.18-4.41-.53-1.25-.36-2.24-.86-2.97-1.52-.73-.66-1.16-1.43-1.29-2.31h-6.54l1.87-4.08c2.25.88,5.09,1.44,8.53,1.7l6.7.56c2.2.17,3.67.5,4.41.99s1.12,1.13,1.12,1.9c0,1.12-.65,1.95-1.95,2.49h0Z"/>
  <path class="st1" d="M39.21,9.74c0,5.38-4.36,9.74-9.75,9.74s-9.75-4.36-9.75-9.74S24.08,0,29.47,0s9.75,4.36,9.75,9.74"/>
  <path class="st0" d="M109.68,25.16h1.08l.99-2.35h6.43l.99,2.35h4.34l-5.86-13.08h-5.37l-4.23,9.47h-6.28v-9.47h-4.06v13.08h11.98,0ZM113.12,19.56l1.86-4.41,1.85,4.41h-3.71Z"/>
  <polygon class="st0" points="140.25 35.94 151.26 11.94 143.45 11.94 136.11 28.96 128.73 11.94 120.77 11.94 131.77 35.94 140.25 35.94"/>
  <path class="st0" d="M148.63,23.94c0,2.52.6,4.72,1.81,6.59s2.89,3.34,5.06,4.38c2.16,1.04,4.69,1.57,7.57,1.57s5.4-.52,7.57-1.57,3.85-2.51,5.06-4.38c1.21-1.88,1.81-4.08,1.81-6.59s-.6-4.72-1.81-6.59-2.89-3.34-5.06-4.38-4.69-1.57-7.57-1.57-5.4.52-7.57,1.57c-2.17,1.04-3.85,2.51-5.06,4.38-1.21,1.88-1.81,4.08-1.81,6.59h0ZM156.98,20.79c.55-.89,1.35-1.57,2.38-2.05s2.27-.72,3.7-.72,2.66.24,3.69.72c1.04.48,1.83,1.16,2.38,2.05.55.89.83,1.93.83,3.15s-.28,2.27-.83,3.15c-.55.89-1.35,1.57-2.38,2.05s-2.27.72-3.69.72-2.66-.24-3.7-.72c-1.04-.48-1.83-1.16-2.38-2.05s-.83-1.93-.83-3.15.28-2.27.83-3.15Z"/>
  <rect class="st0" x="178.53" y="11.94" width="7.46" height="24"/>
  <polygon class="st0" points="196.09 35.94 201.74 28.58 207.35 35.94 216.54 35.94 206.42 23.47 215.86 11.94 206.68 11.94 201.9 18.3 197.02 11.94 187.7 11.94 197.23 23.48 187.06 35.94 196.09 35.94"/>
  <path class="st0" d="M105.64,27.34c-.84-.39-1.82-.58-2.94-.58h-4.8v9.33h4.8c1.12,0,2.1-.19,2.94-.58.84-.39,1.5-.93,1.96-1.63s.7-1.52.7-2.46-.24-1.77-.7-2.46-1.12-1.24-1.96-1.62ZM105.09,32.53c-.2.31-.48.56-.85.73-.37.17-.81.25-1.31.25h-2.15v-4.18h2.15c.51,0,.94.09,1.31.25s.65.41.85.72c.2.31.3.68.3,1.11s-.1.79-.3,1.11h0Z"/>
  <polygon class="st0" points="116.94 33.78 111.18 33.78 111.39 32.44 116.51 32.44 116.51 30.4 111.39 30.4 111.18 29.07 116.88 29.07 116.88 26.76 108.1 26.76 108.8 31.43 108.1 36.09 116.94 36.09 116.94 33.78"/>
  <path class="st0" d="M123.64,33.9c-.32.13-.76.2-1.34.2-.42,0-.77-.04-1.08-.13s-.55-.21-.73-.37c-.18-.16-.28-.35-.32-.57h-2.93c.01.65.24,1.22.66,1.71s1.01.88,1.76,1.15c.74.27,1.61.41,2.6.41s1.8-.14,2.52-.42,1.28-.67,1.67-1.17c.4-.5.6-1.09.6-1.75,0-.55-.12-1-.37-1.36-.25-.36-.65-.65-1.2-.86-.55-.21-1.28-.35-2.17-.42l-1.8-.15c-.48-.04-.81-.12-.99-.24-.18-.12-.27-.27-.27-.45,0-.25.15-.43.45-.56.3-.12.71-.19,1.22-.19.39,0,.73.04,1.01.11s.5.18.65.32.25.3.28.48h2.93c-.04-.62-.27-1.17-.69-1.64-.42-.47-.98-.83-1.69-1.09s-1.52-.39-2.43-.39-1.77.12-2.46.35-1.24.57-1.63,1.03-.58,1.01-.58,1.68c0,.82.3,1.47.9,1.96s1.57.78,2.92.88l1.64.14c.54.04.9.12,1.08.24s.27.28.27.47c0,.27-.16.48-.48.61h0Z"/>
  <path class="st1" d="M119.05,48.36c-1.44-.55-3.32-.91-5.65-1.09l-4.7-.39c-1.25-.11-2.11-.31-2.57-.61-.46-.3-.7-.69-.7-1.17,0-.65.39-1.13,1.18-1.46.79-.32,1.85-.49,3.19-.49,1.01,0,1.89.1,2.62.29s1.3.47,1.7.83c.4.36.64.77.73,1.25h7.64c-.11-1.62-.71-3.04-1.8-4.26-1.09-1.22-2.56-2.16-4.41-2.83s-3.96-1-6.33-1-4.6.3-6.41.91c-1.82.61-3.23,1.5-4.24,2.67-1.01,1.18-1.52,2.64-1.52,4.39,0,2.14.78,3.84,2.35,5.1,1.56,1.26,4.1,2.02,7.59,2.28l4.27.36c1.4.11,2.34.32,2.82.63s.71.72.71,1.22c0,.71-.42,1.24-1.25,1.59s-1.99.52-3.48.52c-1.08,0-2.02-.11-2.82-.34s-1.43-.55-1.89-.97c-.46-.42-.74-.91-.83-1.47h-7.64c.04,1.68.61,3.17,1.71,4.45,1.1,1.28,2.62,2.28,4.57,2.99s4.2,1.07,6.77,1.07,4.69-.36,6.56-1.09,3.32-1.74,4.36-3.04,1.55-2.82,1.55-4.55c0-1.43-.33-2.61-.97-3.54-.65-.94-1.69-1.68-3.13-2.23h.01,0Z"/>
  <path class="st1" d="M143.76,39.05c-1.52-.71-3.34-1.07-5.46-1.07h-13.89v24.29h7.55v-7.06h6.35c2.11,0,3.93-.36,5.46-1.07,1.52-.71,2.68-1.72,3.48-3.01.8-1.29,1.2-2.81,1.2-4.53s-.4-3.26-1.2-4.55c-.8-1.28-1.96-2.28-3.48-2.99h0ZM140.03,48.54c-.53.48-1.27.71-2.22.71h-5.86v-5.31h5.86c.95,0,1.69.23,2.22.68.53.45.79,1.11.79,1.98s-.27,1.47-.79,1.94h0Z"/>
  <path class="st1" d="M170.87,39.02c-2.19-1.06-4.75-1.59-7.66-1.59s-5.47.53-7.66,1.59c-2.19,1.06-3.9,2.54-5.12,4.43-1.22,1.9-1.83,4.12-1.83,6.67s.61,4.77,1.83,6.67,2.93,3.38,5.12,4.43c2.19,1.06,4.75,1.59,7.66,1.59s5.47-.53,7.66-1.59,3.9-2.54,5.12-4.43c1.22-1.9,1.83-4.12,1.83-6.67s-.61-4.77-1.83-6.67-2.93-3.38-5.12-4.43ZM169.37,53.32c-.56.89-1.37,1.59-2.41,2.07-1.05.49-2.29.73-3.74.73s-2.69-.24-3.74-.73c-1.05-.49-1.85-1.18-2.41-2.07-.56-.89-.84-1.96-.84-3.19s.28-2.29.84-3.19,1.37-1.59,2.41-2.07c1.05-.49,2.29-.73,3.74-.73s2.69.24,3.74.73c1.05.49,1.85,1.18,2.41,2.07.56.89.84,1.96.84,3.19s-.28,2.29-.84,3.19Z"/>
  <path class="st1" d="M198.4,52.86c1.43-.66,2.54-1.59,3.33-2.78s1.2-2.57,1.2-4.13-.4-2.99-1.2-4.18c-.8-1.19-1.91-2.11-3.33-2.78-1.43-.67-3.08-1-4.96-1h-14.83v24.29h7.55v-8.42h3.01l6,8.42h8.65l-6.58-8.96c.41-.13.8-.28,1.18-.45h0s0,0,0,0ZM186.16,43.42h6.15c.95,0,1.69.22,2.22.65.53.43.79,1.06.79,1.88s-.27,1.45-.79,1.88-1.27.65-2.22.65h-6.15v-5.05h0Z"/>
  <polygon class="st1" points="229.25 37.99 203.7 37.99 203.7 44.69 212.71 44.61 212.71 62.28 220.25 62.28 220.25 44.54 224.07 44.51 229.25 37.99"/>
  <path class="st1" d="M249.04,50.6c-.65-.94-1.69-1.68-3.13-2.23s-3.32-.91-5.65-1.09l-4.7-.39c-1.25-.11-2.11-.31-2.57-.61-.46-.3-.7-.69-.7-1.17,0-.65.39-1.13,1.18-1.46.79-.32,1.85-.49,3.19-.49,1.01,0,1.89.1,2.62.29s1.3.47,1.7.83c.4.36.64.77.73,1.25h7.64c-.11-1.62-.71-3.04-1.8-4.26-1.09-1.22-2.56-2.16-4.41-2.83s-3.96-1-6.33-1-4.6.3-6.41.91l-5.28,6.86c0,2.14.3,4.04,1.86,5.3s4.1,2.02,7.59,2.28l4.27.36c1.4.11,2.34.32,2.82.63s.71.72.71,1.22c0,.71-.42,1.24-1.25,1.59s-1.99.52-3.48.52c-1.08,0-2.02-.11-2.82-.34s-1.43-.55-1.89-.97c-.46-.42-.74-.91-.83-1.47h-7.64c.04,1.68.61,3.17,1.71,4.45s2.62,2.28,4.57,2.99,4.2,1.07,6.77,1.07,4.69-.36,6.56-1.09,3.32-1.74,4.36-3.04,1.55-2.82,1.55-4.55c0-1.43-.33-2.61-.97-3.54h.01,0Z"/>
  <rect class="st0" x="86.7" y="21.61" width=".52" height="32.51"/>
</svg>`;

	async function generateStoryCanvas(): Promise<HTMLCanvasElement> {
		const W = 1080, H = 1920;
		const canvas = document.createElement('canvas');
		canvas.width = W;
		canvas.height = H;
		const ctx = canvas.getContext('2d')!;

		try {
			await Promise.all([
				document.fonts.load('italic 800 1px "Barlow Condensed"'),
				document.fonts.load('600 1px "Barlow"'),
				document.fonts.load('400 1px "Barlow"'),
			]);
		} catch {}

		const logoImg = await new Promise<HTMLImageElement | null>(resolve => {
			const img = new Image();
			img.crossOrigin = 'anonymous';
			img.onload = () => resolve(img);
			img.onerror = () => resolve(null);
			img.src = `${base}/logo.svg`;
		});

		// Background
		if (photoDataUrl) {
			const photoImg = await new Promise<HTMLImageElement | null>(resolve => {
				const img = new Image();
				img.onload = () => resolve(img);
				img.onerror = () => resolve(null);
				img.src = photoDataUrl!;
			});
			if (photoImg) {
				const scale = Math.max(W / photoImg.naturalWidth, H / photoImg.naturalHeight);
				const sw = W / scale, sh = H / scale;
				ctx.drawImage(photoImg, (photoImg.naturalWidth - sw) / 2, (photoImg.naturalHeight - sh) / 2, sw, sh, 0, 0, W, H);
			} else {
				ctx.fillStyle = '#0a0a0a'; ctx.fillRect(0, 0, W, H);
			}
			ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, W, H);
		} else {
			ctx.fillStyle = '#0a0a0a'; ctx.fillRect(0, 0, W, H);
			ctx.strokeStyle = 'rgba(255,255,255,0.06)'; ctx.lineWidth = 1;
			for (let x = 0; x < W; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
			for (let y = 0; y < H; y += 80) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
		}

		// Header
		if (logoImg) {
			const lh = 105;
			const ar = logoImg.naturalWidth > 0 && logoImg.naturalHeight > 0
				? logoImg.naturalWidth / logoImg.naturalHeight : 1.548;
			const lw = Math.min(lh * ar, 620);
			ctx.drawImage(logoImg, (W - lw) / 2, 55, lw, lh);
		}
		ctx.textAlign = 'center';
		ctx.font = '600 28px "Barlow"';
		ctx.fillStyle = 'rgba(255,255,255,0.38)';
		(ctx as any).letterSpacing = '6px';
		ctx.fillText('SEMI-MARATHON DE PHALEMPIN 2026', W / 2, 207);
		(ctx as any).letterSpacing = '0px';
		ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1;
		ctx.beginPath(); ctx.moveTo(80, 245); ctx.lineTo(W - 80, 245); ctx.stroke();

		// Time
		ctx.font = 'italic 800 200px "Barlow Condensed"'; ctx.fillStyle = '#00eabd'; ctx.textAlign = 'center';
		ctx.fillText(runner.temps_str, W / 2, 492);
		ctx.font = 'italic 800 68px "Barlow Condensed"'; ctx.fillStyle = 'rgba(255,255,255,0.92)';
		ctx.fillText(formatName(runner.nom), W / 2, 590, W - 120);
		ctx.font = '600 34px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.35)';
		(ctx as any).letterSpacing = '5px';
		ctx.fillText(race.toUpperCase(), W / 2, 649);
		(ctx as any).letterSpacing = '0px';
		ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth = 1;
		ctx.beginPath(); ctx.moveTo(80, 695); ctx.lineTo(W - 80, 695); ctx.stroke();

		// Stats grid
		const BW = 460, BH = 215, BGAP = 40, BVGAP = 30;
		const bx0 = (W - 2 * BW - BGAP) / 2;
		const by0 = 730;

		const blocks = [
			{ val: `#${fmtThousands(runner.pos)}`, lbl: 'classement général',              sub: `/${fmtThousands(stats.global.n)} finishers` },
			{ val: `#${fmtThousands(catPos)}`,     lbl: getCategoryLabel(cat),              sub: `/${fmtThousands(catTotal)} en cat.` },
			{ val: `#${fmtThousands(gPos)}`,       lbl: runner.genre === 'M' ? 'hommes' : 'femmes', sub: `/${fmtThousands(gTotal)} classés` },
			{ val: pace,                            lbl: 'allure /km',                      sub: `≈ ${fmtTime(marathonSec)} marathon` },
		];

		for (let i = 0; i < 4; i++) {
			const col = i % 2, row = Math.floor(i / 2);
			const bx = bx0 + col * (BW + BGAP);
			const by = by0 + row * (BH + BVGAP);
			const bcx = bx + BW / 2;
			const s = blocks[i];

			drawRoundRect(ctx, bx, by, BW, BH, 12);
			ctx.fillStyle = 'rgba(255,255,255,0.05)'; ctx.fill();
			ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1.5; ctx.stroke();

			ctx.font = 'italic 800 80px "Barlow Condensed"'; ctx.fillStyle = '#00eabd'; ctx.textAlign = 'center';
			ctx.fillText(s.val, bcx, by + 103, BW - 30);

			ctx.font = '600 29px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.9)';
			ctx.fillText(s.lbl, bcx, by + 143, BW - 30);

			ctx.font = '400 26px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.85)';
			ctx.fillText(s.sub, bcx, by + 178, BW - 30);
		}

		const statsBottom = by0 + 2 * BH + BVGAP;
		ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth = 1;
		ctx.beginPath(); ctx.moveTo(80, statsBottom + 28); ctx.lineTo(W - 80, statsBottom + 28); ctx.stroke();

		// Percentile
		const pY = statsBottom + 78;
		ctx.font = '600 36px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.42)'; ctx.textAlign = 'center';
		(ctx as any).letterSpacing = '6px'; ctx.fillText('DEVANT', W / 2, pY); (ctx as any).letterSpacing = '0px';
		ctx.font = 'italic 800 170px "Barlow Condensed"'; ctx.fillStyle = '#00eabd';
		ctx.fillText(`${pct}%`, W / 2, pY + 170);
		ctx.font = 'italic 600 44px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.72)';
		ctx.fillText('des coureurs derrière vous', W / 2, pY + 236);

		const barTop = pY + 275;
		const barL = 80, barRW = W - 160, barH = 16;
		drawRoundRect(ctx, barL, barTop, barRW, barH, 8); ctx.fillStyle = 'rgba(255,255,255,0.1)'; ctx.fill();
		const fillW = Math.max(barH, (pct / 100) * barRW);
		drawRoundRect(ctx, barL, barTop, fillW, barH, 8); ctx.fillStyle = '#00eabd'; ctx.fill();

		// Footer
		const fY = barTop + barH + 52;
		ctx.strokeStyle = 'rgba(255,255,255,0.08)'; ctx.lineWidth = 1;
		ctx.beginPath(); ctx.moveTo(80, fY); ctx.lineTo(W - 80, fY); ctx.stroke();
		ctx.font = '700 29px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.28)'; ctx.textAlign = 'center';
		(ctx as any).letterSpacing = '4px';
		ctx.fillText("C'EST VOTRE COURSE. PARTAGEZ-LA FIÈREMENT.", W / 2, fY + 95, W - 120);
		(ctx as any).letterSpacing = '0px';
		// Logo watermark bas-droite — SVG inline en blob URL pour éviter CORS/sécurité canvas.
		await new Promise<void>(resolve => {
			const blob = new Blob([LOGO_SVG], { type: 'image/svg+xml' });
			const url = URL.createObjectURL(blob);
			const img = new Image();
			img.onload = () => {
				const w = 120;
				const h = (img.naturalHeight / img.naturalWidth) * w;
				ctx.globalAlpha = 0.9;
				ctx.drawImage(img, W - w - 16, H - h - 16, w, h);
				ctx.globalAlpha = 1;
				URL.revokeObjectURL(url);
				resolve();
			};
			img.onerror = () => { URL.revokeObjectURL(url); resolve(); };
			img.src = url;
		});

		previewUrl = canvas.toDataURL('image/png');
		return canvas;
	}

	async function shareStory() {
		storyLoading = true;
		storyToast = '';
		(window as any).umami?.track('story_generee');
		try {
			const canvas = await generateStoryCanvas();
			const blob = await new Promise<Blob>((resolve, reject) => {
				canvas.toBlob(b => b ? resolve(b) : reject(new Error('toBlob failed')), 'image/png');
			});
			const file = new File([blob], 'story-phalempin-2026.png', { type: 'image/png' });

			const canShareFiles =
				typeof navigator.share === 'function' &&
				typeof navigator.canShare === 'function' &&
				navigator.canShare({ files: [file] });

			if (canShareFiles) {
				await navigator.share({ files: [file] });
			} else {
				const url = URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url; a.download = 'story-phalempin-2026.png'; a.click();
				setTimeout(() => URL.revokeObjectURL(url), 5000);
				storyToast = "Image téléchargée ! Ouvrez Instagram → + → Story → sélectionnez l'image.";
				setTimeout(() => { storyToast = ''; }, 7000);
			}
		} catch (err) {
			if (!(err instanceof Error && err.name === 'AbortError')) {
				storyToast = "Erreur lors de la génération. Réessayez.";
				setTimeout(() => { storyToast = ''; }, 4000);
			}
		} finally {
			storyLoading = false;
		}
	}
</script>

<SlideShell tone="hot">
	<div class="partage-slide">
		<p class="eyebrow">C'EST VOTRE COURSE.</p>
		<p class="time-val">{runner.temps_str}</p>
		<p class="runner-name">{formatName(runner.nom)}</p>
		<p class="runner-race">{race}</p>

		<div class="card">
			<div class="card-grid">
				<div class="stat-block">
					<span class="stat-val">#{fmtThousands(runner.pos)}</span>
					<span class="stat-lbl">classement général</span>
					<span class="stat-sub">/{fmtThousands(stats.global.n)}</span>
				</div>
				<div class="stat-block">
					<span class="stat-val">#{fmtThousands(catPos)}</span>
					<span class="stat-lbl">catégorie {cat}</span>
					<span class="stat-sub">/{fmtThousands(catTotal)}</span>
				</div>
				<div class="stat-block">
					<span class="stat-val">#{fmtThousands(gPos)}</span>
					<span class="stat-lbl">{runner.genre === 'M' ? 'hommes' : 'femmes'}</span>
					<span class="stat-sub">/{fmtThousands(gTotal)}</span>
				</div>
				<div class="stat-block">
					<span class="stat-val">{pace}</span>
					<span class="stat-lbl">allure /km</span>
					<span class="stat-sub">≈ {fmtTime(marathonSec)} marathon</span>
				</div>
			</div>

			<div class="pct-highlight">
				<span class="pct-num">{pct} %</span>
				<span class="pct-txt"> des coureurs derrière vous</span>
			</div>
		</div>

		<p class="tagline">Vous pouvez être fier(e) de vous ! Partagez votre course ! 🏅</p>

		<div class="share-btns">
			<button type="button" class="share-chip" onclick={shareX} aria-label="Partager sur X">
				<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
				X
			</button>
			<button type="button" class="share-chip" onclick={shareFacebook} aria-label="Partager sur Facebook">
				<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
				Facebook
			</button>
			<button type="button" class="share-chip" onclick={shareWhatsApp} aria-label="Partager sur WhatsApp">
				<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
				WhatsApp
			</button>
			<button type="button" class="share-chip" onclick={copyLink} aria-label="Copier le lien">
				{#if copied}✓ Copié !{:else}
					<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
					Lien
				{/if}
			</button>
		</div>

		<!-- ── Story section ─────────────────────────────────────── -->
		<div class="story-section">

			<!-- Photo picker -->
			{#if photoDataUrl}
				<div class="photo-selected">
					<img src={photoDataUrl} class="photo-thumb-lg" alt="" aria-hidden="true" />
					<div class="photo-selected-body">
						<p class="photo-added-txt">Photo ajoutée ✓</p>
						<label class="photo-change-label">
							<input type="file" accept="image/*" onchange={onPhotoChosen} class="sr-only" />
							✕ Changer de photo
						</label>
						<button type="button" class="photo-remove-link" onclick={removePhoto}>
							Supprimer
						</button>
						<p class="photo-selected-hint">Appuyez sur "Partager en Story" pour générer votre image personnalisée.</p>
					</div>
				</div>
			{:else}
				<label class="photo-add-label">
					<input type="file" accept="image/*" onchange={onPhotoChosen} class="sr-only" />
					<span class="photo-add-icon" aria-hidden="true">📷</span>
					<span class="photo-add-body">
						<strong>Personnalisez votre Story avec une photo de la course</strong>
						<small>Votre photo reste sur votre appareil, elle n'est pas envoyée</small>
					</span>
				</label>
			{/if}

			<!-- Live preview -->
			<div class="preview-wrap">
				{#if previewUrl}
					<img src={previewUrl} class="preview-canvas" style="width:200px;height:356px;object-fit:contain" alt="Aperçu Story" />
				{:else}
					<canvas bind:this={previewCanvasEl} class="preview-canvas" aria-label="Aperçu Story"></canvas>
				{/if}
				<span class="preview-label">Aperçu Story</span>
			</div>

			<!-- Story button -->
			<button
				type="button"
				class="story-btn"
				onclick={shareStory}
				disabled={storyLoading}
				aria-label="Générer et partager une Stories Instagram"
			>
				{#if storyLoading}
					<span class="story-spinner" aria-hidden="true"></span>Génération…
				{:else}
					📸 Partager en Story
				{/if}
			</button>

			{#if storyToast}
				<div class="story-toast" role="status">{storyToast}</div>
			{/if}
		</div>

		<button class="btn-restart" onclick={onrestart}>
			Chercher un autre coureur
		</button>

		<p class="legal">Données issues des résultats officiels du Semi-Marathon de Phalempin 2026. Aucune donnée personnelle n'est stockée.</p>
	</div>
</SlideShell>

<style>
	.partage-slide { display: flex; flex-direction: column; gap: 16px; }

	.eyebrow {
		font-size: 0.75rem;
		letter-spacing: 0.15em;
		color: var(--hot);
		font-weight: 700;
	}

	.time-val {
		font-family: var(--font-display);
		font-size: clamp(60px, 16vw, 128px);
		font-weight: 800;
		font-style: italic;
		line-height: 0.9;
		color: #00eabd;
		font-variant-numeric: tabular-nums;
	}

	.runner-name {
		font-family: var(--font-display);
		font-size: clamp(22px, 5vw, 48px);
		font-weight: 800;
		font-style: italic;
		line-height: 1;
		color: var(--ink);
	}

	.runner-race {
		font-size: 0.9rem;
		color: var(--ink-3);
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.card {
		border: 1px solid var(--hot);
		border-radius: 18px;
		padding: 20px;
		background: var(--bg-2);
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.card-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 16px 12px;
	}

	@media (min-width: 540px) {
		.card-grid { grid-template-columns: repeat(4, 1fr); }
	}

	.stat-block { display: flex; flex-direction: column; gap: 2px; }

	.stat-val {
		font-family: var(--font-display);
		font-size: clamp(24px, 5.5vw, 44px);
		font-weight: 800;
		color: var(--hot);
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	.stat-lbl { font-size: 0.82rem; color: #ffffff; font-weight: 600; }
	.stat-sub { font-size: 0.77rem; color: #ffffff; }

	.pct-highlight {
		border-top: 1px solid var(--line);
		padding-top: 14px;
		display: flex;
		align-items: baseline;
		gap: 4px;
		flex-wrap: wrap;
	}

	.pct-num {
		font-family: var(--font-display);
		font-size: clamp(28px, 6vw, 50px);
		font-weight: 800;
		color: var(--hot);
		line-height: 1;
	}

	.pct-txt { font-size: 0.95rem; color: var(--ink-2); }

	.tagline {
		font-size: 0.9rem;
		color: var(--ink-2);
		font-style: italic;
	}

	.share-btns {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.share-chip {
		background: rgba(255,255,255,0.1);
		border: 1px solid rgba(255,255,255,0.2);
		border-radius: 20px;
		padding: 8px 14px;
		color: white;
		display: flex;
		align-items: center;
		gap: 6px;
		cursor: pointer;
		font: inherit;
		font-size: 0.85rem;
		font-weight: 600;
		transition: background 0.15s;
	}

	.share-chip:hover { background: rgba(255,255,255,0.2); }

	/* ── Story section ──────────────────────────────────────────────────────── */
	.story-section {
		display: flex;
		flex-direction: column;
		gap: 14px;
	}

	/* ── Visually hidden input (accessible but not visible) ─────────────────── */
	.sr-only {
		position: absolute;
		width: 1px; height: 1px;
		padding: 0; margin: -1px;
		overflow: hidden;
		clip: rect(0,0,0,0);
		white-space: nowrap;
		border: 0;
	}

	/* ── Photo: before selection ────────────────────────────────────────────── */
	.photo-add-label {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 16px 18px;
		border: 1.5px dashed rgba(255,255,255,0.3);
		border-radius: 14px;
		background: rgba(255,255,255,0.04);
		cursor: pointer;
		transition: border-color 0.2s, background 0.2s;
	}

	.photo-add-label:hover {
		border-color: rgba(255,255,255,0.55);
		background: rgba(255,255,255,0.08);
	}

	.photo-add-icon { font-size: 2rem; flex-shrink: 0; line-height: 1; }

	.photo-add-body {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.photo-add-body strong {
		font-size: 0.88rem;
		color: rgba(255,255,255,0.9);
		font-weight: 600;
		line-height: 1.35;
	}

	.photo-add-body small {
		font-size: 0.72rem;
		color: rgba(255,255,255,0.4);
		line-height: 1.4;
	}

	/* ── Photo: after selection ─────────────────────────────────────────────── */
	.photo-selected {
		display: flex;
		align-items: flex-start;
		gap: 14px;
		padding: 14px 16px;
		border: 1.5px solid rgba(0,234,189,0.3);
		border-radius: 14px;
		background: rgba(0,234,189,0.05);
	}

	.photo-thumb-lg {
		width: 80px;
		height: 80px;
		border-radius: 8px;
		object-fit: cover;
		flex-shrink: 0;
		border: 1px solid rgba(255,255,255,0.15);
	}

	.photo-selected-body {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.photo-added-txt {
		font-size: 0.88rem;
		font-weight: 700;
		color: #00eabd;
	}

	.photo-change-label {
		display: inline-block;
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255,255,255,0.7);
		cursor: pointer;
		border: 1px solid rgba(255,255,255,0.2);
		border-radius: 16px;
		padding: 5px 12px;
		width: fit-content;
		transition: background 0.15s;
	}

	.photo-change-label:hover { background: rgba(255,255,255,0.1); }

	.photo-remove-link {
		font-size: 0.72rem;
		color: rgba(255,255,255,0.35);
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		text-decoration: underline;
		font: inherit;
		width: fit-content;
	}

	.photo-remove-link:hover { color: rgba(225,19,94,0.8); }

	.photo-selected-hint {
		font-size: 0.75rem;
		color: rgba(255,255,255,0.5);
		line-height: 1.45;
		max-width: 260px;
	}

	/* ── Preview canvas ─────────────────────────────────────────────────────── */
	.preview-wrap {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 6px;
	}

	.preview-canvas {
		border-radius: 10px;
		display: block;
		border: 1px solid rgba(255,255,255,0.1);
	}

	.preview-label {
		font-size: 0.68rem;
		color: rgba(255,255,255,0.3);
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	/* ── Story button ───────────────────────────────────────────────────────── */
	.story-btn {
		align-self: flex-start;
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 11px 18px;
		border-radius: 20px;
		border: 1.5px solid rgba(0,234,189,0.5);
		background: rgba(0,234,189,0.08);
		color: #00eabd;
		font: inherit;
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s, border-color 0.15s;
	}

	.story-btn:hover:not(:disabled) {
		background: rgba(0,234,189,0.18);
		border-color: #00eabd;
	}

	.story-btn:disabled { opacity: 0.6; cursor: wait; }

	.story-spinner {
		display: inline-block;
		width: 13px; height: 13px;
		border: 2px solid rgba(0,234,189,0.25);
		border-top-color: #00eabd;
		border-radius: 50%;
		animation: story-spin 0.7s linear infinite;
	}

	@keyframes story-spin { to { transform: rotate(360deg); } }

	.story-toast {
		font-size: 0.78rem;
		color: rgba(255,255,255,0.7);
		background: rgba(0,234,189,0.08);
		border: 1px solid rgba(0,234,189,0.2);
		border-radius: 10px;
		padding: 10px 14px;
		line-height: 1.55;
		max-width: 380px;
	}

	/* ── Bottom ─────────────────────────────────────────────────────────────── */
	.btn-restart {
		align-self: flex-start;
		padding: 12px 20px;
		border-radius: 10px;
		border: 1.5px solid var(--line-2);
		background: transparent;
		color: var(--ink-3);
		font: inherit;
		font-weight: 600;
		cursor: pointer;
		transition: border-color 0.2s, color 0.2s;
	}

	.btn-restart:hover { border-color: var(--hot); color: var(--hot); }

	.legal {
		font-size: 0.65rem;
		color: var(--ink-4);
		line-height: 1.5;
		max-width: 480px;
	}
</style>
