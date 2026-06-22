<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { search, formatName, type Runner } from '$lib/data.ts';

	const {
		runners,
		onselect
	}: {
		runners: Runner[];
		onselect: (runner: Runner) => void;
	} = $props();

	let query = $state('');
	let suggestions = $state<Runner[]>([]);
	let showSugg = $state(false);
	let error = $state('');
	let logoSvg = $state('');
	let searchWrapEl = $state<HTMLElement | null>(null);

	function onFocusField() {
		setTimeout(() => {
			searchWrapEl?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}, 300);
	}

	onMount(async () => {
		try {
			const res = await fetch(`${base}/logo.svg`);
			if (res.ok) logoSvg = await res.text();
		} catch {}
	});

	function onInput() {
		error = '';
		const q = query.trim();
		if (q.length >= 2) {
			suggestions = search(runners, q).slice(0, 8);
			showSugg = suggestions.length > 0 && isNaN(Number(q));
		} else {
			suggestions = [];
			showSugg = false;
		}
	}

	function doSearch() {
		showSugg = false;
		const q = query.trim();
		if (!q) return;
		const results = search(runners, q);
		if (results.length === 1) {
			pick(results[0]);
		} else if (results.length > 1) {
			suggestions = results.slice(0, 8);
			showSugg = true;
		} else {
			error = `"${q}" introuvable dans le classement.`;
		}
	}

	function pick(r: Runner) {
		showSugg = false;
		query = formatName(r.nom);
		(window as any).umami?.track('recherche_dossard', { dossard: r.dossard, genre: r.genre });
		onselect(r);
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') doSearch();
		if (e.key === 'Escape') showSugg = false;
	}
</script>

<div class="cover">
	{#if logoSvg}
		<div class="logo-wrap">{@html logoSvg}</div>
	{/if}

	<h1>Le récap de<br />votre course.</h1>

	<p class="race-label">Semi-Marathon de Phalempin 2026</p>

	<div class="search-wrap" bind:this={searchWrapEl}>
		<div class="field-row">
			<input
				type="search"
				class="field"
				placeholder="Dossard ou nom…"
				bind:value={query}
				oninput={onInput}
				onkeydown={onKeydown}
				onfocus={onFocusField}
				autocomplete="off"
				autocorrect="off"
				spellcheck="false"
				aria-label="Rechercher un coureur"
			/>
			<button class="cta" onclick={doSearch}>Voir mes stats</button>
		</div>

		{#if showSugg}
			<ul class="suggestions" role="listbox">
				{#each suggestions as s}
					<li role="option" aria-selected="false">
						<button onclick={() => pick(s)}>
							<span class="s-nom">{formatName(s.nom)}</span>
							<span class="s-meta">{s.temps_str} · #{s.dossard}</span>
						</button>
					</li>
				{/each}
			</ul>
		{/if}

		{#if error}
			<p class="error" role="alert">{error}</p>
		{/if}
	</div>

	<p class="privacy">Données issues des résultats officiels du Semi-Marathon de Phalempin 2026. Aucune donnée personnelle n'est stockée.</p>
</div>

<style>
	.cover {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 28px;
		text-align: center;
		min-height: 90dvh;
		justify-content: center;
		padding: 40px var(--slide-pad);
	}

	.logo-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		max-width: 360px;
	}

	:global(.logo-wrap svg) {
		width: 100%;
		height: auto;
		max-height: 72px;
	}

	h1 {
		font-family: var(--font-display);
		font-size: clamp(48px, 13vw, 112px);
		font-weight: 800;
		font-style: italic;
		line-height: 0.95;
		color: var(--ink);
	}

	.race-label {
		font-size: 0.85rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--hot);
		font-weight: 600;
	}

	.search-wrap {
		position: relative;
		width: 100%;
		max-width: 480px;
	}

	.field-row { display: flex; gap: 8px; }

	.field {
		flex: 1;
		padding: 14px 18px;
		border-radius: 12px;
		border: 1.5px solid var(--line-2);
		background: var(--bg-2);
		color: var(--ink);
		font: inherit;
		font-size: 1rem;
		outline: none;
		transition: border-color 0.2s;
	}

	.field:focus { border-color: var(--hot); }

	.cta {
		padding: 14px 22px;
		border-radius: 12px;
		border: none;
		background: var(--hot);
		color: var(--bg);
		font: inherit;
		font-weight: 700;
		cursor: pointer;
		white-space: nowrap;
		transition: opacity 0.15s;
	}

	.cta:hover { opacity: 0.85; }
	.cta:active { opacity: 0.7; }

	.suggestions {
		position: absolute;
		top: calc(100% + 6px);
		left: 0;
		right: 0;
		background: var(--bg-2);
		border: 1px solid var(--line-2);
		border-radius: 12px;
		list-style: none;
		overflow: hidden;
		z-index: 50;
		box-shadow: 0 8px 24px rgba(0,0,0,0.4);
	}

	.suggestions li button {
		width: 100%;
		padding: 12px 16px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		background: none;
		border: none;
		color: var(--ink);
		cursor: pointer;
		font: inherit;
		text-align: left;
		transition: background 0.1s;
	}

	.suggestions li button:hover { background: var(--bg-3); }

	.s-nom { font-weight: 600; }
	.s-meta { font-size: 0.8rem; color: var(--ink-3); white-space: nowrap; }

	.error { margin-top: 8px; color: #e1135e; font-size: 0.875rem; text-align: left; }

	.privacy {
		font-size: 0.68rem;
		color: var(--ink-4);
		max-width: 400px;
		line-height: 1.6;
		text-align: center;
	}
</style>
