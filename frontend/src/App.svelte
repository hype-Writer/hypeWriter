<script lang="ts">
	import Navigation from './lib/components/navigation.svelte';
	import Home from './lib/pages/home.svelte';
	import World from './lib/pages/world.svelte';
	import Characters from './lib/pages/characters.svelte';
	import Outline from './lib/pages/outline.svelte';
	import Chapters from './lib/pages/chapters.svelte';

	let currentPath = $state(window.location.pathname);

	$effect(() => {
		window.addEventListener('popstate', () => {
			currentPath = window.location.pathname;
		});
	});
</script>

<Navigation />

<main>
	{#if currentPath === '/'}
		<Home />
	{:else if currentPath === '/world'}
		<World />
	{:else if currentPath === '/characters'}
		<Characters />
	{:else if currentPath === '/outline'}
		<Outline />
		<!-- {:else if currentPath === '/chapters'}
		<Chapters /> -->
	{:else}
		<p>Page not found</p>
	{/if}
</main>

<style>
	main {
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
	}
</style>
