# Project PEN (Personal Engagement Navigator)

**Project PEN** is a sophisticated, locally-run AI assistant designed to organize your digital life. It integrates data sources like WhatsApp, Email, and Google Drive to provide you with a context-aware, personalized, and proactive experience.

The system is powered by **Google Gemini 2.5 Flash**, and all personal data remains on your device.

This project was developed for the Google AI Hackathon and serves as a reference architecture showcasing how modern AI agents can be built at production-grade level.

---

## 🎯 Core Features

- **Unified Data Integration** -- Consolidates WhatsApp, Email, and Drive data.
- **Advanced 4-Layer Memory System** -- Multi-layered memory design for context and long-term information management.
- **46 Specialized Tools** -- Comprehensive automation infrastructure across 10 categories.
- **Calendar System** -- Event management with fixed, windowed, and uncertain event types.
- **File Upload & Processing** -- Support for images, PDFs, and DOCX files with automatic analysis.
- **PENotes** -- Markdown-based note-taking system with category organization.
- **Real-time Tool Activity** -- Server-Sent Events (SSE) for live tool execution monitoring.
- **Modular Web Interface** -- Modern UI with 19 JavaScript and 11 CSS modules.
- **Multi-Model Support** -- Pluggable architecture supporting Gemini, OpenAI, and Anthropic models.
- **Privacy-First Architecture** -- All data processing is local; only LLM requests go to the cloud.
- **Cross-Platform** -- Windows, macOS, and Linux support with dedicated scripts.

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

## 🛠️ Tool Architecture

A total of **46 tools** are available across 10 categories:

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

## 🏗️ Project Structure

```
project-pen/
├── src/
│   ├── agent/           # Agent core, tool executor, definitions
│   ├── agent_tools/     # Tool implementations (46 tools)
│   ├── models/          # Multi-model support (Gemini, OpenAI, Anthropic)
│   ├── parsers/         # WhatsApp, Email, Drive parsers
│   ├── storage/         # Data management, document manager
│   └── utils/           # Logging, usage tracking
├── layers/              # Memory layer implementations (L1, L2, L2.5, L4, Calendar)
├── web/                 # Web interface (19 JS + 11 CSS modules)
│   ├── css/             # Modular stylesheets
│   ├── js/              # Modular JavaScript
│   └── index.html       # Main interface
├── data/                # User data (gitignored)
├── logs/                # Application logs (gitignored)
├── main.py              # Data sync pipeline
├── web_server.py        # Web server (localhost:8000)
└── .env.example         # Environment template
```

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone <repository_url>
cd "project PEN/V1"

pip install -r requirements.txt
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

### Step 3 --- Run main.py

```bash
python main.py
```

---

## ☁️ Google Drive API Setup

```
SERVICE_ACCOUNT_FILE=service_account.json
DRIVE_FOLDER_NAME=Wpmesages
```

---

## ⚙️ Configure `.env`

```env
GEMINI_API_KEY=your_api_key

SERVICE_ACCOUNT_FILE=service_account.json
DRIVE_FOLDER_NAME=Wpmesages

EMAIL_ENABLED=false
EMAIL_ADDRESS=
EMAIL_PASSWORD=
```

---

## ▶️ Run Pipelines

### Sync pipeline:

```bash
python main.py
```

### Start PENNY
(as CLI)
```bash
python pen_agent.py
```

(as localhost = http://localhost:8000/)
```bash
python web_server.py
```

## 📈 Performance

- **12 core tools** -- 240 tests → 100% success
- **6 memory tools** -- tested separately → 100% success
- **Memory ops** -- 150 tests → 100% accuracy
- **End-to-end** -- 4 scenarios → 100% correct tool selection
- Average response time: ~25 seconds

---

## 🔮 Roadmap

- [x] Calendar Integration
- [x] File Upload System
- [x] Real-time Tool Activity (SSE)
- [x] Modular Frontend Architecture
- [ ] L6 Memory Layer (Chronological Event Log)
- [ ] Proactive Notifications
- [ ] WebSocket Support
- [ ] SQLite / Postgres Migration
- [ ] Mobile Application

---

---

**Documentation written with Claude 4.5 Sonnet.**
