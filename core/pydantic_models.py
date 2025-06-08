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

# TTS Models
class TTSRequest(BaseModel):
    text: str
    voice: str = "bf_emma"
    response_format: str = "mp3"

class ChapterTTSRequest(BaseModel):
    chapter_number: int
    voice: str = "bf_emma"
    response_format: str = "mp3"

# Project Management Models
class ProjectMetadata(BaseModel):
    id: str
    title: str
    author: str = ""
    genre: str = ""
    created_date: str
    last_modified: str
    description: str = ""
    chapter_count: int = 0
    word_count: int = 0

class CreateProjectRequest(BaseModel):
    title: str
    author: str = ""
    genre: str = ""
    description: str = ""

class ImportAnalysisRequest(BaseModel):
    file_path: str

class ImportNovelRequest(BaseModel):
    title: str
    author: str = ""
    genre: str = ""
    file_path: str
    auto_generate_metadata: bool = True
