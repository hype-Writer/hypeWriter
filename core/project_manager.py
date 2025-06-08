"""
Project management utilities for hypeWriter multi-book support
"""

import os
import json
import uuid
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .pydantic_models import ProjectMetadata
from .import_utils import DocumentParser, ImportAnalyzer


class ProjectManager:
    """Manage multiple book projects in hypeWriter"""
    
    def __init__(self, base_path: str = "library"):
        self.base_path = Path(base_path)
        self.projects_file = self.base_path / "projects.json"
        self.ensure_directory_structure()
    
    def ensure_directory_structure(self):
        """Ensure the project directory structure exists"""
        self.base_path.mkdir(exist_ok=True)
        (self.base_path / "imports").mkdir(exist_ok=True)
        
        # Create projects.json if it doesn't exist
        if not self.projects_file.exists():
            self._save_projects_index({})
    
    def _load_projects_index(self) -> Dict:
        """Load the projects index from JSON"""
        try:
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_projects_index(self, projects: Dict):
        """Save the projects index to JSON"""
        with open(self.projects_file, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
    
    def list_projects(self) -> List[ProjectMetadata]:
        """List all projects"""
        projects_data = self._load_projects_index()
        projects = []
        
        for project_id, data in projects_data.items():
            try:
                project = ProjectMetadata(**data)
                projects.append(project)
            except Exception as e:
                print(f"Warning: Invalid project data for {project_id}: {e}")
        
        # Sort by last modified (newest first)
        projects.sort(key=lambda p: p.last_modified, reverse=True)
        return projects
    
    def get_project(self, project_id: str) -> Optional[ProjectMetadata]:
        """Get a specific project by ID"""
        projects_data = self._load_projects_index()
        if project_id not in projects_data:
            return None
        
        try:
            return ProjectMetadata(**projects_data[project_id])
        except Exception:
            return None
    
    def create_project(self, title: str, author: str = "", genre: str = "", description: str = "") -> ProjectMetadata:
        """Create a new project"""
        project_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        project = ProjectMetadata(
            id=project_id,
            title=title,
            author=author,
            genre=genre,
            description=description,
            created_date=now,
            last_modified=now
        )
        
        # Create project directory with sanitized title
        folder_name = self._sanitize_folder_name(title, project_id)
        project_dir = self.base_path / folder_name
        project_dir.mkdir(exist_ok=True)
        (project_dir / "chapters").mkdir(exist_ok=True)
        
        # Save project metadata
        self._save_project_metadata(project)
        
        # Update projects index
        projects_data = self._load_projects_index()
        projects_data[project_id] = project.dict()
        self._save_projects_index(projects_data)
        
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its files"""
        projects_data = self._load_projects_index()
        if project_id not in projects_data:
            return False
        
        # Remove project directory
        project_dir = self.base_path / project_id
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        # Remove from index
        del projects_data[project_id]
        self._save_projects_index(projects_data)
        
        return True
    
    def update_project(self, project: ProjectMetadata) -> bool:
        """Update an existing project"""
        projects_data = self._load_projects_index()
        if project.id not in projects_data:
            return False
        
        project.last_modified = datetime.now().isoformat()
        
        # Update index
        projects_data[project.id] = project.dict()
        self._save_projects_index(projects_data)
        
        # Save project metadata
        self._save_project_metadata(project)
        
        return True
    
    def _save_project_metadata(self, project: ProjectMetadata):
        """Save project metadata to its directory"""
        project_dir = self.get_project_path(project.id)
        metadata_file = project_dir / "metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(project.dict(), f, indent=2, ensure_ascii=False)
    
    def _sanitize_folder_name(self, title: str, project_id: str) -> str:
        """Convert title to filesystem-safe folder name"""
        # Remove/replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        sanitized = re.sub(r'\s+', '-', sanitized.strip())
        sanitized = sanitized[:50]  # Limit length
        
        # Ensure uniqueness by appending short ID
        short_id = project_id[:8]
        return f"{sanitized}-{short_id}"
    
    def get_project_path(self, project_id: str) -> Path:
        """Get the path to a project directory by finding its folder"""
        # Look for folder that contains this project_id
        for folder in self.base_path.iterdir():
            if folder.is_dir() and folder.name.endswith(f"-{project_id[:8]}"):
                return folder
        
        # Fallback to old UUID-based path if not found
        return self.base_path / project_id
    
    def import_novel(self, file_path: str, title: str = "", author: str = "", 
                    genre: str = "", auto_generate_metadata: bool = True, agent_config: Dict = None) -> ProjectMetadata:
        """Import a novel from a file and create a new project"""
        
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
            raise ValueError(f"Unsupported file format: {file_path}. Supported formats: .docx, .odt, .epub")
        
        # Extract title and author if not provided
        if not title or not author:
            # For EPUB files, try metadata extraction first
            if file_path.endswith('.epub'):
                epub_title, epub_author = parser.extract_epub_metadata(file_path)
                title = title or epub_title
                author = author or epub_author
            
            # Fallback to content-based extraction if needed
            if not title or not author:
                extracted_title, extracted_author = parser.extract_title_and_author(text, file_path)
                title = title or extracted_title
                author = author or extracted_author
        
        # Detect chapters
        chapters = parser.detect_chapters(text)
        
        # Create the project
        project = self.create_project(title, author, genre)
        project_dir = self.get_project_path(project.id)
        
        # Save chapters
        self._save_chapters_to_project(project.id, chapters)
        
        # Update project stats
        total_words = sum(len(ch['content'].split()) for ch in chapters)
        project.chapter_count = len(chapters)
        project.word_count = total_words
        
        # Generate metadata if requested
        if auto_generate_metadata:
            analyzer = ImportAnalyzer(agent_config or {})
            analysis = analyzer.analyze_for_import(chapters, title)
            
            # Save AI analysis results as structured JSON files
            from .text_to_json import parse_characters_text_to_json, parse_world_text_to_json, parse_outline_text_to_json
            import json
            
            # Save characters as JSON
            if 'suggested_characters' in analysis:
                characters_data = parse_characters_text_to_json(analysis['suggested_characters'])
                with open(project_dir / "characters.json", 'w', encoding='utf-8') as f:
                    json.dump(characters_data.dict(), f, indent=2, ensure_ascii=False)
            
            # Save world as JSON  
            if 'suggested_world' in analysis:
                world_data = parse_world_text_to_json(title, analysis['suggested_world'])
                with open(project_dir / "world.json", 'w', encoding='utf-8') as f:
                    json.dump(world_data.dict(), f, indent=2, ensure_ascii=False)
            
            # Save outline as JSON if available
            if 'suggested_outline' in analysis:
                outline_data = parse_outline_text_to_json(title, analysis['suggested_outline'])
                with open(project_dir / "outline.json", 'w', encoding='utf-8') as f:
                    json.dump(outline_data.dict(), f, indent=2, ensure_ascii=False)
            
            # Also save traditional import_analysis.txt for reference
            with open(project_dir / "import_analysis.txt", 'w', encoding='utf-8') as f:
                f.write(f"Import Analysis for: {title}\n")
                f.write(f"Author: {author}\n")
                f.write(f"Chapters: {len(chapters)}\n")
                f.write(f"Words: {total_words}\n\n")
                f.write("AI-Generated Analysis:\n")
                f.write("- characters.json: Structured character data\n")
                f.write("- world.json: Structured world-building data\n")
                if 'suggested_outline' in analysis:
                    f.write("- outline.json: Structured story outline\n")
                f.write(f"\nGenerated: {analysis.get('generated_date', 'Unknown')}\n")
        
        # Update project metadata
        self.update_project(project)
        
        return project
    
    def _save_chapters_to_project(self, project_id: str, chapters: List[Dict]):
        """Save chapters to a project"""
        project_dir = self.get_project_path(project_id)
        chapters_dir = project_dir / "chapters"
        
        # Save individual chapter files
        for chapter in chapters:
            chapter_file = chapters_dir / f"chapter_{chapter['chapter_number']}.txt"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(chapter['content'])
        
        # Save chapters.json structure
        chapters_json = []
        for chapter in chapters:
            chapters_json.append({
                'chapter_number': chapter['chapter_number'],
                'title': chapter['title'],
                'prompt': f"Content for {chapter['title']}"  # Basic prompt
            })
        
        with open(project_dir / "chapters.json", 'w', encoding='utf-8') as f:
            json.dump(chapters_json, f, indent=2, ensure_ascii=False)