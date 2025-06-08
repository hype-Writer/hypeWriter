"""
Convert AI-generated text content to structured JSON
"""

import re
from typing import List, Dict, Any
from .json_schemas import WorldData, CharactersData, OutlineData, Character, CharacterRelationship

def parse_world_text_to_json(title: str, ai_content: str) -> WorldData:
    """Parse AI-generated world text into structured JSON"""
    
    # Initialize with basic structure
    world_data = WorldData.from_ai_text(title, ai_content)
    
    # Try to extract structured information from the text
    content_lower = ai_content.lower()
    
    # Extract genre
    if any(word in content_lower for word in ['dystopian', 'post-apocalyptic', 'wasteland']):
        world_data.genre = "Dystopian/Post-Apocalyptic"
    elif any(word in content_lower for word in ['fantasy', 'magic', 'wizard', 'spell']):
        world_data.genre = "Fantasy"
    elif any(word in content_lower for word in ['sci-fi', 'science fiction', 'space', 'future', 'technology']):
        world_data.genre = "Science Fiction"
    elif any(word in content_lower for word in ['horror', 'terror', 'nightmare', 'fear']):
        world_data.genre = "Horror"
    
    # Extract time period
    if any(word in content_lower for word in ['medieval', 'middle ages', 'knights', 'castles']):
        world_data.time_period = "Medieval"
    elif any(word in content_lower for word in ['modern', 'contemporary', 'present day']):
        world_data.time_period = "Modern"
    elif any(word in content_lower for word in ['future', 'futuristic', 'advanced', 'space age']):
        world_data.time_period = "Future"
    elif any(word in content_lower for word in ['post-apocalyptic', 'after the', 'ruins', 'wasteland']):
        world_data.time_period = "Post-Apocalyptic"
    
    # Extract magic system information
    if any(word in content_lower for word in ['magic', 'spell', 'wizard', 'mage', 'enchant', 'arcane']):
        world_data.magic_system.exists = True
        world_data.magic_system.type = "Unknown magic system"
    
    # Extract themes from content
    themes = []
    if 'survival' in content_lower:
        themes.append("Survival")
    if any(word in content_lower for word in ['power', 'corruption', 'authority']):
        themes.append("Power and Corruption")
    if any(word in content_lower for word in ['good', 'evil', 'moral', 'ethics']):
        themes.append("Good vs Evil")
    if any(word in content_lower for word in ['sacrifice', 'loss', 'death']):
        themes.append("Sacrifice and Loss")
    if any(word in content_lower for word in ['technology', 'progress', 'advancement']):
        themes.append("Technology and Progress")
    
    world_data.themes = themes
    
    # Extract setting summary (first paragraph or up to 200 chars)
    lines = ai_content.split('\n')
    for line in lines:
        clean_line = line.strip()
        if len(clean_line) > 50 and not clean_line.startswith('*') and not clean_line.startswith('#'):
            world_data.setting_summary = clean_line[:200] + "..." if len(clean_line) > 200 else clean_line
            break
    
    return world_data

def parse_characters_text_to_json(ai_content: str) -> CharactersData:
    """Parse AI-generated character text into structured JSON"""
    
    # Initialize with basic structure  
    characters_data = CharactersData.from_ai_text(ai_content)
    
    # Try to extract character information
    characters = []
    
    # Look for character profile patterns
    character_sections = re.split(r'\*\*Character Profile \d+:', ai_content)
    if len(character_sections) < 2:
        # Try alternative patterns
        character_sections = re.split(r'\*\*\d+\.\d+\s+[\w\s]+\*\*', ai_content)
    
    for section in character_sections[1:]:  # Skip first empty section
        character = _extract_character_from_section(section)
        if character:
            characters.append(character)
    
    characters_data.characters = characters
    
    # Extract relationship summary
    if len(characters) > 1:
        characters_data.relationship_summary = f"Story features {len(characters)} characters with interconnected relationships"
    
    return characters_data

def _extract_character_from_section(section: str) -> Character:
    """Extract character information from a text section"""
    
    lines = section.split('\n')
    
    # Extract name (usually in the first few lines)
    name = "Unknown Character"
    for line in lines[:5]:
        line = line.strip()
        if line.startswith('**') and line.endswith('**'):
            name = line.replace('*', '').strip()
            break
        elif 'Name:' in line:
            name = line.split('Name:')[-1].replace('*', '').strip()
            break
    
    # Extract role
    role = "supporting"
    role_text = section.lower()
    if any(word in role_text for word in ['protagonist', 'main character', 'hero']):
        role = "protagonist"
    elif any(word in role_text for word in ['antagonist', 'villain', 'enemy']):
        role = "antagonist"
    
    # Extract importance
    importance = "secondary"
    if 'main character' in role_text or 'protagonist' in role_text:
        importance = "main"
    elif any(word in role_text for word in ['minor', 'background', 'brief']):
        importance = "minor"
    
    # Extract personality traits
    personality = []
    if 'personality' in role_text:
        personality_section = re.search(r'personality.*?(?=\*|$)', section, re.IGNORECASE | re.DOTALL)
        if personality_section:
            personality_text = personality_section.group(0)
            # Look for bullet points or traits
            traits = re.findall(r'[*-]\s*\*\*([^*]+)\*\*', personality_text)
            personality = [trait.strip() for trait in traits]
    
    # Extract goals
    goals = []
    if 'goal' in role_text:
        goals_section = re.search(r'goal.*?(?=\*|$)', section, re.IGNORECASE | re.DOTALL)
        if goals_section:
            goals_text = goals_section.group(0)
            goal_matches = re.findall(r'[*-]\s*\*\*([^*]+)\*\*', goals_text)
            goals = [goal.strip() for goal in goal_matches]
    
    return Character(
        name=name,
        role=role,
        importance=importance,
        personality=personality,
        goals=goals,
        physical_description="",
        background="",
        character_arc=""
    )

def parse_outline_text_to_json(title: str, ai_content: str) -> OutlineData:
    """Parse AI-generated outline text into structured JSON"""
    
    # Initialize with basic structure
    outline_data = OutlineData.from_ai_text(title, ai_content)
    
    content_lower = ai_content.lower()
    
    # Extract genre
    if any(word in content_lower for word in ['sci-fi', 'science fiction', 'space', 'future']):
        outline_data.story_structure.genre = "Science Fiction"
    elif any(word in content_lower for word in ['fantasy', 'magic', 'wizard']):
        outline_data.story_structure.genre = "Fantasy"
    elif any(word in content_lower for word in ['mystery', 'detective', 'crime']):
        outline_data.story_structure.genre = "Mystery"
    elif any(word in content_lower for word in ['romance', 'love', 'relationship']):
        outline_data.story_structure.genre = "Romance"
    
    # Extract themes
    themes = []
    if 'identity' in content_lower:
        themes.append("Identity")
    if 'friendship' in content_lower:
        themes.append("Friendship")
    if 'survival' in content_lower:
        themes.append("Survival")
    if any(word in content_lower for word in ['power', 'corruption']):
        themes.append("Power and Corruption")
    
    outline_data.story_structure.themes = themes
    
    # Try to extract plot structure
    if 'beginning' in content_lower:
        beginning_match = re.search(r'beginning[:\s]*([^*]+?)(?=middle|end|$)', ai_content, re.IGNORECASE | re.DOTALL)
        if beginning_match:
            outline_data.plot_outline.beginning = beginning_match.group(1).strip()
    
    if 'middle' in content_lower:
        middle_match = re.search(r'middle[:\s]*([^*]+?)(?=end|climax|$)', ai_content, re.IGNORECASE | re.DOTALL)
        if middle_match:
            outline_data.plot_outline.rising_action = middle_match.group(1).strip()
    
    if 'climax' in content_lower:
        climax_match = re.search(r'climax[:\s]*([^*]+?)(?=resolution|end|$)', ai_content, re.IGNORECASE | re.DOTALL)
        if climax_match:
            outline_data.plot_outline.climax = climax_match.group(1).strip()
    
    return outline_data