from contextlib import closing
from datetime import datetime
from pathlib import Path
import time
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parent / "ecopc.db"


def initialize_database():
    """Create the required tables without deleting existing data."""

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                presence INTEGER,
                cpu_usage REAL,
                memory_usage REAL,
                idle_seconds REAL,
                absence_seconds REAL,
                state TEXT NOT NULL,
                decision TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS energy_summary (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                timestamp TEXT NOT NULL,
                waste_seconds REAL NOT NULL,
                estimated_energy_wh REAL NOT NULL
            )
        """)


def pause_warning(seconds):
    """Store a single shared warning pause for Flask and the monitor."""
    until = time.time() + seconds
    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS warning_pause (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                expires_at REAL NOT NULL
            )
        """)
        connection.execute("""
            INSERT INTO warning_pause (id, expires_at) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET expires_at = excluded.expires_at
        """, (until,))
    return until


def get_warning_pause_until():
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'warning_pause'"
        ).fetchone()
        if table is None:
            return 0.0
        row = connection.execute(
            "SELECT expires_at FROM warning_pause WHERE id = 1"
        ).fetchone()
    return row[0] if row else 0.0


def save_log(
    presence,
    cpu_usage,
    memory_usage,
    idle_seconds,
    absence_seconds,
    state,
    decision,
):
    """Save one monitoring reading."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute("""
            INSERT INTO logs (
                timestamp,
                presence,
                cpu_usage,
                memory_usage,
                idle_seconds,
                absence_seconds,
                state,
                decision
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            presence,
            cpu_usage,
            memory_usage,
            idle_seconds,
            absence_seconds,
            state,
            decision,
        ))


def get_recent_logs(limit=10):
    """Return the newest monitoring readings first."""

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            "SELECT * FROM logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]


def save_event(event_type, message):
    """Save an important monitoring event."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute("""
            INSERT INTO events (
                timestamp,
                event_type,
                message
            )
            VALUES (?, ?, ?)
        """, (
            timestamp,
            event_type,
            message,
        ))


def get_recent_events(limit=10):
    """Return the newest events first."""

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]


def save_energy_summary(waste_seconds, estimated_energy_wh):
    """Save the latest energy estimate for the monitoring session."""

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute("""
            INSERT INTO energy_summary (
                id,
                timestamp,
                waste_seconds,
                estimated_energy_wh
            )
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                timestamp = excluded.timestamp,
                waste_seconds = excluded.waste_seconds,
                estimated_energy_wh = excluded.estimated_energy_wh
        """, (
            timestamp,
            waste_seconds,
            estimated_energy_wh,
        ))


def get_energy_summary():
    """Return the latest saved session estimate."""

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.row_factory = sqlite3.Row

        table_exists = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'energy_summary'
        """).fetchone()

        if table_exists is None:
            return None

        row = connection.execute(
            "SELECT * FROM energy_summary WHERE id = 1"
        ).fetchone()

        return dict(row) if row else None


if __name__ == "__main__":
    try:
        initialize_database()
        print("Database ready. Existing data preserved.")
    except sqlite3.Error as error:
        print(f"Database setup failed: {error}")
        raise SystemExit(1)