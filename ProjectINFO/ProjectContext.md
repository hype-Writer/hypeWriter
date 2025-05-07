# Project Context: HypeWriter

## Project Summary

### Current Focus
- **Frontend Development**: We are actively migrating core application views to a modern, reactive Svelte SPA, utilizing reusable components. This SPA is built using Vite and integrated into the existing FastAPI-served Jinja2 template structure.
- **Current Status**: The 'Home' page frontend is complete and functional. The core, reusable `Chat.svelte` component has been successfully developed and integrated into the `World Building` page, which is now functional and stable. The `Character Development` page is still under active rebuild, but will leverage the new `Chat.svelte` component for its conversational features.

### Your Resume

You are a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices. You focus on using the latest version of Svelte 5 with Runes and TypeScript, Python, FastAPI. You know to only use the latest versions and features of each and not to use outdated or deprecated features from previous versions.

### Development Environment
- **OS**: Arch Linux
- **Editor**: Zed with agentic ai assistant
- **Local Database**: undetermined. need to decide on db type (sql vs nosql)

### Technology Standards
- **Always use current versions**: Implement solutions using the latest stable versions of frameworks and libraries.
- **Avoid deprecated patterns**: Never suggest deprecated methods or syntax (e.g., Pydantic v1 patterns, legacy Svelte syntax).
- **Frontend**: Implement using Svelte 5 Runes (`$state`, `$effect`, `$derived`, `$props`, `$bindable`, `onclick`, snippets) instead of older reactive patterns. Prioritize building reusable components. Client-side data fetching preferred where appropriate, leveraging SvelteKit where its routing/loading benefits apply.
- **Code Commenting Standards**:
    - Avoid adding inline comments (`// comment` or `# comment`) within generated code blocks unless essential for complex logic.
    - Avoid extensive block comments (`/* ... */` or `""" ... """`) unless for file/section headers or complex explanations.
    - For Svelte templates, use standard HTML comments (`<!-- ... -->`) or simple Svelte comments (`{# comment }`). Never use incorrect syntax like `{#-- ... --}` within tags or control flow blocks.
    - When responding with code that the user has previously provided and potentially modified (e.g., by removing comments), respect those removals and do not add the comments back.

## I. Project Overview

**HypeWriter** is an AI-assisted writing tool for developing full-length novels through conversational prompting and content generation. The app provides a structured workflow for world building, character creation, outline generation, and chapter/scene writing.

## II. Current Architecture

*   **Backend:** FastAPI (Python)
    *   Handles API requests, manages application logic, interacts with LLMs (Gemini via the Google ADK, eventually ollama, maybe others), and saves/loads project data.
    *   Still serves the base HTML structure using Jinja2 templates into which the Svelte SPA is embedded.
*   **Frontend:** Svelte SPA (built with Vite) integrated into the base Jinja2 template.
    *   Provides the interactive user interface for core application features as pages are migrated, utilizing reusable components like the `Chat.svelte` component.
    *   The 'Home' page and the `World Building` page are currently implemented and functional in Svelte. The `Character Development` page is under active rebuild.
*   **Data Storage:**
    *   Text files (`.txt`) for world themes, character profiles, and outlines.
    *   JSON files (`.json`) for chapter structures.
    *   Potentially a vector database (ChromaDB, Pinecone, etc.) for full novel integration.

## III. Key Features

1.  **Conversational Prompting:** Users can engage in conversations with AI agents to brainstorm and refine their novel's elements. The core conversational prompting logic is encapsulated in a reusable `Chat.svelte` component, currently integrated and functional on the `World Building` page.
2.  **World Building (Split into Lore and Locations):** Define the history, culture, and magic systems (Lore), and the specific geographical settings (Locations) of the novel's world. (Frontend page implemented and functional).
3.  **Character Development (Split into Individuals and Factions):** Develop detailed character profiles for main and supporting characters (Individuals), and define the roles, goals and relationships of groups within the story (Factions). (Frontend page under rebuild, will use `Chat.svelte`).
4.  **Developing Metadata (Overall Outline and Synopsis):** Create the overall structure of the novel, including a high-level plot summary (Synopsis) and a detailed chapter outline.
5.  **Chapter and Scene Generation (with Chapter Summaries):** Generate content for individual chapters and scenes. Create plot synopses for each individual chapter.
6.  **Short Story Integration (Planned):** Analyze existing short stories to automatically generate the initial world, characters, and outline for a new novel project.
7.  **Full Novel Integration (Planned):** Process and index existing full novels to enable AI to generate new, consistent content based on the novel's themes, characters, and plot.
8.  **Author Style Ingestion:** System where the llm can ingest examples of the author's writing style, to use as context when creating new chapters etc (to more closely match the authors unique style and voice).
9.  **LLM selection via component settings:** System where the author can pick from available models in order to use the llm of their choice, but at first, focused on incorporating local llms via ollama.

## IV. Technologies Used

*   Python
*   FastAPI
*   Svelte 5 (with Runes, TypeScript, Vite for the frontend SPA)
*   Google Agent Development Kit (ADK) for Vertex AI (for interacting with LLMs)
*   future: Vector database (ChromaDB, Pinecone, etc. - for full novel integration)
*   future: Celery/RQ (potentially for background task processing)

## V. Project Goals

1.  Continue migrating core application views to a modern, reactive Svelte SPA, integrated using Vite into the existing Jinja2 serving structure, leveraging reusable components like `Chat.svelte`.
2.  Implement the "Generate Project from Short Story" feature.
3.  Implement the "Integrate and Generate Content from Existing Full Novel" feature.
4.  Improve the user experience and overall functionality of the application.
5.  Create a scalable and maintainable architecture.

## VI. Key Files and Directories

*   `hypewriter/`: Root directory
*   `hypewriter/hypewriter.py`: Main FastAPI application file (includes Jinja2 template serving logic)
*   `hypewriter/agents.py`: Contains the logic for interacting with AI agents
*   `hypewriter/prompts.py`: Defines the prompts used to instruct the AI agents
*   `hypewriter/config.py`: Configuration settings
*   `hypewriter/templates/`: Jinja2 templates (serve as the shell for the Svelte SPA)
*   `hypewriter/static/`: Static files (CSS, JavaScript)
*   `hypewriter/book_output/`: Directory for saving generated project data
*   `hypewriter/plan.md`: Project plan
*   `hypewriter/context.md`: This file - project context
*   `hypewriter/best_practices.md`: Python and ADK best practices
*   `frontend/`: Contains the SvelteKit project source code and Vite build configuration.
*   `frontend/src/lib/components/`: (Assuming this structure) Directory for reusable components like `Chat.svelte`.

## VII. Important Considerations

*   **API Design:** The existing API might need adjustments to better suit the Svelte frontend and new features.
*   **SPA Integration:** Careful consideration is needed for embedding the Svelte SPA into the Jinja2 template and ensuring smooth data flow and routing.
*   **State Management:** Choosing the right state management solution within the Svelte SPA is crucial (leveraging runes for component-level state, `+$state` objects within context or stores for global/shared state).
*   **Performance:** Optimizing performance is important, especially when dealing with large amounts of data (full novel integration).
*   **LLM Costs:** Be mindful of the costs associated with LLM API calls, especially during full novel processing and content generation.
*   **Error Handling:** Implement robust error handling throughout the application.
*   **Frontend prefers client-side data fetching with Svelte 5 Runes unless server-side rendering or data preloading offers significant benefits for a specific route.**
*   **Reusable Components:** Leverage reusable components like `Chat.svelte` across relevant pages to maintain consistency and reduce code duplication.
