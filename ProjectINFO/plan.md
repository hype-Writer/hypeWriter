# Project Plan: HypeWriter - Svelte Frontend and Feature Expansion

## I. Project Overview

This document outlines the plan for migrating the HypeWriter project to a Svelte-based frontend, as well as integrating new features for short story and full novel content generation. The existing backend is built with FastAPI, and the current UI is served using Jinja2 templates. This plan details the steps required to transition to a modern, reactive frontend using Svelte, and to incorporate the new AI-powered content generation capabilities.

## II. Svelte Frontend Migration

**Goal:** Replace the existing Jinja2 templates with a fully implemented Svelte frontend.

**Steps:**

1.  **Set up a new Svelte project:**

    *   Use `npm create vite@latest` or similar to initialize a new Svelte project in a separate directory (e.g., `frontend`).
    *   Configure the Svelte project with TypeScript for improved code maintainability.
    *   Set up ESLint and Prettier for consistent code style.
2.  **Identify and recreate UI components in Svelte:**

    *   Analyze the existing Jinja2 templates (`templates/`) and identify reusable UI components (e.g., chat interface, form elements, progress indicators, navigation).
    *   Recreate these components in Svelte, focusing on modularity and reusability.
    *   Implement Svelte stores for managing application state (e.g., world theme, characters, outline, chapters).
3.  **Implement API calls to the FastAPI backend:**

    *   Use `fetch` or a library like `axios` to make API calls to the FastAPI backend endpoints.
    *   Define TypeScript interfaces for request and response data to ensure type safety.
    *   Implement error handling for API calls, displaying user-friendly error messages.
4.  **Replace Jinja2 templates with Svelte components:**

    *   Replace the existing HTML templates in FastAPI with a single entry point that serves the Svelte application.
    *   Ensure that the Svelte app handles all routing and rendering of UI components.
    *   Remove the `templates/` directory and Jinja2-related code from the FastAPI backend.
5.  **Update routing to use Svelte's routing:**

    *   Implement client-side routing using `svelte-navigator` or a similar library.
    *   Map Svelte routes to the corresponding UI components.
    *   Ensure that all navigation links and redirects are updated to use the new Svelte routes.

## III. Experiment: Svelte Single-File Compilation

**Goal:** Investigate if Svelte can compile the entire frontend into a single, static HTML/JS/CSS file for simplified deployment with FastAPI.

**Steps:**

1.  **Configure Svelte build process:**

    *   Explore Svelte build configurations (e.g., using Vite) to output a single HTML file with embedded JavaScript and CSS.
2.  **Integrate with FastAPI:**

    *   Place the generated HTML file in the FastAPI `static/` directory.
    *   Create a FastAPI route that serves this single HTML file.
    *   Test if the Svelte application functions correctly when served this way.

**Potential Benefits:**

*   Simplified deployment: Easier to deploy and manage a single static file.
*   Potentially improved performance: Reduced overhead compared to serving multiple files.

**Potential Challenges:**

*   Limited flexibility: May be difficult to integrate with more complex backend logic or dynamic content.
*   Increased file size: A single file may be larger than multiple smaller files, potentially impacting load times.

## IV. Short Story Integration

**Goal:** Allow users to provide an existing short story, have the AI analyze it, and automatically generate the initial World, Characters, and Outline for a new novel project based on that story.

**Steps:**

1.  **Create UI components for short story input and analysis:**

    *   Add a new page or section in the Svelte frontend for importing short stories.
    *   Implement a `<textarea>` element for pasting short story text.
    *   Optionally, add an `<input type="file">` element for uploading `.txt` files.
    *   Add a button to trigger the analysis and project generation process.
2.  **Implement API endpoint calls for short story analysis and project generation:**

    *   Create a new FastAPI endpoint (e.g., `/analyze_story`) that receives the short story text as input.
    *   Implement the logic in `agents.py` to analyze the short story and generate the world, characters, and outline.
    *   Save the generated data to the appropriate files (`book_output/world.txt`, `book_output/characters.txt`, `book_output/outline.txt`, `book_output/chapters.json`).
3.  **Integrate the generated project data into the existing UI:**

    *   Update the Svelte stores with the generated world, characters, and outline data.
    *   Navigate the user to the appropriate page (e.g., `/world`, `/characters`, `/outline`) to review and edit the generated content.

## V. Full Novel Integration

**Goal:** Allow users to upload a completed novel (~85k words), enable the AI to gain a deep, searchable understanding of its content (themes, characters, world, plot), and generate new, consistent content (scenes, chapters, answers) based on that understanding.

**Steps:**

1.  **Design UI for novel uploading and processing:**

    *   Add a new page or section in the Svelte frontend for importing full novels.
    *   Implement a file upload input (`<input type="file">`) that accepts `.txt`, `.docx`, or `.epub` files.
    *   Display a progress bar to indicate the upload and processing status.
2.  **Implement API endpoints for novel processing and indexing:**

    *   Create a new FastAPI endpoint (e.g., `/process_novel`) that receives the uploaded novel file.
    *   Implement the logic for extracting text content, chunking the text, generating embeddings, and indexing the content in a vector database (ChromaDB, Pinecone, etc.).
    *   Store high-level summaries of the novel (plot, themes, characters) for quick reference.
3.  **Develop UI components for querying and generating content from the novel:**

    *   Create a new UI section for interacting with the processed novel.
    *   Implement a text area for users to ask questions about the novel.
    *   Implement a text area for users to request new content based on the novel.
    *   Display the AI's answer or generated content.
4.  **Handle large file uploads and background processing:**

    *   Use a background task queue (e.g., Celery, RQ) to handle the novel processing and indexing tasks asynchronously.
    *   Implement chunked uploading for large files to avoid exceeding server limits.
    *   Provide real-time progress updates to the user during the processing.

## VI. UI Consistency and Theme Implementation

**Goal:** Update all application pages to match the new Severance-inspired dashboard design with consistent dark theme and cyan accents.

**Steps:**

1. **Audit existing pages and components:**
   * Identify all pages that need UI updates (world, characters, outline, chapters, etc.)
   * List components that need theme consistency (modals, forms, buttons, cards)
   * Document current inconsistencies with the new dashboard design

2. **Apply consistent theming across all pages:**
   * Update all pages to use the Severance-inspired color scheme:
     - `--color-cyan-bright: #00d4ff` (Primary cyan accent)
     - `--color-dark-primary: #1a2332` (Primary dark background)
     - `--color-dark-base: #141b26` (Base dark background)
     - `--color-dark-secondary: #2a3441` (Secondary dark surfaces)
   * Ensure consistent typography, spacing, and layout patterns
   * Apply unified card styles, button designs, and interactive elements

3. **Standardize navigation and layout:**
   * Implement consistent header/navigation across all pages
   * Ensure uniform sidebar/menu styling and behavior
   * Standardize page layouts and content organization

4. **Update component library:**
   * Refactor shared components (buttons, inputs, cards, modals) for theme consistency
   * Create reusable styled components to maintain design system
   * Implement consistent hover states, transitions, and interactive feedback

**Priority:** High (user experience and visual consistency)

## VII. Testing and Deployment

**Goal:** Ensure the application is stable, reliable, and ready for deployment.

**Steps:**

1.  **Write tests for Svelte components and API integrations:**

    *   Use Jest or Vitest for unit testing Svelte components.
    *   Write integration tests to verify the interaction between the Svelte frontend and the FastAPI backend.
    *   Implement end-to-end tests using Cypress or Playwright to simulate user interactions.
2.  **Deploy the updated application with the Svelte frontend:**

    *   Build the Svelte application for production.
    *   Configure the FastAPI backend to serve the Svelte application's static files.
    *   Deploy the application to a cloud platform like Google Cloud, AWS, or Azure.
    *   Set up continuous integration and continuous deployment (CI/CD) to automate the testing and deployment process.

## VII. Future Enhanced API Endpoints (Post-JSON Migration)

**Goal:** Leverage the structured JSON data format to provide enhanced analytics, search, and management capabilities.

**Planned Endpoints:**

1.  **Project Analytics API:**
    *   `GET /api/projects/{project_id}/analytics` - Comprehensive project statistics
    *   Word count trends, character distribution, theme analysis
    *   Genre insights, story structure completeness metrics
    *   Perfect for dashboard widgets and project insights

2.  **Advanced Search & Filter API:**
    *   `GET /api/projects/search` - Search across all projects with filters
    *   Query parameters: `?genre=sci-fi&themes=survival&min_words=1000&author=Smith`
    *   Enable project discovery, organization, and collection management
    *   Support for complex filtering on structured JSON metadata

3.  **AI Re-analysis API:**
    *   `POST /api/projects/{project_id}/reanalyze` - Re-run AI analysis on existing projects
    *   Update JSON structures with improved extraction algorithms
    *   Useful for enhancing old imports with latest AI models
    *   Optional parameters for specific analysis types (characters, world, themes)

4.  **Project Export API:**
    *   `GET /api/projects/{project_id}/export` - Export projects in various formats
    *   Query parameters: `?format=markdown&include=world,characters,outline`
    *   Support formats: JSON, Markdown, structured text, PDF
    *   Great for sharing, backup, and integration with other tools

5.  **Bulk Operations API:**
    *   `POST /api/projects/bulk/analyze` - Batch analysis of multiple projects
    *   `POST /api/projects/bulk/export` - Bulk export functionality
    *   `PUT /api/projects/bulk/update` - Bulk metadata updates

**Implementation Priority:** Medium (after core functionality and UI are stable)

## VIII. Potential Challenges & Considerations

*   **API Changes:** The existing API might need to be adjusted to better fit the needs of the Svelte frontend.
*   **State Management:** Choosing the right state management solution (Svelte stores, Zustand, etc.) is crucial for maintaining a reactive and efficient UI.
*   **Performance:** Optimizing the Svelte application for performance is important, especially when dealing with large amounts of data.
*   **Authentication:** Implement user authentication and authorization to protect sensitive data and functionality.
*   **Scalability:** Consider the scalability of the application when designing the architecture and choosing the deployment platform.
