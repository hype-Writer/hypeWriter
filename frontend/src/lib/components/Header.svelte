<script lang="ts">
	import { percentComplete } from '../refinery.svelte';
	import LumonLogo from '../assets/lumon-logo.svg?raw';
	import { formatPercent } from '../formatters';

	let { progressOverride = null } = $props();

	let currentProgress = $derived(
		progressOverride !== null ? progressOverride : percentComplete.current
	);
	let formattedPctComplete = $derived(formatPercent(currentProgress));
	let progressSlots = $derived(Math.ceil(currentProgress * 50));
</script>

<header>
	<div class="inner">
		<ul class="progress" style:--progress={formattedPctComplete}>
			{#each { length: progressSlots } as _, index}
				<li style:--index={index}></li>
			{/each}
		</ul>
		<h1>hypeWriter</h1>
		<h2>
			{formattedPctComplete} Complete
		</h2>
	</div>
	{@html LumonLogo}
</header>

<style>
	header {
		border-bottom: var(--border);
		padding-inline: 4rem;
		display: grid;
		grid-template-columns: 1fr auto;
		align-items: center;
		--logo-overlap: 26px;

		.inner {
			display: grid;
			align-items: center;
			border: var(--border);
			border-right: none;
			margin-right: calc(-1 * var(--logo-overlap));
			height: 70px;

			> * {
				grid-area: 1 / -1;
				height: 100%;
			}
		}

		.progress {
			display: grid;
			grid-template-columns: repeat(50, 1fr);
			list-style: none;
			padding: 0;
			z-index: -1;
			clip-path: inset(0 calc(100% - var(--progress, 0%)) 0 0);
			transition: clip-path 0.5s ease-out;

			li {
				background: var(--color-text-1);
				width: calc(var(--index) * 2%);
				opacity: min(calc(var(--index) * 2.5%), 100%);
			}
		}

		:is(h1, h2) {
			display: grid;
			align-items: center;
			margin: 0;
			font-size: 3em;
			white-space: nowrap;
			overflow: hidden;
		}

		h1 {
			margin-left: 1rem;
			font-weight: 500;
		}

		h2 {
			margin-right: calc(var(--logo-overlap) + 2rem);
			text-align: right;
			color: var(--color-bg);
			-webkit-text-stroke: var(--color-text-1) 2.5px;
		}

		:global(svg) {
			height: 112px;
			translate: 0 1px;

			:global(.bg) {
				fill: var(--color-bg);
			}

			:global(.fg) {
				fill: var(--color-text-1);
			}
		}
	}
</style>
