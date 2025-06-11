/**
 * Global project store for managing multiple projects and current project state
 */

interface ProjectMetadata {
  id: string;
  title: string;
  author: string;
  genre: string;
  description: string;
  word_count: number;
  chapter_count: number;
  created_date: string;
  last_modified: string;
}

interface ProjectStore {
  // Current project state
  currentProject: ProjectMetadata | null;
  
  // All available projects
  projects: ProjectMetadata[];
  
  // Loading states
  isLoading: boolean;
  isProjectLoading: boolean;
  
  // Error states
  error: string | null;
  
  // UI state
  showCreateModal: boolean;
  showImportModal: boolean;
}

class ProjectStoreClass {
  private store: ProjectStore = {
    currentProject: null,
    projects: [],
    isLoading: false,
    isProjectLoading: false,
    error: null,
    showCreateModal: false,
    showImportModal: false,
  };

  // Getters for reactive access
  get currentProject() { return this.store.currentProject; }
  get projects() { return this.store.projects; }
  get isLoading() { return this.store.isLoading; }
  get isProjectLoading() { return this.store.isProjectLoading; }
  get error() { return this.store.error; }
  get showCreateModal() { return this.store.showCreateModal; }
  get showImportModal() { return this.store.showImportModal; }

  // Project Management Actions
  async loadProjects() {
    this.store.isLoading = true;
    this.store.error = null;

    try {
      const response = await fetch('/api/projects');
      if (!response.ok) {
        throw new Error(`Failed to load projects: ${response.statusText}`);
      }
      
      const projects = await response.json();
      this.store.projects = projects;
      
      // If no current project, try to load the most recently modified one
      if (!this.store.currentProject && projects.length > 0) {
        await this.setCurrentProject(projects[0].id);
      }
    } catch (error) {
      this.store.error = error instanceof Error ? error.message : 'Failed to load projects';
      console.error('Error loading projects:', error);
    } finally {
      this.store.isLoading = false;
    }
  }

  async setCurrentProject(projectId: string) {
    this.store.isProjectLoading = true;
    this.store.error = null;

    try {
      // Activate the project on the backend
      const response = await fetch(`/api/projects/${projectId}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to activate project: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // Update current project in store
      this.store.currentProject = result.project;
      
      // Update URL without full navigation
      const newUrl = `/project/${projectId}`;
      window.history.pushState({ projectId }, '', newUrl);
      
    } catch (error) {
      this.store.error = error instanceof Error ? error.message : 'Failed to switch project';
      console.error('Error setting current project:', error);
    } finally {
      this.store.isProjectLoading = false;
    }
  }

  async createProject(projectData: {
    title: string;
    author: string;
    genre: string;
    description: string;
  }) {
    this.store.isLoading = true;
    this.store.error = null;

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      });

      if (!response.ok) {
        throw new Error(`Failed to create project: ${response.statusText}`);
      }

      const newProject = await response.json();
      
      // Add to projects list
      this.store.projects = [newProject, ...this.store.projects];
      
      // Set as current project
      await this.setCurrentProject(newProject.id);
      
      // Close modal
      this.store.showCreateModal = false;
      
      return newProject;
    } catch (error) {
      this.store.error = error instanceof Error ? error.message : 'Failed to create project';
      console.error('Error creating project:', error);
      throw error;
    } finally {
      this.store.isLoading = false;
    }
  }

  async deleteProject(projectId: string) {
    this.store.isLoading = true;
    this.store.error = null;

    try {
      const response = await fetch(`/api/projects/${projectId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`Failed to delete project: ${response.statusText}`);
      }

      // Remove from projects list
      this.store.projects = this.store.projects.filter(p => p.id !== projectId);
      
      // If deleted project was current, clear current project
      if (this.store.currentProject?.id === projectId) {
        this.store.currentProject = null;
        
        // Set first available project as current, or redirect to dashboard
        if (this.store.projects.length > 0) {
          await this.setCurrentProject(this.store.projects[0].id);
        } else {
          window.history.pushState({}, '', '/');
        }
      }
      
    } catch (error) {
      this.store.error = error instanceof Error ? error.message : 'Failed to delete project';
      console.error('Error deleting project:', error);
      throw error;
    } finally {
      this.store.isLoading = false;
    }
  }

  async importProject(importData: {
    file_path: string;
    title: string;
    author: string;
    genre: string;
    auto_generate_metadata: boolean;
  }) {
    this.store.isLoading = true;
    this.store.error = null;

    try {
      const response = await fetch('/api/import/novel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importData)
      });

      if (!response.ok) {
        throw new Error(`Failed to import project: ${response.statusText}`);
      }

      const result = await response.json();
      const newProject = result.project;
      
      // Add to projects list
      this.store.projects = [newProject, ...this.store.projects];
      
      // Set as current project
      await this.setCurrentProject(newProject.id);
      
      // Close modal
      this.store.showImportModal = false;
      
      return newProject;
    } catch (error) {
      this.store.error = error instanceof Error ? error.message : 'Failed to import project';
      console.error('Error importing project:', error);
      throw error;
    } finally {
      this.store.isLoading = false;
    }
  }

  // UI Actions
  openCreateModal() {
    this.store.showCreateModal = true;
  }

  closeCreateModal() {
    this.store.showCreateModal = false;
  }

  openImportModal() {
    this.store.showImportModal = true;
  }

  closeImportModal() {
    this.store.showImportModal = false;
  }

  clearError() {
    this.store.error = null;
  }

  // Computed getters
  get hasProjects() {
    return this.store.projects.length > 0;
  }

  get currentProjectIndex() {
    if (!this.store.currentProject) return -1;
    return this.store.projects.findIndex(p => p.id === this.store.currentProject!.id);
  }

  // Initialize store
  async initialize() {
    // Load projects on startup
    await this.loadProjects();
    
    // Check if we're on a project-specific route
    const pathMatch = window.location.pathname.match(/^\/project\/([^\/]+)/);
    if (pathMatch) {
      const projectId = pathMatch[1];
      const project = this.store.projects.find(p => p.id === projectId);
      if (project) {
        await this.setCurrentProject(projectId);
      } else {
        // Project not found, redirect to dashboard
        window.history.pushState({}, '', '/');
      }
    }
  }
}

// Export singleton instance
export const projectStore = new ProjectStoreClass();