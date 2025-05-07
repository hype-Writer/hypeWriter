from pydantic import BaseModel
from typing import List, Optional, Dict

# --- Pydantic Models for Request Bodies ---

class SaveWorldRequest(BaseModel):
    world_theme: str

class SaveCharactersRequest(BaseModel):
    characters: str

class ChatRequestData(BaseModel):
    message: str
    chat_history: List[Dict[str, str]]
    topic: Optional[str] = None
    num_chapters: Optional[int] = 10

class FinalizeRequestData(BaseModel):
    chat_history: List[Dict[str, str]]
    topic: Optional[str] = None
    num_characters: Optional[int] = 3
    num_chapters: Optional[int] = 10

class SaveOutlineRequest(BaseModel):
    outline: str
    num_chapters: int = 20

class GenerateChaptersRequest(BaseModel):
    num_chapters: int = 20

class GenerateChapterContentRequest(BaseModel):
    additional_context: str

class SaveChapterRequest(BaseModel):
    chapter_content: str

class GenerateSceneRequest(BaseModel):
    scene_description: str
