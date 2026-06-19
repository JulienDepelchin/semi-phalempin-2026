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
		window.open(
			`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`,
			'_blank', 'noopener'
		);
	}

	function shareFacebook() {
		window.open(
			`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
			'_blank', 'noopener'
		);
	}

	function shareWhatsApp() {
		window.open(
			`https://wa.me/?text=${encodeURIComponent(`${shareText} Retrouvez mes stats 👉 ${shareUrl}`)}`,
			'_blank', 'noopener'
		);
	}

	async function copyLink() {
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
		ctx.fillText('SEMI-MARATHON DE PHALEMPIN 2025', W / 2, 207);
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
		ctx.font = '400 24px "Barlow"'; ctx.fillStyle = 'rgba(255,255,255,0.18)';
		ctx.fillText(shareUrl, W / 2, fY + 155, W - 120);

		// Logo watermark bas-droite — chargement isolé pour garantir que
		// drawImage s'exécute dans le callback onload, pas avant.
		await new Promise<void>(resolve => {
			const img = new Image();
			img.onload = () => {
				const w = 120;
				const h = (img.naturalHeight / img.naturalWidth) * w;
				ctx.globalAlpha = 0.9;
				ctx.drawImage(img, W - w - 16, H - h - 16, w, h);
				ctx.globalAlpha = 1;
				resolve();
			};
			img.onerror = () => resolve();
			img.src = `${base}/logo.svg`;
		});

		return canvas;
	}

	async function shareStory() {
		storyLoading = true;
		storyToast = '';
		try {
			const canvas = await generateStoryCanvas();
			const blob = await new Promise<Blob>((resolve, reject) => {
				canvas.toBlob(b => b ? resolve(b) : reject(new Error('toBlob failed')), 'image/png');
			});
			const file = new File([blob], 'story-phalempin-2025.png', { type: 'image/png' });

			const canShareFiles =
				typeof navigator.share === 'function' &&
				typeof navigator.canShare === 'function' &&
				navigator.canShare({ files: [file] });

			if (canShareFiles) {
				await navigator.share({ files: [file] });
			} else {
				const url = URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url; a.download = 'story-phalempin-2025.png'; a.click();
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
				<canvas bind:this={previewCanvasEl} class="preview-canvas" aria-label="Aperçu Story"></canvas>
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

		<p class="legal">Données issues des résultats officiels du Semi-Marathon de Phalempin 2025. Aucune donnée personnelle n'est stockée.</p>
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
