"""
Agent Bridge - Minimal coordination for Claude Code + OpenCode
No heavy dependencies. Just Python stdlib + SQLite.
"""

import sqlite3
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib

DB_PATH = Path.home() / ".agent-bridge" / "bridge.db"


def get_db() -> sqlite3.Connection:
    """Get database connection, create tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT,
            thread_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT,
            ack_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            name TEXT PRIMARY KEY,
            program TEXT,
            model TEXT,
            task TEXT,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_locks (
            path TEXT PRIMARY KEY,
            agent TEXT NOT NULL,
            reason TEXT,
            expires_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


# =============================================================================
# Agent Registration
# =============================================================================

def register_agent(name: str, program: str = "unknown", model: str = "unknown", task: str = "") -> dict:
    """Register or update an agent."""
    conn = get_db()
    conn.execute("""
        INSERT INTO agents (name, program, model, task, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            program = excluded.program,
            model = excluded.model,
            task = excluded.task,
            last_seen = excluded.last_seen
    """, (name, program, model, task, datetime.utcnow().isoformat()))
    conn.commit()
    return {"status": "registered", "name": name}


def list_agents() -> list:
    """List all registered agents."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM agents ORDER BY last_seen DESC").fetchall()
    return [dict(r) for r in rows]


# =============================================================================
# Messaging
# =============================================================================

def send_message(sender: str, recipient: str, subject: str, body: str = "", thread_id: str = None) -> dict:
    """Send a message to another agent."""
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO messages (sender, recipient, subject, body, thread_id)
        VALUES (?, ?, ?, ?, ?)
    """, (sender, recipient, subject, body, thread_id))
    conn.commit()
    return {"status": "sent", "id": cur.lastrowid}


def fetch_inbox(agent: str, unread_only: bool = True, limit: int = 20) -> list:
    """Fetch messages for an agent."""
    conn = get_db()
    query = "SELECT * FROM messages WHERE recipient = ?"
    if unread_only:
        query += " AND read_at IS NULL"
    query += " ORDER BY created_at DESC LIMIT ?"
    rows = conn.execute(query, (agent, limit)).fetchall()
    return [dict(r) for r in rows]


def mark_read(message_id: int, agent: str) -> dict:
    """Mark a message as read."""
    conn = get_db()
    conn.execute("""
        UPDATE messages SET read_at = ? WHERE id = ? AND recipient = ?
    """, (datetime.utcnow().isoformat(), message_id, agent))
    conn.commit()
    return {"status": "read", "id": message_id}


def ack_message(message_id: int, agent: str) -> dict:
    """Acknowledge a message."""
    conn = get_db()
    conn.execute("""
        UPDATE messages SET ack_at = ?, read_at = COALESCE(read_at, ?)
        WHERE id = ? AND recipient = ?
    """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), message_id, agent))
    conn.commit()
    return {"status": "acknowledged", "id": message_id}


# =============================================================================
# File Locks
# =============================================================================

def lock_file(path: str, agent: str, reason: str = "", ttl_seconds: int = 1800) -> dict:
    """Lock a file for exclusive editing."""
    conn = get_db()
    expires = datetime.utcnow().timestamp() + ttl_seconds
    expires_str = datetime.fromtimestamp(expires).isoformat()

    # Check for existing lock
    existing = conn.execute(
        "SELECT * FROM file_locks WHERE path = ? AND expires_at > ?",
        (path, datetime.utcnow().isoformat())
    ).fetchone()

    if existing and existing["agent"] != agent:
        return {"status": "conflict", "holder": existing["agent"], "path": path}

    conn.execute("""
        INSERT INTO file_locks (path, agent, reason, expires_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            agent = excluded.agent,
            reason = excluded.reason,
            expires_at = excluded.expires_at
    """, (path, agent, reason, expires_str))
    conn.commit()
    return {"status": "locked", "path": path, "expires_at": expires_str}


def unlock_file(path: str, agent: str) -> dict:
    """Release a file lock."""
    conn = get_db()
    conn.execute("DELETE FROM file_locks WHERE path = ? AND agent = ?", (path, agent))
    conn.commit()
    return {"status": "unlocked", "path": path}


def list_locks(agent: str = None) -> list:
    """List active file locks."""
    conn = get_db()
    now = datetime.utcnow().isoformat()
    if agent:
        rows = conn.execute(
            "SELECT * FROM file_locks WHERE agent = ? AND expires_at > ?",
            (agent, now)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM file_locks WHERE expires_at > ?", (now,)
        ).fetchall()
    return [dict(r) for r in rows]


# =============================================================================
# Simple Memory (key-value with tags)
# =============================================================================

def remember(content: str, tags: list = None) -> dict:
    """Store a memory."""
    mem_id = hashlib.sha256(content.encode()).hexdigest()[:12]
    conn = get_db()
    conn.execute("""
        INSERT INTO memory (id, content, tags)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET tags = excluded.tags
    """, (mem_id, content, json.dumps(tags or [])))
    conn.commit()
    return {"status": "stored", "id": mem_id}


def recall(query: str, limit: int = 5) -> list:
    """Search memories (simple LIKE search)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM memory WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?
    """, (f"%{query}%", limit)).fetchall()
    return [dict(r) for r in rows]


def forget(mem_id: str) -> dict:
    """Delete a memory."""
    conn = get_db()
    conn.execute("DELETE FROM memory WHERE id = ?", (mem_id,))
    conn.commit()
    return {"status": "forgotten", "id": mem_id}


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python bridge.py <command> [args]")
        print("Commands: register, send, inbox, lock, unlock, locks, remember, recall, agents")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "register":
        name = sys.argv[2] if len(sys.argv) > 2 else "test-agent"
        print(json.dumps(register_agent(name), indent=2))

    elif cmd == "agents":
        print(json.dumps(list_agents(), indent=2))

    elif cmd == "send":
        sender, recipient, subject = sys.argv[2:5]
        body = sys.argv[5] if len(sys.argv) > 5 else ""
        print(json.dumps(send_message(sender, recipient, subject, body), indent=2))

    elif cmd == "inbox":
        agent = sys.argv[2]
        print(json.dumps(fetch_inbox(agent), indent=2))

    elif cmd == "lock":
        path, agent = sys.argv[2:4]
        print(json.dumps(lock_file(path, agent), indent=2))

    elif cmd == "unlock":
        path, agent = sys.argv[2:4]
        print(json.dumps(unlock_file(path, agent), indent=2))

    elif cmd == "locks":
        print(json.dumps(list_locks(), indent=2))

    elif cmd == "remember":
        content = sys.argv[2]
        print(json.dumps(remember(content), indent=2))

    elif cmd == "recall":
        query = sys.argv[2]
        print(json.dumps(recall(query), indent=2))

    else:
        print(f"Unknown command: {cmd}")
