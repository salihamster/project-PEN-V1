# Project PEN (Personal Engagement Navigator)

**Project PEN** is a sophisticated, locally-run AI assistant designed to organize your digital life. It integrates data sources like WhatsApp, Email, and Google Drive to provide you with a context-aware, personalized, and proactive experience.

The system is powered by **Google Gemini 2.5 Flash**, and all personal data remains on your device.

This project was developed for the Google AI Hackathon and serves as a reference architecture showcasing how modern AI agents can be built at production-grade level.

---

## 🎯 Core Features

- **Unified Data Integration** -- Consolidates WhatsApp, Email, and Drive data.
- **Advanced 4-Layer Memory System** -- Multi-layered memory design for context and long-term information management.
- **Intelligent Tool-Calling Agent** -- A powerful automation infrastructure with 18 specialized tools (12 core + 6 memory tools).
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

A total of **18 tools** are available:

- **12 Core Tools** -- Data retrieval, parsing, processing, pipelines
- **6 Memory Tools** -- Memory CRUD, search, and index operations (tested separately)

---

## 🏗️ Project Structure

```
V1/
├── src/
│   ├── agent/
│   ├── agent_tools/
│   ├── layers/
│   ├── parsers/
│   ├── storage/
│   └── utils/
├── data/          # gitignored
├── logs/          # gitignored
├── experiments/
├── main.py
├── pen_agent.py
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

### Step 3 --- Run PEN

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

### Interactive agent:

```bash
python -m pen_agent
```

---

## 📈 Performance

- **12 core tools** -- 240 tests → 100% success
- **6 memory tools** -- tested separately → 100% success
- **Memory ops** -- 150 tests → 100% accuracy
- **End-to-end** -- 4 scenarios → 100% correct tool selection
- Average response time: ~25 seconds

---

## 🔮 Roadmap

- [ ] L6 Memory Layer
- [ ] Calendar Integration
- [ ] Web interface improvements
- [ ] Proactive notifications
- [ ] Statistics dashboard
- [ ] SQLite / Postgres migration

---

**This README is built with ❤️ and Google Gemini 2.5 Flash.**
