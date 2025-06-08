"""
JSON schemas for structured story data
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class WorldLocation(BaseModel):
    name: str
    description: str
    importance: str  # "major", "minor", "landmark"
    dangers: List[str] = []
    resources: List[str] = []

class MagicSystem(BaseModel):
    exists: bool = False
    type: Optional[str] = None  # "elemental", "ritual", "divine", etc.
    rules: List[str] = []
    limitations: List[str] = []
    users: List[str] = []

class Technology(BaseModel):
    level: str = "modern"  # "stone age", "medieval", "modern", "futuristic", "post-apocalyptic"
    notable_tech: List[str] = []
    restrictions: List[str] = []
    lost_tech: List[str] = []

class Society(BaseModel):
    government: Optional[str] = None
    social_structure: List[str] = []
    culture: List[str] = []
    beliefs: List[str] = []
    conflicts: List[str] = []

class WorldData(BaseModel):
    title: str = ""
    genre: str = "To be determined"
    setting_summary: str = ""
    time_period: str = "Unknown"
    
    geography: Dict[str, Any] = {}
    magic_system: MagicSystem = MagicSystem()
    technology: Technology = Technology()
    society: Society = Society()
    
    themes: List[str] = []
    atmosphere: str = ""
    
    generated_date: str
    raw_content: str  # Full AI-generated text for backward compatibility
    
    @classmethod
    def from_ai_text(cls, title: str, ai_content: str) -> "WorldData":
        """Create WorldData from AI-generated text content"""
        return cls(
            title=title,
            genre="To be determined",
            setting_summary="Extracted from AI analysis",
            time_period="To be determined",
            generated_date=datetime.now().isoformat(),
            raw_content=ai_content
        )

class CharacterRelationship(BaseModel):
    character: str
    relationship_type: str  # "friend", "enemy", "family", "mentor", etc.
    description: str

class Character(BaseModel):
    name: str
    role: str  # "protagonist", "antagonist", "supporting"
    importance: str  # "main", "secondary", "minor"
    
    physical_description: str = ""
    background: str = ""
    personality: List[str] = []
    goals: List[str] = []
    motivations: List[str] = []
    
    relationships: List[CharacterRelationship] = []
    character_arc: str = ""
    
    skills: List[str] = []
    weaknesses: List[str] = []

class CharactersData(BaseModel):
    characters: List[Character]
    relationship_summary: str = ""
    dynamics: List[str] = []
    
    generated_date: str
    raw_content: str  # Full AI-generated text for backward compatibility
    
    @classmethod
    def from_ai_text(cls, ai_content: str) -> "CharactersData":
        """Create CharactersData from AI-generated text content"""
        return cls(
            characters=[],
            generated_date=datetime.now().isoformat(),
            raw_content=ai_content
        )

class ChapterOutline(BaseModel):
    chapter_number: int
    title: str
    summary: str
    characters_involved: List[str] = []
    plot_points: List[str] = []
    themes: List[str] = []
    conflicts: List[str] = []

class StoryStructure(BaseModel):
    genre: str = "To be determined"
    themes: List[str] = []
    tone: str = ""
    pacing: str = ""
    point_of_view: str = ""

class PlotOutline(BaseModel):
    beginning: str = ""
    inciting_incident: str = ""
    rising_action: str = ""
    climax: str = ""
    falling_action: str = ""
    resolution: str = ""

class OutlineData(BaseModel):
    story_structure: StoryStructure
    plot_outline: PlotOutline
    chapters: List[ChapterOutline] = []
    
    character_arcs: List[str] = []
    plot_threads: List[str] = []
    major_conflicts: List[str] = []
    
    generated_date: str
    raw_content: str  # Full AI-generated text for backward compatibility
    
    @classmethod
    def from_ai_text(cls, title: str, ai_content: str) -> "OutlineData":
        """Create OutlineData from AI-generated text content"""
        return cls(
            story_structure=StoryStructure(genre="To be determined"),
            plot_outline=PlotOutline(),
            generated_date=datetime.now().isoformat(),
            raw_content=ai_content
        )