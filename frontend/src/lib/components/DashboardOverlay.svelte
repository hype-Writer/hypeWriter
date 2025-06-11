<script lang="ts">
  import Dashboard from '../pages/Dashboard.svelte';
</script>

<div class="dashboard-overlay">
  <div class="dashboard-wrapper">
    <Dashboard />
  </div>
</div>

<style>
  .dashboard-overlay {
    position: absolute;
    inset: 0;
    background: transparent;
    padding: 2rem;
    overflow: hidden;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none; /* Allow clicks to pass through */
  }

  .dashboard-wrapper {
    width: 100%;
    max-width: 1400px;
    background: transparent;
    pointer-events: auto; /* But capture clicks on actual content */
    /* Allow scrolling if content is too tall */
    max-height: 90vh;
    overflow-y: auto;
  }
</style>