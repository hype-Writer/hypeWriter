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
		content?: string;
	}>();

	let isLoading = $state(false);
	let error = $state('');
	
	// TTS related state
	let isTtsLoading = $state(false);
	let ttsError = $state('');
	let availableVoices = $state<Array<{id: string, name: string}>>([]);
	let selectedVoice = $state('bf_emma');
	let audioUrl = $state<string | null>(null);
	let ttsStatus = $state<'available' | 'unavailable' | 'checking'>('checking');

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

	// TTS Functions
	async function checkTtsStatus() {
		try {
			const response = await fetch('/api/tts/status');
			const result = await response.json();
			ttsStatus = result.status === 'available' ? 'available' : 'unavailable';
			
			if (ttsStatus === 'available') {
				await loadVoices();
			}
		} catch (err) {
			console.error('TTS status check failed:', err);
			ttsStatus = 'unavailable';
		}
	}

	async function loadVoices() {
		try {
			const response = await fetch('/api/tts/voices');
			const result = await response.json();
			
			if (result.error) {
				console.error('Failed to load voices:', result.error);
				return;
			}
			
			// Convert voices to format expected by dropdown
			availableVoices = Object.entries(result.voices || {}).map(([id, name]) => ({
				id,
				name: name as string
			}));
		} catch (err) {
			console.error('Failed to load voices:', err);
		}
	}

	async function handleReadChapter() {
		if (!chapter.content || chapter.content.trim() === '') {
			ttsError = 'No chapter content to read. Please generate content first.';
			return;
		}

		isTtsLoading = true;
		ttsError = '';
		audioUrl = null;

		try {
			const response = await fetch(`/api/tts/chapter/${chapter.chapter_number}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					chapter_number: chapter.chapter_number,
					voice: selectedVoice,
					response_format: 'mp3'
				})
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to generate audio: ${response.status} ${response.statusText} - ${errorText}`);
			}

			const result = await response.json();
			
			if (result.success) {
				// Create audio URL for the generated file
				audioUrl = `/static/chapters/chapter_${chapter.chapter_number}.mp3?t=${Date.now()}`;
				console.log('Chapter audio generated successfully:', result.filename);
			} else {
				throw new Error(result.error || 'Failed to generate audio');
			}
		} catch (err: unknown) {
			console.error('TTS generation error:', err);
			if (err instanceof Error) {
				ttsError = err.message;
			} else {
				ttsError = 'An unknown error occurred during audio generation.';
			}
		} finally {
			isTtsLoading = false;
		}
	}

	// Check TTS status on component mount
	$effect(() => {
		checkTtsStatus();
	});
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

			<div class="d-flex justify-content-between mb-3">
				<button class="btn btn-success" onclick={handleSaveChapter}>Save Chapter</button>
				<button class="btn btn-warning" onclick={handleGenerateChapter} disabled={isLoading}>
					{#if isLoading}
						Regenerating...
					{:else}
						Regenerate Chapter
					{/if}
				</button>
			</div>

			<!-- TTS Controls -->
			{#if ttsStatus === 'available'}
				<div class="border rounded p-3 mb-3 bg-light">
					<h6>Text-to-Speech</h6>
					
					<div class="row align-items-center mb-2">
						<div class="col-md-6">
							<label for="voiceSelect_{chapter.chapter_number}" class="form-label small">Voice:</label>
							<select 
								id="voiceSelect_{chapter.chapter_number}"
								class="form-select form-select-sm" 
								bind:value={selectedVoice}
							>
								<option value="bf_emma">Emma (British Female)</option>
								{#each availableVoices as voice}
									<option value={voice.id}>{voice.name}</option>
								{/each}
							</select>
						</div>
						<div class="col-md-6">
							<label class="form-label small">&nbsp;</label>
							<div>
								<button 
									class="btn btn-primary btn-sm" 
									onclick={handleReadChapter} 
									disabled={isTtsLoading}
								>
									{#if isTtsLoading}
										<span class="spinner-border spinner-border-sm me-1"></span>
										Generating Audio...
									{:else}
										🔊 Read Chapter
									{/if}
								</button>
							</div>
						</div>
					</div>

					{#if audioUrl}
						<div class="mt-2">
							<audio controls class="w-100">
								<source src={audioUrl} type="audio/mpeg" />
								Your browser does not support the audio element.
							</audio>
						</div>
					{/if}

					{#if ttsError}
						<div class="alert alert-warning alert-sm mt-2">
							{ttsError}
						</div>
					{/if}
				</div>
			{:else if ttsStatus === 'unavailable'}
				<div class="alert alert-info">
					<small>TTS server unavailable. Start Kokoro-FastAPI to enable chapter reading.</small>
				</div>
			{:else}
				<div class="alert alert-secondary">
					<small>Checking TTS availability...</small>
				</div>
			{/if}

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
	</div>
</div>
