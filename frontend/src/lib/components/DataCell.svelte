<script lang="ts">
	import type { Coordinate } from '../coordinate';
	import { type TransitionConfig, fade } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { cursorRadius, maxScale, selectedScale } from '../settings';
	import { randomInt } from '../random';
	import { getNodeMidpoint, getDistance, getNodeDistance, scaleDistance } from '../distance';
	import { refinery, viewport, binManager } from '../refinery.svelte';

	interface CellInfo {
		value: number;
		range: number;
		duration: number;
		axis: 'x' | 'y';
	}

	interface Props {
		index: number;
		cursor: Coordinate;
		selected: boolean;
	}

	let { index, cursor, selected }: Props = $props();

	let element: HTMLDivElement | undefined = $state();

	let cellInfo: CellInfo | undefined = $state();

	let sendingToBin = $derived(selected && refinery.current === 'fillingBin');

	let scale = $derived.by(() => {
		if (!element) return 1;
		if (selected) return selectedScale;

		const { magnitude } = getDistance(cursor, getNodeMidpoint(element));
		if (magnitude > cursorRadius) return 1;

		// calculate ratio to scale by (between 0 and 1)
		const scaleRatio = (cursorRadius - magnitude) / cursorRadius;

		// apply scaleRatio up to maxScale
		return 1 + (maxScale - 1) * scaleRatio;
	});

	// initialize empty cell values (on initial load or after binning completes)
	$effect(() => {
		if (refinery.current === 'ready' && !cellInfo) setCellInfo();
	});

	function setCellInfo() {
		setTimeout(() => {
			cellInfo = {
				value: randomInt(0, 9),
				range: Math.random() * 15,
				duration: randomInt(3000, 10000),
				axis: randomInt(0, 1) ? 'x' : 'y'
			};
		});
	}

	function handleOutroEnd() {
		refinery.send('addToBin', index);
		cellInfo = undefined;
	}

	function funnelToBin(node: HTMLElement): TransitionConfig {
		if (!binManager.selectedBin) return {};

		const distance = getNodeDistance(node, binManager.selectedBin);
		const { dx, dy } = scaleDistance(distance, viewport.scale);

		return {
			duration: distance.magnitude * 1.25,
			css: (_, u) => `translate: ${dx * cubicOut(u)}px ${dy * u}px`
		};
	}
</script>

<div bind:this={element} class="data-cell" data-index={index}>
	{#if cellInfo && !sendingToBin}
		{@const { value, axis, range, duration } = cellInfo}
		<div
			class={['inner', axis]}
			style:--range="{range}%"
			style:--duration="{duration}ms"
			style:--number-scale={scale}
			onoutroend={handleOutroEnd}
			in:fade={{ duration: duration / 2 }}
			out:funnelToBin
		>
			{value}
		</div>
	{/if}
</div>

<style>
	div {
		display: grid;
	}

	.data-cell {
		width: 5rem;
		height: 5rem;
		pointer-events: auto;
	}

	.inner {
		place-content: center;
		font-size: 1.25rem;
		font-weight: 300;
		pointer-events: none;
		scale: var(--number-scale);
		transition: scale 0.5s ease-out;
		animation: var(--duration) infinite wiggle alternate linear;

		&.x {
			--translate-from: calc(-1 * var(--range));
			--translate-to: var(--range);
		}

		&.y {
			--translate-from: 0 calc(-1 * var(--range));
			--translate-to: 0 var(--range);
		}
	}

	@keyframes wiggle {
		from {
			translate: var(--translate-from);
		}
		to {
			translate: var(--translate-to);
		}
	}
</style>