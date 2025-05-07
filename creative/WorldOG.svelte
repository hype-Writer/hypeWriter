<script lang="ts">
	interface ChatMessage {
		role: 'user' | 'assistant';
		content: string;
	}

	let worldTheme = $state(''); // Stores the finalized/saved world theme
	let topic = $state(''); // Stores the book topic
	let message = $state(''); // User input message
	let chatHistory = $state<ChatMessage[]>([]); // Stores chat messages
	let isGenerating = $state(false); // Indicates if AI is generating
	let streamingContent = $state(''); // Temporarily holds streaming AI response
	let showFullWorld = $state(false); // Toggles visibility of full world theme in result area
	let showResults = $state(false); // Toggles between chat and final result display

	// Derived state to control visibility of chat vs results
	let showChat = $derived(!worldTheme || !showResults);
	let showWorldResult = $derived(worldTheme && showResults);

	// Load existing data when component mounts
	$effect(() => {
		(async () => {
			try {
				const response = await fetch('/api/world');
				const data = await response.json();

				worldTheme = data.world_theme;
				topic = data.topic; // Load topic

				// If world theme exists on load, show the results area
				if (worldTheme) {
					showResults = true;
				}

				// Initial message if no world theme exists
				if (!worldTheme && !chatHistory.length) {
					// Add an initial AI prompt message
					chatHistory.push({
						role: 'assistant',
						content:
							'Tell me about the world you want to create for your book. What kind of setting, time period, or genre are you interested in?'
					});
				}
			} catch (error) {
				console.error('Failed to load world data:', error);
				// Handle error loading data - maybe show a message
			}
		})();
	});

	// Effect to scroll chat to bottom when history or streaming content updates
	$effect(() => {
		// This effect runs after DOM updates
		const chatMessagesDiv = document.getElementById('chatMessages');
		if (chatMessagesDiv) {
			chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
		}
	});

	async function handleSubmit() {
		if (!message.trim()) return;

		const userMessage = message.trim();
		message = ''; // Clear input field
		isGenerating = true; // Show typing indicator

		// Add user message to chat history immediately
		chatHistory = [...chatHistory, { role: 'user', content: userMessage }];

		// Initialize streaming content placeholder for AI's response
		streamingContent = '';

		// Extract topic if this is the first actual user message
		if (!topic && chatHistory.filter((msg) => msg.role === 'user').length === 1) {
			// Simple heuristic: take the first few words of the first message as topic
			topic = userMessage.split(' ').slice(0, 5).join(' ');
			console.log('Derived topic:', topic);
		}

		try {
			const response = await fetch('/world_chat_stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					message: userMessage,
					chat_history: chatHistory.slice(0, -1), // Send history *without* the current user message (it's the 'message' field)
					topic: topic
				})
			});

			if (!response.ok) {
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Stream request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			const reader = response.body?.getReader();
			if (!reader) throw new Error('No reader available for stream');

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = new TextDecoder().decode(value);
				const lines = chunk.split('\n');

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						try {
							const data = JSON.parse(line.slice(6));
							if (data.content === '[DONE]') {
								// Stream complete - add accumulated content to chat history
								chatHistory = [
									...chatHistory,
									{
										role: 'assistant',
										content: streamingContent
									}
								];
								streamingContent = ''; // Clear streaming buffer
							} else {
								// Append new content chunk
								streamingContent += data.content;
							}
						} catch (e) {
							console.error('Error parsing SSE data line:', e, line);
						}
					}
				}
			}
		} catch (error) {
			console.error('Chat stream error:', error);
			// Add an error message to chat history
			chatHistory = [
				...chatHistory,
				{
					role: 'assistant',
					content: `Sorry, there was an error processing your request: ${error.message}`
				}
			];
			streamingContent = ''; // Clear any partial streaming content
		} finally {
			isGenerating = false; // Hide typing indicator
		}
	}

	async function finalizeWorld() {
		isGenerating = true; // Show generating indicator
		showResults = false; // Hide potentially old results while generating new

		// Clear previous final world theme while generating new one
		worldTheme = '';

		try {
			const response = await fetch('/finalize_world_stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					chat_history: chatHistory, // Send the full chat history
					topic: topic // Send the determined topic
				})
			});

			if (!response.ok) {
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Finalize stream request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			const reader = response.body?.getReader();
			if (!reader) throw new Error('No reader available for finalize stream');

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = new TextDecoder().decode(value);
				const lines = chunk.split('\n');

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						try {
							const data = JSON.parse(line.slice(6));
							if (data.content === '[DONE]') {
								// Stream complete - show the results area
								showResults = true;
							} else {
								// Append new content chunk to the final worldTheme state
								worldTheme += data.content;
							}
						} catch (e) {
							console.error('Error parsing SSE data line:', e, line);
						}
					}
				}
			}
		} catch (error) {
			console.error('Error finalizing world:', error);
			worldTheme = `[Error generating final world: ${error.message}]`; // Display error in the textarea
			showResults = true; // Show the results area even on error
		} finally {
			isGenerating = false; // Hide generating indicator
		}
	}

	async function saveWorld() {
		// Clean up the worldTheme text before saving
		const worldThemeCleaned = worldTheme
			.replace(/\r\n/g, '\n')
			.trim()
			.replace(/\n{3,}/g, '\n\n');

		try {
			// UPDATED: Use JSON instead of FormData
			const response = await fetch('/save_world', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json' // Set Content-Type to JSON
				},
				body: JSON.stringify({ world_theme: worldThemeCleaned }) // Send data as JSON string
			});

			if (!response.ok) {
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Save request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			// Optional: show a success message or indication
			console.log('World theme saved successfully');
			// For now, just navigate as in original code
			// history.pushState(null, '', '/characters');
			// window.dispatchEvent(new PopStateEvent('popstate'));
			// If you want a success message in UI:
			// alert('World theme saved successfully!');
		} catch (error) {
			console.error('Error saving world theme:', error);
			// Show error message to user
			alert(`Error saving world theme: ${error.message}`);
		}
	}

	// Helper function to format message content (like adding line breaks)
	function formatMessage(content: string): string {
		// Basic formatting: replace newlines with <br> for display in HTML
		return content.replace(/\n/g, '<br>');
	}
</script>

<div class="world-container">
	<header>
		<h1>World Building</h1>
		<div class="navigation-buttons">
			<a href="/" class="btn btn-light">&laquo; Back to Home</a>
			<a href="/characters" class="btn btn-light">Next: Characters &raquo;</a>
		</div>
	</header>

	{#if !topic && chatHistory.filter((msg) => msg.role === 'user').length > 0 && !isGenerating}
		<div class="alert alert-info">Analyzing your input to determine the book's topic...</div>
	{/if}

	{#if showChat}
		<div class="card chat-card">
			<div class="card-header bg-primary text-white">
				<h3 class="h5 mb-0">World Building Chat</h3>
			</div>
			<div class="card-body">
				<p class="lead">
					Start by chatting with the AI to develop your book's world. Describe your ideas, answer
					questions, and explore different aspects of your world together.
				</p>
				<div id="chatMessages" class="chat-messages-area p-3 mb-3 border rounded">
					{#each chatHistory as msg (msg.role + msg.content)}
						<div class="message {msg.role}">
							<div class="content">{@html formatMessage(msg.content)}</div>
						</div>
					{/each}

					{#if streamingContent}
						<div class="message assistant">
							<!-- Use @html to render formatted text including <br> -->
							<div class="content">
								{@html formatMessage(streamingContent)}<span class="typing-cursor">▌</span>
							</div>
						</div>
					{/if}

					{#if isGenerating}
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
						Send
					</button>
				</div>

				<div class="mt-3 text-center">
					<button
						onclick={finalizeWorld}
						disabled={isGenerating || chatHistory.filter((msg) => msg.role === 'user').length === 0}
						class="finalize-button btn btn-success"
					>
						Finalize World Setting
					</button>
				</div>
			</div>
		</div>
	{/if}

	{#if showWorldResult}
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
	/* Add or adapt styles from your world.html and Characters.svelte */
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

	.chat-messages-area {
		height: 400px; /* Fixed height for chat window */
		overflow-y: auto; /* Enable scrolling */
		display: flex; /* Use flexbox to keep messages at bottom */
		flex-direction: column; /* Stack messages vertically */
		justify-content: flex-end; /* Keep content aligned to the bottom */
	}

	.message {
		margin-bottom: 0.75rem; /* Slightly less space than Characters.svelte */
		padding: 0.75rem; /* Slightly less padding */
		border-radius: 8px; /* More rounded corners */
		max-width: 80%; /* Limit bubble width */
		word-break: break-word; /* Prevent long words from overflowing */
	}

	.message.user {
		background: #e3f2fd;
		align-self: flex-end; /* Align user messages to the right */
	}

	.message.assistant {
		background: #f5f5f5;
		align-self: flex-start; /* Align assistant messages to the left */
	}

	.typing-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		background: #f8f9fa;
		border-radius: 4px;
		margin-top: 0.5rem;
		align-self: flex-start; /* Align indicator to the left */
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
		width: 100%;
		min-height: 60px; /* Smaller default height for chat input */
		padding: 0.75rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-size: 1rem;
		resize: vertical;
	}

	.input-container textarea.form-control {
		flex-grow: 1; /* Allow textarea to fill space */
	}

	button.btn {
		padding: 0.5rem 1rem; /* Smaller button padding */
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
		transition: background-color 0.2s;
	}

	button.btn:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.send-button {
		background: #3498db;
		color: white;
	}

	.send-button:hover:not(:disabled) {
		background: #2980b9;
	}

	.finalize-button {
		background: #2ecc71;
		color: white;
	}

	.finalize-button:hover:not(:disabled) {
		background: #27ae60;
	}

	.save-button {
		background: #2ecc71;
		color: white;
	}

	.save-button:hover {
		background: #27ae60;
	}

	.alert {
		padding: 1rem;
		margin-bottom: 1rem;
		border-radius: 4px;
	}

	.alert-warning {
		background: #fff3cd;
		border: 1px solid #ffeeba;
		color: #856404;
	}

	.alert-info {
		background: #cfe2ff;
		border: 1px solid #b9daff;
		color: #084298;
	}

	.alert-link {
		color: #533f03;
		font-weight: bold;
	}

	/* Style for the blinking cursor during streaming */
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
</style>
