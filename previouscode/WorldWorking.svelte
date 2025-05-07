<script lang="ts">
	let { initial_world_theme = '', initial_topic = '' } = $props<{
		initial_world_theme?: string;
		initial_topic?: string;
	}>();

	let chatHistory = $state<{ role: 'user' | 'ai' | 'system'; content: string }[]>([]);
	let userMessageInput = $state('');
	let chatTypingIndicatorVisible = $state(false);
	let worldThemeTextarea = $state('');
	let topic = $state('');
	let loadingInitialData = $state(true);
	let initialDataError = $state<string | null>(null);
	let savingIndicatorVisible = $state(false);
	let savedIndicatorVisible = $state(false);
	let saveError = $state<string | null>(null);
	let finalizeChatButtonDisabled = $state(false);
	let saveWorldButtonDisabled = $state(false);
	let chatSendButtonDisabled = $state(false);

	let isEditingMode = $derived(!loadingInitialData && worldThemeTextarea.length > 0);

	let chatMessagesContainer: HTMLElement;
	let worldThemeTextareaElement: HTMLTextAreaElement;

	$effect(() => {
		// This effect runs once when the component is first mounted because it has no dependencies.
		async function loadInitialWorldData() {
			loadingInitialData = true;
			initialDataError = null;

			try {
				const response = await fetch('/api/world');
				if (!response.ok) {
					// Attempt to read error body if available
					const errorText = await response.text();
					throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
				}
				const data = await response.json();
				// console.log('Fetched initial world data:', data); // Commented out log

				// Update state based on fetched data
				// Use fetched data if available, otherwise fall back to initial props
				worldThemeTextarea = data.world_theme || initial_world_theme;
				topic = data.topic || initial_topic;
			} catch (error: any) {
				console.error('Error loading initial world data:', error);
				initialDataError = `Failed to load initial data: ${error.message}`;
				// Fallback to initial props even on error, if they exist
				worldThemeTextarea = initial_world_theme;
				topic = initial_topic;
			} finally {
				loadingInitialData = false;
				// Re-evaluate button disabled states now that loading is done
				finalizeChatButtonDisabled = isEditingMode;
				saveWorldButtonDisabled = !isEditingMode;
			}
		}

		loadInitialWorldData();
	});

	$effect(() => {
		// Dependency: chatHistory
		if (chatMessagesContainer) {
			chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
		}
	});

	// Effect to scroll world theme textarea to bottom during streaming
	// This runs after Svelte has updated the DOM
	$effect(() => {
		if (worldThemeTextareaElement && isEditingMode && !savingIndicatorVisible) {
			worldThemeTextareaElement.scrollTop = worldThemeTextareaElement.scrollHeight;
		}
	});

	// Function to format messages (e.g., replace newlines)
	function formatMessage(message: string): string {
		return message.replace(/\n/g, '<br>');
	}

	// Function to handle sending a user message
	async function sendUserMessage() {
		const message = userMessageInput.trim();
		if (!message || chatSendButtonDisabled) return;

		chatSendButtonDisabled = true;
		finalizeChatButtonDisabled = true;

		// Add user message to chat history
		chatHistory.push({ role: 'user', content: message });
		userMessageInput = '';

		// Show AI is thinking indicator
		chatTypingIndicatorVisible = true;

		// Add a placeholder for the AI response immediately
		const aiMessageIndex = chatHistory.length;
		chatHistory.push({ role: 'ai', content: '<span class="typing-cursor">▌</span>' });
		// Trigger reactivity explicitly after pushing
		chatHistory = [...chatHistory];

		// Scroll chat immediately after adding message (effect will also handle this)
		if (chatMessagesContainer) {
			chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
		}

		// Extract topic if this is the first user message and topic wasn't already set
		if (chatHistory.filter((msg) => msg.role === 'user').length === 1 && !topic) {
			const topicText = message.split(' ').slice(0, 5).join(' '); // Take first 5 words as topic
			topic = topicText; // Update topic state
		}

		// Prepare request data for the backend API
		const requestData = {
			message: message,
			// Send all previous messages except the current one being processed
			chat_history: chatHistory.slice(0, aiMessageIndex),
			topic: topic
		};

		let responseContent = '';

		try {
			const response = await fetch('/world_chat_stream', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(requestData)
			});

			if (!response.ok || !response.body) {
				// Check response status *before* trying to read body as stream
				const errorText = await response.text();
				throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();

			// Remove the initial typing cursor from the placeholder before streaming
			chatHistory[aiMessageIndex].content = '';
			chatHistory = [...chatHistory];

			// Read and process the stream chunks
			while (true) {
				const { value, done } = await reader.read();
				if (done) {
					break;
				}

				const chunk = decoder.decode(value);

				// Process each event within the chunk
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
								if (data.content) {
									responseContent += data.content;
									// Update the specific AI message in history reactively with new content + cursor
									chatHistory[aiMessageIndex].content =
										formatMessage(responseContent) + '<span class="typing-cursor">▌</span>';
									chatHistory = [...chatHistory];

									// Scroll after each content update during streaming (effect also handles this)
									if (chatMessagesContainer) {
										chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
									}
								}
							} catch (e: any) {
								console.error('Error parsing JSON from stream:', e, jsonData);
								chatHistory[aiMessageIndex].content =
									formatMessage(responseContent) +
									` [Parsing Error: ${e.message}]` +
									'<span class="typing-cursor">▌</span>';
								chatHistory = [...chatHistory];
							}
						}
					});
			}

			// Stream complete
			chatHistory[aiMessageIndex].content = formatMessage(responseContent);
			chatHistory = [...chatHistory];
			chatTypingIndicatorVisible = false;
			chatSendButtonDisabled = false;
			// Re-enable finalize button only if we are still in chat mode (not already finalized)
			if (!isEditingMode) {
				finalizeChatButtonDisabled = false;
			}
		} catch (error: any) {
			console.error('Fetch error during chat streaming:', error);
			chatTypingIndicatorVisible = false;
			chatSendButtonDisabled = false;
			// Re-enable finalize button only if not already finalized
			if (!isEditingMode) {
				finalizeChatButtonDisabled = false;
			}
			// Add error message to the last AI message or as a system message
			if (chatHistory[aiMessageIndex]) {
				// Keep partial content, add error, remove cursor
				chatHistory[aiMessageIndex].content =
					formatMessage(responseContent) + ` [Error: ${error.message}]`;
				chatHistory = [...chatHistory];
			} else {
				chatHistory.push({
					role: 'system',
					content: `Error communicating with AI: ${error.message}. Please check the console.`
				});
				chatHistory = [...chatHistory];
			}
		}
	}

	// Function to finalize the chat and generate the final world setting
	async function finalizeChat() {
		if (finalizeChatButtonDisabled) return;

		chatTypingIndicatorVisible = true;
		finalizeChatButtonDisabled = true;
		chatSendButtonDisabled = true;

		// Clear previous content in the textarea and prepare for streaming
		worldThemeTextarea = '';

		const requestData = {
			chat_history: chatHistory,
			topic: topic
		};

		let responseContent = '';

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

			// Read and process the stream chunks for the final setting
			while (true) {
				const { value, done } = await reader.read();
				if (done) {
					break;
				}

				const chunk = decoder.decode(value);

				// Process each event within the chunk
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
								if (data.content) {
									responseContent += data.content;
									worldThemeTextarea = responseContent;

									// Scroll textarea to follow updates during streaming (effect also handles this)
									if (worldThemeTextareaElement) {
										worldThemeTextareaElement.scrollTop = worldThemeTextareaElement.scrollHeight;
									}
								}
							} catch (e: any) {
								console.error('Error parsing JSON from stream:', e, jsonData);
								worldThemeTextarea += ` [Parsing Error: ${e.message}]`;
							}
						}
					});
			}

			// Stream complete
			chatTypingIndicatorVisible = false;
			finalizeChatButtonDisabled = false;
			chatSendButtonDisabled = true;
		} catch (error: any) {
			console.error('Fetch error for final world setting:', error);
			chatTypingIndicatorVisible = false;
			finalizeChatButtonDisabled = false;
			chatSendButtonDisabled = false;
			worldThemeTextarea =
				`Error finalizing world setting: ${error.message}\n\n` + worldThemeTextarea;
		}
	}

	// Function to handle saving the world theme
	async function saveWorld() {
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
				// Handle non-2xx responses
				const errorText = await response.text();
				throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
			}

			savingIndicatorVisible = false;
			savedIndicatorVisible = true;
			saveWorldButtonDisabled = false;

			// Hide the saved indicator after 3 seconds
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

	// Helper function to navigate
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

		<!-- Loading Indicator -->
		{#if loadingInitialData}
			<div class="col-12 mb-4">
				<div class="alert alert-info d-flex align-items-center" role="status">
					<div class="spinner-border spinner-border-sm me-2" aria-hidden="true"></div>
					Loading world data...
				</div>
			</div>
		{/if}

		<!-- Chat interface section -->
		{#if !isEditingMode && !loadingInitialData}
			<div class="col-12 mb-4">
				<div class="card">
					<div class="card-header bg-primary text-white">
						<h2 class="h5 mb-0">World Building Chat</h2>
					</div>
					<div class="card-body">
						<div
							bind:this={chatMessagesContainer}
							id="chatMessages"
							class="p-3 mb-3 border rounded"
							style="height: 400px; overflow-y: auto"
						>
							{#if chatHistory.length === 0}
								<div class="text-center p-3">
									<p>
										Tell me about the world you want to create for your book. What kind of setting,
										time period, or genre are you interested in?
									</p>
								</div>
							{/if}

							{#each chatHistory as message, index (index)}
								<div
									class="mb-3 {message.role === 'user'
										? 'text-end'
										: message.role === 'ai'
											? 'text-start'
											: 'text-center'}"
								>
									<div
										class="d-inline-block p-2 rounded-3"
										class:bg-primary={message.role === 'user'}
										class:text-white={message.role === 'user'}
										class:bg-light={message.role === 'ai'}
										class:bg-warning={message.role === 'system'}
										style="max-width: 80%"
									>
										{#if message.role === 'system'}
											{message.content}
										{:else}
											{@html formatMessage(message.content)}
										{/if}
									</div>
								</div>
							{/each}
						</div>

						<div class="d-flex">
							<input
								type="text"
								bind:value={userMessageInput}
								class="form-control me-2"
								placeholder="Type your ideas about the world you want to create..."
								onkeypress={(e) => {
									if (e.key === 'Enter') {
										sendUserMessage();
										e.preventDefault();
									}
								}}
								disabled={chatSendButtonDisabled}
							/>
							<button
								onclick={sendUserMessage}
								class="btn btn-primary"
								disabled={chatSendButtonDisabled}
							>
								Send
							</button>
						</div>

						<div class="mt-3">
							<button
								onclick={finalizeChat}
								class="btn btn-success"
								disabled={finalizeChatButtonDisabled}
							>
								Finalize World Setting
							</button>
						</div>

						{#if chatTypingIndicatorVisible}
							<div class="alert alert-info mt-3">
								<div class="d-flex align-items-center">
									<div class="spinner-border spinner-border-sm me-2" role="status">
										<span class="visually-hidden">Loading...</span>
									</div>
									<div>AI is thinking...</div>
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}

		<!-- Final world setting container -->
		{#if isEditingMode}
			<div class="col-12">
				<div class="card">
					<div class="card-header bg-success text-white">
						<h2 class="h5 mb-0">Your World Setting</h2>
					</div>
					<div class="card-body">
						<!-- Corrected onsubmit syntax -->
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
	/* Basic container styling, referencing Home.svelte structure */
	.world-container {
		/* Using a distinct class name */
		max-width: 1200px; /* Increased max-width slightly */
		margin: 0 auto;
		padding: 2rem;
		/* Add any other layout styles as needed */
	}

	/* Basic animation for the typing cursor */
	.typing-cursor {
		display: inline-block;
		animation: blink 1s infinite steps(1);
	}

	@keyframes blink {
		0% {
			opacity: 1;
		}
		50% {
			opacity: 0;
		}
		100% {
			opacity: 1;
		}
	}

	/* Additional styles from the second code block for completeness/comparison */
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

	.card-body .lead {
		margin-bottom: 1.5rem;
	}

	/* Specific chat styles */
	.chat-container {
		padding: 0; /* Removed extra padding if card-body has it */
	}

	.chat-messages-area {
		height: 400px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		word-break: break-word;
		/* Added some padding/margin */
		padding: 0.5rem;
		margin-bottom: 1rem;
	}

	.chat-messages-area .message .content {
		white-space: pre-wrap;
	}

	.message {
		margin-bottom: 0.75rem;
		padding: 0.75rem;
		border-radius: 8px;
		max-width: 80%;
		/* Added specific classes from V2's styling */
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

	/* Assuming form-control handles basic textarea styling */
	/* textarea.form-control {
		min-height: 60px;
		resize: vertical;
	} */

	.input-container textarea.form-control {
		flex-grow: 1;
	}

	button.btn:disabled {
		/* Ensure disabled style is applied */
		opacity: 0.65; /* Standard disabled opacity */
		cursor: not-allowed;
	}
</style>
