<script lang="ts">
	import type { Snippet } from 'svelte';
	import Chat from '../components/chat.svelte';

	interface ChatMessage {
		role: 'user' | 'assistant' | 'system';
		content: string;
		id?: number;
	}

	let characters = $state(''); // Stores the generated character descriptions
	let worldTheme = $state(''); // To display context
	let chatHistory = $state<ChatMessage[]>([]);
	let showFullWorld = $state(false); // To toggle visibility of full world theme
	let numCharacters = $state(5); // Default number of characters to generate
	let showResults = $state(false); // To toggle between chat and results view

	let message = $state(''); // Current message input
	let isGenerating = $state(false); // State bound from Chat component (or managed here)
	let streamingContent = $state(''); // For displaying streaming AI responses
	let streamingError = $state<string | null>(null); // New state for streaming errors

	// Reference to the chat messages area for scrolling
	let chatMessagesDiv: HTMLElement | null = null; // No $state needed for bind:this

	// Effect to scroll chat to bottom when history or streaming content updates
	$effect(() => {
		if (chatMessagesDiv) {
			chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
		}
	});

	async function handleSubmit() {
		if (!message.trim() || isGenerating) return;

		const userMessage: ChatMessage = { role: 'user', content: message };
		chatHistory = [...chatHistory, userMessage];
		message = '';
		isGenerating = true;
		streamingContent = ''; // Clear previous streaming content on new message
		streamingError = null; // Clear previous errors

		const requestData = {
			chat_history: chatHistory,
			world_theme: worldTheme, // Include world theme in the request context
			num_characters: numCharacters // Include the desired number of characters
		};

		let controller = new AbortController();
		let signal = controller.signal;

		try {
			const response = await fetch('/characters_chat_stream', {
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
			let assistantResponse = '';

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
							streamingError = `AI streaming error: ${event.substring(event.indexOf('[STREAMING ERROR: '))}`;
							// Do not append error to chat history content
							isGenerating = false; // Stop generating state
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
									assistantResponse += data.content;
									streamingContent = assistantResponse; // Update streaming content reactively
								}
							} catch (e: any) {
								console.error('Error parsing JSON from stream:', e, jsonData);
								streamingError = 'Failed to parse AI response chunk.'; // Indicate a parsing issue
							}
						}
					});

				// If an error was received and aborted, stop processing chunks
				if (signal.aborted) {
					break;
				}
			}

			// Add the complete assistant message to chat history if no streaming error occurred
			if (!streamingError) {
				chatHistory = [...chatHistory, { role: 'assistant', content: assistantResponse }];
			}
		} catch (error: any) {
			// This catch handles fetch errors or errors thrown before the stream starts/while reading
			if (error.name === 'AbortError') {
				console.log('Fetch aborted due to streaming error.');
				// Error message already set by the streaming loop check
			} else {
				console.error('Fetch or stream reading error for chat stream:', error);
				streamingError = `Fetch or stream error: ${error.message}`;
				// Optionally add a system message to chat history for non-streaming errors
				chatHistory = [...chatHistory, { role: 'system', content: `Error: ${error.message}` }];
			}
		} finally {
			// Ensure loading state is off unless a streaming error occurred that stopped generation
			if (!streamingError) {
				isGenerating = false;
				streamingContent = ''; // Clear streaming content after generation completes without error
			}
		}
	}

	function formatMessage(text: string): string {
		// Basic formatting for markdown code blocks and paragraphs
		// This is a very simple implementation and could be enhanced
		return text
			.split('\n\n') // Split into paragraphs
			.map((para) => {
				if (para.startsWith('```')) {
					// Simple code block detection
					return `<pre><code>${para.substring(3).replace('```', '')}</code></pre>`;
				}
				return `<p>${para}</p>`; // Wrap paragraphs
			})
			.join('');
	}

	// isFinalizeButtonDisabled depends on chat history, loading, and isGenerating
	let isFinalizeButtonDisabled = $derived(
		chatHistory.filter((msg) => msg.role === 'user').length === 0 || isGenerating
	);

	const initialChatPrompt =
		'Based on your world setting, what kind of characters are you thinking of? You can describe individuals, archetypes, or groups. I can help you brainstorm or generate character concepts.';

	$effect(() => {
		// Fetch world theme and existing characters when the component mounts
		async function loadContextData() {
			try {
				const worldResponse = await fetch('/api/world');
				if (!worldResponse.ok) throw new Error('Failed to fetch world data');
				const worldData = await worldResponse.json();
				worldTheme = worldData.world_theme || 'No world theme set.';

				const charactersResponse = await fetch('/api/characters');
				if (!charactersResponse.ok) {
					// If no characters exist, start the initial chat
					chatHistory = [{ role: 'assistant', content: initialChatPrompt }];
					showResults = false;
				} else {
					const charactersData = await charactersResponse.json();
					characters = charactersData.characters || '';
					if (characters) {
						// If characters exist, show results immediately
						showResults = true;
					} else {
						// If characters exist but are empty, start initial chat
						chatHistory = [{ role: 'assistant', content: initialChatPrompt }];
						showResults = false;
					}
				}
			} catch (error: any) {
				console.error('Error loading context data:', error);
				chatHistory = [
					{ role: 'system', content: `Error loading context data: ${error.message}` },
					{ role: 'assistant', content: initialChatPrompt }
				];
				showResults = false; // Stay in chat view on error
			}
		}
		loadContextData();
	});

	async function finalizeCharacters() {
		// Keep the check for at least one user message
		if (chatHistory.filter((msg) => msg.role === 'user').length === 0) {
			alert('Please send at least one message to the AI before finalizing.');
			return;
		}
		if (isFinalizeButtonDisabled) return;

		isGenerating = true; // Use isGenerating for the finalization process loading state
		streamingContent = ''; // Clear previous streaming content
		characters = ''; // Clear previous characters content
		streamingError = null; // Clear previous errors

		const requestData = {
			chat_history: chatHistory,
			world_theme: worldTheme,
			num_characters: numCharacters
		};

		let controller = new AbortController();
		let signal = controller.signal;

		try {
			const response = await fetch('/finalize_characters_stream', {
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
			let finalizedContent = '';

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
							streamingError = `AI streaming error: ${event.substring(event.indexOf('[STREAMING ERROR: '))}`;
							// Do not append error to characters content
							isGenerating = false; // Stop generating state
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
									finalizedContent += data.content;
									characters = finalizedContent; // Update characters content as stream progresses
								}
							} catch (e: any) {
								console.error('Error parsing JSON from finalize stream:', e, jsonData);
								characters += ` [Parsing Error: ${e.message}]`; // Add error to characters view
								streamingError = 'Failed to parse AI response chunk during finalization.'; // Indicate a parsing issue
							}
						}
					});

				// If an error was received and aborted, stop processing chunks
				if (signal.aborted) {
					break;
				}
			}

			showResults = true; // Switch to the results view after finalization attempts
		} catch (error: any) {
			// This catch handles fetch errors or errors thrown before the stream starts/while reading
			if (error.name === 'AbortError') {
				console.log('Fetch aborted due to streaming error.');
				// Error message already set by the streaming loop check
			} else {
				console.error('Fetch error for final characters:', error);
				streamingError = `Error finalizing characters: ${error.message}`;
				characters = `Error finalizing characters: ${error.message}\n\n` + characters;
				showResults = true; // Still show results view, but with error message
			}
		} finally {
			// Ensure loading state is off unless a streaming error occurred that stopped generation
			if (!streamingError) {
				isGenerating = false;
				// Do not clear `characters` content here on success, it holds the result
			}
		}
	}

	async function saveCharacters() {
		// Simple save logic
		const requestData = { characters: characters };
		try {
			const response = await fetch('/save_characters', {
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
			alert('Characters saved successfully!');
		} catch (error: any) {
			console.error('Error saving characters:', error);
			alert(`Failed to save characters: ${error.message}`);
		}
	}
</script>

<div class="characters-container">
	<div class="row">
		<div class="col-12 mb-4">
			<div class="card">
				<div
					class="card-header bg-primary text-white d-flex justify-content-between align-items-center"
				>
					<h1 class="h4 mb-0">Develop Characters</h1>
					<div class="navigation-buttons">
						<a href="/world" class="btn btn-light"> &laquo; Previous: World </a>
						{#if characters}
							<a href="/outline" class="btn btn-light"> Next: Outline &raquo; </a>
						{/if}
					</div>
				</div>
				<div class="card-body">
					<p class="lead">
						Chat with the AI to brainstorm and develop your book's characters. Define their roles,
						personalities, and backstories.
					</p>
				</div>
			</div>
		</div>

		{#if !worldTheme}
			<div class="col-12 mb-4">
				<div class="alert alert-warning">
					<strong>Context needed!</strong> Please ensure you have set your
					<a href="/world" class="alert-link">World Setting</a> before developing characters.
				</div>
			</div>
		{/if}

		{#if streamingError}
			<div class="col-12 mb-4">
				<div class="alert alert-danger mt-3" role="alert">
					{streamingError}
				</div>
			</div>
		{/if}

		{#if worldTheme}
			<div class="col-12">
				<div class="world-context mb-4">
					<h3>World Setting Context:</h3>
					<div class="context-card card bg-light">
						<div class="card-body">
							<p class="card-text small mb-0">
								{showFullWorld ? worldTheme : worldTheme.substring(0, 200) + '...'}
							</p>
							<button
								class="btn btn-link btn-sm p-0"
								onclick={() => (showFullWorld = !showFullWorld)}
							>
								{showFullWorld ? 'Show less' : 'Show more'}
							</button>
							{#if showFullWorld}
								<div class="full-world mt-2 pt-2 border-top">
									<p>{worldTheme}</p>
								</div>
							{/if}
						</div>
					</div>
				</div>

				{#if !showResults}
					<div class="mb-3">
						<label for="numCharacters" class="form-label"
							>Approximate number of main characters to generate:</label
						>
						<input
							type="number"
							id="numCharacters"
							class="form-control"
							bind:value={numCharacters}
							min="1"
							max="20"
							step="1"
						/>
					</div>

					<div class="card chat-card">
						<div class="card-header bg-primary text-white">
							<h3 class="h5 mb-0">Character Building Chat</h3>
						</div>
						<div class="chat-container card-body">
							<p class="lead">
								Chat here to brainstorm ideas for your characters. When you're ready, click
								"Finalize Characters" to generate structured character descriptions based on the
								conversation.
							</p>
							<div bind:this={chatMessagesDiv} class="chat-messages-area">
								{#each chatHistory as msg (msg.role + msg.content)}
									<div class="message {msg.role}">
										<div class="content">{@html formatMessage(msg.content)}</div>
									</div>
								{/each}
								{#if streamingContent}
									<div class="message assistant">
										<div class="content">
											{@html formatMessage(streamingContent)}<span class="typing-cursor">|</span>
										</div>
									</div>
								{/if}
								{#if isGenerating && !streamingContent}
									<div class="typing-indicator">
										<div class="spinner"></div>
										<span>AI is thinking...</span>
									</div>
								{/if}
							</div>
							<div class="input-container d-flex">
								<textarea
									class="form-control"
									placeholder="Describe a character or type your ideas..."
									rows="1"
									bind:value={message}
									onkeypress={(e) => {
										if (e.key === 'Enter' && !e.shiftKey) {
											e.preventDefault();
											handleSubmit();
										}
									}}
									disabled={isGenerating}
								></textarea>
								<button class="btn btn-primary ms-2" onclick={handleSubmit} disabled={isGenerating}>
									Send
								</button>
							</div>
							<div class="mt-3 text-center">
								<button
									onclick={finalizeCharacters}
									class="btn btn-success"
									disabled={isFinalizeButtonDisabled}
								>
									Finalize Characters
								</button>
							</div>
						</div>
					</div>
				{:else}
					<div class="card results-card">
						<div class="card-header bg-success text-white">
							<h3 class="h5 mb-0">Your Characters</h3>
						</div>
						<div class="card-body">
							<p class="lead">
								Here are the generated character descriptions. You can edit them directly.
							</p>
							<div class="form-group mb-3">
								<label for="charactersContent" class="form-label">Edit your characters:</label>
								<textarea
									id="charactersContent"
									bind:value={characters}
									rows="15"
									class="form-control"
								></textarea>
							</div>
							<div class="d-flex justify-content-between">
								<button onclick={saveCharacters} class="save-button btn btn-success">
									Save Characters
								</button>
								<a href="/outline" class="btn btn-primary"> Continue to Outline </a>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	/* Keep your existing styles or adapt them to fit the new structure */
	.characters-container {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
	}

	/* Removed unused header and navigation-buttons styles */

	.world-context {
		margin-bottom: 2rem;
	}

	.context-card {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 4px;
	}

	.full-world {
		margin-top: 1rem;
		padding-top: 1rem; /* Added padding top */
		border-top: 1px solid #ddd; /* Added border top */
		background: white; /* Changed background */
		border-radius: 4px;
	}

	.chat-card,
	.results-card {
		margin-bottom: 2rem;
	}

	/* Styles specific to Characters.svelte layout */
	.card-body .lead {
		margin-bottom: 1.5rem; /* Add space below the lead paragraph */
	}

	/* === Chat Component Styles - Copied from Chat.svelte === */
	.chat-container {
		padding: 1.5rem;
	}

	.chat-messages-area {
		height: 400px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		word-break: break-word;
	}

	.chat-messages-area .message .content {
		white-space: pre-wrap;
	}

	.message {
		margin-bottom: 0.75rem;
		padding: 0.75rem;
		border-radius: 8px;
		max-width: 80%;
	}

	.message.user {
		background: #e3f2fd;
		align-self: flex-end;
	}

	.message.assistant {
		background: #f5f5f5;
		align-self: flex-start;
	}

	.typing-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: #f8f9fa;
		border-radius: 4px;
		margin-top: 0.5rem;
		align-self: flex-start;
		font-style: italic;
		color: #666;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid #f3f3f3;
		border-top: 2px solid #3498db;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	.input-container {
		margin-top: 1rem;
	}

	textarea.form-control {
		min-height: 60px;
		resize: vertical;
	}

	.input-container textarea.form-control {
		flex-grow: 1;
	}

	button.btn:disabled {
		opacity: 0.65;
		cursor: not-allowed;
	}

	.typing-cursor {
		display: inline-block;
		margin-left: 2px;
		animation: blink 0.7s infinite steps(1);
	}

	@keyframes blink {
		50% {
			opacity: 0;
		}
	}
	/* === End Copied Chat Component Styles === */
</style>
