<script lang="ts">
	import { fly } from 'svelte/transition';
	import { refinery } from '../refinery.svelte';
	import BoxLid from './BoxLid.svelte';
	import BinDrawer from './BinDrawer.svelte';
	import { maxTemperCount } from '../settings';
	import { getRandomTemper } from '../tempers';
	import { formatPercent } from '../formatters';
	import { Confetti } from 'svelte-confetti';

	const height = 20;
	const duration = 500;

	interface Props {
		index: number;
		selected: boolean;
	}

	let { index, selected }: Props = $props();

	let element: HTMLElement;

	let temperCounts = $state({
		WO: 0,
		FC: 0,
		DR: 0,
		MA: 0
	});

	let binCount = $derived(Object.values(temperCounts).reduce((sum, count) => sum + count, 0));

	let percentFull = $derived(formatPercent(binCount / (maxTemperCount * 4)));

	let binOpen = $derived(selected && refinery.current !== 'ready');

	let drawerOpen = $derived(selected && refinery.current === 'binDrawerOpen');

	let width = $state() as number;
	
	let showConfetti = $state(false);
	let hasTriggeredConfetti = $state(false);

	const confettiConfigs = [
		{ x: [-0.25, 1.5] },   // Bin 1
		{ x: [-0.25, 0.75] },  // Bin 2  
		{ x: [-0.25, 0.25] },  // Bin 3
		{ x: [-0.75, 0.25] },  // Bin 4
		{ x: [-1.5, 0.25] }    // Bin 5
	];

	$effect(() => {
		if (binCount >= maxTemperCount * 4 && !hasTriggeredConfetti) {
			showConfetti = true;
			hasTriggeredConfetti = true;
			setTimeout(() => {
				showConfetti = false;
			}, 2100);
		}
	});

	export function getBoundingClientRect() {
		return element.getBoundingClientRect();
	}

	export function addItem() {
		const temper = getRandomTemper();
		if (temperCounts[temper] < maxTemperCount) {
			temperCounts[temper]++;
		}
	}

	export function getBinCount() {
		return binCount;
	}

	export function reset() {
		temperCounts = {
			WO: 0,
			FC: 0,
			DR: 0,
			MA: 0
		};
		hasTriggeredConfetti = false;
	}
</script>

<div
	bind:this={element}
	class="bin"
	style:--height="{height}px"
	style:--width="{width}px"
	bind:offsetWidth={width}
>
	<div class="box">
		<div class="front">0{index}</div>
		{#if binOpen}
			<div
				class="rear-lid"
				onintroend={() => refinery.send('transitionEnded')}
				transition:fly={{ duration, opacity: 1, y: height }}
			></div>
			<BoxLid {height} {width} {duration} side="left" />
			<BoxLid {height} {width} {duration} side="right" />
			<BinDrawer
				{index}
				{temperCounts}
				open={drawerOpen}
				ontransitionend={() => refinery.send('transitionEnded')}
			/>
		{/if}
		{#if showConfetti}
			<div class="confetti-container" data-bin="{index}">
				<Confetti 
					cone
					x={confettiConfigs[index - 1].x}
					y={[0.75, 2.25]}
					amount="50"
					rounded
					size="15"
					fallDistance="250px"
					colorArray={['#a8e0d8', '#f0f5c0', '#f0c8e8', '#7cc5e8']}
				/>
			</div>
		{/if}
	</div>
	<div class="progress">
		<div class="bar" style:width={percentFull}></div>
		<div class="value">{percentFull}</div>
	</div>
</div>

<style>
	.bin {
		--space: 8px;
		flex: 1;
		min-width: 8rem;
		max-width: 20rem;
		display: grid;
		grid-template-rows: 1fr 1fr;
		gap: var(--space);
		padding-block: var(--space);
		font-size: 1.8rem;
	}

	.box {
		position: relative;

		> :global(*) {
			position: absolute;
		}
	}

	.front {
		border: var(--border);
		width: 100%;
		height: 100%;
		display: grid;
		font-weight: bold;
		place-content: center;
	}

	.rear-lid {
		border-top: var(--border);
		background: var(--color-bg);
		width: 100%;
		height: var(--height);
		translate: 0 -100%;
		z-index: -1;
	}

	.progress {
		border: var(--border);
		display: grid;
		align-items: center;

		> * {
			grid-area: 1 / -1;
		}

		.bar {
			height: 100%;
			background: var(--color-text-1);
			transition: width 0.1s ease-out;
		}

		.value {
			padding-left: 0.5rem;
			font-weight: 300;
			letter-spacing: 0.05em;
			mix-blend-mode: difference;
		}
	}
	
	.confetti-container {
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%);
		width: 100px;
		height: 20px;
		pointer-events: none;
		z-index: 100;
	}
</style>