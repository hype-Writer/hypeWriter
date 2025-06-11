<script lang="ts">
  import Button from '../ui/Button.svelte';
  import Card from '../ui/Card.svelte';

  // Props
  let { onClose, onProjectCreated }: { 
    onClose: () => void;
    onProjectCreated?: (project: any) => void;
  } = $props();

  let formData = $state({
    title: '',
    author: '',
    genre: '',
    description: ''
  });

  let isSubmitting = $state(false);
  let formErrors = $state<Record<string, string>>({});

  function validateForm() {
    formErrors = {};
    
    if (!formData.title.trim()) {
      formErrors.title = 'Title is required';
    }
    
    if (!formData.author.trim()) {
      formErrors.author = 'Author is required';
    }
    
    return Object.keys(formErrors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;
    
    isSubmitting = true;
    
    try {
      const response = await fetch('/api/library/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const project = await response.json();
      resetForm();
      
      if (onProjectCreated) {
        onProjectCreated(project);
      } else {
        onClose();
      }
    } catch (error) {
      console.error('Failed to create project:', error);
      alert('Failed to create project. Please try again.');
    } finally {
      isSubmitting = false;
    }
  }

  function resetForm() {
    formData = {
      title: '',
      author: '',
      genre: '',
      description: ''
    };
    formErrors = {};
  }

  function handleClose() {
    onClose();
    resetForm();
  }

  // Genre suggestions
  const genreSuggestions = [
    'Science Fiction', 'Fantasy', 'Mystery', 'Romance', 'Thriller', 
    'Horror', 'Historical Fiction', 'Contemporary Fiction', 'Young Adult',
    'Literary Fiction', 'Adventure', 'Crime', 'Dystopian', 'Memoir'
  ];
</script>

  <div 
    class="modal-overlay" 
    role="dialog" 
    aria-modal="true"
    onclick={handleClose}
    onkeydown={(e) => e.key === 'Escape' && handleClose()}
  >
    <div 
      class="modal-container" 
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.stopPropagation()}
    >
      <Card variant="highlighted" padding="lg">
        <form class="create-form" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <div class="modal-header">
            <h2 class="modal-title">Create New Project</h2>
            <button 
              type="button" 
              class="close-button"
              onclick={handleClose}
              aria-label="Close modal"
            >
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>

          <div class="form-fields">
            <div class="field-group">
              <label for="title" class="field-label">Project Title *</label>
              <input
                id="title"
                type="text"
                class="field-input"
                class:field-error={formErrors.title}
                bind:value={formData.title}
                placeholder="Enter your book title"
                required
              />
              {#if formErrors.title}
                <span class="error-message">{formErrors.title}</span>
              {/if}
            </div>

            <div class="field-group">
              <label for="author" class="field-label">Author *</label>
              <input
                id="author"
                type="text"
                class="field-input"
                class:field-error={formErrors.author}
                bind:value={formData.author}
                placeholder="Your name"
                required
              />
              {#if formErrors.author}
                <span class="error-message">{formErrors.author}</span>
              {/if}
            </div>

            <div class="field-group">
              <label for="genre" class="field-label">Genre</label>
              <select
                id="genre"
                class="field-input"
                bind:value={formData.genre}
              >
                <option value="">Select a genre (optional)</option>
                {#each genreSuggestions as genre}
                  <option value={genre}>{genre}</option>
                {/each}
              </select>
            </div>

            <div class="field-group">
              <label for="description" class="field-label">Description</label>
              <textarea
                id="description"
                class="field-input field-textarea"
                bind:value={formData.description}
                placeholder="Brief description of your book (optional)"
                rows="3"
              ></textarea>
            </div>
          </div>

          <div class="modal-actions">
            <Button variant="ghost" onclick={handleClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="primary" 
              loading={isSubmitting}
              disabled={isSubmitting}
            >
              Create Project
            </Button>
          </div>
        </form>
      </Card>
    </div>
  </div>

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: var(--space-4);
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
  }

  .modal-container {
    width: 100%;
    max-width: 32rem;
    max-height: 90vh;
    overflow-y: auto;
    animation: slideInUp 0.3s ease;
  }

  .create-form {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .modal-title {
    font-size: var(--font-size-2xl);
    color: var(--color-text-accent);
    margin: 0;
  }

  .close-button {
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--space-2);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-button:hover {
    color: var(--color-text-primary);
    background: var(--color-bg-tertiary);
  }

  .close-button svg {
    width: 1.25rem;
    height: 1.25rem;
  }

  .form-fields {
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
  }

  .field-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .field-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-primary);
  }

  .field-input {
    padding: var(--space-3) var(--space-4);
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    color: var(--color-text-primary);
    font-size: var(--font-size-base);
    transition: all var(--transition-fast);
    font-family: inherit;
  }

  .field-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
  }

  .field-input::placeholder {
    color: var(--color-text-muted);
  }

  .field-textarea {
    resize: vertical;
    min-height: 4rem;
  }

  .field-error {
    border-color: var(--color-error);
  }

  .error-message {
    font-size: var(--font-size-sm);
    color: var(--color-error);
  }

  .modal-actions {
    display: flex;
    gap: var(--space-3);
    justify-content: flex-end;
    padding-top: var(--space-4);
    border-top: 1px solid var(--color-border);
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes slideInUp {
    from {
      opacity: 0;
      transform: translateY(2rem) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @media (max-width: 768px) {
    .modal-container {
      max-width: 100%;
      margin: var(--space-4);
    }

    .modal-actions {
      flex-direction: column-reverse;
    }
  }
</style>