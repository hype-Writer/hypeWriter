<script lang="ts">
  // Import theme
  import './lib/styles/theme.css';
  
  // Import pages
  import Dashboard from './lib/pages/Dashboard.svelte';
  import World from './lib/pages/world.svelte';
  import Characters from './lib/pages/characters.svelte';
  import Outline from './lib/pages/outline.svelte';
  import Chapters from './lib/pages/chapters.svelte';
  import ToastContainer from './lib/components/ui/ToastContainer.svelte';
  
  // Import MDR components
  import Header from './lib/components/Header.svelte';
  import DataField from './lib/components/DataField.svelte';
  import Bins from './lib/components/Bins.svelte';
  import Footer from './lib/components/Footer.svelte';
  import BigExplosion from './lib/components/BigExplosion.svelte';
  import DashboardOverlay from './lib/components/DashboardOverlay.svelte';
  import { binManager, percentComplete } from './lib/refinery.svelte';
  import cursorUrl from './lib/assets/cursor.svg';

  const cursor = `url("${cursorUrl}"), default`;
  
  let showBigExplosion = $state(false);
  let hasTriggeredBigExplosion = $state(false);

  // MDR explosion logic
  $effect(() => {
    if (binManager.percentComplete >= 1 && !hasTriggeredBigExplosion) {
      hasTriggeredBigExplosion = true;
      
      setTimeout(() => {
        showBigExplosion = true;
        
        setTimeout(() => {
          binManager.resetAllBins();
          percentComplete.target = 0;
          hasTriggeredBigExplosion = false;
        }, 1000);
        
        setTimeout(() => {
          showBigExplosion = false;
        }, 2000);
        
      }, 2200);
    }
  });


  // Simple client-side routing
  let currentPath = $state(window.location.pathname);

  function handleNavigation() {
    currentPath = window.location.pathname;
  }

  window.addEventListener('popstate', handleNavigation);

</script>

<div class="mdr-background" style:cursor={cursor}>
  <main>
    <Header />
    
    <!-- DataField with hypeWriter overlay -->
    <div class="datafield-container">
      <DataField />
      
      <!-- Show current page content over MDR background -->
      {#if currentPath === '/' || currentPath === ''}
        <DashboardOverlay />
      {:else}
        <div class="page-overlay">
          {#if currentPath === '/world'}
            <World />
          {:else if currentPath === '/characters'}
            <Characters />
          {:else if currentPath === '/outline'}
            <Outline />
          {:else if currentPath === '/chapters'}
            <Chapters />
          {/if}
        </div>
      {/if}
    </div>
    
    <Bins />
    <Footer />
  </main>

  <BigExplosion show={showBigExplosion} />
  <ToastContainer />
</div>

<style>
  .mdr-background {
    width: 100%;
    height: 100vh;
    position: relative;
  }

  main {
    height: 100vh;
    display: grid;
    grid-template-rows: 9rem 1fr 8rem 4rem;
    --border: 3px solid var(--color-text-1);
  }

  .datafield-container {
    position: relative;
    overflow: hidden;
  }

  .page-overlay {
    position: absolute;
    inset: 0;
    background: transparent;
    z-index: 1;
    overflow-y: auto;
  }

</style>