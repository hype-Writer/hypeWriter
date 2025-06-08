<script lang="ts">
  import { onMount } from 'svelte';
  
  // Import theme
  import './lib/styles/theme.css';
  
  // Import pages
  import Dashboard from './lib/pages/Dashboard.svelte';
  import Navigation from './lib/components/navigation.svelte';
  import Home from './lib/pages/home.svelte';
  import World from './lib/pages/world.svelte';
  import Characters from './lib/pages/characters.svelte';
  import Outline from './lib/pages/outline.svelte';
  import Chapters from './lib/pages/chapters.svelte';

  // Simple reactive state for routing
  let currentRoute = $state(window.location.pathname);

  onMount(() => {
    // Listen for route changes
    const handlePopState = () => {
      currentRoute = window.location.pathname;
    };
    
    window.addEventListener('popstate', handlePopState);
    
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  });

  // Route matching using Svelte 5 derived
  const isNewDashboard = $derived(currentRoute === '/' || currentRoute === '/dashboard');
  const isLegacyRoute = $derived(['/world', '/characters', '/outline', '/chapters'].includes(currentRoute));
  const isProjectRoute = $derived(currentRoute.startsWith('/project/'));
</script>

<!-- Always show navigation for legacy routes -->
{#if isLegacyRoute}
  <Navigation />
{/if}

<main class="app-main" class:with-nav={isLegacyRoute}>
  {#if isNewDashboard}
    <!-- New Dashboard -->
    <Dashboard />
  {:else if isLegacyRoute}
    <!-- Legacy routes (keeping for now during transition) -->
    {#if currentRoute === '/world'}
      <World />
    {:else if currentRoute === '/characters'}
      <Characters />
    {:else if currentRoute === '/outline'}
      <Outline />
    {:else if currentRoute === '/chapters'}
      <Chapters />
    {/if}
  {:else if isProjectRoute}
    <!-- Project-specific routes (to be implemented) -->
    <div class="project-view">
      <h1>Project View</h1>
      <p>Project route: {currentRoute}</p>
      <p>This will show the specific project interface.</p>
    </div>
  {:else}
    <!-- 404 or unknown route -->
    <div class="not-found">
      <h1>Page Not Found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <button onclick={() => { window.history.pushState({}, '', '/'); currentRoute = '/'; }}>
        Go to Dashboard
      </button>
    </div>
  {/if}
</main>

<style>
  .app-main {
    min-height: 100vh;
  }

  .app-main.with-nav {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .project-view {
    padding: var(--space-8);
    max-width: 1200px;
    margin: 0 auto;
    text-align: center;
    color: var(--color-text-primary);
  }

  .project-view h1 {
    color: var(--color-text-accent);
    margin-bottom: var(--space-4);
  }

  .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: var(--space-8);
    text-align: center;
    color: var(--color-text-primary);
  }

  .not-found h1 {
    color: var(--color-text-accent);
    margin-bottom: var(--space-4);
  }

  .not-found p {
    color: var(--color-text-secondary);
    margin-bottom: var(--space-6);
  }

  .not-found button {
    padding: var(--space-3) var(--space-6);
    background: var(--color-primary);
    color: var(--color-text-primary);
    border: none;
    border-radius: var(--radius-lg);
    cursor: pointer;
    font-size: var(--font-size-base);
    transition: all var(--transition-base);
  }

  .not-found button:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
  }
</style>