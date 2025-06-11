<script lang="ts">
	import type { Snippet } from 'svelte';
	import Chat from '../components/chat.svelte';

	interface ChatMessage {
		role: 'user' | 'assistant' | 'system';
		content: string;
		id?: number;
	}

	interface Chapter {
		title: string;
		summary: string;
	}

	let outlineContent = $state('');
	let chapters = $state<Chapter[]>([]);
	let worldTheme = $state('');
	let characters = $state('');
	let numChapters = $state(10);
	let showWorld = $state(false);
	let showCharacters = $state(false);
	let showResults = $state(false);

	let chatHistory = $state<ChatMessage[]>([]);
	let message = $state('');
	let isGenerating = $state(false);
	let streamingContent = $state('');
	let streamingError = $state<string | null>(null);

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
		streamingContent = '';
		streamingError = null; // Clear previous errors

		const requestData = {
			chat_history: chatHistory,
			world_theme: worldTheme,
			characters: characters,
			num_chapters: numChapters // Include numChapters in the request
		};

		let controller = new AbortController();
		let signal = controller.signal;

		try {
			const response = await fetch('/outline_chat_stream', {
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
									streamingContent = assistantResponse;
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
				console.error('Fetch error for chat stream:', error);
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
		'Based on the world setting and characters, what kind of plot outline or story beats are you thinking of?';

	$effect(() => {
		// Fetch world theme and characters when the component mounts
		async function loadContextData() {
			try {
				const worldResponse = await fetch('/api/world');
				if (!worldResponse.ok) throw new Error('Failed to fetch world data');
				const worldData = await worldResponse.json();
				worldTheme = worldData.world_theme || 'No world theme set.';

				const charactersResponse = await fetch('/api/characters');
				if (!charactersResponse.ok) throw new Error('Failed to fetch characters data');
				const charactersData = await charactersResponse.json();
				characters = charactersData.characters || 'No characters set.';

				// Fetch existing outline if available
				const outlineResponse = await fetch('/api/outline');
				if (!outlineResponse.ok) {
					// If no outline exists, start the initial chat
					chatHistory = [{ role: 'assistant', content: initialChatPrompt }];
					showResults = false;
				} else {
					const outlineData = await outlineResponse.json();
					outlineContent = outlineData.outline || '';
					if (outlineContent) {
						// If outline exists, show results immediately
						showResults = true;
						// Optionally, parse the outlineContent to populate chapters array
						// This depends on how the backend formats the saved outline
					} else {
						// If outline exists but is empty, start initial chat
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

	async function finalizeOutline() {
		// Keep the check for at least one user message
		if (chatHistory.filter((msg) => msg.role === 'user').length === 0) {
			alert('Please send at least one message to the AI before finalizing.');
			return;
		}
		if (isFinalizeButtonDisabled) return;

		isGenerating = true; // Use isGenerating for the finalization process loading state
		streamingContent = '';
		outlineContent = ''; // Clear previous outline content
		streamingError = null; // Clear previous errors

		const requestData = {
			chat_history: chatHistory,
			world_theme: worldTheme,
			characters: characters,
			num_chapters: numChapters
		};

		let controller = new AbortController();
		let signal = controller.signal;

		try {
			const response = await fetch('/finalize_outline_stream', {
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
							// Do not append error to outline content
							outlineContent = `Error finalizing outline: ${streamingError}\n\n` + outlineContent; // Prepend error to textarea
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
									outlineContent = finalizedContent; // Update outlineContent as stream progresses
								}
							} catch (e: any) {
								console.error('Error parsing JSON from finalize stream:', e, jsonData);
								outlineContent += ` [Parsing Error: ${e.message}]`; // Append parsing error to the textarea
								streamingError = 'Failed to parse AI response chunk during finalization.'; // Indicate a parsing issue
							}
						}
					});

				// If an error was received and aborted, stop processing chunks
				if (signal.aborted) {
					break;
				}
			}

			// After stream is complete, attempt to parse outlineContent into chapters if needed
			// This parsing logic is a placeholder; adjust based on expected output format
			try {
				// Example: If the output is a JSON string of chapters
				// chapters = JSON.parse(outlineContent);
				// Or if it's a text format you need to parse
			} catch (e) {
				console.warn('Could not parse finalized outline into chapters:', e);
				chapters = []; // Reset chapters if parsing fails
			}

			showResults = true; // Switch to the results view after finalization
		} catch (error: any) {
			// This catch handles fetch errors or errors thrown before the stream starts/while reading
			if (error.name === 'AbortError') {
				console.log('Fetch aborted due to streaming error.');
				// Error message already set by the streaming loop check or prepended to textarea
			} else {
				console.error('Fetch error for final outline:', error);
				streamingError = `Error finalizing outline: ${error.message}`;
				outlineContent = `Error finalizing outline: ${error.message}\n\n` + outlineContent;
				showResults = true; // Still show results view, but with error message
			}
		} finally {
			// Ensure loading state is off unless a streaming error occurred that stopped generation
			if (!streamingError) {
				isGenerating = false;
				streamingContent = ''; // Clear streaming content after generation completes without error
			}
		}
	}

	async function saveOutline() {
		// Simple save logic
		const requestData = { outline: outlineContent };
		try {
			const response = await fetch('/save_outline', {
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
			alert('Outline saved successfully!');
		} catch (error: any) {
			console.error('Error saving outline:', error);
			alert(`Failed to save outline: ${error.message}`);
		}
	}

	async function regenerateChapters() {
		if (!outlineContent) {
			alert('Please finalize the outline first.');
			return;
		}

		isGenerating = true;
		chapters = []; // Clear existing chapters
		let streamedChapters = '';
		streamingError = null; // Clear previous errors

		const requestData = {
			outline: outlineContent
		};

		let controller = new AbortController();
		let signal = controller.signal;

		try {
			const response = await fetch('/regenerate_chapters_stream', {
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

			// Assuming the stream sends chunks of chapter data
			while (true) {
				const { value, done } = await reader.read();
				if (done) {
					break;
				}

				const chunk = decoder.decode(value);
				streamedChapters += chunk; // Accumulate streamed data

				// Check for the specific streaming error format from the backend
				if (chunk.includes('[STREAMING ERROR: ')) {
					// Check chunk directly as chapter data might not be data: prefixed
					console.error('Received streaming error:', chunk);
					streamingError = `AI streaming error: ${chunk.substring(chunk.indexOf('[STREAMING ERROR: '))}`;
					// Do not attempt to parse as chapters
					isGenerating = false; // Stop generating state
					controller.abort(); // Abort the fetch
					return; // Stop processing this chunk and further chunks
				}

				// Basic attempt to parse accumulated data - this needs refinement
				// based on the actual stream format from the backend
				try {
					// If backend streams JSON objects or a parsable format
					// Example: chapters = parseStreamedChapters(streamedChapters);
				} catch (e) {
					console.warn('Could not parse streamed chapter data:', e);
					streamingError = 'Failed to parse streamed chapter data.'; // Indicate a parsing issue
				}
			}
			// Final parsing attempt after stream is done, if necessary and no streaming error occurred
			if (!streamingError) {
				try {
					// Example: chapters = JSON.parse(streamedChapters);
				} catch (e) {
					console.error('Failed to parse final streamed chapter data:', e);
					alert('Failed to parse regenerated chapters.');
					chapters = []; // Clear chapters on final parsing failure
					streamingError = 'Failed to parse final streamed chapter data.'; // Indicate a parsing issue
				}
			}
		} catch (error: any) {
			// This catch handles fetch errors or errors thrown before the stream starts/while reading
			if (error.name === 'AbortError') {
				console.log('Fetch aborted due to streaming error.');
				// Error message already set by the streaming loop check
			} else {
				console.error('Fetch error for regenerating chapters:', error);
				alert(`Failed to regenerate chapters: ${error.message}`);
				chapters = []; // Clear chapters on fetch error
				streamingError = `Failed to regenerate chapters: ${error.message}`; // Indicate fetch error
			}
		} finally {
			// Ensure loading state is off unless a streaming error occurred that stopped generation
			if (!streamingError) {
				isGenerating = false;
			}
		}
	}
</script>

<div class="outline-container">
	<div class="row">
		<div class="col-12 mb-4">
			<div class="card">
				<div
					class="card-header bg-primary text-white d-flex justify-content-between align-items-center"
				>
					<h1 class="h4 mb-0">Develop Outline</h1>
					<div class="navigation-buttons">
						<a href="/characters" class="btn btn-light"> &laquo; Previous: Characters </a>
						{#if chapters.length > 0}
							<a href="/chapters" class="btn btn-light"> Next: Chapters &raquo; </a>
						{/if}
					</div>
				</div>
				<div class="card-body">
					<p class="lead">
						Chat with the AI to brainstorm and refine your book's outline. You can generate a full
						outline and then break it down into individual chapters.
					</p>
				</div>
			</div>
		</div>

		{#if !worldTheme || !characters}
			<div class="col-12 mb-4">
				<div class="alert alert-warning">
					<strong>Context needed!</strong> Please ensure you have set your
					<a href="/world" class="alert-link">World Setting</a> and
					<a href="/characters" class="alert-link">Characters</a> before generating an outline.
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

		{#if worldTheme && characters}
			<div class="col-12">
				<div class="context-accordion mb-4">
					<div class="accordion" id="contextAccordion">
						<div class="accordion-item">
							<h2 class="accordion-header" id="worldContextHeading">
								<button
									class="accordion-button collapsed"
									type="button"
									data-bs-toggle="collapse"
									data-bs-target="#worldContextCollapse"
									aria-expanded={showWorld}
									aria-controls="worldContextCollapse"
									onclick={() => (showWorld = !showWorld)}
								>
									World Setting
								</button>
							</h2>
							<div
								id="worldContextCollapse"
								class="accordion-collapse collapse"
								class:show={showWorld}
								aria-labelledby="worldContextHeading"
								data-bs-parent="#contextAccordion"
							>
								<div class="accordion-body small">
									<p>{worldTheme}</p>
								</div>
							</div>
						</div>
						<div class="accordion-item">
							<h2 class="accordion-header" id="charactersContextHeading">
								<button
									class="accordion-button collapsed"
									type="button"
									data-bs-toggle="collapse"
									data-bs-target="#charactersContextCollapse"
									aria-expanded={showCharacters}
									aria-controls="charactersContextCollapse"
									onclick={() => (showCharacters = !showCharacters)}
								>
									Characters
								</button>
							</h2>
							<div
								id="charactersContextCollapse"
								class="accordion-collapse collapse"
								class:show={showCharacters}
								aria-labelledby="charactersContextHeading"
								data-bs-parent="#contextAccordion"
							>
								<div class="accordion-body small">
									<p>{characters}</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				{#if !showResults}
					<div class="mb-3">
						<label for="numChapters" class="form-label"
							>Approximate number of chapters for the final outline:</label
						>
						<input
							type="number"
							id="numChapters"
							class="form-control"
							bind:value={numChapters}
							min="1"
							max="100"
							step="1"
						/>
					</div>

					<div class="card chat-card">
						<div class="card-header bg-primary text-white">
							<h3 class="h5 mb-0">Outline Building Chat</h3>
						</div>
						<div class="chat-container card-body">
							<p class="lead">
								Chat here to brainstorm ideas for your outline. When you're ready, click "Finalize
								Outline" to generate a structured outline based on the conversation.
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
									placeholder="Type your ideas about the outline..."
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
									onclick={finalizeOutline}
									class="btn btn-success"
									disabled={isFinalizeButtonDisabled}
								>
									Finalize Outline
								</button>
							</div>
						</div>
					</div>
				{:else}
					<div class="card results-card">
						<div class="card-header bg-success text-white">
							<h3 class="h5 mb-0">Your Outline</h3>
						</div>
						<div class="card-body">
							<p class="lead">Here is the generated outline. You can edit it directly.</p>
							<div class="form-group mb-3">
								<label for="outlineContent" class="form-label">Edit your outline:</label>
								<textarea
									id="outlineContent"
									bind:value={outlineContent}
									rows="15"
									class="form-control"
								></textarea>
							</div>
							<div class="d-flex justify-content-between align-items-center">
								<button onclick={saveOutline} class="save-button btn btn-success">
									Save Outline
								</button>
								<a href="/chapters" class="btn btn-primary"> Continue to Chapters </a>
							</div>

							{#if chapters.length > 0}
								<div class="mt-3">
									<h4>Generated Chapters:</h4>
									<button onclick={regenerateChapters} class="btn btn-sm btn-secondary mb-2">
										Regenerate Chapters from Outline
									</button>
									<ul class="list-group list-group-flush">
										{#each chapters as chapter, index (index)}
											<li class="list-group-item">
												<strong>{chapter.title}</strong>
												<p class="text-muted small mb-0">{chapter.summary}</p>
											</li>
										{/each}
									</ul>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	/* Keep your existing styles or adapt them to fit the new structure */
	.outline-container {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
	}

	/* Removed unused header and navigation-buttons styles */

	.context-accordion {
		margin-bottom: 2rem;
	}

	.chat-card,
	.results-card {
		margin-bottom: 2rem;
	}

	/* Styles specific to Outline.svelte layout */
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
