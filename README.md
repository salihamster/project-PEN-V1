# Project PEN (Personal Engagement Navigator)

**Project PEN** is a sophisticated, locally-run AI assistant designed to organize your digital life. It integrates data sources like WhatsApp, Email, and Google Drive to provide you with a context-aware, personalized, and proactive experience.

The system is powered by **Google Gemini**, and all personal data remains on your device.

This project was developed for the Google AI Hackathon and serves as a reference architecture showcasing how modern AI agents can be built at production-grade level.

---

## 📦 Available Versions

This repository contains multiple versions of Project PEN. Choose the version that best fits your needs:

| Version | Status | Description | Key Features |
|---------|--------|-------------|--------------|
| **[V1.0](./V1)** | Stable | Initial release | 18 tools, CLI interface, 4-layer memory |
| **[V1.1](./V1.1)** | Stable | Enhanced version | 29 tools, web interface, multi-model support |
| **[PEN-X1.5](./PEN-X1.5)** | Latest | Advanced version | 46 tools, calendar, file upload, real-time monitoring |

### Version Comparison

| Feature | V1.0 | V1.1 | PEN-X1.5 |
|---------|------|------|----------|
| Tools | 18 | 29 | 46 |
| Interface | CLI | CLI + Web | CLI + Web (Modular) |
| Calendar | ❌ | ❌ | ✅ |
| File Upload | ❌ | ❌ | ✅ |
| Real-time Monitoring | ❌ | ❌ | ✅ (SSE) |
| PENotes | ❌ | ❌ | ✅ |
| Frontend Modules | - | 3 files | 30+ files |
| Cross-Platform Scripts | ❌ | ❌ | ✅ |

---

## 🎯 Core Features

- **Unified Data Integration** -- Consolidates WhatsApp, Email, and Drive data.
- **Advanced 4-Layer Memory System** -- Multi-layered memory design for context and long-term information management.
- **Intelligent Tool-Calling Agent** -- Powerful automation infrastructure with specialized tools.
- **Web Interface** -- Modern web UI at localhost:8000 for easy interaction.
- **Multi-Model Support** -- Pluggable architecture supporting Gemini, OpenAI, and Anthropic models.
- **Privacy-First Architecture** -- All data processing is local; only LLM requests go to the cloud.
- **Production-Ready** -- Includes type safety, modular structure, error handling, and detailed logging.

---

## 🧠 Memory Architecture

The architecture of this memory system was originally designed in the **PENELOPE project**, and all layer concepts and rights belong to me.

PEN uses a transplanted, minimal subset of this architecture. Because of this, L3 and L5 are intentionally not included.

Below are the active layers used in PEN:

| Layer | Name | Purpose | Persistence | Speed |
|-------|------|---------|-------------|-------|
| **L1** | Active Session Memory | Current conversation context | Session | ⚡️ Instant |
| **L2** | Historical Archive | Full record of all past sessions | Permanent | 🐢 Slow |
| **L2.5** | Indexed Archive | Indexed, fast-search version of L2 | Permanent | 🏎️ Fast |
| **L4** | User Profile & Contexts | User information, projects, goals | Permanent | ⚡️ Instant |
| **L6** (Planned) | Chronological Event Log | User's life/project evolution timeline | Permanent | 💨 Moderate |

---

## 🚀 Quick Start

### 1. Choose Your Version

Navigate to the version directory you want to use:
- `V1/` - Initial stable release
- `V1.1/` - Enhanced with web interface
- `PEN-X1.5/` - Latest with advanced features

### 2. Installation

```bash
git clone <repository_url>
cd "project-pen/<version_folder>"
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and configure:

```env
GEMINI_API_KEY=your_api_key
SERVICE_ACCOUNT_FILE=service_account.json
DRIVE_FOLDER_NAME=Wpmesages
EMAIL_ENABLED=false
EMAIL_ADDRESS=
EMAIL_PASSWORD=
```

### 4. Run

**Data Sync:**
```bash
python main.py
```

**Start Agent:**
```bash
# CLI
python pen_agent.py

# Web Interface (V1.1 and PEN-X1.5)
python web_server.py
# Then open http://localhost:8000
```

---

## 📱 WhatsApp Integration (Semi-Manual)

Due to WhatsApp not providing an official API, integration proceeds in a legal, semi-manual manner.

> **Note on folder naming:**  
> The folder is specifically named **Wpmesages** (this name was misspelled in the initial design but was later adopted and kept in the system).

### Step 1 --- Create Drive Folder

Google Drive → My Drive →  
Create a folder named **Wpmesages** (must be written exactly like this).

### Step 2 --- Export Chat on Phone

- Chat → Three dots → **More** → **Export chat**
- **Without Media**
- Send to Google Drive → Upload to **Wpmesages** folder

### Step 3 --- Run Sync

```bash
python main.py
```

---

## 🛠️ Tool Architecture by Version

### V1.0 (18 tools)
Basic tool set across 6 categories: Core, WhatsApp, Email, Drive, Web, Context/Memory

### V1.1 (29 tools)
Added invoice parsing, OCR, web scraping tools

### PEN-X1.5 (46 tools)
Comprehensive tool set across 10 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| **Core** | 2 | Time, statistics |
| **WhatsApp** | 5 | List chats, get messages, participants, search, context |
| **Email** | 5 | List, get content, search, refresh |
| **Drive** | 3 | Search files, refresh, check updates |
| **Web** | 2 | Web search, fetch webpage |
| **Context/Memory** | 6 | Create, update, search, get details, link, delete |
| **Invoice** | 5 | Parse HTML, scrape URL, OCR, trusted domains |
| **Calendar** | 6 | Create, read, update, delete, chain events, get details |
| **File System** | 4 | Read, write, list, search files in workspace |
| **Media** | 3 | Process images, extract PDF text, extract DOCX text |
| **PENotes** | 4 | Create, list, search, delete notes |

---

## 📈 Performance
(v1 - v1.1)
- **12 core tools** -- 240 tests → 100% success
- **6 memory tools** -- tested separately → 100% success
- **Memory ops** -- 150 tests → 100% accuracy
- **End-to-end** -- 4 scenarios → 100% correct tool selection
- Average response time: ~25 seconds

---

## 🔮 Roadmap

### Completed (PEN-X1.5)
- [x] Calendar Integration
- [x] File Upload System
- [x] Real-time Tool Activity (SSE)
- [x] Modular Frontend Architecture

### Planned
-
---

## 📝 Version History

### PEN-X1.5 (January 2026)
- **46 tools** across 10 categories
- Calendar system with event management
- File upload and processing (images, PDFs, DOCX)
- PENotes markdown note-taking system
- Real-time tool activity monitoring (SSE)
- Modular frontend (19 JS + 11 CSS modules)
- Cross-platform scripts (Windows, macOS, Linux)
- Message undo functionality
- Usage statistics and cost tracking

### V1.1 (December 2025)
- **29 tools** (up from 18)
- Web interface at localhost:8000
- Multi-model support (Gemini, OpenAI, Anthropic)
- Sleep cycle for automated session archival
- Invoice parsing, OCR, web scraping tools
- Improved memory system
- Full English codebase

### V1.0 (November 2025)
- Initial release for Google AI Hackathon
- 4-Layer Memory System (L1, L2, L2.5, L4)
- WhatsApp, Email, Drive integration
- 18 specialized tools
- CLI interface

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## 🙏 Acknowledgments

- Google AI Hackathon for the inspiration
- Google Gemini for powering the AI capabilities
- Open source community for the tools and libraries

---

**Documentation written with Claude 4.5 Sonnet.**
