import json
import uuid
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from db import get_db, init_db
from models import CanonicalState
from renderer import render_for_codex


mcp = FastMCP("compound")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_latest_active_session(source_tool: str | None = None):
    db = get_db()
    try:
        if source_tool:
            return db.execute(
                """
                SELECT *
                FROM sessions
                WHERE status = 'active' AND source_tool = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (source_tool,),
            ).fetchone()

        return db.execute(
            """
            SELECT *
            FROM sessions
            WHERE status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        db.close()


def create_session_record(title: str, goal: str, source_tool: str) -> dict:
    session_id = str(uuid.uuid4())
    now = utc_now_iso()
    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO sessions
            (session_id, title, source_tool, status, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (session_id, title, source_tool, now, now),
        )
        db.execute(
            """
            INSERT INTO canonical_state
            (session_id, goal, constraints, reasoning, decisions,
             open_questions, blockers, next_action, version, updated_at)
            VALUES (?, ?, '[]', '[]', '[]', '[]', '[]', '', 1, ?)
            """,
            (session_id, goal, now),
        )
        db.commit()
    finally:
        db.close()

    return {
        "session_id": session_id,
        "title": title,
        "source_tool": source_tool,
        "created_at": now,
    }


@mcp.tool()
def get_active_session(source_tool: str = "claude_desktop") -> dict:
    """Get the latest active session for a source tool."""
    session = fetch_latest_active_session(source_tool=source_tool)
    if not session:
        return {
            "found": False,
            "source_tool": source_tool,
            "message": "No active session found.",
        }

    return {
        "found": True,
        "session_id": session["session_id"],
        "title": session["title"],
        "source_tool": session["source_tool"],
        "status": session["status"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
    }


@mcp.tool()
def get_or_create_active_session(
    title: str, goal: str, source_tool: str = "claude_desktop"
) -> dict:
    """Reuse the latest active session for a source tool, or create one."""
    session = fetch_latest_active_session(source_tool=source_tool)
    if session:
        return {
            "session_id": session["session_id"],
            "title": session["title"],
            "source_tool": session["source_tool"],
            "status": session["status"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "reused": True,
        }

    created = create_session_record(title=title, goal=goal, source_tool=source_tool)
    created["reused"] = False
    return created


@mcp.tool()
def create_session(
    title: str, goal: str, source_tool: str = "claude_desktop"
) -> dict:
    """Create a new Compound tracking session."""
    return create_session_record(title=title, goal=goal, source_tool=source_tool)


@mcp.tool()
def update_canonical_state(
    session_id: str,
    goal: str,
    constraints: list[str],
    reasoning: list[str],
    decisions: list[str],
    open_questions: list[str],
    blockers: list[str],
    next_action: str,
) -> dict:
    """Update the canonical state for an active session."""
    CanonicalState(
        session_id=session_id,
        goal=goal,
        constraints=constraints,
        reasoning=reasoning,
        decisions=decisions,
        open_questions=open_questions,
        blockers=blockers,
        next_action=next_action,
    )

    now = utc_now_iso()
    db = get_db()
    try:
        session = db.execute(
            "SELECT session_id, status FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not session:
            raise ValueError(f"Session '{session_id}' does not exist.")
        if session["status"] != "active":
            raise ValueError(f"Session '{session_id}' is not active.")

        row = db.execute(
            """
            SELECT version
            FROM canonical_state
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        version = (row["version"] + 1) if row else 1
        db.execute(
            """
            INSERT INTO canonical_state
            (session_id, goal, constraints, reasoning, decisions,
             open_questions, blockers, next_action, version, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                goal,
                json.dumps(constraints),
                json.dumps(reasoning),
                json.dumps(decisions),
                json.dumps(open_questions),
                json.dumps(blockers),
                next_action,
                version,
                now,
            ),
        )
        db.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (now, session_id),
        )
        db.commit()
    finally:
        db.close()

    return {"version": version, "updated_at": now}


@mcp.tool()
def get_latest_for_destination(destination: str) -> str:
    """Get the latest session state formatted for a destination tool."""
    session = fetch_latest_active_session()
    if not session:
        return "No active sessions found."

    db = get_db()
    try:
        state = db.execute(
            """
            SELECT *
            FROM canonical_state
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session["session_id"],),
        ).fetchone()
        if not state:
            return "Session found but no state recorded yet."

        if destination == "codex":
            return render_for_codex(session, state)

        return f"Destination '{destination}' not supported in v1."
    finally:
        db.close()


@mcp.tool()
def close_session(session_id: str) -> dict:
    """Mark a session as closed so a new active session can be created later."""
    now = utc_now_iso()
    db = get_db()
    try:
        row = db.execute(
            "SELECT session_id, status FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Session '{session_id}' does not exist.")
        if row["status"] == "closed":
            return {"session_id": session_id, "status": "closed", "updated_at": now}

        db.execute(
            "UPDATE sessions SET status = 'closed', updated_at = ? WHERE session_id = ?",
            (now, session_id),
        )
        db.commit()
    finally:
        db.close()

    return {"session_id": session_id, "status": "closed", "updated_at": now}


if __name__ == "__main__":
    init_db()
    mcp.run(transport="stdio")
