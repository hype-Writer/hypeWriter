# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Development Guidelines

### CRITICAL: UI WORK LOCATION
- **ALL UI WORK MUST BE DONE IN `/frontend` DIRECTORY ONLY**
- **NEVER edit `static/app.css` or `static/app.js` directly** - these are auto-generated build artifacts
- **ALWAYS work in `/frontend/src/` for all UI changes**
- Build process automatically copies frontend assets to static/ directory
- Editing static/ files directly will be overwritten on next build

### NO MOCK DATA
- **NEVER use mock/fake/hardcoded data** in components
- **ALWAYS connect to real backend APIs** when displaying data
- **NO fake placeholders or sample data** - this makes it impossible to see what's actually working
- If an API endpoint doesn't exist yet, create it or ask about it first
- All data must come from the FastAPI backend to validate real functionality
- Mock data hides broken integrations and incomplete features

## Development Commands

### Backend Development
- **Start development server**: `uvicorn hypewriter:app --reload` (serves on http://localhost:8000)
- **Code quality**: `black .`, `flake8 .`, `mypy .` (linting and type checking)
- **Tests**: `pytest` (testing framework available)

### Frontend Development
- **Development server**: `cd frontend && npm run dev` (for frontend-only development)
- **Build for production**: `cd frontend && npm run build` (copies assets to backend static/templates)
- **Code quality**: `cd frontend && npm run lint` (ESLint + Prettier)
- **Type checking**: `cd frontend && npm run check`

### Environment Setup
- Backend: `pip install -r requirements.txt`
- Frontend: `cd frontend && npm install`
- Required: `.env` file with `GOOGLE_API_KEY`, `GEMINI_MODEL_NAME`, and `APP_SECRET_KEY`
- TTS Feature: Requires Kokoro-FastAPI server running on `localhost:8880`

## Architecture Overview

**hypeWriter** is an AI-assisted novel writing application with hybrid architecture:

### Backend (FastAPI/Python)
- **Main server**: `hypewriter.py` - FastAPI app with Jinja2 templating
- **Core modules**: `core/` directory contains agents, config, prompts, and data models
- **AI Integration**: Google Gemini via `google-generativeai`
- **Storage**: File-based in `library/` directory with project-specific folders (world.txt, characters.txt, outline.json, chapters/)
- **Sessions**: Server-side session management with starlette-session

### Frontend (Svelte 5/TypeScript)
- **Framework**: Modern Svelte 5 using Runes API (`$state`, `$effect`, `$derived`)
- **Build**: Vite bundler with TypeScript, assets copied to backend static/templates
- **Architecture**: SPA embedded in Jinja2 template structure
- **Components**: Reusable `Chat.svelte` component for AI interactions

### Key Patterns
- **Agent-based AI**: Specialized agents for different writing tasks (world building, character creation, etc.)
- **Streaming responses**: Real-time AI content generation with Server-Sent Events
- **Conversational interface**: Chat-based interactions throughout the application
- **File persistence**: All generated content stored locally for easy access
- **Hybrid deployment**: Single FastAPI server serves both SPA and API

### Development Notes
- Frontend development requires building (`npm run build`) to integrate with backend
- All Svelte components use modern Runes syntax, not legacy reactive statements
- AI responses are streamed for better user experience
- Session state maintains conversation context across interactions
- Generated content is immediately saved to local files for persistence

### New Features Added

**FastAPI MCP Integration**
- MCP server automatically mounted at application startup
- Enables Claude Code to interact with the FastAPI backend directly
- Added `fastapi_mcp>=0.1.0` dependency

**Text-to-Speech (TTS) Integration**
- Kokoro-FastAPI integration for high-quality audiobook generation
- API endpoints: `/api/tts/voices`, `/api/tts/generate`, `/api/tts/chapter/{id}`, `/api/tts/status`
- Frontend TTS controls in chapter view with voice selection and audio player
- Supports full chapter conversion to MP3/WAV/FLAC formats
- No length limits (can process entire chapters)
- 60+ voices available (defaults to Emma - British Female)
- Requires Kokoro-FastAPI server running on `localhost:8880`

**TTS Usage**
- Start Kokoro-FastAPI: `cd ~/dev/orbat/kokoro-fastapi && ./start-cpu.sh`
- TTS controls appear automatically in chapter view when server is available
- Generated audio files saved to `library/{project_id}/chapters/chapter_X.mp3`

### Project Structure
- `hypewriter.py`: Main FastAPI application with MCP and TTS endpoints
- `core/`: Backend logic (agents, config, prompts, models)
- `frontend/`: Svelte 5 SPA source code with TTS and MDR integration
- `static/` + `templates/`: Built frontend assets served by FastAPI
- `library/`: Project-based novel content storage with individual project directories (includes audio files)
- `library/projects.json`: Project registry and metadata
- `zclaudestuff/`: Contains TTS integration docs and future feature roadmap

## 🎯 CURRENT PROJECT STATUS

### ✅ COMPLETED FEATURES
- **Multi-Project System**: Full support for creating, importing, and managing multiple novel projects
- **MDR Background Integration**: Complete Severance-themed animation system integrated as interactive background
- **Real-Time Dashboard**: Progress tracking based on actual file content analysis with working navigation
- **Novel Import System**: Support for .docx, .odt, .epub, .mobi files with automatic chapter detection
- **TTS Integration**: High-quality audiobook generation with 60+ voice options via Kokoro-FastAPI
- **Svelte 5 Migration**: Modern component architecture using Runes API with proper routing
- **Production Build System**: Automated frontend build process integrated with FastAPI backend
- **Core Functionality Restored**: All hypewriter pages (world, characters, outline, chapters) now visible and accessible

### 🔧 ARCHITECTURE HIGHLIGHTS
- **Hybrid UI/UX**: Traditional dashboard functionality seamlessly integrated with animated background
- **Smart Interactions**: Selective pointer-events allow both dashboard functionality and background interaction
- **Real Data Loading**: No mock data - all components connect to actual FastAPI endpoints
- **Project Isolation**: Each project stored in separate directories with complete data separation
- **Functional Routing**: Client-side navigation between dashboard and writing sections working properly

### 🚧 NEXT DEVELOPMENT PRIORITIES

#### **High Priority - UI/Design Updates**
1. **Update Page Layouts**: Convert characters.svelte, outline.svelte, chapters.svelte to new Severance theme
2. **Modernize Components**: Replace Bootstrap classes with new design system components
3. **Responsive Design**: Ensure all pages work properly on mobile devices
4. **Clean CSS**: Remove unused selectors and streamline stylesheets

#### **Medium Priority - Core Functionality**
1. **AI Workflow Testing**: Verify end-to-end AI functionality (world → characters → outline → chapters)
2. **Performance Optimization**: Improve loading times and reduce bundle size
3. **Error Handling**: Better error states and user feedback throughout the application
4. **Accessibility**: Fix accessibility warnings from build process

#### **Lower Priority - Polish**
1. **Code Efficiency**: Refactor and optimize component logic
2. **Type Safety**: Improve TypeScript coverage and fix type warnings
3. **Testing**: Add unit tests for critical functionality
4. **Documentation**: Update inline code documentation

## Key Integrations

### ✅ MDR Background Animation System (COMPLETED)
- **Severance-themed UI**: Full integration of interactive data cell and bin animations as background layer
- **Seamless Interaction**: Dashboard functionality works alongside background number interaction
- **Complete Component Migration**: All MDR components (Header, DataField, DataCell, Bins, etc.) successfully integrated
- **Hybrid Experience**: Users can work on writing projects while MDR animations run subtly in background
- **Smart Pointer Events**: Selective interactivity allows both dashboard clicks and background number selection
- **Path Aliases**: Vite configured with `$lib` aliases for clean imports
- **Theme Integration**: MDR color variables (WO, FC, DR, MA) fully integrated into design system
- **Production Ready**: Built and deployed with ~125KB bundle size

## Key Features
1. **Smart Project Management**: Create, import, and manage multiple novel projects with real progress tracking
2. **Real Data Dashboard**: Progress bars and completion indicators based on actual file content analysis
3. **Novel Import System**: Import from `.docx`, `.odt`, `.epub`, `.mobi` files with automatic chapter detection
4. **Multi-format Export**: Export projects to various formats
5. **TTS Integration**: Convert chapters to high-quality audio with 60+ voice options
6. **Seamless Navigation**: Client-side routing between world building, character creation, outlining, and chapter writing
7. **Content Validation**: Intelligent file checking with fallback mechanisms for different file formats

## Theme Colors (Severance TV Show Inspired)
```css
--color-cyan-bright: #00d4ff;      /* Primary cyan accent */
--color-dark-primary: #1a2332;     /* Primary dark background */
--color-dark-base: #141b26;        /* Base dark background */
--color-dark-secondary: #2a3441;   /* Secondary dark surfaces */
```

## Important Notes
- **UI Development**: ALL frontend work must be done in `/frontend/src/` - NEVER edit `static/app.css` or `static/app.js`
- **Real Data Only**: NO mock data allowed - all components must connect to real FastAPI endpoints
- **Current State**: Core functionality restored but UI design needs updating for consistency
- Frontend is fully Svelte 5 compliant with modern Runes syntax (`$state`, `$derived`, `$props`)
- Production build requires `npm run build` to integrate with FastAPI backend
- Dashboard provides real-time project progress based on actual file content analysis
- Project uses `library/` directory structure with project-specific folders
- All generated content is organized by project ID in separate directories
- Progress tracking validates actual content length and structure, not just file existence

## 📋 DEVELOPMENT WORKFLOW

### **For UI/Design Work:**
1. Work in `/frontend/src/` directory only
2. Use existing Severance theme components (Card, Button) from `/frontend/src/lib/components/ui/`
3. Follow established color variables and spacing system in `/frontend/src/lib/styles/theme.css`
4. Build with `npm run build` to integrate changes
5. Test both dashboard functionality and background MDR interaction

### **For Core Functionality:**
1. Backend AI agents and prompts are in `/core/` directory
2. API endpoints are in `hypewriter.py`
3. Test streaming responses and file persistence
4. Verify multi-project isolation and session management

## Dashboard Data Loading Logic
- **World Progress**: Checks `world.json` or `world.txt` for content >50 characters
- **Characters Progress**: Validates `characters.json` or `characters.txt` for character data or substantial content
- **Outline Progress**: Examines `outline.json` or `outline.txt` for outline structure or content >50 characters
- **Chapter Progress**: Counts actual chapters from `chapters.json` or individual chapter files in chapters directory
- **Fallback Handling**: Gracefully handles missing files, parsing errors, and different file formats