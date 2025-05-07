<script lang="ts">
	import Chat from '../components/chat.svelte';
	import type { Snippet } from 'svelte';

	interface ChatMessage {
		role: 'user' | 'assistant' | 'system';
		content: string;
		id?: number;
	}

	let { initial_world_theme = '', initial_topic = '' } = $props<{
		initial_world_theme?: string;
		initial_topic?: string;
	}>();

	let chatHistory = $state<ChatMessage[]>([]);
	let worldThemeTextarea = $state('');
	let topic = $state(initial_topic || '');
	let loadingInitialData = $state(true);
	let initialDataError = $state<string | null>(null);

	let savingIndicatorVisible = $state(false);
	let savedIndicatorVisible = $state(false);
	let saveError = $state<string | null>(null);
	let saveWorldButtonDisabled = $state(true);
	let isChatGenerating = $state(false); // State bound from Chat component

	// isFinalizing state removed, loading is now just isChatGenerating (bound from Chat)

	// isFinalizeButtonDisabled depends on chat history, loading, and isChatGenerating
	let isFinalizeButtonDisabled = $derived(
		chatHistory.filter((msg) => msg.role === 'user').length === 0 ||
			loadingInitialData ||
			isChatGenerating
	);

	let isEditingMode = $derived(!loadingInitialData && worldThemeTextarea.length > 0);
	let worldThemeTextareaElement: HTMLTextAreaElement;

	const initialChatPromptText =
		'Tell me about the world you want to create for your book. What kind of setting, time period, or genre are you interested in?';

	$effect(() => {
		async function loadInitialWorldData() {
			loadingInitialData = true;
			initialDataError = null;
			saveWorldButtonDisabled = true;

			try {
				const response = await fetch('/api/world');
				if (!response.ok) {
					const errorText = await response.text();
					throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
				}
				const data = await response.json();

				worldThemeTextarea = data.world_theme || initial_world_theme;
				topic = data.topic || initial_topic;

				if (worldThemeTextarea) {
					chatHistory = [
						{ role: 'system', content: 'Loaded existing World Setting:' },
						{ role: 'assistant', content: worldThemeTextarea }
					];
				} else {
					chatHistory = [{ role: 'assistant', content: initialChatPromptText }];
				}
			} catch (error: any) {
				console.error('Error loading initial world data:', error);
				initialDataError = `Failed to load initial data: ${error.message}`;
				worldThemeTextarea = initial_world_theme;
				topic = initial_topic;
				chatHistory = [
					{ role: 'system', content: `Error loading previous world data: ${error.message}` },
					{ role: 'assistant', content: initialChatPromptText }
				];
			} finally {
				loadingInitialData = false;
				saveWorldButtonDisabled = !isEditingMode;
			}
		}
		loadInitialWorldData();
	});

	$effect(() => {
		if (!savingIndicatorVisible && !loadingInitialData && isEditingMode) {
			saveWorldButtonDisabled = false;
		} else if (!isEditingMode) {
			saveWorldButtonDisabled = true;
		}
	});

	async function finalizeChat() {
		// Keep the check for at least one user message
		if (chatHistory.filter((msg) => msg.role === 'user').length === 0) {
			alert('Please send at least one message to the AI before finalizing.');
			return;
		}
		if (isFinalizeButtonDisabled) return;

		worldThemeTextarea = '';

		const requestData = {
			chat_history: chatHistory,
			topic: topic
		};

		let responseContent = '';

		// isChatGenerating will be handled by the Chat component stream if this goes through Chat's submit
		// If finalize uses a separate backend endpoint not routed through Chat.svelte,
		// we might need a specific loading state for finalization here.
		// Assuming for now that the finalize endpoint handles its own streaming and state updates
		// back to the World component, potentially through binding isChatGenerating.

		try {
			const response = await fetch('/finalize_world_stream', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(requestData)
			});

			if (!response.ok || !response.body) {
				const errorText = await response.text();
				throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();

			while (true) {
				const { value, done } = await reader.read();
				if (done) {
					break;
				}

				const chunk = decoder.decode(value);

				chunk
					.split('\n\n')
					.filter(Boolean)
					.forEach((event) => {
						if (event.startsWith('data: ')) {
							try {
								const jsonData = event.substring(6);
								if (jsonData === '[DONE]') {
									return;
								}
								const data = JSON.parse(jsonData);
								if (data.content !== undefined) {
									responseContent += data.content;
									worldThemeTextarea = responseContent;
								}
							} catch (e: any) {
								console.error('Error parsing JSON from finalize stream:', e, jsonData);
								worldThemeTextarea += ` [Parsing Error: ${e.message}]`;
							}
						}
					});
			}
		} catch (error: any) {
			console.error('Fetch error for final world setting:', error);
			worldThemeTextarea =
				`Error finalizing world setting: ${error.message}\n\n` + worldThemeTextarea;
		} finally {
			// Ensure loading state is off
			isChatGenerating = false;
		}
	}

	async function saveWorld(event: Event) {
		event.preventDefault();

		if (saveWorldButtonDisabled) return;

		savingIndicatorVisible = true;
		savedIndicatorVisible = false;
		saveError = null;
		saveWorldButtonDisabled = true;

		const requestData = {
			world_theme: worldThemeTextarea
		};

		try {
			const response = await fetch('/save_world', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(requestData)
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
			}

			savingIndicatorVisible = false;
			savedIndicatorVisible = true;

			setTimeout(() => {
				savedIndicatorVisible = false;
			}, 3000);
		} catch (error: any) {
			console.error('Error saving world theme:', error);
			saveError = `Error saving world theme: ${error.message}`;
			savingIndicatorVisible = false;
			saveWorldButtonDisabled = false;
		}
	}

	function navigate(path: string) {
		history.pushState(null, '', path);
		window.dispatchEvent(new PopStateEvent('popstate'));
	}
</script>

<div class="world-container">
	<div class="row">
		<div class="col-12 mb-4">
			<div class="card">
				<div
					class="card-header bg-primary text-white d-flex justify-content-between align-items-center"
				>
					<h1 class="h4 mb-0">Create World Setting</h1>
					<button
						onclick={() => navigate('/characters')}
						class="btn btn-light btn-sm"
						disabled={!worldThemeTextarea || savingIndicatorVisible || loadingInitialData}
					>
						Next: Characters &raquo;
					</button>
				</div>
				<div class="card-body">
					<!-- Corrected card-body div -->
					<p class="lead">
						Start by chatting with the AI to develop your book's world. Describe your ideas, answer
						questions, and explore different aspects of your world together.
					</p>
					{#if topic}
						<p>Current Topic: <strong>{topic}</strong></p>
					{/if}
					{#if initialDataError}
						<div class="alert alert-danger mt-3" role="alert">
							{initialDataError}
						</div>
					{/if}
				</div>
			</div>
		</div>

		{#if loadingInitialData}
			<div class="col-12 mb-4">
				<div class="alert alert-info d-flex align-items-center" role="status">
					<div class="spinner-border spinner-border-sm me-2" aria-hidden="true"></div>
					Loading world data...
				</div>
			</div>
		{/if}

		{#if !isEditingMode && !loadingInitialData}
			<div class="col-12 mb-4">
				<div class="card">
					<div class="card-header bg-primary text-white">
						<h2 class="h5 mb-0">World Building Chat</h2>
					</div>
					<div class="card-body">
						<Chat
							chatEndpoint="/world_chat_stream"
							bind:chatHistory
							bind:isGenerating={isChatGenerating}
							bind:topic
							contextData={{}}
							placeholderText="Type your ideas about the world you want to create..."
						>
							{#snippet introText()}{/snippet}
							{#snippet belowInput()}
								<button
									onclick={finalizeChat}
									class="btn btn-success mt-3"
									disabled={isFinalizeButtonDisabled}
								>
									Finalize World Setting
								</button>
								{#if isChatGenerating}
									<div class="alert alert-info mt-3">
										<div class="d-flex align-items-center">
											<div class="spinner-border spinner-border-sm me-2" role="status">
												<span class="visually-hidden">Loading...</span>
											</div>
											<div>AI is thinking...</div>
										</div>
									</div>
								{/if}
							{/snippet}
						</Chat>
					</div>
				</div>
			</div>
		{/if}

		{#if isEditingMode}
			<div class="col-12">
				<div class="card">
					<div class="card-header bg-success text-white">
						<h2 class="h5 mb-0">Your World Setting</h2>
					</div>
					<div class="card-body">
						<form onsubmit={saveWorld}>
							<div class="mb-3">
								<label for="worldTheme" class="form-label">Edit your world setting if needed:</label
								>
								<textarea
									bind:this={worldThemeTextareaElement}
									class="form-control"
									id="worldTheme"
									name="world_theme"
									rows="12"
									bind:value={worldThemeTextarea}
								></textarea>
							</div>
							<div class="d-flex justify-content-between">
								<button type="submit" class="btn btn-success" disabled={saveWorldButtonDisabled}>
									Save Changes
								</button>
								<button
									onclick={() => navigate('/characters')}
									class="btn btn-primary"
									disabled={!worldThemeTextarea || savingIndicatorVisible || loadingInitialData}
								>
									Continue to Characters
								</button>
							</div>
						</form>

						{#if savingIndicatorVisible}
							<div class="alert alert-info mt-3">
								<div class="d-flex align-items-center">
									<div class="spinner-border spinner-border-sm me-2" role="status">
										<span class="visually-hidden">Saving...</span>
									</div>
									<div>Saving changes...</div>
								</div>
							</div>
						{/if}

						{#if savedIndicatorVisible}
							<div class="alert alert-success mt-3">
								<div>World setting saved successfully!</div>
							</div>
						{/if}

						{#if saveError}
							<div class="alert alert-danger mt-3" role="alert">
								{saveError}
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.world-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	.navigation-buttons {
		display: flex;
		gap: 1rem;
	}

	.card {
		margin-bottom: 2rem;
	}

	.card-body .lead {
		margin-bottom: 1.5rem;
	}

	button.btn:disabled {
		opacity: 0.65;
		cursor: not-allowed;
	}
</style>
