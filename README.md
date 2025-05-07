# hypeWriter

An AI-assisted writing tool for developing full-length novels through conversational prompting and content generation. The app provides a structured workflow for world building, character creation, outline generation, and chapter/scene writing.

## Features

- Web-based user interface with no authentication required
- Step-by-step guided book writing process
- Real-time AI generation of:
  - World settings and environments
  - Character profiles and development
  - Book outlines with chapter structure
  - Scene generation for individual chapters
  - Full chapter content
- Local AI model support
- Progress tracking
- Ability to edit and save generated content
- All content stored in local files for easy access

## Architecture

The application consists of:

The application consists of:

-   **FastAPI Backend**: Provides the API endpoints and manages the book generation process.
-   **Frontend (Svelte/Vite)**: The user interface is developed using Svelte and bundled into a single-page application using Vite. This bundled application is then integrated into the Jinja2 templating structure for serving static files.
-   **AI Agents**: Specialized agents for different aspects of book creation...
-   **Prompt Management**: Centralized prompt templates in `prompts.py`
-   **File Storage**: Local storage of all generated content in the `book_output` directory


1.  Clone the repository:

    ```bash
    git clone https://github.com/hype-Writer/hypeWriter
    cd hypewriter
    ```
2.  Create a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install backend dependencies:

    ```bash
    pip install -r requirements.txt
    ```

**(Optional) Only if you want to do Frontend Development:**

If you wish to contribute to or modify the frontend, follow these steps:

1.  Install Node.js and npm:
2.  The `frontend` directory already contains a Svelte project, initialized using `npx sv create frontend`
3.  Navigate to the frontend directory:

    ```bash
    cd frontend
    ```
4.  Install frontend dependencies:

    ```bash
    npm install
    ```
5.  Run the frontend development server:

    ```bash
    npm run dev -- --opem
    ```

**Important:** The `frontend` directory contains the Svelte project which is only necessary for modifying the existing frontend. It is not needed for running the app itself. If you only want to *use* the application, you don't need to follow these steps.




## Usage

1.  Start the local AI model server according to your `config.py` settings.
2.  Run the web application:

    ```bash
    uvicorn hypewriter:app --reload
    ```
3.  Open your browser and navigate to:

    ```
    http://localhost:8000
    ```
4.  Follow the step-by-step process in the web interface:

    *   Create a world setting
    *   Generate characters
    *   Create a book outline
    *   Work chapter by chapter to generate your book


## Book Writing Workflow

The application guides you through a logical book creation process:

1.  **World Building (Lore and Locations)**: Define the history, culture, magic systems, and geographical settings of your novel's world.
2.  **Character Development (Individuals and Factions)**: Develop detailed character profiles and define the roles and relationships of groups within the story.
3.  **Developing Metadata (Outline and Synopsis)**: Create the overall structure of the novel, including a high-level plot summary and a detailed chapter outline.
4.  **Chapter and Scene Generation (with Chapter Summaries)**: Generate content for individual chapters and scenes and create plot synopses for each individual chapter.
5.  **Author Style Ingestion**: Ingest examples of the author's writing style for context during content creation.
6.  **LLM Selection**: Choose from available language models, initially focusing on local models via Ollama.

## Output Structure

All generated content is saved in the `book_output` directory:


```
book_output/
├── world.txt                # World setting
├── characters.txt           # Character profiles
├── outline.txt              # Full book outline
├── outline.json             # Structured outline data
├── chapters/
│   ├── chapter_1.txt
│   ├── chapter_2.txt
│   └── ...
│   └── chapter_1_scenes/    # Generated scenes for chapters
│       ├── scene_1.txt
│       └──
...

## Requirements

-   Python 3.8+
-   FastAPI
-   Svelte
-   Local AI model (as configured in your existing `config.py`)
-   Other dependencies listed in requirements.txt

## Configuration

The system can be configured through `config.py` for the AI model settings and `prompts.py` for generation prompts.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
