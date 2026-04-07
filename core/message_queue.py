"""
AIKO MESSAGE QUEUE
SQLite-based message queue for inter-process communication
Replaces direct HTTP calls between bots and Neural Hub
"""

import sqlite3
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger("MessageQueue")


class MessageQueue:
    """
    Persistent SQLite message queue for Discord/Telegram bots and Neural Hub.

    Features:
    - Persistent storage across process restarts
    - Priority queue support
    - Automatic message expiration
    - Batch operations for performance
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = Path(__file__).parent.parent / "data"
            base_dir.mkdir(exist_ok=True)
            db_path = base_dir / "aiko_queue.db"

        self.db_path = str(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Main message queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                created_at REAL DEFAULT (unixepoch()),
                expires_at REAL,
                processed_at REAL,
                processed_by TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_time ON messages (queue_name, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires ON messages (expires_at)")

        # Events table for pub/sub
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL DEFAULT (unixepoch())
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_time ON events (channel, created_at)")

        # Process registry for monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processes (
                name TEXT PRIMARY KEY,
                pid INTEGER,
                status TEXT DEFAULT 'starting',
                started_at REAL DEFAULT (unixepoch()),
                last_heartbeat REAL DEFAULT (unixepoch()),
                restart_count INTEGER DEFAULT 0
            )
        """)

        conn.commit()

    def enqueue(self, queue_name: str, payload: dict, priority: int = 5,
                ttl_seconds: int = 300) -> int:
        """
        Add message to queue.

        Args:
            queue_name: Queue identifier (e.g., 'discord_in', 'telegram_in', 'hub_out')
            payload: Message data
            priority: 1-10 (lower is higher priority)
            ttl_seconds: Time to live before message expires
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        expires_at = time.time() + ttl_seconds if ttl_seconds else None

        cursor.execute(
            "INSERT INTO messages (queue_name, payload, priority, expires_at) VALUES (?, ?, ?, ?)",
            (queue_name, json.dumps(payload), priority, expires_at)
        )
        conn.commit()

        return cursor.lastrowid

    def dequeue(self, queue_name: str, processor_id: str = None,
                batch_size: int = 1, timeout: float = 0) -> List[Dict]:
        """
        Get messages from queue (non-blocking).

        Args:
            queue_name: Queue to read from
            processor_id: Identifier for this processor
            batch_size: Number of messages to fetch
            timeout: Not used (for API compatibility)

        Returns:
            List of message dicts with 'id', 'payload', 'created_at'
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        now = time.time()

        # Get highest priority, oldest messages
        cursor.execute("""
            SELECT id, payload, created_at, retry_count FROM messages
            WHERE queue_name = ? AND processed_at IS NULL
            AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY priority ASC, created_at ASC
            LIMIT ?
        """, (queue_name, now, batch_size))

        rows = cursor.fetchall()
        if not rows:
            return []

        messages = []
        for row in rows:
            # Mark as processed
            cursor.execute(
                "UPDATE messages SET processed_at = ?, processed_by = ?, retry_count = retry_count + 1 WHERE id = ?",
                (now, processor_id, row['id'])
            )

            try:
                payload = json.loads(row['payload'])
            except json.JSONDecodeError:
                payload = {"raw": row['payload']}

            messages.append({
                'id': row['id'],
                'payload': payload,
                'created_at': row['created_at'],
                'retry_count': row['retry_count']
            })

        conn.commit()
        return messages

    def dequeue_one(self, queue_name: str, processor_id: str = None) -> Optional[Dict]:
        """Get single message from queue."""
        messages = self.dequeue(queue_name, processor_id, batch_size=1)
        return messages[0] if messages else None

    def peek(self, queue_name: str, limit: int = 10) -> List[Dict]:
        """Preview messages without marking as processed."""
        conn = self._get_conn()
        cursor = conn.cursor()
        now = time.time()

        cursor.execute("""
            SELECT id, payload, created_at FROM messages
            WHERE queue_name = ? AND processed_at IS NULL
            AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY priority ASC, created_at ASC
            LIMIT ?
        """, (queue_name, now, limit))

        return [{
            'id': row['id'],
            'payload': json.loads(row['payload']),
            'created_at': row['created_at']
        } for row in cursor.fetchall()]

    def acknowledge(self, message_id: int):
        """Permanently delete processed message."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        conn.commit()

    def requeue(self, message_id: int, delay_seconds: int = 5):
        """Reset message for retry."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET processed_at = NULL, processed_by = NULL WHERE id = ?",
            (message_id,)
        )
        conn.commit()

    def get_queue_stats(self, queue_name: str = None) -> Dict:
        """Get queue statistics."""
        conn = self._get_conn()
        cursor = conn.cursor()
        now = time.time()

        if queue_name:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN processed_at IS NULL AND (expires_at IS NULL OR expires_at > ?) THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN processed_at IS NOT NULL THEN 1 ELSE 0 END) as processing,
                    SUM(CASE WHEN expires_at IS NOT NULL AND expires_at <= ? THEN 1 ELSE 0 END) as expired
                FROM messages WHERE queue_name = ?
            """, (now, now, queue_name))
            row = cursor.fetchone()
            return {
                'queue': queue_name,
                'total': row['total'] or 0,
                'pending': row['pending'] or 0,
                'processing': row['processing'] or 0,
                'expired': row['expired'] or 0
            }
        else:
            cursor.execute("""
                SELECT queue_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN processed_at IS NULL AND (expires_at IS NULL OR expires_at > ?) THEN 1 ELSE 0 END) as pending
                FROM messages GROUP BY queue_name
            """, (now,))
            return {row['queue_name']: {'total': row['total'], 'pending': row['pending']}
                    for row in cursor.fetchall()}

    # === Process Monitoring ===

    def register_process(self, name: str, pid: int):
        """Register a process for monitoring."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processes (name, pid, status, started_at, last_heartbeat)
            VALUES (?, ?, 'running', unixepoch(), unixepoch())
            ON CONFLICT(name) DO UPDATE SET
                pid = excluded.pid,
                status = 'running',
                started_at = unixepoch(),
                last_heartbeat = unixepoch(),
                restart_count = processes.restart_count + 1
        """, (name, pid))
        conn.commit()

    def heartbeat(self, name: str):
        """Update process heartbeat."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE processes SET last_heartbeat = unixepoch() WHERE name = ?",
            (name,)
        )
        conn.commit()

    def get_process_status(self, name: str = None) -> Dict:
        """Get process status. Returns dict of process statuses."""
        conn = self._get_conn()
        cursor = conn.cursor()
        now = time.time()

        if name:
            cursor.execute(
                "SELECT * FROM processes WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                return {}
            return {
                'name': row['name'],
                'pid': row['pid'],
                'status': row['status'],
                'started_at': row['started_at'],
                'last_heartbeat': row['last_heartbeat'],
                'restart_count': row['restart_count'],
                'is_alive': (now - row['last_heartbeat']) < 30 if row['last_heartbeat'] else False
            }
        else:
            cursor.execute("SELECT * FROM processes")
            return {
                row['name']: {
                    'pid': row['pid'],
                    'status': row['status'],
                    'is_alive': (now - row['last_heartbeat']) < 30 if row['last_heartbeat'] else False,
                    'restart_count': row['restart_count']
                }
                for row in cursor.fetchall()
            }

    def mark_process_dead(self, name: str):
        """Mark process as crashed/stopped."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE processes SET status = 'crashed' WHERE name = ?",
            (name,)
        )
        conn.commit()

    # === Pub/Sub Events ===

    def publish_event(self, channel: str, event_type: str, payload: dict):
        """Publish event to channel."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (channel, event_type, payload) VALUES (?, ?, ?)",
            (channel, event_type, json.dumps(payload))
        )
        conn.commit()

    def get_events(self, channel: str, since: float = None, limit: int = 100) -> List[Dict]:
        """Get events from channel."""
        conn = self._get_conn()
        cursor = conn.cursor()

        if since:
            cursor.execute(
                "SELECT * FROM events WHERE channel = ? AND created_at > ? ORDER BY created_at ASC LIMIT ?",
                (channel, since, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM events WHERE channel = ? ORDER BY created_at DESC LIMIT ?",
                (channel, limit)
            )

        return [{
            'id': row['id'],
            'type': row['event_type'],
            'payload': json.loads(row['payload']),
            'created_at': row['created_at']
        } for row in cursor.fetchall()]

    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old processed messages and events."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cutoff = time.time() - (max_age_hours * 3600)

        cursor.execute("DELETE FROM messages WHERE processed_at IS NOT NULL AND processed_at < ?", (cutoff,))
        cursor.execute("DELETE FROM events WHERE created_at < ?", (cutoff,))

        deleted_messages = cursor.rowcount
        conn.commit()

        logger.info(f"[Queue] Cleaned up {deleted_messages} old messages")
        return deleted_messages


# Global queue instance
_message_queue = None

def get_queue(db_path: str = None) -> MessageQueue:
    """Get global message queue instance."""
    global _message_queue
    if _message_queue is None:
        _message_queue = MessageQueue(db_path)
    return _message_queue


# === Convenience functions for bots ===

def send_to_hub(source: str, user_id: str, message: str, metadata: dict = None) -> int:
    """
    Send message from bot to Neural Hub.

    Args:
        source: 'discord' or 'telegram'
        user_id: User identifier
        message: Message content
        metadata: Additional data
    """
    queue = get_queue()
    payload = {
        'source': source,
        'user_id': user_id,
        'message': message,
        'metadata': metadata or {},
        'timestamp': time.time()
    }
    return queue.enqueue(f'{source}_in', payload, priority=3)


def get_response_for_user(source: str, user_id: str, timeout: float = 30) -> Optional[str]:
    """
    Get response from Hub for specific user.
    This is a polling function - use sparingly.
    """
    queue = get_queue()
    messages = queue.peek(f'{source}_out')

    for msg in messages:
        if msg['payload'].get('user_id') == user_id:
            queue.acknowledge(msg['id'])
            return msg['payload'].get('response')

    return None


def send_response(source: str, user_id: str, response: str, emotion: str = "neutral"):
    """Send response from Hub back to bot."""
    queue = get_queue()
    payload = {
        'source': source,
        'user_id': user_id,
        'response': response,
        'emotion': emotion,
        'timestamp': time.time()
    }
    return queue.enqueue(f'{source}_out', payload, priority=3)


if __name__ == "__main__":
    # Test the queue
    q = MessageQueue()

    # Test basic queue
    msg_id = q.enqueue("test_queue", {"hello": "world"}, priority=1)
    print(f"Enqueued message: {msg_id}")

    msg = q.dequeue_one("test_queue", processor_id="test")
    print(f"Dequeued: {msg}")

    q.acknowledge(msg['id'])
    print("Acknowledged")

    # Test process monitoring
    q.register_process("test_process", 12345)
    print(f"Process status: {q.get_process_status('test_process')}")

    print(f"Queue stats: {q.get_queue_stats()}")

    print("\n✅ Message Queue tests passed!")
