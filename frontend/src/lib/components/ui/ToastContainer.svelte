<script>
	import { toastStore } from '../../stores/toastStore.ts';
	import Toast from './Toast.svelte';
	
	let toasts = $state([]);
	
	// Subscribe to toast store
	toastStore.subscribe((newToasts) => {
		toasts = newToasts;
	});
	
	function removeToast(id) {
		toastStore.remove(id);
	}
</script>

<div class="toast-container">
	{#each toasts as toast (toast.id)}
		<Toast
			message={toast.message}
			type={toast.type}
			duration={toast.duration}
			onClose={() => removeToast(toast.id)}
		/>
	{/each}
</div>

<style>
	.toast-container {
		position: fixed;
		bottom: var(--space-6);
		right: var(--space-6);
		z-index: 1000;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		pointer-events: none;
	}
	
	.toast-container > :global(*) {
		pointer-events: auto;
	}
	
	@media (max-width: 640px) {
		.toast-container {
			bottom: var(--space-4);
			right: var(--space-4);
			left: var(--space-4);
		}
		
		.toast-container > :global(.toast) {
			min-width: unset;
			max-width: unset;
		}
	}
</style>