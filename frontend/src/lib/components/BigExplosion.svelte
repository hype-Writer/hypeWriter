<script>
	import { Confetti } from 'svelte-confetti';

	let { show = false } = $props();
</script>

{#if show}
	<div class="big-explosion">
		<!-- Multiple confetti bursts for bigger effect -->

		<Confetti
			noGravity
			amount="300"
			size="25"
			x={[-3, 3]}
			y={[-3, 3]}
			delay={[0, 550]}
			duration="550"
			rounded
			colorArray={['#a8e0d8', '#f0f5c0', '#f0c8e8', '#7cc5e8']}
		/>
		<Confetti
			noGravity
			amount="200"
			size="15"
			x={[-3, 3]}
			y={[-2.5, 2.5]}
			delay={[150, 750]}
			duration="750"
			rounded
			colorArray={['#a8e0d8', '#f0f5c0', '#f0c8e8', '#7cc5e8']}
		/>
		<Confetti
			noGravity
			amount="300"
			size="15"
			x={[-3, 3]}
			y={[-2, 2]}
			delay={[200, 1050]}
			duration="1200"
			rounded
			colorArray={['#40E7F6', '#00A1D3', '#91F2FF', '#A4DAE3']}
		/>
	</div>
{/if}

<style>
	.big-explosion {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 200px;
		height: 200px;
		pointer-events: none;
		z-index: 1000;
	}
</style>