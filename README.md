# ARIA — Voice-Based AI Agent with Memory & Tools

> **A**daptive **R**ecall & **I**ntelligence **A**ssistant — a voice-enabled AI agent that manages your To-Do list and remembers important personal information, powered by Google Gemini 2.5 Flash.

---

## Features

- 🎤 **Voice Interface** — Push-to-talk speech recognition (Web Speech API) with text-to-speech responses
- ✅ **To-Do Management** — Add, update, delete, and list tasks with priority levels and due dates
- 🧠 **Memory System** — Stores and recalls important user information across sessions
- ⚡ **Gemini Function Calling** — Agent autonomously decides when to use tools vs. respond conversationally
- 💬 **Multi-turn Sessions** — Full conversation history maintained per session
- 🎨 **Rich UI** — Dark glassmorphism theme with animated waveform, three-panel layout

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Model | Google Gemini 2.5 Flash (automatic function calling) |
| Backend | Python · FastAPI · Uvicorn |
| Database | SQLite (todos, memories, conversation_history) |
| Voice I/O | Web Speech API (browser-native STT + TTS) |
| Frontend | Vanilla HTML / CSS / JavaScript |

---

## Project Structure

```
voice/
├── backend/
│   ├── __init__.py
│   ├── agent.py        # Gemini agent, system prompt, chat sessions
│   ├── database.py     # SQLite schema initialisation
│   ├── main.py         # FastAPI app & REST endpoints
│   └── tools.py        # 6 tool functions for Gemini function calling
├── frontend/
│   ├── index.html      # Three-panel layout
│   ├── style.css       # Glassmorphism dark theme
│   └── app.js          # Voice manager, API client, UI rendering
├── .env                # API key (not committed)
├── .gitignore
├── requirements.txt
└── run.sh              # One-command setup & launch
```

---

## Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/Nivedita-Chhokar/Jarvis1.0.git
cd Jarvis1.0
```

### 2. Add your Gemini API key
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```
Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run
```bash
bash run.sh
```
The script will automatically create a virtual environment, install dependencies, and start the server.

### 4. Open in Chrome
```
http://localhost:8000
```
> ⚠️ **Use Google Chrome** — the Web Speech API has the best support there.

---

## How to Use

| Voice Command | What Happens |
|---|---|
| *"Add buy groceries with high priority"* | Task added to your list |
| *"Add call the dentist, due 2025-12-15"* | Task with due date |
| *"Show me all my tasks"* | Agent reads your list aloud |
| *"Mark task 1 as done"* | Status updated to ✓ Done |
| *"Delete buy groceries"* | Task removed |
| *"Remember: my standup is every day at 9am"* | Saved to Memory Log |
| *"What did I tell you about my meetings?"* | Memory recalled aloud |

You can also click **⌨** to switch to text input mode.

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message to the agent |
| `GET` | `/api/todos` | List all to-do items |
| `DELETE` | `/api/todos/{id}` | Delete a specific task |
| `GET` | `/api/memories` | Retrieve stored memories |
| `GET` | `/api/health` | Health check |

---

## Agent Tools

The agent has 6 tools registered for Gemini function calling:

| Tool | Description |
|---|---|
| `add_todo` | Add a new task with optional priority and due date |
| `update_todo` | Update title, status, priority, or due date of a task |
| `delete_todo` | Permanently remove a task by ID |
| `list_todos` | List all tasks, optionally filtered by status |
| `store_memory` | Save an important fact about the user to long-term memory |
| `recall_memories` | Search and retrieve stored memories by keyword |

---

## Memory System

ARIA uses **two separate storage layers**:

- **Conversation History** — Every message is automatically stored and fed back to Gemini (last 50 messages) so the agent maintains context within a session.
- **Memory Log** — The agent proactively calls `store_memory` when you share something personally significant (schedules, preferences, birthdays). These persist across sessions and appear in the Memory Log panel.

---

## Notes

- The free tier of Gemini 2.5 Flash allows **20 requests/day**. For uninterrupted demo use, enable billing on your Google AI account.
- The SQLite database (`agent.db`) is created automatically on first run and is excluded from version control.
