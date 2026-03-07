# Changelog

All notable changes to Project PEN are documented in this file.

---

## [1.5.0] - 2026-01-15

### Added

**Calendar System**
- Event management with three event types: fixed, windowed, and uncertain
- Six calendar tools: create, read, update, delete, chain events, get details
- Calendar data persistence in `layers/data/calendar.json`
- Smart reminders for upcoming events on session start

**File Upload & Processing**
- Drag-and-drop file upload interface
- Support for images (PNG, JPG, JPEG, GIF, WEBP, SVG)
- PDF text extraction using PyMuPDF
- DOCX text extraction using python-docx
- Image analysis using Gemini Vision API
- File metadata tracking and preview

**PENotes System**
- Markdown-based note-taking with category organization
- Four note tools: create, list, search, delete
- Notes stored in `data/user_docs/` directory
- Automatic timestamp and metadata tracking

**File System Tools**
- Four workspace tools: read, write, list, search files
- Document Manager for secure file operations
- Path traversal protection
- Artifact panel for viewing created files

**Real-time Tool Activity**
- Server-Sent Events (SSE) implementation
- Live tool execution monitoring in UI
- Tool status tracking: running, completed, error
- Event broadcasting system with thread-safe queue

**Frontend Architecture**
- Modular structure: 19 JavaScript modules, 11 CSS modules
- Separated concerns: API, state, DOM, events, utilities
- Individual modules for chat, calendar, notes, settings, history
- Responsive design with mobile support

**Cross-Platform Support**
- Windows scripts (.bat)
- macOS scripts (.command)
- Linux scripts (.sh)
- Platform-specific installation and startup scripts

**Additional Features**
- Message undo functionality
- Usage statistics and API cost tracking
- Document workspace management
- Archived session viewing
- Model selection dropdown
- Settings panel with masked API keys

### Changed

**Tool Count**
- Increased from 29 to 46 tools (+17 tools)
- Added four new tool categories: Calendar, File System, Media, PENotes

**Frontend Structure**
- Monolithic (3 files) → Modular (30+ files)
- Single CSS file → 11 modular CSS files
- Single JS file → 19 modular JS files
- Code size: 1,358 lines → 9,891 lines (+628%)

**Backend Structure**
- Added DocumentManager for workspace file operations
- Added UsageLogger for API usage tracking
- Enhanced tool executor with SSE event emission
- Code size: 12,155 lines → 16,839 lines (+38.5%)

**Default Model**
- Changed from `gemini-2.5-flash` to `gemini-3-flash-preview`

**Dependencies**
- Added: `httpx<0.28.0`, `pymupdf>=1.24.0`, `python-pptx==0.6.23`, `python-docx==1.1.0`
- Removed: `lxml==5.1.0` (Python 3.13 compatibility)

### Removed

- `sleep_trigger.bat` - Replaced with web interface sleep button
- Monolithic frontend files (replaced with modular structure)

### Fixed

- Context cleanup with TTL (Time-to-Live) system for tool outputs
- Tool output collapse mechanism to prevent context overflow
- Memory leak in conversation history
- SSE connection stability and auto-reconnect
- Path traversal security in file operations

---

## [1.1.0] - 2025-12-01

### Added
- 29 tools (up from 18)
- Invoice parsing tools: HTML parser, URL scraper, OCR
- Web interface at localhost:8000
- Multi-model support: Gemini, OpenAI, Anthropic
- Sleep cycle for automated session archival (L1 → L2 + L2.5)
- Model factory pattern for provider abstraction

### Changed
- Full English codebase (previously mixed languages)
- Improved logging system with structured logs
- Better L4 context rendering
- Enhanced duplicate detection in memory system

---

## [1.0.0] - 2025-11-01

### Added
- Initial release for Google AI Hackathon
- 4-Layer Memory System (L1, L2, L2.5, L4)
- WhatsApp integration via Google Drive sync
- Email integration via IMAP
- Google Drive integration via Service Account
- 18 specialized tools across 6 categories
- CLI interface
- Data sync pipeline
- Basic web interface

---

**Changelog written with Claude 3.5 Sonnet.**
