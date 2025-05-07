<script lang="ts">
	// Define an interface for chat messages if you plan to integrate chat later
	interface ChatMessage {
		role: 'user' | 'assistant';
		content: string;
	}

	let { chapter } = $props<{
		chapter_number: number;
		title: string;
		prompt: string;
		content?: string; // content might exist if already generated
	}>();

	let isLoading = $state(false);
	let error = $state('');

	async function handleGenerateChapter() {
		isLoading = true;
		error = ''; // Clear previous errors

		try {
			// We need to collect additional context here eventually, perhaps from a chat history state
			// For now, sending an empty string placeholder to match the backend model
			const additionalContext = ''; // Placeholder for now

			const response = await fetch(`/chapter/${chapter.chapter_number}`, {
				// Corrected endpoint based on backend route
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					chapter_number: chapter.chapter_number,
					additional_context: additionalContext // Include additional context (placeholder)
				})
			});

			if (!response.ok) {
				const errorText = await response.text(); // Read error response body for more detail
				throw new Error(
					`Failed to generate chapter: ${response.status} ${response.statusText} - ${errorText}`
				);
			}

			const result = await response.json();
			chapter.content = result.chapter_content; // Update content prop with generated content
			console.log('Chapter generated. Snippet:', result.chapter_content.slice(0, 100) + '...'); // Log snippet for confirmation
		} catch (err: unknown) {
			// Explicitly type err as unknown for safety
			console.error('Generation error:', err);
			if (err instanceof Error) {
				error = err.message;
			} else {
				error = 'An unknown error occurred during generation.';
			}
		} finally {
			isLoading = false;
		}
	}

	// Function to save chapter content (adapted from chapter.html JS)
	async function handleSaveChapter() {
		// Assuming chapter.content holds the current editable content
		if (chapter.content === undefined || chapter.content === null) {
			console.warn('No content to save.');
			return;
		}

		// Optional: Add saving state indicator
		// let isSaving = $state(false);
		// isSaving = true;

		try {
			const response = await fetch(`/save_chapter/${chapter.chapter_number}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ chapter_content: chapter.content })
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(
					`Failed to save chapter: ${response.status} ${response.statusText} - ${errorText}`
				);
			}

			console.log('Chapter saved successfully!');
			// Optional: Show a temporary success message in the UI
			// Need a state variable for save success message
		} catch (err: unknown) {
			console.error('Save error:', err);
			if (err instanceof Error) {
				// Need a state variable for save error message
				console.error('Save failed:', err.message);
			} else {
				console.error('An unknown error occurred during saving.');
			}
		} // finally { isSaving = false; }
	}
</script>

<div class="card h-100">
	<div class="card-body">
		<h4 class="h6 card-title">
			Chapter {chapter.chapter_number}: {chapter.title}
		</h4>

		{#if !chapter.content}
			<!-- Display prompt snippet and Generate button if content doesn't exist -->
			<p class="card-text small">
				{#if chapter.prompt.length > 100}
					{chapter.prompt.slice(0, 100)}...
				{:else}
					{chapter.prompt}
				{/if}
			</p>

			<button class="btn btn-sm btn-primary" onclick={handleGenerateChapter} disabled={isLoading}>
				{#if isLoading}
					Generating...
				{:else}
					Generate Chapter
				{/if}
			</button>

			{#if isLoading}
				<div class="alert alert-info mt-2" role="status">
					<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
					Generating chapter content...
				</div>
			{/if}

			{#if error}
				<div class="alert alert-danger mt-2">
					Error: {error}
				</div>
			{/if}
		{:else}
			<!-- Display content area and Save/Regenerate buttons if content exists -->
			<p class="card-text small text-muted mb-3">
				Outline: {#if chapter.prompt.length > 100}{chapter.prompt.slice(
						0,
						100
					)}...{:else}{chapter.prompt}{/if}
			</p>

			<div class="mb-3">
				<label for="chapterContent_{chapter.chapter_number}" class="form-label"
					>Chapter Content:</label
				>
				<textarea
					id="chapterContent_{chapter.chapter_number}"
					class="form-control"
					bind:value={chapter.content}
					rows="20"
				></textarea>
			</div>

			<div class="d-flex justify-content-between">
				<button class="btn btn-success" onclick={handleSaveChapter}>Save Chapter</button>
				<button class="btn btn-warning" onclick={handleGenerateChapter} disabled={isLoading}>
					{#if isLoading}
						Regenerating...
					{:else}
						Regenerate Chapter
					{/if}
				</button>
				<!-- Navigation buttons (Next/Previous) will need to be added back, perhaps outside this conditional block or managed differently -->
			</div>

			{#if isLoading}
				<div class="alert alert-info mt-2" role="status">
					<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
					Regenerating chapter content...
				</div>
			{/if}

			{#if error}
				<div class="alert alert-danger mt-2">
					Error: {error}
				</div>
			{/if}
		{/if}

		<!-- Removed the old navigation link here -->
		<!--
		<a href="/chapter/{chapter.chapter_number}" class="btn btn-sm btn-outline-primary">
			{#if chapter.chapter_number === 1}
				Start Writing
			{:else}
				Write This Chapter
			{/if}
		</a>
		-->
	</div>
</div>
