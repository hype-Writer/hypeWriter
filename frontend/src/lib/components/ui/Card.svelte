<script lang="ts">
  interface Props {
    variant?: 'default' | 'interactive' | 'highlighted' | 'journey';
    padding?: 'sm' | 'md' | 'lg' | 'none';
    glowing?: boolean;
    clickable?: boolean;
    completed?: boolean;
    progress?: number; // 0-100
    onclick?: () => void;
    children?: any;
  }

  let {
    variant = 'default',
    padding = 'md',
    glowing = false,
    clickable = false,
    completed = false,
    progress,
    onclick,
    children
  }: Props = $props();

  const isClickable = $derived(clickable || !!onclick);
</script>

{#if isClickable}
  <button
    type="button"
    class="card card-{variant} card-padding-{padding} card-clickable"
    class:card-glow={glowing}
    class:card-completed={completed}
    onclick={onclick}
  >
    {#if progress !== undefined}
      <div class="card-progress">
        <div class="card-progress-bar" style="width: {progress}%"></div>
      </div>
    {/if}
    
    {#if completed}
      <div class="card-completion-indicator">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
      </div>
    {/if}
    
    <div class="card-content">
      {@render children?.()}
    </div>
  </button>
{:else}
  <div
    class="card card-{variant} card-padding-{padding}"
    class:card-glow={glowing}
    class:card-completed={completed}
  >
    {#if progress !== undefined}
      <div class="card-progress">
        <div class="card-progress-bar" style="width: {progress}%"></div>
      </div>
    {/if}
    
    {#if completed}
      <div class="card-completion-indicator">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
      </div>
    {/if}
    
    <div class="card-content">
      {@render children?.()}
    </div>
  </div>
{/if}

<style>
  .card {
    position: relative;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-card);
    transition: all var(--transition-base);
    overflow: hidden;
    
    /* Subtle background gradient */
    background-image: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 100%);
    
    /* Glass morphism effect */
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  /* Padding variants */
  .card-padding-none {
    padding: 0;
  }

  .card-padding-sm {
    padding: var(--space-4);
  }

  .card-padding-md {
    padding: var(--space-6);
  }

  .card-padding-lg {
    padding: var(--space-8);
  }

  /* Card variants */
  .card-default {
    /* Default styling is in base .card */
  }

  .card-interactive {
    border-color: var(--color-border-hover);
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg), 0 0 25px rgba(0, 212, 255, 0.15);
      border-color: var(--color-primary);
    }
  }

  .card-highlighted {
    border-color: var(--color-primary);
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, var(--color-bg-card) 100%);
    box-shadow: var(--shadow-lg), var(--shadow-cyan);
  }

  .card-journey {
    border-color: var(--color-border-hover);
    background: linear-gradient(135deg, var(--color-bg-card) 0%, rgba(45, 55, 72, 0.6) 100%);
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: var(--shadow-xl), 0 0 30px rgba(0, 212, 255, 0.2);
      border-color: var(--color-primary);
    }
  }

  /* Clickable states */
  .card-clickable {
    cursor: pointer;
    user-select: none;
    
    &:focus-visible {
      outline: 2px solid var(--color-primary);
      outline-offset: 2px;
    }
    
    &:active {
      transform: translateY(0);
      transition: transform 0.05s ease;
    }
  }

  /* Completed state */
  .card-completed {
    border-color: var(--color-success);
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, var(--color-bg-card) 100%);
  }

  /* Glowing effect */
  .card-glow {
    animation: var(--animation-glow);
  }

  /* Progress bar */
  .card-progress {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: rgba(255, 255, 255, 0.1);
    overflow: hidden;
  }

  .card-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-success) 100%);
    transition: width var(--transition-slow);
    position: relative;
    
    /* Animated shine effect */
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%);
      animation: shine 2s infinite;
    }
  }

  @keyframes shine {
    0% { left: -100%; }
    100% { left: 100%; }
  }

  /* Completion indicator */
  .card-completion-indicator {
    position: absolute;
    top: var(--space-3);
    right: var(--space-3);
    width: 1.5rem;
    height: 1.5rem;
    background: var(--color-success);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: var(--shadow-md);
    
    svg {
      width: 1rem;
      height: 1rem;
    }
  }

  /* Content area */
  .card-content {
    position: relative;
    z-index: 1;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .card {
      border-radius: var(--radius-lg);
    }
    
    .card-padding-md {
      padding: var(--space-4);
    }
    
    .card-padding-lg {
      padding: var(--space-6);
    }
  }
</style>