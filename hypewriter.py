"""
FastAPI web application for hypeWriter
"""
import os
import json
import re
import requests
from typing import List, Optional, Dict, Any, AsyncGenerator, Iterable

from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    StreamingResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi_mcp import FastApiMCP


# Configuration and Agents
from core.config import GEMINI_CONFIG_LIST, APP_SECRET_KEY
from core.agents import BookAgents
from core import prompts

# --- Pydantic Models for Request Bodies ---
from core.pydantic_models import (
    ChatRequestData,
    FinalizeRequestData,
    SaveOutlineRequest,
    GenerateChaptersRequest,
    SaveWorldRequest,
    SaveCharactersRequest,
    GenerateChapterContentRequest,
    SaveChapterRequest,
    GenerateSceneRequest,
    TTSRequest,
    ChapterTTSRequest,
    ProjectMetadata,
    CreateProjectRequest,
    ImportAnalysisRequest,
    ImportNovelRequest,
)


# --- FastAPI App Setup ---
app = FastAPI()

# Session Middleware (Using MemoryStore - consider alternatives for production)
# Note: Requires 'itsdangerous' to be installed implicitly by starlette
app.add_middleware(
    SessionMiddleware,
    secret_key=APP_SECRET_KEY or "change-me-in-production",  # Ensure a key is set
    https_only=False,  # Set to True if using HTTPS
    same_site="lax",
)

# Initialize MCP integration
mcp = FastApiMCP(app)
mcp.mount()


static_dir_path = "static"

if not os.path.isdir(static_dir_path):
    print(f"ERROR: Static directory '{static_dir_path}' not found relative to CWD '{os.getcwd()}'. Cannot mount static files.")
    # Optionally, you might want to raise an exception here if static files are critical
    # raise RuntimeError(f"Static directory '{static_dir_path}' not found.")
else:
    try:
        app.mount("/static", StaticFiles(directory=static_dir_path), name="static")
        print(f"Successfully mounted static directory '{static_dir_path}' at /static")
    except Exception as mount_exc:
        # Catch any other potential exception during mounting
        print(f"ERROR: Failed to mount static directory '{static_dir_path}': {mount_exc}")
        # Optionally re-raise the exception
        # raise mount_exc

# Templates (can stay after static mounting)
templates = Jinja2Templates(directory="templates")

# Ensure library directory exists
os.makedirs("library/chapters", exist_ok=True)

# Agent Configuration
agent_config = {"config_list": GEMINI_CONFIG_LIST, "temperature": 0.7}

# TTS Configuration
KOKORO_API_BASE_URL = "http://localhost:8880/v1"


# === Helper Function for Streaming (FastAPI Version) ===
# Changed stream_iterator type hint to Iterable as it's synchronous
async def generate_sse_stream(
    stream_iterator: Iterable, request: Request, request_data: Optional[Dict] = None
) -> AsyncGenerator[str, None]:
    """
    Generates Server-Sent Events (SSE) from a Gemini stream iterator for FastAPI.
    Handles potential saving logic for finalizing routes based on request path.
    """
    # Send initial empty data to help establish connection if needed
    yield 'data: {"content": ""}\n\n'

    collected_content = []
    route_path = request.url.path # Get path from FastAPI Request object

    try:
        # Changed async for to standard for loop
        for chunk in stream_iterator:
            if hasattr(chunk, "text"):
                content = chunk.text
                collected_content.append(content)
                yield f"data: {json.dumps({'content': content})}\n\n"
            elif hasattr(chunk, "parts"): # Check for parts structure if text is missing
                 try:
                     content = "".join(part.text for part in chunk.parts)
                     collected_content.append(content)
                     yield f"data: {json.dumps({'content': content})}\n\n"
                 except AttributeError:
                     # Handle cases where parts don't have text (e.g., function calls)
                     print(f"Skipping non-text part in stream chunk: {chunk}")
            # Added a check for empty content chunks which can occur in Gemini streams
            elif chunk is not None:
                 print(f"Received non-text chunk type: {type(chunk)}. Skipping.")


    except Exception as e:
        print(f"Error during streaming generation: {e}")
        error_message = f"[STREAMING ERROR: {e}]"
        yield f"data: {json.dumps({'content': error_message})}\n\n"
    finally:
        # --- Perform saving logic ONLY for finalize_*_stream routes ---
        if route_path.startswith("/finalize_"):
            complete_content = "".join(collected_content)
            print(f"Finalizing content for route: {route_path}")

            # --- Session Interaction within Async Function ---
            # Note: Modifying session within the stream generator can be tricky.
            # It's generally better to handle session writes *after* the stream
            # has finished in the main route function if possible, or use
            # background tasks. For simplicity here, we attempt direct modification,
            # but be aware of potential concurrency issues.

            if route_path == "/finalize_world_stream":
                world_theme = complete_content.strip()
                world_theme = re.sub(r"\n+", "\n", world_theme)
                request.session["world_theme"] = world_theme # Use request.session
                try:
                    # Save to project-specific path if available
                    current_project_id = request.session.get("current_project_id")
                    if current_project_id:
                        from core.project_manager import ProjectManager
                        pm = ProjectManager()
                        project_dir = pm.get_project_path(current_project_id)
                        from core.text_to_json import parse_world_text_to_json
                        world_data = parse_world_text_to_json("Current Project", world_theme)
                        world_file = project_dir / "world.json"
                        with open(world_file, "w", encoding="utf-8") as f:
                            json.dump(world_data.model_dump(), f, indent=2, ensure_ascii=False)
                    else:
                        # Legacy fallback
                        world_file = "library/world.txt"
                        with open(world_file, "w", encoding="utf-8") as f:
                            f.write(world_theme)
                    print("Final world theme saved from stream.")
                except Exception as write_error:
                    print(f"Error saving final world theme: {write_error}")

            elif route_path == "/finalize_characters_stream":
                characters_content = complete_content.strip()
                request.session["characters"] = characters_content
                try:
                    # Save to current project if available
                    current_project_id = request.session.get("current_project_id")
                    if current_project_id:
                        from core.project_manager import ProjectManager
                        from core.text_to_json import parse_characters_text_to_json
                        pm = ProjectManager()
                        project_dir = pm.get_project_path(current_project_id)
                        characters_data = parse_characters_text_to_json(characters_content)
                        with open(project_dir / "characters.json", "w", encoding="utf-8") as f:
                            json.dump(characters_data.model_dump(), f, indent=2, ensure_ascii=False)
                    else:
                        # Legacy fallback
                        with open("book_output/characters.txt", "w", encoding="utf-8") as f:
                            f.write(characters_content)
                    print("Final characters saved from stream.")
                except Exception as write_error:
                    print(f"Error saving final characters: {write_error}")

            elif route_path == "/finalize_outline_stream":
                outline_content = complete_content.strip()
                request.session["outline"] = outline_content
                try:
                    # Save to current project if available
                    current_project_id = request.session.get("current_project_id")
                    if current_project_id:
                        from core.project_manager import ProjectManager
                        from core.text_to_json import parse_outline_text_to_json
                        pm = ProjectManager()
                        project_dir = pm.get_project_path(current_project_id)
                        outline_data = parse_outline_text_to_json("Current Project", outline_content)
                        with open(project_dir / "outline.json", "w", encoding="utf-8") as f:
                            json.dump(outline_data.model_dump(), f, indent=2, ensure_ascii=False)
                    else:
                        # Legacy fallback
                        with open("book_output/outline.txt", "w", encoding="utf-8") as f:
                            f.write(outline_content)
                    print("Final outline saved from stream.")
                except Exception as write_error:
                    print(f"Error saving final outline: {write_error}")

                try:
                    # Use request_data passed to the helper for num_chapters
                    num_chapters_fallback = 10
                    if request_data and "num_chapters" in request_data:
                        num_chapters_from_request = int(request_data.get("num_chapters", num_chapters_fallback))
                    else:
                        num_chapters_from_request = num_chapters_fallback
                        print("Warning: num_chapters not found in request_data for outline finalization, using fallback.")

                    # Ensure parse_outline_to_chapters is available (assuming it's defined in this file or imported)
                    # from .utils import parse_outline_to_chapters # Example import if in utils
                    # For now, assuming it's defined later in this file as per the provided context.
                    chapters = parse_outline_to_chapters(outline_content, num_chapters_from_request)
                    request.session["chapters"] = chapters
                    with open("book_output/chapters.json", "w", encoding="utf-8") as f:
                        json.dump(chapters, f, indent=2)
                    print(f"Chapters ({len(chapters)}) parsed and saved from streamed outline.")
                except Exception as parse_error:
                    print(f"Error parsing/saving chapters after streaming outline: {parse_error}")

        # Send completion marker
        print("Sending [DONE] marker.")
        yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"


# --- Helper to Load Session/File Data ---
def load_context(request: Request) -> Dict[str, Any]:
    """Loads world, characters, outline, chapters from session or JSON files."""
    context = {
        "world_theme": request.session.get("world_theme", ""),
        "characters": request.session.get("characters", ""),
        "outline": request.session.get("outline", ""),
        "chapters": request.session.get("chapters", []),
        "topic": request.session.get("topic", ""),
    }

    # Check if we're working with a specific project
    current_project_id = request.session.get("current_project_id")
    
    if current_project_id:
        # Load from project-specific JSON paths
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        project_dir = pm.get_project_path(current_project_id)
        
        # Load world from world.json
        if not context["world_theme"] and (project_dir / "world.json").exists():
            try:
                with open(project_dir / "world.json", "r", encoding="utf-8") as f:
                    world_data = json.load(f)
                    # Convert JSON back to text format for compatibility
                    world_theme = world_data.get("raw_content", "")
                    if not world_theme:
                        # Generate text from structured data as fallback
                        world_theme = f"Genre: {world_data.get('genre', 'Unknown')}\n"
                        world_theme += f"Setting: {world_data.get('setting_summary', 'Unknown')}\n"
                        world_theme += f"Time Period: {world_data.get('time_period', 'Unknown')}\n"
                        themes = world_data.get('themes', [])
                        if themes:
                            world_theme += f"Themes: {', '.join(themes)}\n"
                    context["world_theme"] = world_theme.strip()
                    request.session["world_theme"] = context["world_theme"]
            except Exception as e:
                print(f"Error reading world.json: {e}")

        # Load characters from characters.json
        if not context["characters"] and (project_dir / "characters.json").exists():
            try:
                with open(project_dir / "characters.json", "r", encoding="utf-8") as f:
                    characters_data = json.load(f)
                    # Convert JSON back to text format for compatibility
                    characters_text = characters_data.get("raw_content", "")
                    if not characters_text:
                        # Generate text from structured data as fallback
                        characters = characters_data.get("characters", [])
                        if characters:
                            characters_text = "CHARACTERS:\n\n"
                            for char in characters:
                                characters_text += f"Name: {char.get('name', 'Unknown')}\n"
                                characters_text += f"Role: {char.get('role', 'Unknown')}\n"
                                if char.get('personality'):
                                    characters_text += f"Personality: {', '.join(char['personality'])}\n"
                                characters_text += "\n"
                    context["characters"] = characters_text.strip()
                    request.session["characters"] = context["characters"]
            except Exception as e:
                print(f"Error reading characters.json: {e}")

        # Load outline from outline.json
        if not context["outline"] and (project_dir / "outline.json").exists():
            try:
                with open(project_dir / "outline.json", "r", encoding="utf-8") as f:
                    outline_data = json.load(f)
                    # Convert JSON back to text format for compatibility
                    outline_text = outline_data.get("raw_content", "")
                    if not outline_text:
                        # Generate text from structured data as fallback
                        story_structure = outline_data.get("story_structure", {})
                        plot_outline = outline_data.get("plot_outline", {})
                        outline_text = f"STORY OUTLINE\n\n"
                        outline_text += f"Genre: {story_structure.get('genre', 'Unknown')}\n"
                        themes = story_structure.get('themes', [])
                        if themes:
                            outline_text += f"Themes: {', '.join(themes)}\n"
                        outline_text += f"\nPlot Structure:\n"
                        outline_text += f"Beginning: {plot_outline.get('beginning', 'TBD')}\n"
                        outline_text += f"Rising Action: {plot_outline.get('rising_action', 'TBD')}\n"
                        outline_text += f"Climax: {plot_outline.get('climax', 'TBD')}\n"
                        outline_text += f"Resolution: {plot_outline.get('resolution', 'TBD')}\n"
                    context["outline"] = outline_text.strip()
                    request.session["outline"] = context["outline"]
            except Exception as e:
                print(f"Error reading outline.json: {e}")

        # Load chapters from chapters.json (already JSON, no conversion needed)
        if not context["chapters"] and (project_dir / "chapters.json").exists():
            try:
                with open(project_dir / "chapters.json", "r", encoding="utf-8") as f:
                    context["chapters"] = json.load(f)
                request.session["chapters"] = context["chapters"]
            except Exception as e:
                print(f"Error reading chapters.json: {e}")

    return context


# --- FastAPI Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_spa(request: Request):
    """Serve the Svelte SPA"""
    # This route serves the initial index.html which loads the Svelte app
    return templates.TemplateResponse("index.html", {"request": request})


# --- API and Streaming Endpoints (Kept as they are used by Svelte components) ---

# World Building API Endpoints
@app.post("/world_chat", response_class=JSONResponse)
async def world_chat(request: Request, data: ChatRequestData):
    """Handle ongoing chat for world building (Non-streaming)"""
    if not data.message:
        raise HTTPException(status_code=400, detail="No message provided")

    if data.topic:
        request.session["topic"] = data.topic # Use request.session

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(data.topic or "", 0)
        ai_response = book_agents.generate_chat_response(
            data.chat_history, data.topic or "", data.message
        )
        return JSONResponse({"message": ai_response.strip()})
    except Exception as e:
        print(f"Error in /world_chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate chat response")


@app.post("/world_chat_stream") # Implicit JSONResponse for errors
async def world_chat_stream(request: Request, data: ChatRequestData):
    """Handle ongoing chat for world building with streaming response"""
    if not data.message:
        raise HTTPException(status_code=400, detail="No message provided")

    if data.topic:
        request.session["topic"] = data.topic

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(data.topic or "", 0)
        # Assuming generate_chat_response_stream returns an async generator now
        stream = book_agents.generate_chat_response_stream(
            data.chat_history, data.topic or "", data.message
        )

        # Pass request object and request data (as dict) to the helper
        return StreamingResponse(
            generate_sse_stream(stream, request, data.dict()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        print(f"Error starting stream in /world_chat_stream: {e}")
        # FastAPI handles raising HTTPException in streaming responses less directly.
        # The helper function yields an error message.
        # We can only raise HTTPException *before* returning StreamingResponse.
        raise HTTPException(status_code=500, detail=f"Failed to start stream: {e}")


@app.post("/finalize_world", response_class=JSONResponse)
async def finalize_world(request: Request, data: FinalizeRequestData):
    """Finalize the world setting based on chat history (Non-streaming)"""
    topic = data.topic or request.session.get("topic", "")
    if not data.chat_history:
        raise HTTPException(status_code=400, detail="Chat history is empty")

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(topic, 0)
        world_theme = book_agents.generate_final_world(data.chat_history, topic)

        world_theme = world_theme.strip()
        world_theme = re.sub(r"\n+", "\n", world_theme)
        request.session["world_theme"] = world_theme
        # Save to current project if available
        current_project_id = request.session.get("current_project_id")
        if current_project_id:
            from core.project_manager import ProjectManager
            from core.text_to_json import parse_world_text_to_json
            pm = ProjectManager()
            project_dir = pm.get_project_path(current_project_id)
            world_data = parse_world_text_to_json("Current Project", world_theme)
            with open(project_dir / "world.json", "w", encoding="utf-8") as f:
                json.dump(world_data.model_dump(), f, indent=2, ensure_ascii=False)
        else:
            # Legacy fallback
            with open("book_output/world.txt", "w", encoding="utf-8") as f:
                f.write(world_theme)

        return JSONResponse({"world_theme": world_theme})
    except Exception as e:
        print(f"Error in /finalize_world: {e}")
        raise HTTPException(status_code=500, detail="Failed to finalize world setting")


@app.post("/finalize_world_stream")
async def finalize_world_stream(request: Request, data: FinalizeRequestData):
    """Finalize the world setting based on chat history with streaming"""
    topic = data.topic or request.session.get("topic", "")
    if not data.chat_history:
        raise HTTPException(status_code=400, detail="Chat history is empty")

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(topic, 0)
        stream = book_agents.generate_final_world_stream(data.chat_history, topic)

        return StreamingResponse(
            generate_sse_stream(stream, request, data.dict()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        print(f"Error starting stream in /finalize_world_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start finalize world stream: {e}")


# save_world route is already updated to accept JSON
@app.post("/save_world", response_class=JSONResponse)
async def save_world(request: Request, data: SaveWorldRequest):
    """Save manually edited world theme"""
    world_theme_cleaned = data.world_theme.replace("\r\n", "\n").strip()
    world_theme_cleaned = re.sub(r"\n{3,}", "\n\n", world_theme_cleaned)

    request.session["world_theme"] = world_theme_cleaned
    try:
        # Save to current project if available
        current_project_id = request.session.get("current_project_id")
        if current_project_id:
            from core.project_manager import ProjectManager
            from core.text_to_json import parse_world_text_to_json
            pm = ProjectManager()
            project_dir = pm.get_project_path(current_project_id)
            world_data = parse_world_text_to_json("Current Project", world_theme_cleaned)
            with open(project_dir / "world.json", "w", encoding="utf-8") as f:
                json.dump(world_data.model_dump(), f, indent=2, ensure_ascii=False)
        else:
            # Legacy fallback
            with open("book_output/world.txt", "w", encoding="utf-8") as f:
                f.write(world_theme_cleaned)
        return JSONResponse({"success": True})
    except Exception as e:
        print(f"Error saving world theme manually: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save world theme: {e}")


# Character Creation API Endpoints
@app.post("/characters_chat_stream")
async def characters_chat_stream(request: Request, data: ChatRequestData):
    """Handle ongoing chat for character creation with streaming"""
    if not data.message:
        raise HTTPException(status_code=400, detail="No message provided")

    context = load_context(request)
    world_theme = context["world_theme"]
    if not world_theme:
        raise HTTPException(status_code=400, detail="World theme not found. Please complete world building.")

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(world_theme, 0)
        stream = book_agents.generate_chat_response_characters_stream(
            data.chat_history, world_theme, data.message
        )
        return StreamingResponse(
            generate_sse_stream(stream, request, data.dict()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        print(f"Error starting stream in /characters_chat_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start character chat stream: {e}")


@app.post("/finalize_characters_stream")
async def finalize_characters_stream(request: Request, data: FinalizeRequestData):
    """Finalize the characters based on chat history with streaming"""
    if not data.chat_history:
        raise HTTPException(status_code=400, detail="Chat history is empty")

    context = load_context(request)
    world_theme = context["world_theme"]
    if not world_theme:
         raise HTTPException(status_code=400, detail="World theme not found. Please complete world building.")

    num_characters = data.num_characters or 3 # Use Pydantic default

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(world_theme, 0)
        stream = book_agents.generate_final_characters_stream(
            data.chat_history, world_theme, num_characters
        )
        return StreamingResponse(
            generate_sse_stream(stream, request, data.dict()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        print(f"Error starting stream in /finalize_characters_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start finalize characters stream: {e}")


# save_characters route is already updated to accept JSON
@app.post("/save_characters", response_class=JSONResponse)
async def save_characters(request: Request, data: SaveCharactersRequest):
    """Save manually edited characters"""
    characters_cleaned = data.characters.replace("\r\n", "\n").strip()
    characters_cleaned = re.sub(r"\n{3,}", "\n\n", characters_cleaned)

    request.session["characters"] = characters_cleaned
    try:
        # Save to current project if available
        current_project_id = request.session.get("current_project_id")
        if current_project_id:
            from core.project_manager import ProjectManager
            from core.text_to_json import parse_characters_text_to_json
            pm = ProjectManager()
            project_dir = pm.get_project_path(current_project_id)
            characters_data = parse_characters_text_to_json(characters_cleaned)
            with open(project_dir / "characters.json", "w", encoding="utf-8") as f:
                json.dump(characters_data.model_dump(), f, indent=2, ensure_ascii=False)
        else:
            # Legacy fallback
            with open("book_output/characters.txt", "w", encoding="utf-8") as f:
                f.write(characters_cleaned)
        return JSONResponse({"success": True})
    except Exception as e:
        print(f"Error saving characters manually: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save characters: {e}")


# Outline Creation API Endpoints
@app.post("/outline_chat_stream")
async def outline_chat_stream(request: Request, data: ChatRequestData):
    """Handle ongoing chat for outline creation with streaming"""
    if not data.message:
        raise HTTPException(status_code=400, detail="No message provided")

    context = load_context(request)
    if not context["world_theme"] or not context["characters"]:
         raise HTTPException(status_code=400, detail="World or Characters not found. Complete previous steps.")

    num_chapters = data.num_chapters or 10 # Use Pydantic default

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(context["world_theme"], num_chapters)
        stream = book_agents.generate_chat_response_outline_stream(
            data.chat_history, context["world_theme"], context["characters"], data.message
        )
        return StreamingResponse(
            generate_sse_stream(stream, request, data.dict()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        print(f"Error starting stream in /outline_chat_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start outline chat stream: {e}")


@app.post("/finalize_outline_stream")
async def finalize_outline_stream(request: Request, data: FinalizeRequestData):
    """Finalize the outline based on chat history with streaming"""
    if not data.chat_history:
        raise HTTPException(status_code=400, detail="Chat history is empty")

    context = load_context(request)
    if not context["world_theme"] or not context["characters"]:
        raise HTTPException(status_code=400, detail="World or Characters not found. Complete previous steps.")

    num_chapters = data.num_chapters or 10 # Use Pydantic default

    try:
        book_agents = BookAgents(agent_config)
        _ = book_agents.create_agents(context["world_theme"], num_chapters)
        stream = book_agents.generate_final_outline_stream(
            data.chat_history, context["world_theme"], context["characters"], num_chapters
        )
        # Pass request data (as dict) so the generator can access num_chapters for parsing
        return StreamingResponse(
            generate_sse_stream(stream, request, data.dict()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        print(f"Error starting stream in /finalize_outline_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start finalize outline stream: {e}")


# save_outline route is already updated to accept JSON
@app.post("/save_outline")
async def save_outline(request: Request, data: SaveOutlineRequest):
    """Save manually edited outline and parse/save chapters structure"""
    outline_cleaned = data.outline.replace("\r\n", "\n").strip()
    outline_cleaned = re.sub(r"\n{3,}", "\n\n", outline_cleaned)

    request.session["outline"] = outline_cleaned
    save_success = False
    save_warning = None

    try:
        # Save to current project if available
        current_project_id = request.session.get("current_project_id")
        if current_project_id:
            from core.project_manager import ProjectManager
            from core.text_to_json import parse_outline_text_to_json
            pm = ProjectManager()
            project_dir = pm.get_project_path(current_project_id)
            outline_data = parse_outline_text_to_json("Current Project", outline_cleaned)
            with open(project_dir / "outline.json", "w", encoding="utf-8") as f:
                json.dump(outline_data.model_dump(), f, indent=2, ensure_ascii=False)
        else:
            # Legacy fallback
            with open("book_output/outline.txt", "w", encoding="utf-8") as f:
                f.write(outline_cleaned)
        save_success = True
    except Exception as e:
        print(f"Error saving outline manually: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save outline file: {e}")

    try:
        chapters = parse_outline_to_chapters(outline_cleaned, num_chapters=data.num_chapters)
        request.session["chapters"] = chapters
        # Save to current project if available
        current_project_id = request.session.get("current_project_id")
        if current_project_id:
            from core.project_manager import ProjectManager
            pm = ProjectManager()
            project_dir = pm.get_project_path(current_project_id)
            with open(project_dir / "chapters.json", "w", encoding="utf-8") as f:
                json.dump(chapters, f, indent=2, ensure_ascii=False)
        else:
            # Legacy fallback
            with open("book_output/chapters.json", "w", encoding="utf-8") as f:
                json.dump(chapters, f, indent=2)
        num_parsed = len(chapters)
    except Exception as e:
        print(f"Error parsing/saving chapters after manual outline save: {e}")
        save_warning = f"Outline saved, but failed to parse chapters: {e}"
        num_parsed = 0

    return {"success": save_success, "num_chapters": num_parsed, "warning": save_warning if save_warning else None}


# Chapter/Scene Generation API Endpoints
# generate_chapters route is already updated to accept JSON
@app.post("/generate_chapters")
async def generate_chapters(request: Request, data: GenerateChaptersRequest):
    """(Re)Generate chapters structure from existing outline file"""
    # Try current project first
    current_project_id = request.session.get("current_project_id")
    if current_project_id:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        project_dir = pm.get_project_path(current_project_id)
        outline_path = project_dir / "outline.json"
        if not outline_path.exists():
            outline_path = "book_output/outline.txt"  # Legacy fallback
    else:
        outline_path = "book_output/outline.txt"

    if not os.path.exists(outline_path):
         raise HTTPException(status_code=404, detail="Outline file not found. Please create or save an outline first.")

    try:
        with open(outline_path, "r", encoding="utf-8") as f:
            outline_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read outline file: {e}")

    try:
        chapters = parse_outline_to_chapters(outline_content, data.num_chapters)
        request.session["chapters"] = chapters
        # Save to current project if available
        current_project_id = request.session.get("current_project_id")
        if current_project_id:
            from core.project_manager import ProjectManager
            pm = ProjectManager()
            project_dir = pm.get_project_path(current_project_id)
            with open(project_dir / "chapters.json", "w", encoding="utf-8") as f:
                json.dump(chapters, f, indent=2, ensure_ascii=False)
        else:
            # Legacy fallback
            with open("book_output/chapters.json", "w", encoding="utf-8") as f:
                json.dump(chapters, f, indent=2)
        return {"success": True, "num_chapters": len(chapters)}
    except Exception as e:
        print(f"Error parsing chapters in /generate_chapters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse chapters from outline: {e}")


# UPDATED: /chapter/{chapter_number} POST route to accept JSON
@app.post("/chapter/{chapter_number}", response_class=JSONResponse)
async def generate_chapter_content(request: Request, chapter_number: int, data: GenerateChapterContentRequest): # Accept the new Pydantic model
    """Generate content for a specific chapter"""
    context = load_context(request)
    chapters = context["chapters"]
    chapter_data = next(
        (ch for ch in chapters if ch.get("chapter_number") == chapter_number), None
    )

    if not chapter_data:
         raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} data not found.")

    world_theme = context["world_theme"]
    characters = context["characters"]
    if not world_theme or not characters:
        raise HTTPException(status_code=400, detail="World theme or characters missing. Cannot generate chapter.")

    # Get previous chapter context
    previous_context_text = ""
    if chapter_number > 1:
        prev_chapter_path = f"book_output/chapters/chapter_{chapter_number-1}.txt"
        if os.path.exists(prev_chapter_path):
            try:
                with open(prev_chapter_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    summary_len = 1500
                    previous_context_text = content[-summary_len:] if len(content) > summary_len else content
                    previous_context_text = f"Summary of previous chapter:\n{previous_context_text}\n---\n"
            except Exception as e:
                print(f"Error reading previous chapter {chapter_number-1}: {e}")

    chapter_outline_detail = chapter_data.get("prompt", f"Write Chapter {chapter_number}")
    # Access additional_context from the Pydantic model
    additional_context = data.additional_context
    if additional_context:
        chapter_outline_detail += f"\n\nAdditional instructions: {additional_context}"

    writer_prompt = prompts.CHAPTER_GENERATION_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_data.get("title", ""),
        chapter_outline=chapter_outline_detail,
        world_theme=world_theme,
        relevant_characters=characters,
        scene_details="", # Scene generation is separate
        previous_context=previous_context_text,
    )

    try:
        book_agents = BookAgents(agent_config, chapters)
        _ = book_agents.create_agents(world_theme, len(chapters))
        print(f"Generating Chapter {chapter_number}...")
        # Consider making generate_content async if BookAgents involves I/O
        chapter_content = book_agents.generate_content("writer", writer_prompt)
        print(f"Chapter {chapter_number} generated (length: {len(chapter_content)}).")

        chapter_content_cleaned = chapter_content.strip()
        chapter_path = f"book_output/chapters/chapter_{chapter_number}.txt"
        with open(chapter_path, "w", encoding="utf-8") as f:
            f.write(chapter_content_cleaned)
        print(f"Chapter {chapter_number} saved to {chapter_path}.")

        return JSONResponse({"chapter_content": chapter_content_cleaned})

    except Exception as e:
        print(f"Error generating chapter {chapter_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate chapter: {e}")


# UPDATED: /save_chapter/{chapter_number} POST route to accept JSON
@app.post("/save_chapter/{chapter_number}", response_class=JSONResponse)
async def save_chapter(request: Request, chapter_number: int, data: SaveChapterRequest): # Accept the new Pydantic model
    """Save manually edited chapter content"""
    # Access chapter_content from the Pydantic model
    chapter_content_cleaned = data.chapter_content.replace("\r\n", "\n").strip()
    chapter_path = f"book_output/chapters/chapter_{chapter_number}.txt"
    try:
        with open(chapter_path, "w", encoding="utf-8") as f:
            f.write(chapter_content_cleaned)
        return JSONResponse({"success": True})
    except Exception as e:
        print(f"Error saving chapter {chapter_number} manually: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save chapter: {e}")


# UPDATED: /scene/{chapter_number} POST route to accept JSON
@app.post("/scene/{chapter_number}", response_class=JSONResponse)
async def generate_scene(request: Request, chapter_number: int, data: GenerateSceneRequest): # Accept the new Pydantic model
    """Generate a new scene for a specific chapter"""
    context = load_context(request)
    chapters = context["chapters"]
    chapter_data = next(
        (ch for ch in chapters if ch.get("chapter_number") == chapter_number), None
    )

    if not chapter_data:
         raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} data not found.")

    world_theme = context["world_theme"]
    characters = context["characters"]
    if not world_theme or not characters:
        raise HTTPException(status_code=400, detail="World theme or characters missing. Cannot generate scene.")

    chapter_outline_detail = chapter_data.get("prompt", "")
    # Access scene_description from the Pydantic model
    scene_desc_text = data.scene_description or "Generate the next logical scene for this chapter."
    scene_prompt = prompts.SCENE_GENERATION_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_data.get("title", ""),
        chapter_outline=f"{chapter_outline_detail}\n\nInstructions for this scene: {scene_desc_text}",
        world_theme=world_theme,
        relevant_characters=characters,
        previous_context="Focus on the current scene based on the chapter outline and instructions.",
    )

    try:
        book_agents = BookAgents(agent_config, chapters)
        _ = book_agents.create_agents(world_theme, len(chapters))
        print(f"Generating scene for Chapter {chapter_number}...")
        scene_content = book_agents.generate_content("writer", scene_prompt)
        print(f"Scene generated (length: {len(scene_content)}).")

        scene_content_cleaned = scene_content.strip()

        # Save scene to file
        scene_dir = f"book_output/chapters/chapter_{chapter_number}_scenes"
        os.makedirs(scene_dir, exist_ok=True)
        scene_count = len([f for f in os.listdir(scene_dir) if f.endswith(".txt")])
        scene_path = f"{scene_dir}/scene_{scene_count + 1}.txt"
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write(scene_content_cleaned)
        print(f"Scene saved to {scene_path}")

        return JSONResponse({"scene_content": scene_content_cleaned, "scene_number": scene_count + 1})

    except Exception as e:
        print(f"Error generating scene for chapter {chapter_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate scene: {e}")


# API Endpoints for Svelte to fetch data (These use GET, no JSON body needed)
@app.get("/api/project-status")
async def get_project_status(request: Request):
    """Get the current status of the book project"""
    context = load_context(request)
    return {
        "hasWorld": bool(context.get("world_theme")),
        "hasCharacters": bool(context.get("characters")),
        "hasOutline": bool(context.get("outline")),
        "chapterCount": len(context.get("chapters", []))
    }

@app.get("/api/world")
async def get_world(request: Request):
    """Get world theme data"""
    context = load_context(request)
    return JSONResponse({
        "world_theme": context.get("world_theme", ""),
        "topic": context.get("topic", "") # Include topic here
    })

@app.get("/api/characters")
async def get_characters(request: Request):
    """Get characters data"""
    context = load_context(request)
    # Assuming context["characters"] is already the string content
    return JSONResponse({
        "characters": context.get("characters", "")
    })

@app.get("/api/outline")
async def get_outline(request: Request):
    """Get outline data"""
    context = load_context(request)
    return JSONResponse({
        "outline": context.get("outline", "")
    })

@app.get("/api/chapters")
async def get_chapters(request: Request):
    """Get chapters data"""
    context = load_context(request)
    # Assuming context["chapters"] is already the list of chapter objects
    return JSONResponse({
        "chapters": context.get("chapters", [])
    })


# TTS API Endpoints
@app.get("/api/tts/voices")
async def get_tts_voices():
    """Get available TTS voices from Kokoro-FastAPI"""
    try:
        response = requests.get(f"{KOKORO_API_BASE_URL}/voices")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to fetch voices", "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"error": f"Kokoro-FastAPI server not available: {str(e)}"}

@app.post("/api/tts/generate")
async def generate_tts(data: TTSRequest):
    """Generate TTS audio from text"""
    try:
        tts_data = {
            "model": "kokoro",
            "voice": data.voice,
            "input": data.text,
            "response_format": data.response_format
        }
        
        response = requests.post(
            f"{KOKORO_API_BASE_URL}/audio/speech",
            json=tts_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Save the audio file
            filename = f"book_output/tts_output.{data.response_format}"
            with open(filename, "wb") as f:
                f.write(response.content)
            
            return {"success": True, "filename": filename, "size": len(response.content)}
        else:
            return {"error": "Failed to generate TTS", "status_code": response.status_code}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Kokoro-FastAPI server not available: {str(e)}"}

@app.post("/api/tts/chapter/{chapter_number}")
async def generate_chapter_tts(chapter_number: int, data: ChapterTTSRequest):
    """Generate TTS audio for a specific chapter"""
    chapter_path = f"book_output/chapters/chapter_{chapter_number}.txt"
    
    if not os.path.exists(chapter_path):
        raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} not found")
    
    try:
        # Read chapter content
        with open(chapter_path, "r", encoding="utf-8") as f:
            chapter_content = f.read()
        
        if not chapter_content.strip():
            raise HTTPException(status_code=400, detail=f"Chapter {chapter_number} is empty")
        
        # Generate TTS
        tts_data = {
            "model": "kokoro",
            "voice": data.voice,
            "input": chapter_content,
            "response_format": data.response_format
        }
        
        response = requests.post(
            f"{KOKORO_API_BASE_URL}/audio/speech",
            json=tts_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Save the audio file
            audio_filename = f"book_output/chapters/chapter_{chapter_number}.{data.response_format}"
            with open(audio_filename, "wb") as f:
                f.write(response.content)
            
            return {
                "success": True, 
                "filename": audio_filename, 
                "size": len(response.content),
                "chapter_number": chapter_number,
                "voice": data.voice
            }
        else:
            return {"error": "Failed to generate chapter TTS", "status_code": response.status_code}
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} file not found")
    except requests.exceptions.RequestException as e:
        return {"error": f"Kokoro-FastAPI server not available: {str(e)}"}

@app.get("/api/tts/status")
async def get_tts_status():
    """Check Kokoro-FastAPI server status"""
    try:
        response = requests.get(f"{KOKORO_API_BASE_URL}/health", timeout=5)
        return {"status": "available", "server_status": response.status_code}
    except requests.exceptions.RequestException:
        return {"status": "unavailable", "error": "Kokoro-FastAPI server not responding"}


# Project Management API Endpoints
@app.get("/api/projects")
async def list_projects():
    """List all book projects"""
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        projects = pm.list_projects()
        return [project.dict() for project in projects]
    except Exception as e:
        print(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {e}")

@app.post("/api/projects")
async def create_project(data: CreateProjectRequest):
    """Create a new book project"""
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        project = pm.create_project(
            title=data.title,
            author=data.author,
            genre=data.genre,
            description=data.description
        )
        return project.dict()
    except Exception as e:
        print(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {e}")

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a book project"""
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        success = pm.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {e}")

@app.post("/api/projects/{project_id}/activate")
async def activate_project(project_id: str, request: Request):
    """Switch to working on a specific project"""
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        project = pm.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Set current project in session
        request.session["current_project_id"] = project_id
        
        # Clear cached data to force reload from new project
        for key in ["world_theme", "characters", "outline", "chapters"]:
            request.session.pop(key, None)
        
        return {"success": True, "project": project.dict()}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error activating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate project: {e}")

@app.get("/api/projects/current")
async def get_current_project(request: Request):
    """Get the currently active project"""
    current_project_id = request.session.get("current_project_id")
    if not current_project_id:
        return {"current_project": None}
    
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        project = pm.get_project(current_project_id)
        if not project:
            # Clear invalid project from session
            request.session.pop("current_project_id", None)
            return {"current_project": None}
        
        return {"current_project": project.dict()}
    except Exception as e:
        print(f"Error getting current project: {e}")
        return {"current_project": None}

# Import API Endpoints  
@app.post("/api/import/analyze")
async def analyze_import_file(data: ImportAnalysisRequest):
    """Analyze an uploaded file for import preview"""
    try:
        from core.import_utils import DocumentParser
        
        file_path = data.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse the document
        parser = DocumentParser()
        if file_path.endswith('.docx'):
            text = parser.parse_docx(file_path)
        elif file_path.endswith('.odt'):
            text = parser.parse_odt(file_path)
        elif file_path.endswith('.epub'):
            text = parser.parse_epub(file_path)
        elif file_path.endswith('.mobi'):
            text = parser.parse_mobi(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Supported formats: .docx, .odt, .epub")
        
        # Extract metadata
        # For EPUB files, try metadata extraction first
        if file_path.endswith('.epub'):
            title, author = parser.extract_epub_metadata(file_path)
            # Fallback to content-based extraction if needed
            if not title or not author:
                content_title, content_author = parser.extract_title_and_author(text, file_path)
                title = title or content_title
                author = author or content_author
        else:
            title, author = parser.extract_title_and_author(text, file_path)
        chapters = parser.detect_chapters(text)
        
        # Basic analysis
        total_words = sum(len(ch['content'].split()) for ch in chapters)
        
        return {
            "title": title,
            "author": author,
            "chapter_count": len(chapters),
            "total_words": total_words,
            "chapters_preview": [
                {
                    "chapter_number": ch["chapter_number"],
                    "title": ch["title"],
                    "word_count": len(ch["content"].split()),
                    "preview": ch["content"][:200] + "..." if len(ch["content"]) > 200 else ch["content"]
                }
                for ch in chapters[:3]  # Show first 3 chapters only
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing import file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {e}")

@app.post("/api/import/novel")
async def import_novel(data: ImportNovelRequest, request: Request):
    """Import a novel and create a new project"""
    try:
        from core.project_manager import ProjectManager
        
        if not os.path.exists(data.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        pm = ProjectManager()
        project = pm.import_novel(
            file_path=data.file_path,
            title=data.title,
            author=data.author,
            genre=data.genre,
            auto_generate_metadata=data.auto_generate_metadata,
            agent_config=agent_config
        )
        
        # Automatically activate the new project
        request.session["current_project_id"] = project.id
        
        # Clear cached data
        for key in ["world_theme", "characters", "outline", "chapters"]:
            request.session.pop(key, None)
        
        return {"success": True, "project": project.dict()}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error importing novel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import novel: {e}")


# --- Outline Parsing Helper ---
# (Remains the same)
def parse_outline_to_chapters(outline_content, num_chapters_fallback):
    """Helper function to parse outline content into structured chapter format"""
    chapters = []
    print(f"Attempting to parse outline (length: {len(outline_content)} chars)...")
    try:
        start_marker = "OUTLINE:"
        end_marker = "END OF OUTLINE"
        start_idx = outline_content.find(start_marker)
        end_idx = outline_content.rfind(end_marker)

        if start_idx != -1:
            if end_idx != -1 and end_idx > start_idx:
                outline_text = outline_content[start_idx + len(start_marker) : end_idx].strip()
                print("Extracted content between OUTLINE: and END OF OUTLINE.")
            else:
                outline_text = outline_content[start_idx + len(start_marker) :].strip()
                print("Extracted content after OUTLINE: (END OF OUTLINE not found or misplaced).")
        else:
            outline_text = outline_content
            print("OUTLINE: marker not found, parsing full content.")

        chapter_pattern = re.compile(r"^\s*Chapter\s+(\d+)\s*:\s*(.*?)\s*$", re.MULTILINE | re.IGNORECASE)
        matches = list(chapter_pattern.finditer(outline_text))
        print(f"Found {len(matches)} potential chapter title matches.")

        seen_chapters = set()
        for i, match in enumerate(matches):
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip() or f"Chapter {chapter_num} (Untitled)"
            match_start = match.start()
            match_end = match.end()

            if chapter_num in seen_chapters:
                print(f"Skipping duplicate chapter number {chapter_num}.")
                continue
            seen_chapters.add(chapter_num)

            content_start = match_end
            content_end = matches[i + 1].start() if (i + 1) < len(matches) else len(outline_text)
            chapter_description = outline_text[content_start:content_end].strip()
            chapter_description = re.sub(r"^\s*-\s*", "* ", chapter_description, flags=re.MULTILINE)

            chapters.append({
                "chapter_number": chapter_num,
                "title": chapter_title,
                "prompt": chapter_description,
            })
            print(f"Parsed Chapter {chapter_num}: '{chapter_title}' (Content length: {len(chapter_description)})")

    except Exception as e:
        print(f"ERROR during outline parsing: {e}. Falling back to default chapter generation.")
        chapters = []

    if not chapters:
        print(f"No chapters successfully parsed. Creating {num_chapters_fallback} default chapter structures.")
        chapters = [
            {"chapter_number": i, "title": f"Chapter {i} (Outline Parsing Failed)", "prompt": f"Content outline for chapter {i} could not be parsed."}
            for i in range(1, num_chapters_fallback + 1)
        ]

    chapters.sort(key=lambda x: x.get("chapter_number", 0))
    print(f"Final parsed chapter count: {len(chapters)}")
    return chapters

# --- Catch-all route for Svelte SPA ---
# This should be the LAST route defined. It serves index.html
# for any path not explicitly handled above (static files or API routes).
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa_fallback(request: Request, full_path: str):
    """Serve the Svelte SPA for any path not otherwise matched."""
    print(f"Serving SPA fallback index.html for path: {full_path}")
    return templates.TemplateResponse("index.html", {"request": request})

# Run the app using: uvicorn hypewriter:app --reload --port 5000
