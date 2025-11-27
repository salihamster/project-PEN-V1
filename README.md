# Project PEN (Personal Engagement Navigator)

**Project PEN** is a sophisticated, locally-run AI assistant designed to bring order and intelligence to your digital life. It integrates seamlessly with your personal data sources (WhatsApp, Email, Google Drive) to provide a proactive, context-aware, and deeply personalized experience. Powered by Google's **Gemini 2.5 Flash**, PEN understands your past, organizes your present, and helps you plan your future—all while ensuring your data remains private and under your control.

This project was developed for the Google AI Hackathon and demonstrates a robust, production-ready architecture for building next-generation AI agents.

## 🎯 Core Features

- **Unified Data Integration**: Connects to WhatsApp, Email, and Google Drive for a 360° view of your digital world.
- **Advanced 4-Layer Memory System**: Provides state-of-the-art context retention, user profiling, and historical recall.
- **Intelligent Tool-Calling Agent**: Leverages 18+ specialized tools for data retrieval, analysis, and memory management.
- **Privacy-First Architecture**: All data is processed and stored locally. Nothing is sent to the cloud except for LLM inference.
- **Production-Ready & Type-Safe**: Built with a modular, type-safe architecture, comprehensive error handling, and structured logging.
- **Cost-Efficient**: Optimized to run on Google's economical Gemini 2.5 Flash model, making it accessible for everyday use.

## 🏗️ System Architecture

Project PEN is built on a set of core principles that ensure quality, maintainability, and scalability.

### 🧠 4-Layer Memory System

The heart of PEN is its multi-layered memory architecture, which enables it to understand context, remember user preferences, and recall historical information with high accuracy.

| Layer | Name | Purpose | Persistence | Access Speed |
|-------|------|---------|-------------|--------------|
| **L1** | **Active Session Memory** | Holds the context of the current conversation (messages, tool calls). | Session | ⚡️ Instant |
| **L2** | **Historical Archive** | Permanently stores all past sessions and interactions in full detail. | Permanent | 🐢 Slow (Full Scan) |
| **L2.5**| **Indexed Archive** | A keyword-indexed summary of L2 for fast, targeted historical searches. | Permanent | 🏎️ Fast (Indexed) |
| **L4** | **User Profile & Contexts**| Stores structured information about the user, their projects, goals, and recurring activities. | Permanent | ⚡️ Instant |
| **L6** | *(Planned)* **Chronological Event Log** | Tracks the evolution of L4 contexts over time to understand project progress and life events. | Permanent | 💨 Moderate |

### 🛠️ Project Structure

The codebase is organized with a clear separation of concerns, making it easy to maintain and extend.

```
V1/
├── src/
│   ├── agent/                # Core agent logic, tool definitions, and executor
│   ├── agent_tools/          # Implementations of all agent tools
│   ├── layers/               # L1, L2, L2.5, L4 memory layer implementations
│   ├── parsers/              # Data parsers for WhatsApp, Email, Drive
│   ├── storage/              # Low-level data persistence
│   └── utils/                # Shared utilities (logger, etc.)
├── data/                     # (Gitignored) Local data storage (JSON files)
├── logs/                     # (Gitignored) Application logs
├── experiments/              # Test runners and performance metrics
├── main.py                   # Main data processing pipeline
├── pen_agent.py              # Interactive CLI for the agent
└── .env                      # (Gitignored) Environment variables
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key (with Tier 1 access for hackathon participants)
- Google Cloud Project with billing enabled (or free credits)

### 1. Installation

```bash
# Clone the repository
git clone <repository_url>
cd "project PEN/V1"

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Drive API Setup (for Automatic Data Sync)

This is required to automatically download your WhatsApp chat exports from a dedicated Google Drive folder.

1.  **Enable Google Drive API**: Go to the [Google Cloud Console](https://console.cloud.google.com/) and enable the **Google Drive API** for your project.
2.  **Create a Service Account**:
    -   In the Cloud Console, navigate to **IAM & Admin > Service Accounts**.
    -   Click **+ CREATE SERVICE ACCOUNT**, give it a name (e.g., `pen-drive-sync`), and click **CREATE AND CONTINUE**.
    -   Grant it the **Viewer** role for basic read-only access to Drive files, then click **DONE**.
3.  **Generate a JSON Key**:
    -   Find your newly created service account in the list, click the three-dot menu under **Actions**, and select **Manage keys**.
    -   Click **ADD KEY > Create new key** and select **JSON** as the key type. A JSON file will be downloaded automatically.
    -   Save this file in the project root. rename it: "service_account.json".
4.  **Share Your Drive Folder**:
    -   Open the downloaded JSON file and copy the `client_email` address (e.g., `pen-drive-sync@your-project-id.iam.gserviceaccount.com`).
    -   In Google Drive, create a folder (Wpmesages - recomendet) and upload your WhatsApp `.txt` chat export files into it.
    -   Share this folder with the `client_email` address you copied, granting it **Viewer** access.

### 3. Configure Your Environment (`.env`)

Create a `.env` file from the example and fill in your credentials.

```bash
cp .env.example .env
```

Update the `.env` file with your specific keys and paths:

```env
# Required for agent functionality
GEMINI_API_KEY=your_gemini_api_key

# --- Automatic Data Sync (Required for main.py) ---
# Full path to your service account JSON file
SERVICE_ACCOUNT_FILE=C:/Users/Administrator/Desktop/project PEN/V1/project-pen-478215-956ca5da00a0.json
# The name of the folder you shared in Google Drive
DRIVE_FOLDER_NAME=WhatsAppExports

# --- Email Integration (Optional) ---
EMAIL_ENABLED=true
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 4. Run the Data Pipeline

Once the setup is complete, run the main data pipeline to sync and process your data. This script uses the settings in your `.env` file to connect to Google Drive and Gmail.

```bash
python main.py
```

This will:
-   ✅ Connect to Google Drive using your service account.
-   ✅ Download new WhatsApp chat files from the specified folder.
-   ✅ Parse all messages into a structured, agent-readable format.
-   ✅ Fetch and parse emails (if configured).
-   ✅ Generate initial statistics for the agent.

### 5. Run the Interactive Agent

After your data is processed, you can start the conversational AI assistant:

```bash
python -m pen_agent
```

## 📈 Performance & Stability

Project PEN has undergone rigorous testing to ensure it is stable, accurate, and performant.

-   **Tool Stability:** 100% success rate across 240 test runs on 12 core tools.
-   **Memory Layer Accuracy:** 100% accuracy rate across 150 CRUD and search operations on all memory layers.
-   **End-to-End Scenarios:** 100% success rate on 4 real-world agent scenarios, demonstrating reliable tool selection and memory utilization.
-   **Response Time:** Average response time for complex queries is ~25 seconds, which includes LLM processing and tool execution.

For detailed metrics, see [docs/metrikler.md](docs/metrikler.md).

## 🔮 Future Enhancements

Project PEN is a strong foundation with a clear roadmap for future development:

-   **[ ] L6 Memory Layer**: Implement the chronological event log to track project evolution.
-   **[ ] Calendar Integration**: Add tools to read and write Google Calendar events.
-   **[ ] Web Interface**: Create a simple web UI for a more user-friendly experience. (there is but.. not that good 😊 - web_server.py )
-   **[ ] Proactive Notifications**: Enable the agent to initiate conversations based on events (e.g., an upcoming meeting).
-   **[ ] Advanced Analytics**: Build a dashboard to visualize user activity, communication patterns, and project progress.
-   **[ ] Database Migration**: Move from JSON files to a robust database like SQLite or PostgreSQL for better concurrency and scalability.

## 🐛 Troubleshooting

1.  **`datetime.UTC` Attribute Error**: This project requires Python 3.11+. The test runner includes a compatibility patch, but using the correct Python version is recommended.
2.  **API Key Not Found**: Ensure `GEMINI_API_KEY` is correctly set in your `.env` file located in the project root.
3.  **Service Account File Not Found**: Make sure the `SERVICE_ACCOUNT_FILE` path in your `.env` file is correct and absolute.
4.  **Email Connection Failed**: Use an app-specific password, not your regular account password. Ensure IMAP is enabled in your Gmail settings.
5.  **Data Parsing Issues**: Ensure WhatsApp chats are exported as `.txt` files "Without media" and are UTF-8 encoded.

For detailed error information, set `DEBUG=true` in your `.env` file and check the log files in the `logs/` directory.

---

**Built with ❤️ and Google Gemini 2.5 Flash**
