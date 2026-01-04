<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=for-the-badge" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/lines-~250-orange?style=for-the-badge" alt="~250 Lines">
  <img src="https://img.shields.io/github/license/goldbar123467/claude-code-to-open-code-bridge?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">🌉 Agent Bridge</h1>

<p align="center">
  <strong>Minimal coordination between Claude Code and OpenCode</strong><br>
  Zero dependencies. Just Python. ~250 lines.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#usage">Usage</a> •
  <a href="#api">API</a> •
  <a href="#why">Why Agent Bridge?</a>
</p>

---

## Quick Start

```bash
curl -sL https://raw.githubusercontent.com/goldbar123467/claude-code-to-open-code-bridge/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/goldbar123467/claude-code-to-open-code-bridge ~/.agent-bridge
```

Then add to your config:

<details>
<summary><b>Claude Code</b> (~/.claude.json)</summary>

```json
{
  "mcpServers": {
    "bridge": {
      "command": "python3",
      "args": ["~/.agent-bridge/mcp_server.py"]
    }
  }
}
```
</details>

<details>
<summary><b>OpenCode</b> (~/.config/opencode/config.json)</summary>

```json
{
  "mcp": {
    "bridge": {
      "command": "python3",
      "args": ["~/.agent-bridge/mcp_server.py"]
    }
  }
}
```
</details>

---

## How It Works

```
┌─────────────────┐                        ┌─────────────────┐
│   Claude Code   │◄───── messages ───────►│    OpenCode     │
│    (Opus 4)     │       file locks       │   (DeepSeek)    │
│                 │       memory           │                 │
└────────┬────────┘                        └────────┬────────┘
         │                                          │
         └─────────────► SQLite ◄──────────────────┘
                    ~/.agent-bridge/bridge.db
```

Both agents connect to the same lightweight SQLite database. No servers. No Docker. No configuration hell.

---

## Features

| Feature | Description |
|---------|-------------|
| 📨 **Messaging** | Send tasks, receive completions, coordinate work |
| 🔒 **File Locks** | Prevent edit conflicts with TTL-based locks |
| 🧠 **Shared Memory** | Key-value store for context across sessions |
| 👥 **Agent Registry** | Track active agents and their status |

---

## Usage

### In Claude Code or OpenCode

```
You: Register me as the coordinator
AI: [calls bridge.register with name="coordinator"]

You: Send a task to the worker agent
AI: [calls bridge.send with recipient="worker", subject="[TASK] Build auth"]

You: Check if worker is done
AI: [calls bridge.inbox to check for [DONE] messages]
```

### CLI

```bash
# Register agents
python3 bridge.py register coordinator
python3 bridge.py register worker

# Send a task
python3 bridge.py send coordinator worker "[TASK] Build login page"

# Check inbox
python3 bridge.py inbox worker

# Lock a file before editing
python3 bridge.py lock src/auth.ts worker

# Release when done
python3 bridge.py unlock src/auth.ts worker

# Store shared context
python3 bridge.py remember "Use JWT tokens for auth"

# Recall context
python3 bridge.py recall "auth"
```

---

## API

### Agent Management

| Tool | Description |
|------|-------------|
| `register` | Register agent with the bridge |
| `agents` | List all active agents |

### Messaging

| Tool | Description |
|------|-------------|
| `send` | Send message to another agent |
| `inbox` | Fetch messages for an agent |
| `mark_read` | Mark message as read |
| `ack` | Acknowledge receipt |

### File Coordination

| Tool | Description |
|------|-------------|
| `lock` | Lock file for exclusive editing |
| `unlock` | Release file lock |
| `locks` | List all active locks |

### Memory

| Tool | Description |
|------|-------------|
| `remember` | Store a note/decision |
| `recall` | Search stored memories |
| `forget` | Delete a memory |

---

## Message Conventions

Use subject prefixes for clear communication:

| Prefix | Meaning |
|--------|---------|
| `[TASK]` | New task assignment |
| `[DONE]` | Task completed |
| `[BLOCKED]` | Need help, stuck |
| `[QUESTION]` | Clarification needed |
| `[HANDOFF]` | Passing to another agent |

---

## Example Workflow

**Terminal 1 — Claude Code (Coordinator)**
```
> Register as coordinator, model opus-4
> Send task to worker: "Build user authentication with JWT"
> Wait for worker to complete, then review
```

**Terminal 2 — OpenCode (Worker)**
```
> Register as worker, model deepseek
> Check inbox for tasks
> Lock src/auth/* files
> Implement authentication
> Unlock files, send [DONE] to coordinator
```

---

## Why Agent Bridge?

| | Agent Bridge | MCP Agent Mail | Custom Solution |
|---|:---:|:---:|:---:|
| Lines of code | **~250** | ~10,000+ | Varies |
| Dependencies | **0** | PostgreSQL, Redis, etc. | Many |
| Setup time | **30 seconds** | 10+ minutes | Hours |
| Docker required | **No** | Yes | Usually |
| Learning curve | **Minimal** | Moderate | High |

**Agent Bridge is for developers who want coordination without complexity.**

---

## File Structure

```
agent-bridge/
├── bridge.py        # Core logic (278 lines)
├── mcp_server.py    # MCP protocol wrapper (281 lines)
├── install.sh       # One-line installer
├── pyproject.toml   # Package metadata
└── examples/
    ├── claude-code.json
    └── opencode.json
```

---

## Requirements

- Python 3.10+
- That's it. No pip install. No npm. No Docker.

---

## Database

SQLite database at `~/.agent-bridge/bridge.db`

**Tables:**
- `agents` — Registered agents
- `messages` — Message queue
- `file_locks` — Active file locks
- `memory` — Shared memories

---

## Contributing

PRs welcome! Keep it simple:
- No new dependencies
- Under 500 total lines
- Must work with just `python3`

---

## License

MIT — Use it however you want.

---

<p align="center">
  <sub>Built for developers who believe the best tool is the simplest one that works.</sub>
</p>
