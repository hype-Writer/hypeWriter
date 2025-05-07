# Plan: Implement "Generate Project from Short Story" Feature

**Goal:** Allow users to provide an existing short story, have the AI analyze it, and automatically generate the initial World, Characters, and Outline for a new novel project based on that story.

---

## I. User Interface (UI) - Frontend Changes

*   **Location:** Modify relevant HTML templates (`templates/`) and potentially add new JavaScript (`static/js/`). Add route logic in `hypewriter.py`.
*   **Components:**
    *   **Input Mechanism:**
        *   Add a large `<textarea>` element for pasting the short story text.
        *   _Optional:_ Add an `<input type="file">` button to allow uploading `.txt` files (or potentially other formats, requiring backend parsing libraries like `python-docx`).
        *   **Placement:** Consider adding this to the home page (`index.html`) or creating a dedicated `/import` page.
    *   **Trigger:** Add a button (e.g., `<button id="analyze-story-btn">Analyze Story & Generate Project</button>`).
    *   **Feedback:**
        *   Implement client-side JavaScript to show a loading indicator (spinner, message) when the "Analyze" button is clicked.
        *   Display success messages (e.g., "Project generated successfully! Redirecting...") or detailed error messages returned from the backend.

## II. Backend Route - Server-Side Logic

*   **Location:** Add a new function decorated with `@app.route(...)` in `hypewriter.py`.
*   **Details:**
    *   **Endpoint:** Define a new route, e.g., `@app.route('/analyze_story', methods=['POST'])`.
    *   **Input Handling:**
        *   The function will receive the POST request triggered by the "Analyze" button.
        *   Extract the short story text from the form data (`request.form['story_text']`) or uploaded file (`request.files['story_file']`). Handle potential file reading errors.
        *   Receive `num_chapters` if the user specifies how long the generated outline should be.
    *   **Orchestration:**
        *   Instantiate `BookAgents`.
        *   Call new analysis methods within `BookAgents` (see Section III) sequentially or via a coordinating method:
            1.  Analyze story for World details.
            2.  Analyze story for Characters.
            3.  Generate Outline based on story (potentially using extracted world/character info as context).
    *   **Data Processing & Saving:**
        *   Receive the structured analysis results (strings containing world info, character profiles, and the full outline) from the `BookAgents` methods.
        *   **Crucially:** Validate and clean the received data.
        *   Overwrite/create the project files:
            *   `book_output/world.txt`
            *   `book_output/characters.txt`
            *   `book_output/outline.txt`
        *   Parse the generated outline string using `parse_outline_to_chapters()` to create the structured `book_output/chapters.json`. Handle parsing errors gracefully.
        *   Update the Flask `session` variables (`session['world_theme']`, `session['characters']`, `session['outline']`, `session['chapters']`) to reflect the new project state.
    *   **Response Handling:**
        *   On success: Return a JSON response indicating success, possibly with a redirect URL (e.g., to `/outline`) for the frontend JavaScript to handle.
        *   On failure (AI error, parsing error, file error): Return a JSON response with a clear error message and an appropriate HTTP status code (e.g., 400 for bad input, 500 for server/AI errors).

## III. AI Interaction Logic - Core Agent Changes

*   **Location:** Modify `agents.py` and potentially add new prompt templates (could be inline or in `prompts.py`).
*   **Key Task:** Shift from *generating* content from scratch to *analyzing* existing text and *extending* it.
*   **New Prompts:**
    *   **`WORLD_EXTRACTION_PROMPT`:**
        *   **Input:** Short story text.
        *   **Goal:** Instruct the LLM to identify/infer setting, time period, mood, locations, culture, tech/magic.
        *   **Output:** Request formatted text, ideally matching the `WORLD_ELEMENTS:` structure used elsewhere.
    *   **`CHARACTER_EXTRACTION_PROMPT`:**
        *   **Input:** Short story text.
        *   **Goal:** Instruct the LLM to identify main/supporting characters, extract/infer descriptions, traits, motivations, roles.
        *   **Output:** Request formatted text, ideally matching the `CHARACTER_PROFILES:` structure.
    *   **`OUTLINE_FROM_STORY_PROMPT`:**
        *   **Input:** Short story text, optionally the extracted world/character summaries, desired number of chapters (`num_chapters`).
        *   **Goal:** Instruct the LLM to:
            1.  Summarize the *existing* plot of the short story.
            2.  Generate a chapter-by-chapter outline that *continues* the story logically for the specified `num_chapters`.
            3.  Maintain consistency with themes, characters, and world details from the story.
        *   **Output:** Request **precise formatting** matching the `OUTLINE:\nChapter X: ...` structure required by `parse_outline_to_chapters`.
*   **New `BookAgents` Methods:**
    *   Define new methods like:
        *   `analyze_story_for_world(self, story_text: str) -> str:` (Calls LLM with `WORLD_EXTRACTION_PROMPT`)
        *   `analyze_story_for_characters(self, story_text: str) -> str:` (Calls LLM with `CHARACTER_EXTRACTION_PROMPT`)
        *   `generate_outline_from_story(self, story_text: str, world_context: str, character_context: str, num_chapters: int) -> str:` (Calls LLM with `OUTLINE_FROM_STORY_PROMPT`)
    *   _Alternative:_ A single method `analyze_and_generate(self, story_text: str, num_chapters: int) -> tuple[str, str, str]` that internally makes the multiple LLM calls. (Separate methods might be cleaner for error handling).
    *   These methods will use `self.gemini_model.generate_content()` with the new prompts.

## IV. Data Handling & Integration

*   **Flow:** UI -> `/analyze_story` route -> `BookAgents` analysis methods -> Route saves results -> UI redirects/updates.
*   **Error Handling:** Implement robust error handling at each stage:
    *   UI: Handle network errors, display backend error messages.
    *   Backend Route: Catch exceptions during file I/O, LLM calls, and parsing. Return informative errors to the UI.
    *   Agent Methods: Handle potential LLM API errors (e.g., connection issues, rate limits, content blocking) and return meaningful errors or empty results.
*   **Parsing Robustness:** The `parse_outline_to_chapters` function is critical. Test it thoroughly with AI-generated outlines based on stories, as formatting might vary. Improve the regex or add fallbacks if needed.

## V. User Workflow & Refinement

*   **Post-Analysis:** After successful analysis and generation, the user should be automatically directed to view the results (e.g., the `/outline` page).
*   **Review & Edit:** The core value proposition includes allowing the user to *refine* the AI's analysis. The existing UI (`/world`, `/characters`, `/outline` pages) with their editing textareas and save buttons (`/save_world`, etc.) should be leveraged directly. The user reviews the AI-generated content and makes necessary corrections before proceeding to generate chapter content.

## VI. Potential Challenges & Considerations

*   **Prompt Engineering:** Achieving consistent and accurate analysis/extension via prompts will require significant experimentation.
*   **AI Accuracy:** LLMs may misinterpret nuances, omit details, or hallucinate. The user editing step is non-negotiable.
*   **Output Format Consistency:** Ensuring the LLM adheres strictly to the requested output format (especially for the outline) is vital for automated parsing. Add format reminders and examples in the prompts.
*   **Context Window Limits:** Very long short stories might exceed the LLM's input token limit. This plan assumes stories fit; handling longer texts would require chunking strategies.
*   **Ambiguity Handling:** How the AI resolves plot points or character details left ambiguous in the original story. Be prepared for the AI to make plausible assumptions.
*   **Processing Time:** Analyzing a story and generating a multi-step project will take noticeable time. Clear UI feedback is essential. Consider asynchronous task processing for very long operations if needed (more complex).
