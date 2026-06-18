<script lang="ts">
	const {
		total,
		active
	}: {
		total: number;
		active: number;
	} = $props();
</script>

<nav class="pips" aria-label="Navigation slides">
	{#each { length: total } as _, i}
		<span class="pip" class:on={i === active}></span>
	{/each}
</nav>

<style>
	.pips {
		position: fixed;
		right: 20px;
		top: 50%;
		transform: translateY(-50%);
		display: flex;
		flex-direction: column;
		gap: 10px;
		z-index: 100;
	}

	.pip {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--line-2);
		transition: background 0.25s, transform 0.25s;
	}

	.pip.on {
		background: var(--hot);
		transform: scale(1.5);
	}
</style>
