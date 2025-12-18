# Project PEN (Personal Engagement Navigator)

**Project PEN** is a sophisticated, locally-run AI assistant designed to organize your digital life. It integrates data sources like WhatsApp, Email, and Google Drive to provide you with a context-aware, personalized, and proactive experience.

The system is powered by **Google Gemini 2.5 Flash**, and all personal data remains on your device.

This project was developed for the Google AI Hackathon and serves as a reference architecture showcasing how modern AI agents can be built at production-grade level.

---

## 🎯 Core Features

- **Unified Data Integration** -- Consolidates WhatsApp, Email, and Drive data.
- **Advanced 4-Layer Memory System** -- Multi-layered memory design for context and long-term information management.
- **Intelligent Tool-Calling Agent** -- A powerful automation infrastructure with **29 specialized tools**.
- **Web Interface** -- Modern web UI at localhost:8000 for easy interaction.
- **Multi-Model Support** -- Pluggable architecture supporting Gemini, OpenAI, and Anthropic models.
- **Privacy-First Architecture** -- All data processing is local; only LLM requests go to the cloud.
- **Production-Ready** -- Includes type safety, modular structure, error handling, and detailed logging.
- **Cost-Efficient** -- Optimized for Gemini 2.5 Flash.

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

A total of **29 tools** are available across 7 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| **Core** | 2 | Time, statistics |
| **WhatsApp** | 5 | List chats, get messages, participants, search, context |
| **Email** | 5 | List, get content, search, refresh |
| **Drive** | 3 | Search files, refresh, check updates |
| **Web** | 2 | Web search, fetch webpage |
| **Context/Memory** | 6 | Create, update, search, get details, link, delete |
| **Invoice** | 5 | Parse HTML, scrape URL, OCR, trusted domains |

---

## 🏗️ Project Structure

```
project-pen/
├── src/
│   ├── agent/           # Agent core, tool executor, definitions
│   ├── agent_tools/     # Tool implementations (29 tools)
│   ├── models/          # Multi-model support (Gemini, OpenAI, Anthropic)
│   ├── memory/          # L4 memory system
│   ├── parsers/         # WhatsApp, Email, Drive parsers
│   ├── storage/         # Data management
│   └── utils/           # Logging utilities
├── layers/              # Memory layer implementations (L1, L2, L2.5, L4)
├── web/                 # Web interface assets
├── data/                # gitignored
├── logs/                # gitignored
├── main.py              # Data sync pipeline
├── pen_agent.py         # CLI interface
├── web_server.py        # Web interface (localhost:8000)
└── .env
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

- [ ] L6 Memory Layer (Chronological Event Log)
- [ ] Calendar Integration
- [ ] Streaming responses (SSE/WebSocket)
- [ ] Proactive notifications
- [ ] Statistics dashboard
- [ ] SQLite / Postgres migration

---

## 📝 Changelog

### v1.1 (December 2025)
- **29 tools** (up from 18) - Added invoice parsing, OCR, web scraping
- **Web Interface** - New localhost:8000 web UI
- **Multi-Model Support** - Pluggable architecture for Gemini, OpenAI, Anthropic
- **Sleep Cycle** - Automated session archival (L1 → L2 + L2.5)
- **Improved Memory** - Better L4 context rendering and duplicate detection
- **Code Quality** - Full English codebase, improved logging

### v1.0 (November 2025)
- Initial release for Google AI Hackathon
- 4-Layer Memory System (L1, L2, L2.5, L4)
- WhatsApp, Email, Drive integration
- 18 specialized tools
- CLI interface

---

**This README is built with ❤️ and Google Gemini 2.5 Flash.**
