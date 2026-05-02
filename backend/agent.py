"""
agent.py — Gemini 2.5 Flash agent with automatic function calling.
Manages multi-turn chat sessions and persists history to SQLite.
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.database import get_connection
from backend.tools import (
    add_todo, update_todo, delete_todo, list_todos,
    store_memory, recall_memories,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are ARIA — an Adaptive Recall & Intelligence Assistant — a friendly, voice-enabled AI agent that helps users manage their To-Do list and remembers important personal information.

## YOUR TOOLS
You have access to 6 tools:

**To-Do Tools:**
- add_todo: When user wants to add a task. Extract the title, and optionally priority (low/medium/high) and due_date.
- update_todo: When user says "mark done", "complete task", "update", "change", "set status". Always use the task's numeric ID.
- delete_todo: When user says "remove", "delete", "cancel", "get rid of" a task.
- list_todos: When user asks "what are my tasks?", "show my list", "what do I have to do?", "any pending tasks?".

**Memory Tools:**
- store_memory: When user shares something important about themselves: schedules, preferences, birthdays, habits, events. Store it proactively.
- recall_memories: When user asks "what did I tell you about X?", "do you remember when...?", or when past context helps answer a question.

## DECISION RULES
1. ALWAYS use tools for task management — never make up task IDs or statuses.
2. ALWAYS call list_todos after add/update/delete to get the fresh state.
3. Store memories proactively — if the user mentions their birthday, a routine, or a preference, store it without being asked.
4. Recall memories when the user references past information or asks "remember".
5. For pure conversation (greetings, thanks, questions about yourself), respond directly without tools.

## VOICE-FRIENDLY RESPONSE RULES
- Keep responses SHORT and NATURAL (1–3 sentences max) — they will be spoken aloud.
- No markdown, no bullet points in your spoken replies.
- Always confirm tool actions: "Done! I've added X to your list."
- For list_todos results, summarize naturally: "You have 3 tasks: buy groceries (high priority), call the dentist, and review the report."
- Be warm, friendly, and conversational.

## PERSONALITY
You are helpful, proactive, and a little witty. You remember things the user tells you and bring them up naturally when relevant. You care about the user's productivity.
"""


def _get_history(session_id: str) -> list[dict]:
    """Load conversation history for a session from the DB."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT role, content FROM conversation_history
               WHERE session_id = ? ORDER BY id ASC LIMIT 50""",
            (session_id,),
        ).fetchall()
    return [{"role": r["role"], "parts": [{"text": r["content"]}]} for r in rows]


def _save_message(session_id: str, role: str, content: str):
    """Persist a message to conversation history."""
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversation_history (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        conn.commit()


def chat(session_id: str, user_message: str) -> dict:
    """
    Send a user message to the agent and return the response.

    Returns a dict with:
        reply        — the agent's text response
        tool_calls   — list of tool names that were called
        todos        — current to-do list (always fresh)
        memories     — current memories
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build tools list
    tools = [add_todo, update_todo, delete_todo, list_todos, store_memory, recall_memories]

    # Load history
    history = _get_history(session_id)

    # Build contents: history + new user message
    contents = []
    for h in history:
        contents.append(types.Content(role=h["role"], parts=[types.Part(text=h["parts"][0]["text"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    # Call Gemini with automatic function calling (retry on 429)
    last_error = None
    response = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=tools,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        maximum_remote_calls=5,
                    ),
                    temperature=0.7,
                ),
            )
            break  # success
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                time.sleep(wait)
            else:
                raise  # non-quota errors bubble up immediately
    if response is None:
        raise last_error

    reply_text = response.text or "I'm here! How can I help you?"

    # Extract tool calls from the response candidates
    tool_calls_made = []
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                tool_calls_made.append(part.function_call.name)

    # Persist messages
    _save_message(session_id, "user", user_message)
    _save_message(session_id, "model", reply_text)

    # Always fetch fresh todos and memories to keep UI in sync
    todos_result   = list_todos()
    memory_result  = recall_memories()

    return {
        "reply":      reply_text,
        "tool_calls": list(set(tool_calls_made)),
        "todos":      todos_result.get("tasks", []),
        "memories":   memory_result.get("memories", []),
    }
