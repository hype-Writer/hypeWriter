<script lang="ts">
	import Chat from '../components/chat.svelte';
	import Button from '../components/ui/Button.svelte';
	import Card from '../components/ui/Card.svelte';
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
	let saveError = $state<string | null>(null); // Using saveError for streaming errors too
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
	let worldThemeTextareaElement: HTMLTextAreaElement; // No $state needed for bind:this

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
		saveError = null; // Clear previous errors

		const requestData = {
			chat_history: chatHistory,
			topic: topic
		};

		let responseContent = '';
		let controller = new AbortController(); // For aborting the fetch
		let signal = controller.signal;

		isChatGenerating = true;

		try {
			const response = await fetch('/finalize_world_stream', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(requestData),
				signal: signal // Use the signal for aborting
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
						// Check for the specific streaming error format from the backend
						if (event.includes('[STREAMING ERROR: ')) {
							console.error('Received streaming error:', event);
							saveError = `AI streaming error: ${event.substring(event.indexOf('[STREAMING ERROR: '))}`;
							// Do not append error to textarea content
							isChatGenerating = false; // Stop generating state
							controller.abort(); // Abort the fetch
							return; // Skip processing this event as data
						}

						if (event.startsWith('data: ')) {
							try {
								const jsonData = event.substring(6);
								if (jsonData === '[DONE]') {
									return;
								}
								const data = JSON.parse(jsonData);
								if (data.content !== undefined) {
									responseContent += data.content;
									worldThemeTextarea = responseContent; // Update textarea reactively
								}
							} catch (e: any) {
								console.error('Error parsing JSON from finalize stream:', e, jsonData);
								// Append parsing error to the textarea, alongside any valid content received
								worldThemeTextarea += ` [Parsing Error: ${e.message}]`;
								saveError = 'Failed to parse AI response chunk.'; // Indicate a parsing issue
							}
						}
					});

				// If an error was received and aborted, stop processing chunks
				if (signal.aborted) {
					break;
				}
			}
		} catch (error: any) {
			// This catch handles fetch errors or errors thrown before the stream starts/while reading
			if (error.name === 'AbortError') {
				console.log('Fetch aborted due to streaming error.');
				// Error message already set by the streaming loop check
			} else {
				console.error('Fetch or stream reading error for final world setting:', error);
				saveError = `Error finalizing world setting: ${error.message}`;
				// Append fetch error to the textarea if it's not a safety/streaming error already handled
				if (!worldThemeTextarea.includes('Error finalizing world setting:')) {
					worldThemeTextarea =
						`Error finalizing world setting: ${error.message}\n\n` + worldThemeTextarea;
				}
			}
		} finally {
			// Ensure loading state is off unless an error occurred that stopped generation
			if (!saveError) {
				isChatGenerating = false;
			}
		}
	}

	async function saveWorld(event: Event) {
		event.preventDefault();

		if (saveWorldButtonDisabled) return;

		savingIndicatorVisible = true;
		savedIndicatorVisible = false;
		saveError = null; // Clear previous errors
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
	<div class="world-content">
		<Card padding="lg">
			<div class="world-header">
				<h1>Create World Setting</h1>
				<Button
					variant="primary"
					size="sm"
					onclick={() => navigate('/characters')}
					disabled={!worldThemeTextarea ||
						savingIndicatorVisible ||
						loadingInitialData ||
						isChatGenerating}
				>
					Next: Characters →
				</Button>
			</div>
			<div class="world-intro">
				<p class="lead-text">
					Start by chatting with the AI to develop your book's world. Describe your ideas, answer
					questions, and explore different aspects of your world together.
				</p>
				{#if topic}
					<p class="topic-display">Current Topic: <strong>{topic}</strong></p>
				{/if}
				{#if initialDataError}
					<div class="error-message">
						{initialDataError}
					</div>
				{/if}
			</div>
		</Card>

		{#if loadingInitialData}
			<Card padding="lg">
				<div class="loading-state">
					<div class="loading-spinner"></div>
					<p>Loading world data...</p>
				</div>
			</Card>
		{/if}

		{#if saveError}
			<Card padding="lg">
				<div class="error-message">
					{saveError}
				</div>
			</Card>
		{/if}

		{#if !isEditingMode && !loadingInitialData}
			<Card padding="lg">
				<div class="chat-section">
					<h2 class="section-title">World Building Chat</h2>
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
							<div class="chat-actions">
								<Button
									variant="success"
									onclick={finalizeChat}
									disabled={isFinalizeButtonDisabled}
								>
									Finalize World Setting
								</Button>
								{#if isChatGenerating}
									<div class="generating-indicator">
										<div class="loading-spinner"></div>
										<span>AI is thinking...</span>
									</div>
								{/if}
							</div>
						{/snippet}
					</Chat>
				</div>
			</Card>
		{/if}

		{#if isEditingMode}
			<Card padding="lg">
				<div class="editing-section">
					<h2 class="section-title">Your World Setting</h2>
					<form onsubmit={saveWorld} class="world-form">
						<div class="field-group">
							<label for="worldTheme" class="field-label">Edit your world setting if needed:</label>
							<textarea
								bind:this={worldThemeTextareaElement}
								class="field-textarea"
								id="worldTheme"
								name="world_theme"
								rows="12"
								bind:value={worldThemeTextarea}
							></textarea>
						</div>
						<div class="form-actions">
							<Button type="submit" variant="success" disabled={saveWorldButtonDisabled}>
								Save Changes
							</Button>
							<Button
								variant="primary"
								onclick={() => navigate('/characters')}
								disabled={!worldThemeTextarea ||
									savingIndicatorVisible ||
									loadingInitialData ||
									isChatGenerating}
							>
								Continue to Characters
							</Button>
						</div>
					</form>

					{#if savingIndicatorVisible}
						<div class="status-message saving">
							<div class="loading-spinner"></div>
							<span>Saving changes...</span>
						</div>
					{/if}

					{#if savedIndicatorVisible}
						<div class="status-message success">
							World setting saved successfully!
						</div>
					{/if}
				</div>
			</Card>
		{/if}
	</div>
</div>

<style>
	.world-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: var(--space-6);
		min-height: 100vh;
		background: linear-gradient(135deg, var(--color-dark-base) 0%, var(--color-dark-primary) 100%);
	}

	.world-content {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.world-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		margin-bottom: var(--space-4);
	}

	.world-header h1 {
		font-size: var(--font-size-3xl);
		color: var(--color-text-accent);
		margin: 0;
		font-weight: var(--font-weight-bold);
	}

	.world-intro {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.lead-text {
		font-size: var(--font-size-lg);
		color: var(--color-text-secondary);
		line-height: 1.6;
		margin: 0;
	}

	.topic-display {
		color: var(--color-text-primary);
		margin: 0;
	}

	.topic-display strong {
		color: var(--color-text-accent);
	}

	.section-title {
		font-size: var(--font-size-2xl);
		color: var(--color-text-accent);
		margin: 0 0 var(--space-4) 0;
		font-weight: var(--font-weight-semibold);
	}

	.chat-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.chat-actions {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: var(--space-3);
		margin-top: var(--space-3);
	}

	.editing-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.world-form {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
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

	.field-textarea {
		padding: var(--space-3);
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		color: var(--color-text-primary);
		font-size: var(--font-size-base);
		font-family: inherit;
		resize: vertical;
		min-height: 300px;
		transition: all var(--transition-fast);
	}

	.field-textarea:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
	}

	.form-actions {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-3);
		padding: var(--space-8);
	}

	.loading-spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--color-border);
		border-top: 3px solid var(--color-primary);
		border-radius: 50%;
		animation: var(--animation-spin);
	}

	.generating-indicator {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		color: var(--color-text-secondary);
		font-style: italic;
	}

	.generating-indicator .loading-spinner {
		width: 20px;
		height: 20px;
		border-width: 2px;
	}

	.status-message {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3) var(--space-4);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-sm);
		margin-top: var(--space-4);
	}

	.status-message.saving {
		background: rgba(0, 212, 255, 0.1);
		color: var(--color-primary);
		border: 1px solid rgba(0, 212, 255, 0.2);
	}

	.status-message.success {
		background: rgba(16, 185, 129, 0.1);
		color: var(--color-success);
		border: 1px solid rgba(16, 185, 129, 0.2);
	}

	.error-message {
		padding: var(--space-3) var(--space-4);
		background: rgba(239, 68, 68, 0.1);
		color: var(--color-error);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-sm);
	}

	@media (max-width: 768px) {
		.world-container {
			padding: var(--space-4);
		}

		.world-header {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--space-3);
		}

		.world-header h1 {
			font-size: var(--font-size-2xl);
		}

		.form-actions {
			flex-direction: column;
			align-items: stretch;
			gap: var(--space-3);
		}
	}
</style>
