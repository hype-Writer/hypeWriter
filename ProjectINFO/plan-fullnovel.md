# Plan: Integrate and Generate Content from Existing Full Novel

**Goal:** Allow users to upload a completed novel (~85k words), enable the AI to gain a deep, searchable understanding of its content (themes, characters, world, plot), and generate new, consistent content (scenes, chapters, answers) based on that understanding.

**Core Technical Challenge:** The novel's length vastly exceeds typical LLM context windows. The primary solution involves indexing the novel content using embeddings and retrieving relevant parts dynamically (Retrieval-Augmented Generation - RAG).

---

## Phase 1: Novel Ingestion, Processing, and Indexing (One-Time Per Novel)

*   **Goal:** Convert the raw novel text into a searchable knowledge base for the AI.

*   **I. User Interface (UI):**
    *   **Upload Mechanism:**
        *   Create a new section or page (e.g., `/import_novel`).
        *   Provide a robust file upload input (`<input type="file">`) accepting common formats (`.txt`, `.docx`, potentially `.epub`). Need backend libraries (`python-docx`, `ebooklib`) for parsing non-txt formats.
        *   Consider handling large file uploads (progress bar, maybe chunked uploading or background processing).
    *   **Initiate Processing:** A button like "Process and Index Novel".
    *   **Feedback:** Display detailed progress updates (e.g., "Uploading...", "Parsing File...", "Chunking Text...", "Generating Embeddings (Chunk X of Y)...", "Indexing Complete!"). This process can take minutes. Display errors clearly.

*   **II. Backend Processing Route:**
    *   **Endpoint:** Define a route like `@app.route('/process_novel', methods=['POST'])`. This might be a long-running task, potentially requiring background task queues (like Celery, RQ) for better UX, but can start simpler.
    *   **File Handling:** Receive the uploaded file, save it temporarily.
    *   **Content Extraction:** Use appropriate libraries to parse the text content from the uploaded file format.
    *   **Text Preprocessing & Cleaning:**
        *   Remove boilerplate (headers, footers, page numbers if possible).
        *   Normalize whitespace and potentially fix common formatting issues.
    *   **Chunking Strategy:**
        *   Divide the cleaned text into smaller, meaningful chunks. This is CRITICAL for RAG effectiveness. Strategies include:
            *   By chapter (if clearly defined).
            *   Fixed token size (e.g., 500-1000 tokens) using a tokenizer (like `tiktoken` or Sentence Transformers tokenizer).
            *   Semantic chunking (grouping paragraphs/sections by topic).
            *   **Overlapping chunks:** Often beneficial for retrieval (e.g., overlap chunks by 50-100 tokens) to avoid cutting off context mid-sentence.
    *   **Embedding Generation:**
        *   **Select Model:** Choose an embedding model (e.g., Google's `text-embedding-004`, OpenAI `text-embedding-3-small/large`, Sentence Transformers).
        *   **Iterate & Embed:** Loop through each text chunk, send it to the embedding model API/library, and get the vector embedding.
        *   **Error Handling/Rate Limits:** Handle potential API errors or rate limits during embedding generation. Store embeddings temporarily.
    *   **Vector Storage:**
        *   **Select Database:** Choose a vector database. Options:
            *   _Local/Simple:_ ChromaDB, FAISS (requires manual indexing/saving). Suitable for single-user or development.
            *   _Managed/Scalable:_ Pinecone, Weaviate, Qdrant. Better for production or multi-user scenarios.
        *   **Indexing:** Store each chunk's text content alongside its vector embedding in the chosen database. Include metadata (e.g., `novel_id`, `chapter_number`, `chunk_index`) for filtering and reference.
    *   **(Optional but Recommended) High-Level Analysis:**
        *   Use the LLM (perhaps processing chapter summaries) to generate overall summaries of:
            *   Main Plot Points / Synopsis
            *   Key Themes
            *   Character Summaries (Core traits, arcs)
            *   World/Setting Overview
        *   Store these high-level summaries separately (e.g., in a JSON file or simple database linked to the novel) for quick reference and broader context priming during generation.
    *   **Completion:** Update the UI to indicate the novel is processed and ready. Store a reference linking the user/project to the indexed novel data (e.g., the vector DB collection name or novel ID).

## Phase 2: Querying and Content Generation (Interactive Use)

*   **Goal:** Allow the user to leverage the indexed knowledge base to ask questions and generate new content consistent with the original novel.

*   **I. User Interface (UI):**
    *   **Dedicated Interface:** Create a new UI section for interacting with the processed novel.
    *   **Query Input:** A text area for users to ask questions about the novel ("What motivates Character X in the final act?").
    *   **Generation Prompt Input:** A text area for users to request new content ("Write a scene from Character Y's perspective during the events of Chapter 5.", "Draft the opening paragraph of a potential sequel.").
    *   **Output Display:** Area to display the AI's answer or generated content.
    *   **(Optional) Context Display:** Show the retrieved text chunks used by the AI to generate the response (aids transparency and debugging).
    *   **(Optional) Parameter Controls:** Allow users to adjust retrieval parameters (e.g., number of chunks to retrieve) or generation parameters (temperature).

*   **II. Backend Query/Generation Routes:**
    *   **Endpoints:** Define routes like:
        *   `@app.route('/query_novel', methods=['POST'])`
        *   `@app.route('/generate_from_novel', methods=['POST'])` (potentially streaming)
    *   **Input:** Receive the user's query or generation prompt, and the ID/reference of the processed novel.
    *   **Retrieval (RAG Core):**
        1.  Generate an embedding for the user's input query/prompt using the *same* embedding model used during indexing.
        2.  Query the vector database associated with the novel using this query embedding. Retrieve the `k` most semantically similar text chunks (e.g., `k=5` or `k=10`).
        3.  Optionally re-rank retrieved chunks for relevance if needed.
    *   **LLM Prompt Construction:**
        1.  **Context:** Assemble the retrieved text chunks. Clearly label them in the prompt (e.g., `--- Relevant Excerpts from Original Novel --- \n[Chunk 1 text]\n---\n[Chunk 2 text]\n---`).
        2.  **(Optional) High-Level Context:** Include relevant parts of the pre-generated high-level summaries (plot, character) if applicable.
        3.  **User Request:** Include the user's original query or generation instruction.
        4.  **Task Instruction:** Add clear instructions for the LLM (e.g., "Based *only* on the provided novel excerpts and summaries, answer the following question:", or "Write a scene consistent with the provided novel excerpts and the user's request. Maintain the original novel's tone, style, and character voices.").
        5.  **Consistency Constraint:** Strongly emphasize adherence to the provided context and facts from the original novel.
    *   **LLM Call:** Send the constructed prompt to the generative LLM (e.g., Gemini).
    *   **Response Handling:** Process the LLM's response. For generation, this might involve cleaning/formatting. For queries, extract the answer. Return the result (or stream it) to the UI.

## Phase 3: Persistence and Management

*   **Vector Store:** Ensure the vector database is persisted correctly. For local DBs like ChromaDB, specify a persistent storage path.
*   **Project Association:** Implement a mechanism to associate uploaded novels and their indexed data/summaries with specific user projects. This might involve updating your project structure or using a simple database.
*   **Re-Indexing:** Consider if/how users can trigger a re-index if they upload an updated version of their novel.

## Potential Challenges & Considerations

*   **RAG Quality:** The effectiveness heavily depends on the chunking strategy, embedding model quality, and retrieval effectiveness. Fine-tuning retrieval parameters (`k`, similarity thresholds) might be needed.
*   **Lost Detail:** Summarization (optional phase) inherently loses detail. RAG mitigates this but might miss subtle connections if relevant context isn't retrieved.
*   **Consistency:** Even with RAG, ensuring the LLM *perfectly* maintains tone, voice, and subtle plot points requires careful prompt engineering and potentially multiple generation/refinement steps.
*   **Cost:** Embedding a large novel and making numerous LLM calls for analysis and generation can incur significant API costs depending on the models used.
*   **Processing Time:** Indexing is slow. Generation involving retrieval + LLM call will be slower than simple prompting. Manage user expectations.
*   **Scalability:** The choice of vector database and potential use of background tasks impacts how well the system scales to many users or very large novels.
