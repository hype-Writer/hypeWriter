# HypeWriter Multi-Book & Import Enhancement Plan

## 🎯 Project Goals

1. **Multi-Book Support**: Enable users to work on multiple book projects simultaneously
2. **Import Existing Novels**: Allow import of pre-written stories with AI-powered metadata generation
3. **AI Backfilling**: Automatically extract characters, world-building, and outlines from existing content
4. **Improved UI/UX**: Modern, intuitive interface for project management

## 📋 Implementation Phases

### Phase 1: Multi-Book Backend Infrastructure ⏳
**Status**: Planning  
**Priority**: High  
**Estimated**: 1-2 days

#### 1.1 Data Structure Redesign
- [x] **NEW**: Project-based directory structure
  ```
  book_output/
  ├── projects.json                    # Project index
  ├── [project-id]/                   # Individual projects
  │   ├── metadata.json
  │   ├── world.txt
  │   ├── characters.txt
  │   ├── outline.txt
  │   ├── chapters.json
  │   └── chapters/
  └── imports/                        # Import staging
  ```

#### 1.2 New Pydantic Models
- [x] `ProjectMetadata` model (id, title, author, genre, dates)
- [x] `ImportNovelRequest` model (title, author, chapter_files, options)
- [x] `CreateProjectRequest` model (title, author, genre, description)
- [ ] `BackfillRequest` model (components to generate)

#### 1.3 Project Management API Endpoints
- [ ] `GET /api/projects` - List all projects
- [ ] `POST /api/projects` - Create new project
- [ ] `DELETE /api/projects/{id}` - Delete project
- [ ] `PUT /api/projects/{id}` - Update project metadata
- [ ] `POST /api/projects/{id}/activate` - Switch active project
- [ ] `GET /api/projects/{id}/export` - Export project as ZIP

#### 1.4 Session Management Updates
- [ ] Add `current_project_id` to session
- [ ] Update `load_context()` to use project-specific paths
- [ ] Modify all file operations to be project-aware

### Phase 2: Import & AI Backfilling System ⏳
**Status**: Planning  
**Priority**: High  
**Estimated**: 2-3 days

#### 2.1 Chapter Import & Parsing
- [x] **NEW**: Chapter detection algorithms
  - [x] Support multiple formats (TXT, DOCX, ODT, EPUB, MD)
  - [x] Auto-detect chapter breaks (regex patterns)
  - [x] Text cleaning and normalization
  - [x] Chapter numbering/titling

#### 2.2 AI Analysis Engine
- [ ] **NEW**: Character extraction from existing text
  ```python
  async def extract_characters_from_chapters(text: str) -> str:
      # AI prompt to identify and profile all characters
      # Returns structured character document
  ```
- [ ] **NEW**: World-building extraction
  ```python
  async def extract_world_from_chapters(text: str) -> str:
      # AI prompt to extract setting, rules, environment
      # Returns comprehensive world document
  ```
- [ ] **NEW**: Outline generation from content
  ```python
  async def generate_outline_from_chapters(text: str) -> str:
      # AI prompt to create chapter-by-chapter outline
      # Returns structured outline with OUTLINE: format
  ```

#### 2.3 Import API Endpoints
- [ ] `POST /api/import/analyze` - Analyze uploaded text (preview)
- [ ] `POST /api/import/novel` - Complete import with backfilling
- [ ] `POST /api/projects/{id}/backfill` - Regenerate metadata from chapters
- [ ] `GET /api/import/status/{task_id}` - Check import progress

#### 2.4 Background Processing
- [ ] **NEW**: Async task management for long-running imports
- [ ] Progress tracking and status updates
- [ ] Error handling and recovery

### Phase 3: Enhanced Frontend UI ⏳
**Status**: Planning  
**Priority**: Medium  
**Estimated**: 2-3 days

#### 3.1 Project Dashboard
- [ ] **NEW**: Projects overview page
  - [ ] Grid/list view of all projects
  - [ ] Project cards with metadata and progress
  - [ ] Search and filter functionality
  - [ ] Quick actions (open, delete, duplicate)

#### 3.2 Project Creation Wizard
- [ ] **NEW**: Create new project flow
  - [ ] Project metadata form
  - [ ] Template selection (blank, import existing)
  - [ ] Initial setup options

#### 3.3 Import Wizard
- [ ] **NEW**: Multi-step import interface
  - [ ] File upload with drag-and-drop
  - [ ] Chapter detection preview
  - [ ] AI analysis progress indicators
  - [ ] Review/edit generated metadata
  - [ ] Final confirmation and save

#### 3.4 Navigation & Project Switching
- [ ] **UPDATE**: Header with project selector dropdown
- [ ] **UPDATE**: Breadcrumb navigation
- [ ] **UPDATE**: Project settings page
- [ ] **NEW**: Export/backup functionality

#### 3.5 UI/UX Improvements
- [ ] **UPDATE**: Modern CSS framework (Tailwind CSS?)
- [ ] **UPDATE**: Consistent component design system
- [ ] **UPDATE**: Responsive design for mobile
- [ ] **UPDATE**: Loading states and error handling
- [ ] **NEW**: Dark mode support

### Phase 4: Testing & Polish ⏳
**Status**: Planning  
**Priority**: Medium  
**Estimated**: 1-2 days

#### 4.1 Import Testing
- [ ] **TEST**: Import various novel formats
- [ ] **TEST**: AI-generated metadata quality
- [ ] **TEST**: Large file handling
- [ ] **TEST**: Error scenarios and edge cases

#### 4.2 Multi-Project Testing
- [ ] **TEST**: Project switching functionality
- [ ] **TEST**: Session isolation between projects
- [ ] **TEST**: File organization and cleanup

#### 4.3 Performance Optimization
- [ ] **OPTIMIZE**: Large project loading times
- [ ] **OPTIMIZE**: AI analysis performance
- [ ] **OPTIMIZE**: File I/O operations

## 🧪 Testing Strategy

### Test Materials Available ✅
- [x] **Short Story**: 5,000 words, DOCX format
  - Perfect for initial development and rapid iteration
  - Small enough for quick AI processing tests
  - Should contain characters and setting elements
  
- [x] **Full Novel**: 65-85,000 words, DOCX/MOBI/EPUB formats
  - Real-world stress testing for large content
  - Multiple formats to test different parsers
  - Comprehensive AI backfilling validation

### Test Cases
- [ ] **Import Tests**:
  - Single file with multiple chapters
  - Multiple files (one per chapter)
  - Different chapter naming conventions
  - Various text formats and encodings
  
- [ ] **AI Backfill Tests**:
  - Character extraction accuracy
  - World-building completeness
  - Outline structure correctness
  - Handling of dialogue vs narrative

- [ ] **Multi-Project Tests**:
  - Creating multiple projects
  - Switching between projects
  - Project isolation verification
  - Concurrent editing scenarios

## 📊 Success Metrics

### Functionality
- [ ] Can import existing novel in < 2 minutes
- [ ] AI generates 80%+ accurate character profiles
- [ ] AI extracts comprehensive world-building details
- [ ] Can manage 10+ projects simultaneously
- [ ] Project switching is instantaneous

### User Experience
- [ ] Import wizard is intuitive for non-technical users
- [ ] UI is responsive and modern
- [ ] All actions have clear feedback/progress indicators
- [ ] Error messages are helpful and actionable

### Technical
- [ ] All existing functionality continues to work
- [ ] FastAPI MCP integration remains functional
- [ ] TTS functionality works with multi-project setup
- [ ] File organization is logical and maintainable

## 🔧 Technical Considerations

### Backward Compatibility
- [ ] **MIGRATION**: Automatic migration of existing single-project data
- [ ] **FALLBACK**: Graceful handling of old file structure
- [ ] **VALIDATION**: Ensure existing workflows continue working

### Performance
- [ ] **LAZY LOADING**: Only load active project data
- [ ] **CACHING**: Cache frequently accessed project metadata
- [ ] **STREAMING**: Stream large file imports

### Security
- [ ] **VALIDATION**: Sanitize uploaded file content
- [ ] **LIMITS**: File size and project count restrictions
- [ ] **ISOLATION**: Ensure project data isolation

## 📅 Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Backend | 1-2 days | - |
| Phase 2: Import/AI | 2-3 days | Phase 1 |
| Phase 3: Frontend | 2-3 days | Phase 1, 2 |
| Phase 4: Testing | 1-2 days | Phase 1, 2, 3 |
| **Total** | **6-10 days** | |

## 📝 Notes

- Maintain full backward compatibility with existing projects
- Use existing AI agent infrastructure for metadata generation
- Keep TTS integration functional throughout refactoring
- Preserve FastAPI MCP integration
- Consider progressive enhancement approach for UI updates

---

**Last Updated**: 2025-06-07  
**Status**: Planning Phase  
**Next Action**: Find example novel for testing import functionality