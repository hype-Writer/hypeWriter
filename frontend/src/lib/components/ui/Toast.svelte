<script>
	import { fade, fly } from 'svelte/transition';
	
	let { 
		message = '',
		type = 'info',
		duration = 4000,
		onClose = () => {}
	} = $props();
	
	let visible = $state(true);
	let timeoutId;
	
	// Auto-dismiss after duration
	if (duration > 0) {
		timeoutId = setTimeout(() => {
			dismiss();
		}, duration);
	}
	
	function dismiss() {
		visible = false;
		clearTimeout(timeoutId);
		// Wait for transition to complete before calling onClose
		setTimeout(onClose, 300);
	}
	
	function handleKeydown(event) {
		if (event.key === 'Escape') {
			dismiss();
		}
	}
</script>

{#if visible}
	<div 
		class="toast toast-{type}"
		transition:fly={{ y: -50, duration: 300 }}
		role="alert"
		aria-live="polite"
		tabindex="0"
		onkeydown={handleKeydown}
	>
		<div class="toast-content">
			<div class="toast-icon">
				{#if type === 'success'}
					<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
					</svg>
				{:else if type === 'error'}
					<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
					</svg>
				{:else if type === 'warning'}
					<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
					</svg>
				{:else}
					<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
					</svg>
				{/if}
			</div>
			<div class="toast-message">{message}</div>
		</div>
		<button class="toast-close" onclick={dismiss} aria-label="Close notification">
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M4.646 4.646a.5.5 0 01.708 0L8 7.293l2.646-2.647a.5.5 0 01.708.708L8.707 8l2.647 2.646a.5.5 0 01-.708.708L8 8.707l-2.646 2.647a.5.5 0 01-.708-.708L7.293 8 4.646 5.354a.5.5 0 010-.708z"/>
			</svg>
		</button>
	</div>
{/if}

<style>
	.toast {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-width: 320px;
		max-width: 480px;
		padding: var(--space-4);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		border: 1px solid;
		backdrop-filter: blur(10px);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
	}
	
	.toast-info {
		background: rgba(26, 35, 50, 0.95);
		border-color: var(--color-cyan-bright);
		color: var(--color-text-primary);
		box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
	}
	
	.toast-success {
		background: rgba(16, 185, 129, 0.1);
		border-color: var(--color-success);
		color: var(--color-success);
		box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
	}
	
	.toast-error {
		background: rgba(239, 68, 68, 0.1);
		border-color: var(--color-error);
		color: var(--color-error);
		box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
	}
	
	.toast-warning {
		background: rgba(245, 158, 11, 0.1);
		border-color: var(--color-warning);
		color: var(--color-warning);
		box-shadow: 0 0 20px rgba(245, 158, 11, 0.2);
	}
	
	.toast-content {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		flex: 1;
	}
	
	.toast-icon {
		flex-shrink: 0;
		display: flex;
		align-items: center;
	}
	
	.toast-message {
		flex: 1;
		line-height: 1.4;
	}
	
	.toast-close {
		flex-shrink: 0;
		background: none;
		border: none;
		color: inherit;
		cursor: pointer;
		padding: var(--space-1);
		border-radius: var(--radius-sm);
		opacity: 0.7;
		transition: opacity var(--transition-fast);
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.toast-close:hover {
		opacity: 1;
		background: rgba(255, 255, 255, 0.1);
	}
	
	.toast-close:focus-visible {
		outline: 2px solid currentColor;
		outline-offset: 2px;
	}
</style>