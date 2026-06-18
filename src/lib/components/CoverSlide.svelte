<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { search, formatName, type Runner, type Race } from '$lib/data.ts';

	const {
		runners10,
		runners6,
		onselect
	}: {
		runners10: Runner[];
		runners6: Runner[];
		onselect: (runner: Runner, race: Race) => void;
	} = $props();

	let query = $state('');
	let race = $state<Race>('10km');
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

	function runners() {
		return race === '10km' ? runners10 : runners6;
	}

	function onInput() {
		error = '';
		const q = query.trim();
		if (q.length >= 2) {
			suggestions = search(runners(), q).slice(0, 8);
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
		const results = search(runners(), q);
		if (results.length === 1) {
			pick(results[0]);
		} else if (results.length > 1) {
			suggestions = results.slice(0, 8);
			showSugg = true;
		} else {
			error = `"${q}" introuvable dans le ${race}.`;
		}
	}

	function pick(r: Runner) {
		showSugg = false;
		query = formatName(r.nom);
		onselect(r, race);
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

	<div class="race-tabs" role="tablist">
		<button role="tab" aria-selected={race === '10km'} class:on={race === '10km'}
			onclick={() => { race = '10km'; query = ''; suggestions = []; error = ''; }}>10 km</button>
		<button role="tab" aria-selected={race === '6km'} class:on={race === '6km'}
			onclick={() => { race = '6km'; query = ''; suggestions = []; error = ''; }}>6 km</button>
	</div>

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

	<p class="privacy">Données issues des résultats officiels de la Course des 2 Stades Domitys 2026. Aucune donnée personnelle n'est stockée. Conformément à l'article 18 du règlement de la course, vous pouvez demander la non-publication de vos résultats en contactant l'organisation.</p>
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
		max-height: 96px;
	}

	h1 {
		font-family: var(--font-display);
		font-size: clamp(48px, 13vw, 112px);
		font-weight: 800;
		font-style: italic;
		line-height: 0.95;
		color: var(--ink);
	}

	.race-tabs {
		display: flex;
		gap: 8px;
		background: var(--bg-2);
		border-radius: 100px;
		padding: 4px;
	}

	.race-tabs button {
		padding: 8px 24px;
		border-radius: 100px;
		border: none;
		background: transparent;
		color: var(--ink-3);
		font: inherit;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s, color 0.2s;
	}

	.race-tabs button.on {
		background: var(--hot);
		color: var(--bg);
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
