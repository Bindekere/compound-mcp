import json
import sqlite3


def render_for_codex(session: sqlite3.Row, state: sqlite3.Row) -> str:
    """Format canonical state as a Codex-ready context prompt."""
    constraints = json.loads(state["constraints"] or "[]")
    reasoning = json.loads(state["reasoning"] or "[]")
    decisions = json.loads(state["decisions"] or "[]")
    questions = json.loads(state["open_questions"] or "[]")
    blockers = json.loads(state["blockers"] or "[]")

    def fmt(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "None"

    lines = [
        f"## Compound Handoff - {session['title']}",
        f"Session: {session['session_id']}",
        f"Last updated: {state['updated_at']}",
        f"State version: {state['version']}",
        "",
        "### Goal",
        state["goal"],
        "",
        "### Constraints",
        fmt(constraints),
        "",
        "### Reasoning so far",
        fmt(reasoning),
        "",
        "### Decisions made",
        fmt(decisions),
        "",
        "### Open questions",
        fmt(questions),
        "",
        "### Blockers",
        fmt(blockers),
        "",
        "### Next action",
        state["next_action"],
        "",
        "---",
        "Continue from this state. Do not ask for context re-explanation.",
    ]
    return "\n".join(lines)
