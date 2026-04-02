# Compound

Compound is a local MCP server for cross-tool AI continuity.

It stores a portable task state while you work in one AI tool, then lets
another tool resume from that state without forcing you to copy and paste an
entire conversation. The current working demo is `Claude Desktop -> Codex`.

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

## Quick start

### 1. Clone the repo

```powershell
git clone https://github.com/Bindekere/compound-mcp.git
cd compound-mcp
```

### 2. Install dependencies

```powershell
uv sync
```

If `uv` has trouble with hidden environment or cache folders on Windows, use:

```powershell
$env:UV_CACHE_DIR="$PWD\uvcache"
$env:UV_PROJECT_ENVIRONMENT="venv"
uv sync
```

### 3. Run the MCP server locally

```powershell
uv run server.py
```

Or, with the same Windows fallback:

```powershell
$env:UV_CACHE_DIR="$PWD\uvcache"
$env:UV_PROJECT_ENVIRONMENT="venv"
uv run server.py
```

If the command stays running quietly, the server has started successfully.

## Install in Claude Desktop

Add a `compound` entry to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "compound": {
      "command": "C:\\Users\\YOUR_USER\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\path\\to\\compound-mcp",
        "run",
        "server.py"
      ],
      "env": {
        "UV_CACHE_DIR": "C:\\path\\to\\compound-mcp\\uvcache",
        "UV_PROJECT_ENVIRONMENT": "venv"
      }
    }
  }
}
```

Restart Claude Desktop after saving the config.

## Install in Codex

Add a `compound` entry to `.codex/config.toml`:

```toml
[mcp_servers.compound]
command = "C:\\Users\\YOUR_USER\\.local\\bin\\uv.exe"
args = [
  "--directory",
  "C:\\path\\to\\compound-mcp",
  "run",
  "server.py",
]
env = { UV_CACHE_DIR = "C:\\path\\to\\compound-mcp\\uvcache", UV_PROJECT_ENVIRONMENT = "venv" }
startup_timeout_sec = 30
```

Restart Codex after saving the config.

## Test the flow in Claude

Open a Claude chat with access to the `compound` MCP server and send:

```text
Call the Compound MCP tool `get_or_create_active_session` with:
- title: "MCP continuity test"
- goal: "Verify Claude can track task state for a Codex handoff"

Then tell me the returned session_id.
```

Then send:

```text
Call the Compound MCP tool `update_canonical_state` for that session_id with:
- goal: "Verify Claude can track task state for Codex handoff"
- constraints: ["Use Compound MCP server", "Keep the test minimal"]
- reasoning: ["Created or reused a tracked test session in Claude"]
- decisions: ["Claude is the source tool", "Codex is the destination tool"]
- open_questions: ["Will Codex load the latest handoff cleanly?"]
- blockers: []
- next_action: "Open Codex and request the latest state from Compound"

Then confirm the returned version.
```

Optional check in Claude:

```text
Call `get_latest_for_destination` with destination "codex" and show me the full returned handoff.
```

## Test the flow in Codex

After Claude has written a session, open Codex and send:

```text
Call the Compound MCP tool `get_latest_for_destination` with destination "codex".
Then summarize:
1. the goal
2. the current constraints
3. the next action
```

If that works, Codex should load the latest Claude-authored state without
asking you to restate the problem.

A stronger round-trip test is:

1. Create and update a session in Claude.
2. Switch to Codex.
3. Ask Codex to load the latest Compound handoff and continue from `next_action`.

## Example usage model

The intended workflow is:

1. Claude starts or reuses a tracked session with `get_or_create_active_session`.
2. Claude updates canonical state as the task evolves.
3. Claude hits a limit, stalls, or the user decides to switch tools.
4. Codex calls `get_latest_for_destination("codex")`.
5. Compound returns a resumable handoff with the latest goal, constraints,
   reasoning, and next action.

## MCP tool reference

### `get_active_session`

Returns the latest active session for a source tool.

Default source tool:

- `claude_desktop`

### `get_or_create_active_session`

Returns the latest active session for a source tool if one exists. Otherwise,
it creates a new one.

Useful for:

- tracked Claude chats
- silent session reuse

### `create_session`

Creates a new session explicitly.

Useful when:

- you want a fresh session instead of reusing the current active one

### `update_canonical_state`

Writes a new canonical state version for an active session.

Required fields:

- `goal`
- `constraints`
- `reasoning`
- `decisions`
- `open_questions`
- `blockers`
- `next_action`

### `get_latest_for_destination`

Loads the latest active session and renders it for a destination tool.

Currently supported destination:

- `codex`

### `close_session`

Marks a session as closed so a later call can create a fresh active session.

## Troubleshooting

### `uv sync` fails on Windows

Try:

```powershell
$env:UV_CACHE_DIR="$PWD\uvcache"
$env:UV_PROJECT_ENVIRONMENT="venv"
uv sync
```

### Claude or Codex does not see the MCP server

Check:

- the config file was saved correctly
- the path to the repo is correct
- `uv sync` has already been run once
- the app was fully restarted after config changes

### The server runs manually but not through the app

Test it directly:

```powershell
cd path\to\compound-mcp
$env:UV_CACHE_DIR="$PWD\uvcache"
$env:UV_PROJECT_ENVIRONMENT="venv"
uv run server.py
```

If it stays running, the server itself is fine and the problem is likely in the
host app config.

### Codex loads nothing

This usually means:

- Claude never wrote a tracked session
- the session was closed
- the wrong Compound instance/path is configured in one of the apps

## Roadmap

- make tracking more automatic and less prompt-dependent
- support richer handoff history and session inspection
- add more destinations beyond Codex
- improve trust and editing around the generated handoff

## License

MIT
