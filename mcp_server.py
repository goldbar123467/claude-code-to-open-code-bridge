#!/usr/bin/env python3
"""
Agent Bridge MCP Server
Minimal MCP server for agent coordination.
"""

import json
import sys
from typing import Any

# Import bridge functions
from bridge import (
    register_agent, list_agents,
    send_message, fetch_inbox, mark_read, ack_message,
    lock_file, unlock_file, list_locks,
    remember, recall, forget
)


def read_message() -> dict:
    """Read a JSON-RPC message from stdin."""
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return json.loads(line)


def write_message(msg: dict):
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def success_response(id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def error_response(id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}


# Tool definitions
TOOLS = [
    {
        "name": "register",
        "description": "Register this agent with the bridge",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name (e.g., 'claude-1', 'opencode-1')"},
                "program": {"type": "string", "description": "Agent program (claude-code, opencode)"},
                "model": {"type": "string", "description": "Model being used"},
                "task": {"type": "string", "description": "Current task description"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "agents",
        "description": "List all registered agents",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "send",
        "description": "Send a message to another agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sender": {"type": "string", "description": "Your agent name"},
                "recipient": {"type": "string", "description": "Target agent name"},
                "subject": {"type": "string", "description": "Message subject (use prefixes: [TASK], [DONE], [BLOCKED])"},
                "body": {"type": "string", "description": "Message body"},
                "thread_id": {"type": "string", "description": "Thread ID for grouping"}
            },
            "required": ["sender", "recipient", "subject"]
        }
    },
    {
        "name": "inbox",
        "description": "Fetch messages for an agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Your agent name"},
                "unread_only": {"type": "boolean", "default": True},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["agent"]
        }
    },
    {
        "name": "mark_read",
        "description": "Mark a message as read",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"},
                "agent": {"type": "string"}
            },
            "required": ["message_id", "agent"]
        }
    },
    {
        "name": "ack",
        "description": "Acknowledge a message",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"},
                "agent": {"type": "string"}
            },
            "required": ["message_id", "agent"]
        }
    },
    {
        "name": "lock",
        "description": "Lock a file for exclusive editing",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to lock"},
                "agent": {"type": "string", "description": "Your agent name"},
                "reason": {"type": "string", "description": "Why you need the lock"},
                "ttl_seconds": {"type": "integer", "default": 1800}
            },
            "required": ["path", "agent"]
        }
    },
    {
        "name": "unlock",
        "description": "Release a file lock",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "agent": {"type": "string"}
            },
            "required": ["path", "agent"]
        }
    },
    {
        "name": "locks",
        "description": "List active file locks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Filter by agent (optional)"}
            }
        }
    },
    {
        "name": "remember",
        "description": "Store a memory/note for later",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "What to remember"},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["content"]
        }
    },
    {
        "name": "recall",
        "description": "Search memories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "forget",
        "description": "Delete a memory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID to delete"}
            },
            "required": ["id"]
        }
    }
]


def handle_tool_call(name: str, args: dict) -> Any:
    """Execute a tool and return the result."""
    if name == "register":
        return register_agent(
            args["name"],
            args.get("program", "unknown"),
            args.get("model", "unknown"),
            args.get("task", "")
        )
    elif name == "agents":
        return list_agents()
    elif name == "send":
        return send_message(
            args["sender"],
            args["recipient"],
            args["subject"],
            args.get("body", ""),
            args.get("thread_id")
        )
    elif name == "inbox":
        return fetch_inbox(
            args["agent"],
            args.get("unread_only", True),
            args.get("limit", 20)
        )
    elif name == "mark_read":
        return mark_read(args["message_id"], args["agent"])
    elif name == "ack":
        return ack_message(args["message_id"], args["agent"])
    elif name == "lock":
        return lock_file(
            args["path"],
            args["agent"],
            args.get("reason", ""),
            args.get("ttl_seconds", 1800)
        )
    elif name == "unlock":
        return unlock_file(args["path"], args["agent"])
    elif name == "locks":
        return list_locks(args.get("agent"))
    elif name == "remember":
        return remember(args["content"], args.get("tags"))
    elif name == "recall":
        return recall(args["query"], args.get("limit", 5))
    elif name == "forget":
        return forget(args["id"])
    else:
        raise ValueError(f"Unknown tool: {name}")


def main():
    """Main MCP server loop."""
    while True:
        try:
            msg = read_message()
        except (json.JSONDecodeError, KeyboardInterrupt):
            break

        method = msg.get("method")
        id = msg.get("id")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                write_message(success_response(id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "agent-bridge", "version": "1.0.0"}
                }))

            elif method == "notifications/initialized":
                pass  # No response needed

            elif method == "tools/list":
                write_message(success_response(id, {"tools": TOOLS}))

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = handle_tool_call(tool_name, tool_args)
                write_message(success_response(id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }))

            else:
                write_message(error_response(id, -32601, f"Unknown method: {method}"))

        except Exception as e:
            write_message(error_response(id, -32000, str(e)))


if __name__ == "__main__":
    main()
