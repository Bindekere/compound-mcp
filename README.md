# Compound

Compound is a local MCP server for cross-tool AI continuity.

It stores a portable task state while you work in one tool, then lets another
tool resume from that state without forcing you to copy and paste an entire
conversation. The current working demo is `Claude Desktop -> Codex`.

## Why this exists

Free-tier AI workflows break often. Sessions expire, usage limits hit, and the
usual recovery path is manual:

1. copy the old conversation
2. open another AI tool
3. paste everything back in
4. explain the task again

Compound replaces that with a shared task-state layer. Instead of moving raw
chat history around, it keeps a structured continuity record that can be
rendered for the next destination tool.

## Current status

This project is an early working prototype.

Today it can:

- create and reuse active tracked sessions
- store canonical task state in SQLite
- update that state during a conversation
- render the latest state into a Codex-ready handoff
- support a working `Claude Desktop -> Codex` continuity flow through MCP

Current limitation:

- session tracking is not fully automatic yet; Claude still needs prompting or
  project instructions to track the session reliably

## How it works

Compound keeps a canonical session state with fields like:

- goal
- constraints
- reasoning
- decisions
- open questions
- blockers
- next action

Claude writes to that state. Codex reads the latest state and resumes from the
`next_action`.

## Tool surface

Current MCP tools:

- `get_active_session`
- `get_or_create_active_session`
- `create_session`
- `update_canonical_state`
- `get_latest_for_destination`
- `close_session`

## Tech stack

- Python 3.13
- [`mcp`](https://github.com/modelcontextprotocol/python-sdk)
- SQLite
- [`uv`](https://github.com/astral-sh/uv)

## Project structure

```text
compound/
|-- db.py
|-- models.py
|-- renderer.py
|-- server.py
|-- pyproject.toml
`-- README.md
```

## Local setup

```powershell
git clone <your-repo-url>
cd compound
uv sync
uv run server.py
```

If `uv` has trouble with hidden environment or cache folders on Windows, this
fallback works well:

```powershell
$env:UV_CACHE_DIR="$PWD\uvcache"
$env:UV_PROJECT_ENVIRONMENT="venv"
uv sync
uv run server.py
```

## Claude Desktop configuration

Example `claude_desktop_config.json` entry:

```json
{
  "mcpServers": {
    "compound": {
      "command": "C:\\Users\\YOUR_USER\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\path\\to\\compound",
        "run",
        "server.py"
      ],
      "env": {
        "UV_CACHE_DIR": "C:\\path\\to\\compound\\uvcache",
        "UV_PROJECT_ENVIRONMENT": "venv"
      }
    }
  }
}
```

## Codex configuration

Example `.codex/config.toml` entry:

```toml
[mcp_servers.compound]
command = "C:\\Users\\YOUR_USER\\.local\\bin\\uv.exe"
args = [
  "--directory",
  "C:\\path\\to\\compound",
  "run",
  "server.py",
]
env = { UV_CACHE_DIR = "C:\\path\\to\\compound\\uvcache", UV_PROJECT_ENVIRONMENT = "venv" }
startup_timeout_sec = 30
```

## Demo flow

1. Claude starts or reuses a tracked session with `get_or_create_active_session`.
2. Claude updates canonical state as the task evolves.
3. Claude hits a limit, stalls, or the user decides to switch tools.
4. Codex calls `get_latest_for_destination("codex")`.
5. Compound returns a resumable handoff with the latest goal, constraints,
   reasoning, and next action.

## Roadmap

- make tracking more automatic and less prompt-dependent
- support richer handoff history and session inspection
- add more destinations beyond Codex
- improve trust and editing around the generated handoff

## License

MIT
