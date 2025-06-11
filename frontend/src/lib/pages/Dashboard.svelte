<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '../components/ui/Button.svelte';
	import Card from '../components/ui/Card.svelte';
	import CreateProjectModal from '../components/modals/CreateProjectModal.svelte';
	import { toast } from '../stores/toastStore.ts';

	// State management
	let showCreateModal = $state(false);
	let importFileInput = $state(null);
	let projectStatus = $state({
		hasWorld: false,
		hasCharacters: false,
		hasOutline: false,
		chapterCount: 0
	});
	let currentProject = $state(null);
	let libraryProjects = $state([]);
	let loading = $state(true);
	let libraryLoading = $state(true);
	let error = $state<string | null>(null);

	// Derived journey steps based on actual project status
	let journeySteps = $derived([
		{
			id: 'world',
			number: 1,
			title: 'World Building',
			description: "Create your story's universe",
			action: projectStatus.hasWorld ? 'Edit World' : 'Start World Building',
			completed: projectStatus.hasWorld,
			progress: projectStatus.hasWorld ? 100 : 0
		},
		{
			id: 'characters',
			number: 2,
			title: 'Characters',
			description: 'Develop your cast',
			action: projectStatus.hasCharacters ? 'Edit Characters' : 'Create Characters',
			completed: projectStatus.hasCharacters,
			progress: projectStatus.hasCharacters ? 100 : 0
		},
		{
			id: 'outline',
			number: 3,
			title: 'Outline',
			description: 'Structure your story',
			action: projectStatus.hasOutline ? 'Edit Outline' : 'Create Outline',
			completed: projectStatus.hasOutline,
			progress: projectStatus.hasOutline ? 100 : 0
		},
		{
			id: 'chapters',
			number: 4,
			title: 'Chapters',
			description: 'Write your story',
			action:
				projectStatus.chapterCount > 0
					? `Continue Writing (${projectStatus.chapterCount} chapters)`
					: 'Start Writing',
			completed: false,
			progress: projectStatus.chapterCount > 0 ? Math.min(projectStatus.chapterCount * 10, 100) : 0
		}
	]);

	// Fetch real project status and library from backend
	onMount(async () => {
		await loadDashboardData();
	});

	async function loadDashboardData() {
		try {
			loading = true;
			libraryLoading = true;

			// Fetch all data in parallel
			const [statusResponse, currentResponse, libraryResponse] = await Promise.all([
				fetch('/api/project-status'),
				fetch('/api/projects/current'),
				fetch('/api/library')
			]);

			if (!statusResponse.ok) {
				throw new Error(`HTTP error! status: ${statusResponse.status}`);
			}
			let initialStatus = await statusResponse.json();

			if (currentResponse.ok) {
				const currentData = await currentResponse.json();
				currentProject = currentData.current_project;
			}

			if (libraryResponse.ok) {
				libraryProjects = await libraryResponse.json();
			}

			// Load actual JSON files from current project to get real progress
			if (currentProject) {
				projectStatus = await loadActualProjectData(currentProject.id, initialStatus);
			} else {
				projectStatus = initialStatus;
			}
		} catch (err) {
			console.error('Failed to fetch data:', err);
			error = 'Failed to load project data';
		} finally {
			loading = false;
			libraryLoading = false;
		}
	}

	async function loadActualProjectData(projectId, fallbackStatus) {
		try {
			// Check for actual JSON files in the project
			const [worldResponse, charactersResponse, outlineResponse, chaptersResponse] = await Promise.all([
				fetch(`/api/projects/${projectId}/world.json`).catch(() => ({ ok: false })),
				fetch(`/api/projects/${projectId}/characters.json`).catch(() => ({ ok: false })),
				fetch(`/api/projects/${projectId}/outline.json`).catch(() => ({ ok: false })),
				fetch(`/api/projects/${projectId}/chapters.json`).catch(() => ({ ok: false }))
			]);

			let hasWorld = false;
			let hasCharacters = false;
			let hasOutline = false;
			let chapterCount = 0;

			// Check world data
			if (worldResponse.ok) {
				try {
					const worldData = await worldResponse.json();
					hasWorld = worldData && (worldData.world_theme || worldData.content) && 
							  (worldData.world_theme?.trim().length > 50 || worldData.content?.trim().length > 50);
				} catch (e) {
					// Check if world.txt exists instead
					const worldTxtResponse = await fetch(`/api/projects/${projectId}/world.txt`).catch(() => ({ ok: false }));
					if (worldTxtResponse.ok) {
						const worldText = await worldTxtResponse.text();
						hasWorld = worldText && worldText.trim().length > 50;
					}
				}
			}

			// Check characters data
			if (charactersResponse.ok) {
				try {
					const charactersData = await charactersResponse.json();
					hasCharacters = charactersData && 
								   (Array.isArray(charactersData) ? charactersData.length > 0 : 
									(charactersData.characters?.length > 0 || charactersData.content?.trim().length > 50));
				} catch (e) {
					// Check if characters.txt exists instead
					const charactersTxtResponse = await fetch(`/api/projects/${projectId}/characters.txt`).catch(() => ({ ok: false }));
					if (charactersTxtResponse.ok) {
						const charactersText = await charactersTxtResponse.text();
						hasCharacters = charactersText && charactersText.trim().length > 50;
					}
				}
			}

			// Check outline data
			if (outlineResponse.ok) {
				try {
					const outlineData = await outlineResponse.json();
					hasOutline = outlineData && 
								(outlineData.outline?.trim().length > 50 || 
								 outlineData.content?.trim().length > 50 ||
								 Array.isArray(outlineData.chapters) && outlineData.chapters.length > 0);
				} catch (e) {
					// Check if outline.txt exists instead
					const outlineTxtResponse = await fetch(`/api/projects/${projectId}/outline.txt`).catch(() => ({ ok: false }));
					if (outlineTxtResponse.ok) {
						const outlineText = await outlineTxtResponse.text();
						hasOutline = outlineText && outlineText.trim().length > 50;
					}
				}
			}

			// Check chapters data
			if (chaptersResponse.ok) {
				try {
					const chaptersData = await chaptersResponse.json();
					if (Array.isArray(chaptersData)) {
						chapterCount = chaptersData.length;
					} else if (chaptersData.chapters && Array.isArray(chaptersData.chapters)) {
						chapterCount = chaptersData.chapters.length;
					} else if (chaptersData.chapter_count) {
						chapterCount = chaptersData.chapter_count;
					}
				} catch (e) {
					// Fallback to checking chapters directory
					const chapterDirResponse = await fetch(`/api/projects/${projectId}/chapters/`).catch(() => ({ ok: false }));
					if (chapterDirResponse.ok) {
						try {
							const dirData = await chapterDirResponse.json();
							if (Array.isArray(dirData)) {
								chapterCount = dirData.filter(file => file.name.endsWith('.txt') || file.name.endsWith('.md')).length;
							}
						} catch (e2) {
							// Use fallback status
							chapterCount = fallbackStatus.chapterCount || 0;
						}
					}
				}
			}

			return {
				hasWorld,
				hasCharacters,
				hasOutline,
				chapterCount
			};
		} catch (err) {
			console.error('Error loading actual project data:', err);
			return fallbackStatus;
		}
	}

	function navigateToStep(stepId: string) {
		// Use client-side routing instead of full page redirect
		window.history.pushState({}, '', `/${stepId}`);
		
		// Trigger a popstate event to update the router
		window.dispatchEvent(new PopStateEvent('popstate'));
	}

	async function handleCreateProject() {
		showCreateModal = true;
	}

	async function handleProjectCreated(projectData) {
		// Refresh library and switch to new project
		try {
			// Switch to the new project
			const switchResponse = await fetch(`/api/library/switch/${projectData.id}`, {
				method: 'POST'
			});

			if (switchResponse.ok) {
				// Reload all dashboard data instead of full page refresh
				await loadDashboardData();
				toast.success(`Switched to project: ${projectData.title}`);
			}
		} catch (err) {
			console.error('Failed to switch to new project:', err);
			toast.error('Failed to switch to new project');
		}
		showCreateModal = false;
	}

	async function handleSwitchProject(projectId) {
		try {
			const response = await fetch(`/api/library/switch/${projectId}`, {
				method: 'POST'
			});

			if (response.ok) {
				// Reload dashboard data instead of full page refresh
				await loadDashboardData();
				const project = libraryProjects.find(p => p.id === projectId);
				if (project) {
					toast.success(`Switched to project: ${project.title}`);
				}
			} else {
				toast.error('Failed to switch project');
			}
		} catch (err) {
			console.error('Failed to switch project:', err);
			toast.error('Failed to switch project');
		}
	}

	async function handleCleanupLibrary() {
		try {
			const response = await fetch('/api/library/cleanup', {
				method: 'POST'
			});
			
			if (response.ok) {
				const result = await response.json();
				toast.success(`Cleanup completed! Removed ${result.removed_count} orphaned entries. ${result.remaining_count} projects remaining.`);
				// Refresh dashboard data
				await loadDashboardData();
			}
		} catch (err) {
			console.error('Failed to cleanup library:', err);
			toast.error('Failed to cleanup library');
		}
	}

	function handleImportProject() {
		// Trigger file input
		if (importFileInput) {
			importFileInput.click();
		}
	}

	async function handleFileImport(event) {
		const file = event.target.files[0];
		if (!file) return;

		// Check file type
		const allowedTypes = ['.docx', '.odt', '.epub'];
		const fileExt = '.' + file.name.split('.').pop().toLowerCase();
		if (!allowedTypes.includes(fileExt)) {
			toast.error(`Unsupported file type. Please use: ${allowedTypes.join(', ')}`);
			return;
		}

		toast.info('Analyzing file for import...');

		try {
			// Create FormData for file upload
			const formData = new FormData();
			formData.append('file', file);

			// Analyze the file first
			const analyzeResponse = await fetch('/api/import/analyze', {
				method: 'POST',
				body: formData
			});

			if (!analyzeResponse.ok) {
				const error = await analyzeResponse.text();
				toast.error(`Analysis failed: ${error}`);
				return;
			}

			const analysis = await analyzeResponse.json();
			toast.success(`Found ${analysis.chapter_count} chapters. Importing "${analysis.title}"...`);

			// Import the novel
			const importFormData = new FormData();
			importFormData.append('file', file);

			const importResponse = await fetch('/api/import/novel', {
				method: 'POST',
				body: importFormData
			});

			if (!importResponse.ok) {
				const error = await importResponse.text();
				toast.error(`Import failed: ${error}`);
				return;
			}

			const result = await importResponse.json();
			toast.success(`Successfully imported "${result.title}" with ${result.chapter_count} chapters!`);

			// Switch to the imported project (this will refresh all data)
			if (result.project_id) {
				await handleSwitchProject(result.project_id);
			} else {
				// If no project_id, just refresh the data
				await loadDashboardData();
			}

		} catch (err) {
			console.error('Import failed:', err);
			toast.error('Import failed. Please try again.');
		} finally {
			// Reset file input
			event.target.value = '';
		}
	}

	async function handleDeleteProject(projectId, projectTitle) {
		// Show warning toast with action required
		toast.warning(`Click delete again to confirm deletion of "${projectTitle}" - this cannot be undone!`);
		
		// Simple double-click protection instead of confirm dialog
		const button = event.target.closest('button');
		if (!button.dataset.confirmDelete) {
			button.dataset.confirmDelete = 'true';
			setTimeout(() => {
				delete button.dataset.confirmDelete;
			}, 3000); // Reset after 3 seconds
			return;
		}

		try {
			const response = await fetch(`/api/projects/${projectId}`, {
				method: 'DELETE'
			});

			if (response.ok) {
				toast.success(`"${projectTitle}" deleted successfully`);
				// Refresh all dashboard data
				await loadDashboardData();
			} else {
				const error = await response.text();
				toast.error(`Failed to delete project: ${error}`);
			}
		} catch (err) {
			console.error('Delete failed:', err);
			toast.error('Failed to delete project');
		}
	}

	// Calculate overall completion using Svelte 5 derived
	const overallProgress = $derived(
		Math.round(journeySteps.reduce((sum, step) => sum + step.progress, 0) / journeySteps.length)
	);
</script>

<div class="dashboard">
	<!-- Main Content -->
	<main class="dashboard-main">
		{#if loading}
			<div class="loading-state">
				<div class="loading-spinner"></div>
				<p>Loading project status...</p>
			</div>
		{:else if error}
			<div class="error-state">
				<p class="error-message">{error}</p>
				<Button variant="outline" onclick={() => window.location.reload()}>Retry</Button>
			</div>
		{:else}
			<!-- Journey Section -->
			<section class="journey-section">
				<div class="journey-grid">
					{#each journeySteps as step}
						<Card
							variant="journey"
							clickable={true}
							completed={step.completed}
							progress={step.progress}
							onclick={() => navigateToStep(step.id)}
						>
							<div class="journey-card">
								<div class="journey-card-header">
									<div class="journey-number">{step.number}</div>
									<h3 class="journey-title">{step.title}</h3>
								</div>

								<p class="journey-description">{step.description}</p>

								<div class="journey-footer">
									<div class="journey-progress">
										<span class="progress-text">{step.progress}%</span>
										<div class="progress-bar-mini">
											<div class="progress-fill" style="width: {step.progress}%"></div>
										</div>
									</div>

									<Button variant="outline" size="sm">
										{step.action}
									</Button>
								</div>
							</div>
						</Card>
					{/each}
				</div>
			</section>

			<!-- Bottom Section -->
			<div class="bottom-section">
				<!-- Library -->
				<Card variant="default" padding="lg">
					<div class="library-section">
						<h3 class="library-title">Project Library</h3>

						{#if libraryLoading}
							<div class="library-loading">
								<div class="loading-spinner"></div>
								<p>Loading library...</p>
							</div>
						{:else if libraryProjects.length === 0}
							<p class="library-empty">
								No projects yet. Create your first project to get started!
							</p>
						{:else}
							<div class="library-grid">
								{#each libraryProjects as project}
									<div class="library-item {currentProject && project.id === currentProject.id ? 'active' : ''}">
										<div class="library-item-content" onclick={() => handleSwitchProject(project.id)}>
											<div class="library-item-header">
												<h4 class="library-item-title">{project.title}</h4>
												<div class="library-item-meta">
													<span class="library-item-progress">{project.chapter_count} chapters</span>
													{#if currentProject && project.id === currentProject.id}
														<span class="active-indicator">Active</span>
													{/if}
												</div>
											</div>
											<p class="library-item-author">by {project.author}</p>
											{#if project.description}
												<p class="library-item-description">{project.description}</p>
											{/if}
										</div>
										<div class="library-item-actions">
											<button 
												class="delete-button"
												onclick={(e) => {
													e.stopPropagation();
													handleDeleteProject(project.id, project.title);
												}}
												aria-label="Delete project"
												title="Delete project"
											>
												<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
													<path d="M5.5 5.5A.5.5 0 016 6v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm2.5 0a.5.5 0 01.5.5v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm3 .5a.5.5 0 00-1 0v6a.5.5 0 001 0V6z"/>
													<path fill-rule="evenodd" d="M14.5 3a1 1 0 01-1 1H13v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h-.5a1 1 0 01-1-1V2a1 1 0 011-1H5a1 1 0 011-1h4a1 1 0 011 1h2.5a1 1 0 011 1v1zM4.118 4L4 4.059V13a1 1 0 001 1h6a1 1 0 001-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
												</svg>
											</button>
										</div>
									</div>
								{/each}
							</div>
						{/if}

						<div class="library-actions">
							<Button variant="outline" onclick={handleCreateProject}>New Project</Button>
							<Button variant="secondary" onclick={handleImportProject}>Import Story</Button>
							<Button variant="ghost" size="sm" onclick={handleCleanupLibrary}>Clean Up</Button>
						</div>
					</div>
				</Card>

				<!-- Quick Stats -->
				<Card variant="default" padding="lg">
					<div class="stats-section">
						<h3 class="stats-title">Project Statistics</h3>
						
						{#if currentProject}
							<div class="current-project-info">
								<h4 class="current-project-title">{currentProject.title}</h4>
								<p class="current-project-author">by {currentProject.author}</p>
							</div>
						{:else}
							<div class="current-project-info">
								<p class="no-project-text">No project selected</p>
							</div>
						{/if}

						<div class="stats-grid">
							<div class="stat-item">
								<span class="stat-icon">📖</span>
								<span class="stat-number">{projectStatus.chapterCount}</span>
								<span class="stat-desc">Chapters Written</span>
							</div>
							<div class="stat-item">
								<span class="stat-icon">🌍</span>
								<span class="stat-number">{projectStatus.hasWorld ? '1' : '0'}</span>
								<span class="stat-desc">World Created</span>
							</div>
							<div class="stat-item">
								<span class="stat-icon">👥</span>
								<span class="stat-number">{projectStatus.hasCharacters ? '✓' : '—'}</span>
								<span class="stat-desc">Characters</span>
							</div>
							<div class="stat-item">
								<span class="stat-icon">📝</span>
								<span class="stat-number">{projectStatus.hasOutline ? '✓' : '—'}</span>
								<span class="stat-desc">Outline</span>
							</div>
						</div>
					</div>
				</Card>
			</div>
		{/if}
	</main>
</div>

<!-- Modals -->
{#if showCreateModal}
	<CreateProjectModal
		onClose={() => (showCreateModal = false)}
		onProjectCreated={handleProjectCreated}
	/>
{/if}

<!-- Hidden file input for import -->
<input
	type="file"
	accept=".docx,.odt,.epub"
	style="display: none;"
	bind:this={importFileInput}
	onchange={handleFileImport}
/>

<style>
	.dashboard {
		background: transparent;
		padding: var(--space-6);
		position: relative;
		/* Ensure dashboard content is visible over MDR background */
		isolation: isolate;
	}


	/* Main Content */
	.dashboard-main {
		max-width: 1400px;
		margin: 0 auto;
	}

	.section-title {
		font-size: var(--font-size-3xl);
		color: var(--color-text-accent);
		margin-bottom: var(--space-8);
		font-weight: var(--font-weight-semibold);
	}

	/* Journey Section */
	.journey-section {
		margin-bottom: var(--space-12);
	}

	.journey-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: var(--space-6);
	}

	.journey-card {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.journey-card-header {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		margin-bottom: var(--space-4);
	}

	.journey-number {
		width: 2rem;
		height: 2rem;
		background: var(--color-bg-secondary);
		color: var(--color-text-accent);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: var(--font-weight-semibold);
		font-size: var(--font-size-sm);
		flex-shrink: 0;
	}

	.journey-title {
		font-size: var(--font-size-lg);
		color: var(--color-text-primary);
		margin: 0;
	}

	.journey-description {
		color: var(--color-text-secondary);
		font-size: var(--font-size-sm);
		margin-bottom: var(--space-4);
		flex: 1;
	}

	.journey-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		margin-top: auto;
	}

	.journey-progress {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.progress-text {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.progress-bar-mini {
		height: 4px;
		background: var(--color-bg-secondary);
		border-radius: var(--radius-sm);
		overflow: hidden;
		width: 100%;
	}

	.progress-fill {
		height: 100%;
		background: var(--color-primary);
		transition: width var(--transition-slow);
	}

	/* Bottom Section */
	.bottom-section {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-8);
	}

	.about-section {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.about-title {
		font-size: var(--font-size-2xl);
		color: var(--color-text-accent);
		margin-bottom: var(--space-4);
	}

	.about-description {
		color: var(--color-text-secondary);
		line-height: 1.6;
		margin-bottom: var(--space-6);
		flex: 1;
	}

	.about-actions {
		display: flex;
		gap: var(--space-3);
		margin-top: auto;
	}

	.progress-section {
		height: 100%;
	}

	.progress-title {
		font-size: var(--font-size-2xl);
		color: var(--color-text-accent);
		margin-bottom: var(--space-6);
	}

	.progress-grid {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.progress-item {
		display: grid;
		grid-template-columns: 4rem 1fr 3rem;
		align-items: center;
		gap: var(--space-3);
	}

	.progress-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		font-weight: var(--font-weight-medium);
	}

	.progress-bar-container {
		height: 0.5rem;
		background: rgba(255, 255, 255, 0.1);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.progress-bar {
		height: 100%;
		border-radius: var(--radius-lg);
		transition: width var(--transition-slow);
		position: relative;

		/* Subtle glow effect */
		box-shadow: 0 0 10px currentColor;
	}

	.progress-value {
		font-size: var(--font-size-sm);
		color: var(--color-text-primary);
		font-weight: var(--font-weight-medium);
		text-align: right;
	}

	/* Library Section */
	.library-section {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.library-title {
		font-size: var(--font-size-2xl);
		color: var(--color-text-accent);
		margin-bottom: var(--space-6);
	}

	.library-loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-8);
	}

	.library-empty {
		color: var(--color-text-muted);
		font-style: italic;
		text-align: center;
		padding: var(--space-8);
	}

	.library-grid {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		margin-bottom: var(--space-6);
		max-height: 300px;
		overflow-y: auto;
	}

	.library-item {
		display: flex;
		align-items: flex-start;
		gap: var(--space-3);
		padding: var(--space-4);
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		transition: all var(--transition-base);
	}

	.library-item:hover {
		background: var(--color-bg-tertiary);
		border-color: var(--color-border-hover);
		transform: translateY(-1px);
	}

	.library-item-content {
		flex: 1;
		cursor: pointer;
	}

	.library-item-actions {
		flex-shrink: 0;
		display: flex;
		align-items: flex-start;
		gap: var(--space-2);
	}

	.delete-button {
		background: none;
		border: none;
		color: var(--color-text-muted);
		cursor: pointer;
		padding: var(--space-1);
		border-radius: var(--radius-sm);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all var(--transition-fast);
		opacity: 0.7;
	}

	.delete-button:hover {
		background: rgba(239, 68, 68, 0.1);
		color: var(--color-error);
		opacity: 1;
	}

	.delete-button:focus-visible {
		outline: 2px solid var(--color-error);
		outline-offset: 2px;
	}

	.library-item.active {
		background: var(--color-bg-tertiary);
		border-color: var(--color-cyan-bright);
		box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
	}

	.library-item-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--space-1);
	}

	.library-item-meta {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: var(--space-1);
	}

	.active-indicator {
		font-size: var(--font-size-xs);
		color: var(--color-cyan-bright);
		background: rgba(0, 212, 255, 0.1);
		padding: var(--space-1) var(--space-2);
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-medium);
	}

	.library-item-title {
		font-size: var(--font-size-base);
		color: var(--color-text-primary);
		margin: 0;
		font-weight: var(--font-weight-semibold);
	}

	.library-item-progress {
		font-size: var(--font-size-xs);
		color: var(--color-text-accent);
		background: var(--color-bg-card);
		padding: var(--space-1) var(--space-2);
		border-radius: var(--radius-sm);
	}

	.library-item-author {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		margin: 0 0 var(--space-1) 0;
	}

	.library-item-description {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin: 0;
		line-height: 1.4;
	}

	.library-actions {
		display: flex;
		gap: var(--space-3);
		margin-top: auto;
	}

	/* Stats Section */
	.stats-section {
		height: 100%;
	}

	.stats-title {
		font-size: var(--font-size-2xl);
		color: var(--color-text-accent);
		margin-bottom: var(--space-6);
	}

	.current-project-info {
		margin-bottom: var(--space-6);
		padding: var(--space-4);
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
	}

	.current-project-title {
		font-size: var(--font-size-lg);
		color: var(--color-text-accent);
		margin: 0 0 var(--space-1) 0;
		font-weight: var(--font-weight-semibold);
	}

	.current-project-author {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin: 0;
	}

	.no-project-text {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		margin: 0;
		text-align: center;
		font-style: italic;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-6);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: var(--space-2);
	}

	.stat-icon {
		font-size: 2rem;
		opacity: 0.8;
	}

	.stat-number {
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-accent);
	}

	.stat-desc {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	/* Loading and Error States */
	.loading-state,
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		gap: var(--space-4);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-border);
		border-top: 3px solid var(--color-primary);
		border-radius: 50%;
		animation: var(--animation-spin);
	}

	.error-message {
		color: var(--color-error);
		font-size: var(--font-size-lg);
	}

	/* Responsive Design */
	@media (max-width: 1200px) {
		.bottom-section {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.dashboard {
			padding: 0;
		}

		.journey-grid {
			grid-template-columns: 1fr;
		}

		.about-actions {
			flex-direction: column;
		}

		.about-actions :global(button) {
			width: 100%;
		}

		.progress-item {
			grid-template-columns: 1fr;
			gap: var(--space-2);
		}

		.progress-value {
			text-align: left;
		}

		.stats-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
