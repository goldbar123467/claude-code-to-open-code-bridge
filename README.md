# Agent Bridge

**Minimal coordination for Claude Code + OpenCode**

Zero dependencies. Just Python stdlib + SQLite. ~200 lines of code.

## What It Does

```
┌─────────────────┐                      ┌─────────────────┐
│   Claude Code   │◄──── messages ──────►│    OpenCode     │
│                 │      file locks      │                 │
│                 │      memory          │                 │
└────────┬────────┘                      └────────┬────────┘
         │                                        │
         └───────────► SQLite DB ◄───────────────┘
                    ~/.agent-bridge/bridge.db
```

## Features

- **Messaging**: Send/receive messages between agents
- **File Locks**: Prevent edit conflicts with TTL-based locks
- **Memory**: Simple key-value store for shared context
- **Agent Registry**: Track active agents

## Installation

```bash
git clone https://github.com/yourusername/agent-bridge
cd agent-bridge
```

No `pip install` needed. It's just Python.

## Usage

### Add to Claude Code (~/.claude.json)

```json
{
  "mcpServers": {
    "bridge": {
      "command": "python3",
      "args": ["/path/to/agent-bridge/mcp_server.py"]
    }
  }
}
```

### Add to OpenCode (~/.config/opencode/config.json)

```json
{
  "mcp": {
    "bridge": {
      "command": "python3",
      "args": ["/path/to/agent-bridge/mcp_server.py"]
    }
  }
}
```

### CLI Testing

```bash
# Register an agent
python bridge.py register claude-1

# Send a message
python bridge.py send claude-1 opencode-1 "[TASK] Build login page" "Use React + Tailwind"

# Check inbox
python bridge.py inbox opencode-1

# Lock a file
python bridge.py lock src/auth.ts opencode-1

# List locks
python bridge.py locks

# Store a memory
python bridge.py remember "Use JWT for auth tokens"

# Search memories
python bridge.py recall "auth"
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `register` | Register agent with bridge |
| `agents` | List all registered agents |
| `send` | Send message to another agent |
| `inbox` | Fetch messages |
| `mark_read` | Mark message as read |
| `ack` | Acknowledge message |
| `lock` | Lock file for editing |
| `unlock` | Release file lock |
| `locks` | List active locks |
| `remember` | Store a memory |
| `recall` | Search memories |
| `forget` | Delete a memory |

## Workflow Example

**Claude Code (coordinator):**
```
1. register(name="claude-1", program="claude-code", model="opus")
2. send(sender="claude-1", recipient="opencode-1", subject="[TASK] Build auth", body="...")
3. inbox(agent="claude-1")  # Check for [DONE] messages
```

**OpenCode (worker):**
```
1. register(name="opencode-1", program="opencode", model="deepseek")
2. inbox(agent="opencode-1")  # Get tasks
3. lock(path="src/auth.ts", agent="opencode-1")
4. ... do work ...
5. unlock(path="src/auth.ts", agent="opencode-1")
6. send(sender="opencode-1", recipient="claude-1", subject="[DONE] Auth complete", body="...")
```

## Message Conventions

Use subject prefixes:
- `[TASK]` - New task assignment
- `[DONE]` - Task completed
- `[BLOCKED]` - Need help/stuck
- `[QUESTION]` - Clarification needed
- `[HANDOFF]` - Passing work to another agent

## File Structure

```
agent-bridge/
├── bridge.py       # Core logic (~150 lines)
├── mcp_server.py   # MCP wrapper (~100 lines)
├── pyproject.toml  # Package metadata
└── README.md       # This file
```

## Database

SQLite at `~/.agent-bridge/bridge.db`

Tables:
- `agents` - Registered agents
- `messages` - Message queue
- `file_locks` - Active file locks
- `memory` - Shared memories

## Why Not MCP Agent Mail?

MCP Agent Mail is great but heavy (~10k lines, PostgreSQL, Git storage, LLM integration).

Agent Bridge is:
- ~250 lines total
- Zero dependencies
- SQLite only
- Copy-paste simple

Use Agent Bridge for simple coordination. Use Agent Mail for production swarms.

## License

MIT
