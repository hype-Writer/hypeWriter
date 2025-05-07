<script lang="ts">
	console.log('World.svelte script running'); // Added log

	interface ChatMessage {
		role: 'user' | 'assistant';
		content: string;
	}

	let worldTheme = $state(''); // Stores the finalized/saved world theme
	let topic = $state(''); // Stores the book topic
	let chatHistory = $state<ChatMessage[]>([]); // Stores chat messages (will be managed directly here)
	let showFullWorld = $state(false); // Toggles visibility of full world theme in result area
	let showResults = $state(false); // Toggles between chat and final result display

	// --- Chat Component State/Logic - Copied from Chat.svelte ---
	let message = $state(''); // Input message
	let isGenerating = $state(false); // AI generation state
	let streamingContent = $state(''); // Content currently being streamed

	// Reference to the chat messages area for scrolling
	let chatMessagesDiv: HTMLElement | null = null;

	// Effect to scroll chat to bottom when history or streaming content updates
	$effect(() => {
		console.log('World.svelte $effect for scrolling triggered'); // Added log
		if (chatMessagesDiv) {
			chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
		}
	});

	// Function to handle sending messages
	async function handleSubmit() {
		console.log('World.svelte handleSubmit called with message:', message); // Added log
		if (!message.trim() || isGenerating) {
			console.log('handleSubmit aborted: message empty or generating', { message, isGenerating }); // Added log
			return;
		}

		const userMessage = message.trim();
		message = '';
		isGenerating = true;
		console.log('World.svelte Setting isGenerating to true'); // Added log

		// Add user message to chat history immediately
		chatHistory = [...chatHistory, { role: 'user', content: userMessage }];
		console.log('World.svelte Updated chatHistory', chatHistory); // Added log

		streamingContent = '';
		console.log('World.svelte Cleared streamingContent'); // Added log

		try {
			// Use the specific endpoint for this page
			console.log('World.svelte Fetching /world_chat_stream'); // Added log
			const response = await fetch('/world_chat_stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					message: userMessage,
					chat_history: chatHistory.slice(0, -1), // Send history *without* the current user message
					topic: topic // Include page-specific context data
				})
			});

			if (!response.ok) {
				console.error('World.svelte Fetch response not OK', response); // Added log
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Chat stream request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			const reader = response.body?.getReader();
			if (!reader) {
				console.error('World.svelte No reader available'); // Added log
				throw new Error('No reader available for stream');
			}

			const decoder = new TextDecoder(); // Use a TextDecoder

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value); // Decode the chunk
				const lines = chunk.split('\n').filter((line) => line.trim() !== ''); // Split and filter empty lines

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						try {
							const data = JSON.parse(line.slice(6));
							console.log('World.svelte Received SSE data:', data); // Added log
							if (data.content === '[DONE]') {
								console.log('World.svelte Received [DONE]'); // Added log
								// Stream complete - add accumulated content to chat history
								chatHistory = [
									...chatHistory,
									{ role: 'assistant', content: streamingContent.trim() }
								];
								streamingContent = '';
								console.log('World.svelte Finalized chatHistory and cleared streamingContent'); // Added log
							} else if (data.content !== undefined) {
								// Ensure content exists
								streamingContent += data.content;
								// Scrolling effect will be triggered by streamingContent update
							}
						} catch (e: any) {
							// Explicitly type error
							console.error('World.svelte Error parsing SSE data line:', e, line); // Added log
							chatHistory = [
								...chatHistory,
								{ role: 'assistant', content: `[Error processing message: ${e.message}]` } // Added error message detail
							];
							streamingContent = '';
							isGenerating = false;
							console.log('World.svelte Error during stream, setting isGenerating to false'); // Added log
							// Break the outer while loop on parsing error to stop the stream
							reader.cancel(); // Cancel the reader to stop the stream
							break; // Exit the inner loop
						}
					}
				}
			}
		} catch (error: any) {
			// Explicitly type error
			console.error('World.svelte Chat stream fetch error:', error); // Added log
			chatHistory = [
				...chatHistory,
				{
					role: 'assistant',
					content: `Sorry, there was an error processing your request: ${error.message}`
				}
			];
			streamingContent = '';
		} finally {
			isGenerating = false;
			console.log('World.svelte Finally block, setting isGenerating to false'); // Added log
		}
	}

	// Helper function to format message content (copied from Chat.svelte)
	function formatMessage(content: string): string {
		return content.replace(/\n/g, '<br>');
	}
	// --- End Copied Chat State/Logic ---

	// Derived state to control visibility of chat vs results
	// Show chat if worldTheme is empty OR if worldTheme exists but we haven't finalized/shown results yet
	let showChatSection = $derived(!worldTheme || !showResults);
	let showWorldResultSection = $derived(worldTheme && showResults);

	// Derived state for the disabled state of the finalize button
	// Calculate this directly here
	let isFinalizeButtonDisabled = $derived(
		chatHistory.filter((msg) => msg.role === 'user').length === 0
	);

	// Initial message for the chat, only shown if history is empty
	const initialChatPrompt =
		'Tell me about the world you want to create for your book. What kind of setting, time period, or genre are you interested in?';

	// Load existing data when component mounts
	$effect(() => {
		console.log('World.svelte load effect running'); // Added log
		(async () => {
			try {
				const response = await fetch('/api/world');
				const data = await response.json();
				console.log('World.svelte Loaded world data:', data); // Added log

				worldTheme = data.world_theme;
				topic = data.topic; // Load topic

				// If world theme exists on load, show the results area
				if (worldTheme) {
					showResults = true;
				}

				// If worldTheme was loaded, we might want to add a simulated assistant message
				// to the chat history to show the user the loaded content in the chat view
				if (worldTheme && chatHistory.length === 0) {
					// Add loaded world theme as an initial assistant message in chat history
					chatHistory = [
						...chatHistory,
						{ role: 'assistant', content: `Loaded existing World Setting:\n\n${worldTheme}` }
					];
					console.log('World.svelte Added loaded world theme to chatHistory'); // Added log
				}
			} catch (error) {
				console.error('World.svelte Failed to load world data:', error); // Added log
				// Handle error loading data - maybe show a message
			}
		})();
	});

	// Effect to add the initial message if provided and chat history is empty AFTER initial load effect
	$effect(() => {
		console.log('World.svelte initial message effect running'); // Added log
		(async () => {
			// Wait for initial load effect to potentially populate chatHistory
			await Promise.resolve(); // Small deferral might be needed

			if (chatHistory.length === 0 && initialChatPrompt) {
				// Add initial AI message if no data was loaded and no prior chat history
				chatHistory = [...chatHistory, { role: 'assistant', content: initialChatPrompt as string }];
				console.log('World.svelte Added initial chat prompt to chatHistory'); // Added log
			}
		})();
	});

	// Effect to derive topic from the first user message if not already set
	// This logic remains the same
	$effect(() => {
		console.log('World.svelte topic derivation effect running'); // Added log
		if (!topic && chatHistory.length > 0) {
			const firstUserMessage = chatHistory.find((msg) => msg.role === 'user');
			if (firstUserMessage) {
				// Simple heuristic: take the first few words of the first message as topic
				const derivedTopic = firstUserMessage.content.split(' ').slice(0, 5).join(' ');
				if (derivedTopic && derivedTopic !== topic) {
					// Added check for derivedTopic not being empty
					topic = derivedTopic;
					console.log('World.svelte Derived topic:', topic); // Added log
					// You might want to save this topic to the backend/session here
					// or handle it during finalization.
				}
			}
		}
	});

	async function finalizeWorld() {
		console.log('World.svelte finalizeWorld called'); // Added log
		// Add check to ensure there are user messages before finalizing
		if (isFinalizeButtonDisabled) {
			// Use the derived state
			alert('Please send at least one message to the AI before finalizing.');
			return;
		}

		let isFinalizing = $state(true); // Local state for finalizing indicator if needed separately from chat's isGenerating
		// isGenerating = true; // You could use the chat component's isGenerating state if preferred
		showResults = false; // Hide potentially old results while generating new

		// Clear previous final world theme while generating new one
		worldTheme = '';
		let finalizeError = $state(''); // Local state for finalize errors

		try {
			console.log('World.svelte Fetching /finalize_world_stream'); // Added log
			const response = await fetch('/finalize_world_stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					chat_history: chatHistory, // Send the full chat history managed by this component
					topic: topic // Send the determined topic
				})
			});

			if (!response.ok) {
				console.error('World.svelte Finalize fetch response not OK', response); // Added log
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Finalize stream request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			const reader = response.body?.getReader();
			if (!reader) {
				console.error('World.svelte No reader available for finalize stream'); // Added log
				throw new Error('No reader available for finalize stream');
			}

			const decoder = new TextDecoder(); // Use a TextDecoder

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value); // Decode the chunk
				const lines = chunk.split('\n').filter((line) => line.trim() !== ''); // Split and filter empty lines

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						try {
							const data = JSON.parse(line.slice(6));
							console.log('World.svelte Received finalize SSE data:', data); // Added log
							if (data.content === '[DONE]') {
								console.log('World.svelte Received finalize [DONE]'); // Added log
								// Stream complete - show the results area
								showResults = true;
								// Optionally clear chat history after finalizing
								// chatHistory = []; // Keep chat history for now, user might want to refine
							} else if (data.content !== undefined) {
								// Ensure content exists
								// Append new content chunk to the final worldTheme state
								worldTheme += data.content;
							}
						} catch (e: any) {
							// Explicitly type error
							console.error('World.svelte Error parsing finalize SSE data line:', e, line); // Added log
							finalizeError = `Error processing stream: ${e.message}`;
							isFinalizing = false;
							showResults = true; // Show results area to display the error
							reader.cancel(); // Cancel the reader to stop the stream
							break; // Stop processing lines
						}
					}
				}
			}
		} catch (error: any) {
			// Explicitly type error
			console.error('World.svelte Error finalizing world:', error); // Added log
			worldTheme = `[Error generating final world: ${error.message}]`; // Display error in the textarea
			showResults = true; // Show the results area even on error
			finalizeError = error.message;
		} finally {
			isFinalizing = false; // Hide generating indicator
			console.log('World.svelte Finalize finally block, setting isFinalizing to false'); // Added log
			// isGenerating = false; // If you used the chat component's state
		}
	}

	async function saveWorld() {
		console.log('World.svelte saveWorld called'); // Added log
		// Clean up the worldTheme text before saving
		const worldThemeCleaned = worldTheme
			.replace(/\r\n/g, '\n')
			.trim()
			.replace(/\n{3,}/g, '\n\n');

		try {
			console.log('World.svelte Fetching /save_world'); // Added log
			const response = await fetch('/save_world', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ world_theme: worldThemeCleaned })
			});

			if (!response.ok) {
				console.error('World.svelte Save fetch response not OK', response); // Added log
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Save request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			console.log('World theme saved successfully'); // Added log
			// Show alert for now
			alert('World theme saved successfully! You can now proceed to the Characters section.');
		} catch (error: any) {
			// Explicitly type error
			console.error('World.svelte Error saving world theme:', error); // Added log
			// Show error message to user
			alert(`Error saving world theme: ${error.message}`);
		}
	}
</script>

<div class="world-container">
	<header>
		<h1>World Building</h1>
		<div class="navigation-buttons">
			<a href="/" class="btn btn-light">&laquo; Back to Home</a>
			<!-- Show "Next" button only if worldTheme is not empty -->
			{#if worldTheme}
				<a href="/characters" class="btn btn-light">Next: Characters &raquo;</a>
			{/if}
		</div>
	</header>

	{#if showChatSection}
		<div class="card chat-card">
			<div class="card-header bg-primary text-white">
				<h3 class="h5 mb-0">World Building Chat</h3>
			</div>

			<!-- Chat HTML structure - Copied from Chat.svelte -->
			<div class="chat-container card-body">
				<p class="lead">
					<!-- Intro text directly in the page -->
					Start by chatting with the AI to develop your book's world. Describe your ideas, answer questions,
					and explore different aspects of your world together.
				</p>

				<div
					id="chatMessages"
					class="chat-messages-area p-3 mb-3 border rounded"
					bind:this={chatMessagesDiv}
				>
					{#each chatHistory as msg (msg.role + msg.content)}
						<div class="message {msg.role}">
							<div class="content">{@html formatMessage(msg.content)}</div>
						</div>
					{/each}

					{#if streamingContent}
						<div class="message assistant">
							<div class="content">
								{@html formatMessage(streamingContent)}<span class="typing-cursor">▌</span>
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
						bind:value={message}
						placeholder="Type your ideas about the world you want to create..."
						onkeydown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
						disabled={isGenerating}
						class="form-control me-2"
					></textarea>
					<button
						onclick={handleSubmit}
						disabled={isGenerating || !message.trim()}
						class="send-button btn btn-primary"
					>
						{isGenerating && !streamingContent ? 'Sending...' : 'Send'}
					</button>
				</div>

				<div class="mt-3 text-center">
					<!-- Below input content (Finalize button) directly in the page -->
					<button
						onclick={finalizeWorld}
						disabled={!!isFinalizeButtonDisabled}
						class="finalize-button btn btn-success"
					>
						Finalize World Setting
					</button>
				</div>
			</div>
			<!-- End Chat HTML structure -->
		</div>
	{/if}

	{#if showWorldResultSection}
		<div class="card results-card">
			<div class="card-header bg-success text-white">
				<h3 class="h5 mb-0">Your World Setting</h3>
			</div>
			<div class="card-body">
				<p class="lead">Edit your world setting if needed, then save.</p>
				<div class="form-group mb-3">
					<label for="worldThemeContent" class="form-label">World Setting Content:</label>
					<textarea id="worldThemeContent" bind:value={worldTheme} rows="12" class="form-control"
					></textarea>
				</div>
				<div class="d-flex justify-content-between">
					<button onclick={saveWorld} class="save-button btn btn-success"> Save Changes </button>
					<a href="/characters" class="btn btn-primary">Continue to Characters</a>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	/* Keep your existing styles or adapt them to fit the new structure */
	.world-container {
		max-width: 800px;
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

	.chat-card,
	.results-card {
		margin-bottom: 2rem;
	}

	/* Styles specific to World.svelte layout, not the chat component internals */
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
		background: #ccc !important;
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
