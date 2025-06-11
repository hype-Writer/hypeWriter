<script lang="ts">
  // Simple test component to verify overlay positioning
  import Dashboard from '../pages/Dashboard.svelte';
</script>

<div class="test-overlay">
  <div class="test-content">
    <div class="test-header">
      <h2>HypeWriter Test Overlay</h2>
      <p>This overlay sits on top of the MDR data field. Dashboard should be visible below:</p>
    </div>
    
    <div class="dashboard-container">
      <Dashboard />
    </div>
  </div>
</div>

<style>
  .test-overlay {
    position: absolute;
    inset: 0;
    background: rgba(26, 35, 50, 0.95); /* Semi-transparent dark background */
    backdrop-filter: blur(2px);
    padding: 2rem;
    overflow-y: auto;
    z-index: 1;
    border: 2px solid var(--color-cyan-bright, #00d4ff);
    border-radius: 8px;
    margin: 1rem;
  }

  .test-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .test-header {
    background: rgba(0, 212, 255, 0.1);
    padding: 1rem;
    border-radius: 4px;
    border: 1px solid var(--color-cyan-bright, #00d4ff);
  }

  .test-header h2 {
    color: var(--color-cyan-bright, #00d4ff);
    margin: 0 0 0.5rem 0;
    font-size: 1.2rem;
  }

  .test-header p {
    color: var(--color-text-1, #b3e5fc);
    margin: 0;
    font-size: 0.9rem;
  }

  .dashboard-container {
    flex: 1;
    overflow-y: auto;
    background: transparent;
  }
</style>