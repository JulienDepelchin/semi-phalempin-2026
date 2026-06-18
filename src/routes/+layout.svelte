<script lang="ts">
	import '../lib/tokens.css';
	import type { Snippet } from 'svelte';
	const { children }: { children: Snippet } = $props();
</script>

{@render children()}
