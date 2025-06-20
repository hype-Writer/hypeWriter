<script lang="ts">
	import type { Coordinate } from '../coordinate';
	import { gridSize } from '../settings';
	import { refinery, viewport, selectedCells } from '../refinery.svelte';
	import DataCell from './DataCell.svelte';

	let cells = $state([]);

	let cursor: Coordinate = $state({ x: 0, y: 0 });

	$effect(() => {
		cells = Array.from({ length: gridSize[0] * gridSize[1] });
	});

	function pan(direction: string) {
		let x = 0;
		let y = 0;

		if (direction === 'Right') x = -1;
		if (direction === 'Left') x = 1;
		if (direction === 'Up') y = 1;
		if (direction === 'Down') y = -1;

		refinery.send('panViewport', { x, y });
	}

	function zoom(key: string) {
		let zoom = 0;
		if (['=', '+'].includes(key)) zoom = 1;
		if (['-', '_'].includes(key)) zoom = -1;
		refinery.send('zoomViewport', zoom);
	}

	function handleKeyUp({ key }: KeyboardEvent) {
		if (key === 'Escape') refinery.send('clearCells');
		if (key.startsWith('Arrow')) pan(key.replace('Arrow', ''));
		if (['=', '+', '-', '_', '0'].includes(key)) zoom(key);
	}

	function handlePointerMove(event: PointerEvent) {
		cursor.x = event.clientX;
		cursor.y = event.clientY;
	}
</script>

<svelte:document onkeyup={handleKeyUp} onpointerdowncapture={() => selectedCells.clear()} />

<section
	style:--cols={gridSize[0]}
	style:--x="{viewport.x}px"
	style:--y="{viewport.y}px"
	style:--scale={viewport.scale}
	onpointermove={handlePointerMove}
	onpointerdown={(e) => refinery.send('selectCell', e)}
	onpointerover={(e) => refinery.send('selectCell', e)}
>
	<div class="inner">
		{#each cells as _, index}
			<DataCell {index} {cursor} selected={selectedCells.has(index)} />
		{/each}
	</div>
</section>

<style>
	section {
		border-block: var(--border);
		margin-block: 6px;
		display: grid;
		place-content: center;
		overflow: hidden;
		user-select: none;
		-webkit-user-select: none;
		pointer-events: none;
	}

	.inner {
		display: grid;
		grid-template-columns: repeat(var(--cols), 1fr);
		transform: scale(var(--scale)) translate(var(--x), var(--y));
		transition: transform 0.4s ease-out;
	}
</style>