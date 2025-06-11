<script lang="ts">
  interface Props {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    fullWidth?: boolean;
    glowing?: boolean;
    type?: 'button' | 'submit' | 'reset';
    onclick?: () => void;
    children?: any;
  }

  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    fullWidth = false,
    glowing = false,
    type = 'button',
    onclick,
    children
  }: Props = $props();

  const isDisabled = $derived(disabled || loading);
</script>

<button
  {type}
  class="btn btn-{variant} btn-{size}"
  class:btn-full={fullWidth}
  class:btn-loading={loading}
  class:btn-glow={glowing && !isDisabled}
  disabled={isDisabled}
  onclick={onclick}
>
  {#if loading}
    <div class="btn-spinner">
      <div class="spinner-ring"></div>
    </div>
  {/if}
  <span class="btn-content" class:btn-content-hidden={loading}>
    {@render children?.()}
  </span>
</button>

<style>
  .btn {
    /* Base button styles */
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    font-weight: var(--font-weight-medium);
    text-decoration: none;
    border: 1px solid transparent;
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: all var(--transition-base);
    font-family: inherit;
    line-height: 1;
    white-space: nowrap;
    background: transparent;
    overflow: hidden;
    
    /* Subtle background gradient */
    background-image: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.05) 100%);
    
    /* Focus styles */
    &:focus-visible {
      outline: 2px solid var(--color-primary);
      outline-offset: 2px;
    }
    
    /* Disabled styles */
    &:disabled {
      cursor: not-allowed;
      opacity: 0.5;
      pointer-events: none;
    }
    
    /* Hover effect overlay */
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 100%);
      opacity: 0;
      transition: opacity var(--transition-fast);
    }
    
    &:hover:not(:disabled)::before {
      opacity: 1;
    }
  }

  /* Size variants */
  .btn-sm {
    padding: var(--space-2) var(--space-4);
    font-size: var(--font-size-sm);
    min-height: 2.25rem;
  }

  .btn-md {
    padding: var(--space-3) var(--space-6);
    font-size: var(--font-size-base);
    min-height: 2.75rem;
  }

  .btn-lg {
    padding: var(--space-4) var(--space-8);
    font-size: var(--font-size-lg);
    min-height: 3.25rem;
  }

  /* Style variants */
  .btn-primary {
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-blue-primary) 100%);
    color: var(--color-text-primary);
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    
    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: var(--shadow-lg), 0 0 20px rgba(0, 212, 255, 0.4);
    }
  }

  .btn-secondary {
    background: var(--color-bg-secondary);
    color: var(--color-text-primary);
    border-color: var(--color-border);
    
    &:hover:not(:disabled) {
      background: var(--color-bg-tertiary);
      border-color: var(--color-border-hover);
    }
  }

  .btn-outline {
    background: transparent;
    color: var(--color-primary);
    border-color: var(--color-primary);
    
    &:hover:not(:disabled) {
      background: var(--color-primary);
      color: var(--color-text-primary);
      box-shadow: var(--shadow-cyan);
    }
  }

  .btn-ghost {
    background: transparent;
    color: var(--color-text-secondary);
    border-color: transparent;
    
    &:hover:not(:disabled) {
      background: var(--color-bg-card);
      color: var(--color-text-primary);
    }
  }

  .btn-danger {
    background: linear-gradient(135deg, var(--color-error) 0%, #dc2626 100%);
    color: var(--color-text-primary);
    border-color: var(--color-error);
    
    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: var(--shadow-lg), 0 0 20px rgba(239, 68, 68, 0.4);
    }
  }

  .btn-success {
    background: linear-gradient(135deg, var(--color-success) 0%, #059669 100%);
    color: var(--color-text-primary);
    border-color: var(--color-success);
    
    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: var(--shadow-lg), 0 0 20px rgba(16, 185, 129, 0.4);
    }
  }

  /* Full width */
  .btn-full {
    width: 100%;
  }

  /* Glowing effect */
  .btn-glow {
    animation: var(--animation-glow);
  }

  /* Loading state */
  .btn-loading {
    pointer-events: none;
  }

  .btn-content {
    transition: opacity var(--transition-fast);
  }

  .btn-content-hidden {
    opacity: 0;
  }

  .btn-spinner {
    position: absolute;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .spinner-ring {
    width: 1.25rem;
    height: 1.25rem;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: var(--animation-spin);
  }

  /* Enhanced interaction feedback */
  .btn:active:not(:disabled) {
    transform: translateY(0);
    transition: transform 0.05s ease;
  }
</style>