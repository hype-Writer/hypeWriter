"""
Import utilities for hypeWriter
Handles parsing of various document formats and chapter detection
"""

import re
import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from docx import Document
from odf import text, teletype
from odf.opendocument import load
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


class DocumentParser:
    """Parse various document formats for import into hypeWriter"""
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """Extract text content from DOCX file"""
        try:
            doc = Document(file_path)
            full_text = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            
            return '\n\n'.join(full_text)
        except Exception as e:
            raise Exception(f"Failed to parse DOCX file: {str(e)}")
    
    @staticmethod
    def parse_odt(file_path: str) -> str:
        """Extract text content from ODT file"""
        try:
            # Load the ODT document
            doc = load(file_path)
            
            # Extract all text
            full_text = []
            
            # Get all paragraphs from the document
            paragraphs = doc.getElementsByType(text.P)
            for paragraph in paragraphs:
                # Extract text from paragraph
                text_content = teletype.extractText(paragraph).strip()
                if text_content:
                    full_text.append(text_content)
            
            # Also get headings
            headings = doc.getElementsByType(text.H)
            for heading in headings:
                text_content = teletype.extractText(heading).strip()
                if text_content:
                    full_text.append(text_content)
            
            return '\n\n'.join(full_text)
        except Exception as e:
            raise Exception(f"Failed to parse ODT file: {str(e)}")
    
    @staticmethod
    def parse_epub(file_path: str) -> str:
        """Extract text content from EPUB file"""
        try:
            # Load the EPUB book
            book = epub.read_epub(file_path)
            
            # Extract text from all chapters
            full_text = []
            
            # Get all items in the book
            for item in book.get_items():
                # Only process XHTML documents (chapters)
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # Parse HTML content
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Extract text, preserving paragraph breaks
                    text_content = soup.get_text(separator='\n\n', strip=True)
                    
                    if text_content:
                        full_text.append(text_content)
            
            return '\n\n'.join(full_text)
        except Exception as e:
            raise Exception(f"Failed to parse EPUB file: {str(e)}")
    
    @staticmethod
    def extract_epub_metadata(file_path: str) -> Tuple[str, str]:
        """Extract title and author from EPUB metadata"""
        try:
            book = epub.read_epub(file_path)
            
            # Get title from metadata
            title = ""
            title_metadata = book.get_metadata('DC', 'title')
            if title_metadata:
                title = title_metadata[0][0]  # First title, first element
            
            # Get author from metadata  
            author = ""
            creator_metadata = book.get_metadata('DC', 'creator')
            if creator_metadata:
                author = creator_metadata[0][0]  # First creator, first element
            
            return title, author
        except Exception:
            return "", ""
    
    @staticmethod
    def parse_mobi(file_path: str) -> str:
        """Extract text content from MOBI file"""
        # MOBI parsing is complex due to DRM and proprietary format
        # For now, provide a helpful error message
        raise Exception(
            "MOBI format is not yet supported due to technical complexity. "
            "Please convert your MOBI file to EPUB format using tools like Calibre, "
            "then import the EPUB version. Supported formats: .docx, .odt, .epub"
        )
    
    @staticmethod
    def detect_chapters(text: str) -> List[Dict[str, any]]:
        """Detect chapter breaks in text and return structured chapters"""
        chapters = []
        
        # Common chapter patterns
        chapter_patterns = [
            r'^\s*chapter\s+(\d+)\s*:?\s*(.*)$',  # "Chapter 1: Title" or "Chapter 1"
            r'^\s*chapter\s+(\w+)\s*:?\s*(.*)$',  # "Chapter One: Title"
            r'^\s*(\d+)\.\s*(.*)$',               # "1. Title"
            r'^\s*part\s+(\d+)\s*:?\s*(.*)$',     # "Part 1: Title"
        ]
        
        lines = text.split('\n')
        current_chapter = None
        chapter_number = 1
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Check if this line is a chapter header
            is_chapter_header = False
            chapter_title = ""
            
            for pattern in chapter_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    # Save previous chapter if exists
                    if current_chapter is not None:
                        current_chapter['content'] = '\n\n'.join(current_content).strip()
                        chapters.append(current_chapter)
                    
                    # Start new chapter
                    chapter_title = match.group(2).strip() if len(match.groups()) > 1 else ""
                    if not chapter_title:
                        chapter_title = f"Chapter {chapter_number}"
                    
                    current_chapter = {
                        'chapter_number': chapter_number,
                        'title': chapter_title,
                        'content': ''
                    }
                    current_content = []
                    chapter_number += 1
                    is_chapter_header = True
                    break
            
            # Add content to current chapter
            if not is_chapter_header:
                current_content.append(line_stripped)
        
        # Don't forget the last chapter
        if current_chapter is not None:
            current_chapter['content'] = '\n\n'.join(current_content).strip()
            chapters.append(current_chapter)
        
        # If no chapters detected, treat entire text as single chapter
        if not chapters:
            chapters.append({
                'chapter_number': 1,
                'title': 'Chapter 1',
                'content': text.strip()
            })
        
        return chapters
    
    @staticmethod
    def extract_title_and_author(text: str, filename: str) -> Tuple[str, str]:
        """Extract title and author from text or filename"""
        lines = text.split('\n')[:20]  # Check first 20 lines
        
        title = ""
        author = ""
        potential_titles = []
        
        # Try to find title/author in first few lines
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # Skip obvious metadata/address lines
            if any(x in line_clean.lower() for x in ['@', 'words', 'maršala', 'tuzla', 'bosnia', 'herzegovina']):
                continue
                
            # Look for "by Author Name" pattern
            by_match = re.search(r'by\s+(.+)', line_clean, re.IGNORECASE)
            if by_match:
                author = by_match.group(1).strip()
                continue
            
            # Collect potential titles (avoid obvious non-titles)
            if (len(line_clean) > 3 and len(line_clean) < 100 and 
                not re.match(r'chapter\s+\d+', line_clean, re.IGNORECASE) and
                not line_clean.isdigit() and
                not re.match(r'\d+\s+words', line_clean, re.IGNORECASE)):
                potential_titles.append((i, line_clean))
        
        # Find the best title candidate
        if potential_titles:
            # Look for a standalone line that looks like a title
            for pos, candidate in potential_titles:
                # If it's a short, clean line and appears early
                if len(candidate) < 50 and pos < 10:
                    title = candidate
                    break
            
            # If no good standalone title, use the first reasonable candidate
            if not title and potential_titles:
                title = potential_titles[0][1]
        
        # Fallback to filename for title
        if not title:
            title = Path(filename).stem
            # Clean up filename-based title
            title = re.sub(r'[-_]', ' ', title)
            title = title.title()
        
        # Extract author from filename if not found in text
        if not author and '-' in filename:
            # Pattern: "Title-Author Name.docx"
            parts = Path(filename).stem.split('-')
            if len(parts) >= 2:
                author = parts[-1].strip()
        
        # Clean up title (remove word counts, extra whitespace)
        if title:
            title = re.sub(r'\d+\s+words?', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+', ' ', title).strip()
        
        return title, author


class ImportAnalyzer:
    """Analyze imported content to extract metadata using AI"""
    
    def __init__(self, agent_config: Dict):
        self.agent_config = agent_config
    
    def analyze_for_import(self, chapters: List[Dict], title: str) -> Dict:
        """Analyze chapters and return suggested metadata using AI"""
        full_text = '\n\n'.join([ch['content'] for ch in chapters])
        
        # Use AI analysis if agent_config is available
        if self.agent_config and self.agent_config.get('config_list'):
            try:
                from datetime import datetime
                analysis = {
                    'title': title,
                    'chapter_count': len(chapters),
                    'total_words': len(full_text.split()),
                    'suggested_characters': self._extract_ai_characters(full_text, title),
                    'suggested_world': self._extract_ai_world(full_text, title),
                    'suggested_outline': self._extract_ai_outline(chapters, title),
                    'generated_date': datetime.now().isoformat(),
                    'chapters': chapters
                }
            except Exception as e:
                print(f"AI analysis failed, falling back to basic analysis: {e}")
                analysis = {
                    'title': title,
                    'chapter_count': len(chapters),
                    'total_words': len(full_text.split()),
                    'suggested_characters': self._extract_basic_characters(full_text),
                    'suggested_world': self._extract_basic_world(full_text),
                    'chapters': chapters
                }
        else:
            # Fallback to basic analysis if no AI config
            analysis = {
                'title': title,
                'chapter_count': len(chapters),
                'total_words': len(full_text.split()),
                'suggested_characters': self._extract_basic_characters(full_text),
                'suggested_world': self._extract_basic_world(full_text),
                'chapters': chapters
            }
        
        return analysis
    
    def _extract_basic_characters(self, text: str) -> str:
        """Basic character extraction (placeholder for AI implementation)"""
        # Find proper nouns that might be character names
        names = set()
        words = text.split()
        
        for word in words:
            # Simple heuristic: capitalized words that aren't common words
            if (word.istitle() and 
                len(word) > 2 and 
                word.lower() not in ['the', 'and', 'but', 'for', 'or', 'nor', 'so', 'yet']):
                names.add(word)
        
        if names:
            return f"Potential characters identified: {', '.join(sorted(list(names)[:10]))}\n\n[This is a basic analysis. AI-powered character extraction will provide detailed profiles.]"
        else:
            return "[No clear character names detected in basic analysis.]"
    
    def _extract_basic_world(self, text: str) -> str:
        """Basic world extraction (placeholder for AI implementation)"""
        word_count = len(text.split())
        return f"""Basic World Analysis:
- Setting: [To be analyzed by AI]
- Word count: {word_count:,} words
- Genre: [To be determined]

[This is a basic analysis. AI-powered world extraction will provide detailed setting, rules, and environment information.]"""
    
    def _extract_ai_characters(self, text: str, title: str) -> str:
        """AI-powered character extraction"""
        from .agents import BookAgents
        
        # Create BookAgents instance for AI analysis
        book_agents = BookAgents(self.agent_config)
        
        # Initialize agents (required for BookAgents to work)
        book_agents.create_agents("Character analysis", 1)
        
        # Truncate text if too long for AI processing
        max_chars = 50000  # Adjust based on AI model limits
        truncated_text = text[:max_chars] + "..." if len(text) > max_chars else text
        
        character_prompt = f"""Analyze the following story text and extract detailed character information:

STORY: {title}
TEXT: {truncated_text}

Please provide a comprehensive character analysis including:

1. MAIN CHARACTERS (3-5 most important):
   - Name
   - Role/occupation
   - Key personality traits
   - Important relationships
   - Character arc/development

2. SECONDARY CHARACTERS (supporting roles):
   - Names and brief descriptions
   - Relationships to main characters

3. CHARACTER RELATIONSHIPS:
   - How characters connect to each other
   - Key conflicts or alliances

Format your response as a detailed character document that would help a writer continue this story.
Focus on characters who have dialogue, actions, or significant story impact.
"""
        
        try:
            character_analysis = book_agents.generate_content("world_builder", character_prompt)
            return character_analysis
        except Exception as e:
            return f"AI character analysis failed: {e}\n\nFalling back to basic analysis:\n{self._extract_basic_characters(text)}"
    
    def _extract_ai_world(self, text: str, title: str) -> str:
        """AI-powered world-building extraction"""
        from .agents import BookAgents
        
        # Create BookAgents instance for AI analysis
        book_agents = BookAgents(self.agent_config)
        
        # Initialize agents (required for BookAgents to work)
        book_agents.create_agents("World analysis", 1)
        
        # Truncate text if too long for AI processing
        max_chars = 50000
        truncated_text = text[:max_chars] + "..." if len(text) > max_chars else text
        
        world_prompt = f"""Analyze the following story text and extract detailed world-building information:

STORY: {title}
TEXT: {truncated_text}

Please provide a comprehensive world analysis including:

1. SETTING:
   - Time period (past, present, future, fantasy era)
   - Location (planet, country, city, fictional world)
   - Physical environment and geography

2. TECHNOLOGY LEVEL:
   - What technology exists in this world?
   - How advanced is the society?
   - Any special or unique technologies?

3. SOCIAL STRUCTURE:
   - Government/political systems
   - Social classes or hierarchies
   - Cultural norms and customs

4. RULES OF THE WORLD:
   - Magic systems (if fantasy)
   - Scientific principles (if sci-fi)
   - Any unique world mechanics or laws

5. ATMOSPHERE & TONE:
   - What genre is this?
   - What mood/feeling does this world create?
   - Key themes or concepts

Format your response as a detailed world-building document that would help a writer maintain consistency when continuing this story.
"""
        
        try:
            world_analysis = book_agents.generate_content("world_builder", world_prompt)
            return world_analysis
        except Exception as e:
            return f"AI world analysis failed: {e}\n\nFalling back to basic analysis:\n{self._extract_basic_world(text)}"
    
    def _extract_ai_outline(self, chapters: List[Dict], title: str) -> str:
        """AI-powered outline generation from existing chapters"""
        from .agents import BookAgents
        
        # Create BookAgents instance for AI analysis
        book_agents = BookAgents(self.agent_config)
        
        # Initialize agents (required for BookAgents to work)
        book_agents.create_agents("Outline analysis", len(chapters))
        
        # Create chapter summaries for analysis
        chapter_summaries = []
        for i, chapter in enumerate(chapters[:20], 1):  # Limit to first 20 chapters for performance
            content = chapter['content']
            # Truncate very long chapters
            summary_text = content[:2000] + "..." if len(content) > 2000 else content
            chapter_summaries.append(f"Chapter {i}: {chapter.get('title', 'Untitled')}\n{summary_text}")
        
        chapters_text = "\n\n" + "="*50 + "\n\n".join(chapter_summaries)
        
        outline_prompt = f"""Analyze the following story chapters and create a structured outline:

STORY: {title}
TOTAL CHAPTERS: {len(chapters)}

CHAPTERS:
{chapters_text}

Please create a detailed outline including:

1. STORY STRUCTURE:
   - Beginning, middle, end overview
   - Major plot points and turning points
   - Climax and resolution

2. CHAPTER-BY-CHAPTER BREAKDOWN:
   - What happens in each chapter
   - How chapters connect to overall plot
   - Character development in each section

3. THEMES & PLOT THREADS:
   - Main themes explored
   - Ongoing plot threads
   - Character arcs and development

4. STORY ANALYSIS:
   - Genre and style
   - Pacing and structure
   - Key conflicts and resolutions

Format this as a comprehensive outline that shows the story's structure and would help a writer understand the narrative flow.
"""
        
        try:
            outline_analysis = book_agents.generate_content("story_planner", outline_prompt)
            return outline_analysis
        except Exception as e:
            return f"AI outline analysis failed: {e}\n\nBasic outline: {len(chapters)} chapters with {sum(len(ch['content'].split()) for ch in chapters):,} total words."