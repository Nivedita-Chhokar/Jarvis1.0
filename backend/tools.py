"""
tools.py — All tool functions for the Voice AI Agent.

To-Do tools  : add_todo, update_todo, delete_todo, list_todos
Memory tools : store_memory, recall_memories

Each function uses clear docstrings + type hints so the Gemini SDK
can auto-introspect the schema for function calling.
"""

from datetime import datetime
from backend.database import get_connection


# ─────────────────────────────────────────────────────────────
# TO-DO TOOLS
# ─────────────────────────────────────────────────────────────

def add_todo(title: str, priority: str = "medium", due_date: str = "") -> dict:
    """
    Add a new task to the To-Do list.

    Args:
        title: The task description, e.g. 'Buy groceries'.
        priority: Task priority level — 'low', 'medium', or 'high'. Defaults to 'medium'.
        due_date: Optional due date in YYYY-MM-DD format, e.g. '2025-12-31'. Leave empty if not specified.

    Returns:
        A dict with the new task's id and a confirmation message.
    """
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO todos (title, status, priority, due_date, created_at, updated_at)
               VALUES (?, 'pending', ?, ?, ?, ?)""",
            (title, priority, due_date or None, now, now),
        )
        conn.commit()
        todo_id = cursor.lastrowid
    return {
        "success": True,
        "id": todo_id,
        "message": f"Task '{title}' added to your list with {priority} priority (ID: {todo_id}).",
    }


def update_todo(
    id: int,
    title: str = "",
    status: str = "",
    priority: str = "",
    due_date: str = "",
) -> dict:
    """
    Update an existing To-Do item by its ID.

    Args:
        id: The numeric ID of the task to update.
        title: New title for the task. Leave empty to keep current title.
        status: New status — 'pending', 'in_progress', or 'done'. Leave empty to keep current.
        priority: New priority — 'low', 'medium', or 'high'. Leave empty to keep current.
        due_date: New due date in YYYY-MM-DD format. Leave empty to keep current.

    Returns:
        A dict with a success flag and a confirmation message.
    """
    now = datetime.now().isoformat()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (id,)).fetchone()
        if not row:
            return {"success": False, "message": f"No task found with ID {id}."}

        new_title    = title    or row["title"]
        new_status   = status   or row["status"]
        new_priority = priority or row["priority"]
        new_due      = due_date or row["due_date"]

        conn.execute(
            """UPDATE todos
               SET title=?, status=?, priority=?, due_date=?, updated_at=?
               WHERE id=?""",
            (new_title, new_status, new_priority, new_due, now, id),
        )
        conn.commit()

    changes = []
    if title:    changes.append(f"title to '{title}'")
    if status:   changes.append(f"status to '{status}'")
    if priority: changes.append(f"priority to '{priority}'")
    if due_date: changes.append(f"due date to '{due_date}'")
    change_str = ", ".join(changes) if changes else "nothing"

    return {
        "success": True,
        "id": id,
        "message": f"Task {id} updated — changed {change_str}.",
    }


def delete_todo(id: int) -> dict:
    """
    Permanently delete a To-Do item by its ID.

    Args:
        id: The numeric ID of the task to delete.

    Returns:
        A dict with a success flag and a confirmation message.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT title FROM todos WHERE id = ?", (id,)).fetchone()
        if not row:
            return {"success": False, "message": f"No task found with ID {id}."}
        title = row["title"]
        conn.execute("DELETE FROM todos WHERE id = ?", (id,))
        conn.commit()
    return {
        "success": True,
        "id": id,
        "message": f"Task '{title}' (ID: {id}) has been deleted.",
    }


def list_todos(filter_status: str = "") -> dict:
    """
    List all To-Do items, optionally filtered by status.

    Args:
        filter_status: Optional status filter — 'pending', 'in_progress', or 'done'.
                       Leave empty to list all tasks.

    Returns:
        A dict with a list of tasks and a summary count.
    """
    with get_connection() as conn:
        if filter_status:
            rows = conn.execute(
                "SELECT * FROM todos WHERE status = ? ORDER BY id", (filter_status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM todos ORDER BY id"
            ).fetchall()

    tasks = [
        {
            "id":         r["id"],
            "title":      r["title"],
            "status":     r["status"],
            "priority":   r["priority"],
            "due_date":   r["due_date"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]

    if not tasks:
        msg = "Your to-do list is empty." if not filter_status else f"No tasks with status '{filter_status}'."
    else:
        msg = f"You have {len(tasks)} task(s)" + (f" with status '{filter_status}'" if filter_status else "") + "."

    return {"success": True, "tasks": tasks, "count": len(tasks), "message": msg}


# ─────────────────────────────────────────────────────────────
# MEMORY TOOLS
# ─────────────────────────────────────────────────────────────

def store_memory(summary: str, importance: str = "normal", tags: str = "") -> dict:
    """
    Store an important piece of information from the user in long-term memory.
    Use this when the user shares something personal, a preference, a schedule,
    an event, or anything they may want recalled later.

    Args:
        summary: A clear, concise statement of what to remember,
                 e.g. 'User has a team meeting every Monday at 10am'.
        importance: Importance level — 'low', 'normal', or 'high'. Defaults to 'normal'.
        tags: Comma-separated keywords to aid recall, e.g. 'meetings,work,schedule'.

    Returns:
        A dict with the memory id and a confirmation message.
    """
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO memories (summary, importance, tags, created_at) VALUES (?, ?, ?, ?)",
            (summary, importance, tags, now),
        )
        conn.commit()
        mem_id = cursor.lastrowid
    return {
        "success": True,
        "id": mem_id,
        "message": f"I've remembered: '{summary}'.",
    }


def recall_memories(query: str = "") -> dict:
    """
    Retrieve stored memories that are relevant to a query or topic.
    Use this when the user asks about something they told you before,
    or when context from past conversations would help answer their question.

    Args:
        query: A keyword or phrase to search memories for, e.g. 'meetings' or 'birthday'.
               Leave empty to retrieve all memories.

    Returns:
        A dict with a list of matching memories.
    """
    with get_connection() as conn:
        if query:
            pattern = f"%{query}%"
            rows = conn.execute(
                """SELECT * FROM memories
                   WHERE summary LIKE ? OR tags LIKE ?
                   ORDER BY importance DESC, created_at DESC
                   LIMIT 10""",
                (pattern, pattern),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY importance DESC, created_at DESC LIMIT 10"
            ).fetchall()

    memories = [
        {
            "id":         r["id"],
            "summary":    r["summary"],
            "importance": r["importance"],
            "tags":       r["tags"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]

    if not memories:
        msg = "I don't have any relevant memories stored yet."
    else:
        msg = f"Found {len(memories)} memory record(s)."

    return {"success": True, "memories": memories, "count": len(memories), "message": msg}
