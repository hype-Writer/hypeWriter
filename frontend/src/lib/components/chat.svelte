<script lang="ts">
	import type { Snippet } from 'svelte';

	interface ChatMessage {
		role: 'user' | 'assistant' | 'system';
		content: string;
		id?: number;
	}

	let {
		chatEndpoint,
		chatHistory = $bindable(),
		contextData = {},
		placeholderText = 'Type your message...',
		introText,
		belowInput,
		isGenerating = $bindable(false),
		topic = $bindable('')
	} = $props<{
		chatEndpoint: string;
		chatHistory: ChatMessage[];
		contextData?: Record<string, any>;
		placeholderText?: string;
		introText?: Snippet;
		belowInput?: Snippet;
		isGenerating?: boolean;
		topic?: string;
	}>();

	let message = $state('');
	let chatMessagesDiv: HTMLElement;

	$effect(() => {
		if (chatMessagesDiv) {
			chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
		}
	});

	async function handleSubmit() {
		const userMessage = message.trim();
		if (!userMessage || isGenerating) return;

		message = '';
		isGenerating = true;

		chatHistory = [...chatHistory, { role: 'user', content: userMessage }];

		if (!topic && chatHistory.filter((msg) => msg.role === 'user').length === 1) {
			topic = userMessage.split(' ').slice(0, 5).join(' ');
			console.log('Derived topic:', topic);
		}

		let aiMessageIndex = chatHistory.length;
		chatHistory = [
			...chatHistory,
			{ role: 'assistant', content: '<span class="typing-cursor">▌</span>' }
		];
		chatHistory = [...chatHistory];

		const requestData = {
			message: userMessage,
			chat_history: chatHistory.slice(0, aiMessageIndex),
			...contextData,
			topic: topic
		};

		let responseContent = '';

		try {
			const response = await fetch(chatEndpoint, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(requestData)
			});

			if (!response.ok || !response.body) {
				const errorDetail = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(
					`Chat stream request failed: ${response.status} ${response.statusText} - ${errorDetail.detail}`
				);
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();

			if (chatHistory[aiMessageIndex]) {
				chatHistory[aiMessageIndex].content = '';
				chatHistory = [...chatHistory];
			} else {
				chatHistory = [...chatHistory, { role: 'assistant', content: '' }];
				aiMessageIndex = chatHistory.length - 1;
				chatHistory = [...chatHistory];
			}

			while (true) {
				const { done, value } = await reader.read();
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
									if (chatHistory[aiMessageIndex]) {
										chatHistory[aiMessageIndex].content =
											formatMessage(responseContent) + '<span class="typing-cursor">▌</span>';
										chatHistory = [...chatHistory];
									}
								}
							} catch (e: any) {
								console.error('Error parsing SSE data line:', e, jsonData);
								if (chatHistory[aiMessageIndex]) {
									chatHistory[aiMessageIndex].content =
										formatMessage(responseContent) +
										` [Parsing Error: ${e.message}]` +
										'<span class="typing-cursor">▌</span>';
									chatHistory = [...chatHistory];
								}
							}
						}
					});
			}

			if (chatHistory[aiMessageIndex]) {
				chatHistory[aiMessageIndex].content = formatMessage(responseContent);
				chatHistory = [...chatHistory];
			}
		} catch (error: any) {
			console.error('Chat stream fetch error:', error);
			if (chatHistory[aiMessageIndex]) {
				chatHistory[aiMessageIndex].content =
					formatMessage(responseContent) + ` [Error: ${error.message}]`;
				chatHistory = [...chatHistory];
			} else {
				chatHistory = [
					...chatHistory,
					{
						role: 'system',
						content: `Error communicating with AI: ${error.message}. Please check the console.`
					}
				];
				chatHistory = [...chatHistory];
			}
		} finally {
			isGenerating = false;
		}
	}

	function formatMessage(content: string): string {
		return content.replace(/\n{2,}/g, '<br><br>').replace(/\n/g, '<br>');
	}
</script>

<div class="chat-container">
	{#if introText}
		{@render introText()}
	{/if}

	<div
		id="chatMessages"
		class="chat-messages-area p-3 mb-3 border rounded"
		bind:this={chatMessagesDiv}
	>
		{#each chatHistory as msg, index (index)}
			<div class="message {msg.role}">
				<div class="content">{@html formatMessage(msg.content)}</div>
			</div>
		{/each}

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
			placeholder={placeholderText}
			onkeydown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
			disabled={isGenerating}
			class="form-control me-2"
		></textarea>
		<button
			onclick={handleSubmit}
			disabled={isGenerating || !message.trim()}
			class="send-button btn btn-primary"
		>
			{isGenerating ? '...' : 'Send'}
		</button>
	</div>

	<div class="mt-3 text-center">
		{#if belowInput}
			{@render belowInput()}
		{/if}
	</div>
</div>

<style>
	.chat-messages-area {
		height: 400px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		word-break: break-word;
		padding: 0.5rem;
		margin-bottom: 1rem;
		justify-content: flex-end;
	}

	.chat-messages-area .message .content {
		white-space: pre-wrap;
	}

	.message {
		margin-bottom: 0.75rem;
		padding: 0.75rem;
		border-radius: 8px;
		max-width: 80%;
		word-break: break-word;
	}

	.message.user {
		background: #e3f2fd;
		align-self: flex-end;
	}

	.message.assistant {
		background: #f5f5f5;
		align-self: flex-start;
	}

	.message.system {
		background: #fff3cd;
		color: #664d03;
		align-self: center;
		font-style: italic;
		text-align: center;
		max-width: 100%;
	}

	.typing-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: #e9ecef;
		border-radius: 4px;
		margin-top: 0.5rem;
		align-self: flex-start;
		font-style: italic;
		color: #6c757d;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid #dee2e6;
		border-top: 2px solid #0d6efd;
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
</style>
