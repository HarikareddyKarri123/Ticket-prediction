"""
SQLite database layer for ProvenTech AI Ticket Portal.

Tables:
    User   — id, name, email (unique), password_hash, created_at
    Ticket — id, user_id (FK), title, description, predicted_priority,
             predicted_category, predicted_department, deadline,
             status, created_at
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def _get_connection() -> sqlite3.Connection:
    """Return a new connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = _get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS User (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'Employee',
                created_at    TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Ticket (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id              INTEGER NOT NULL,
                title                TEXT    NOT NULL,
                description          TEXT    NOT NULL,
                predicted_priority   TEXT,
                predicted_category   TEXT,
                predicted_department TEXT,
                assigned_department  TEXT,
                deadline             TEXT,
                status               TEXT    NOT NULL DEFAULT 'Open',
                created_at           TEXT    NOT NULL,
                FOREIGN KEY (user_id) REFERENCES User(id)
            );
            """
        )
        conn.commit()

        # Run dynamic schema migrations for existing databases
        try:
            conn.execute("ALTER TABLE User ADD COLUMN role TEXT NOT NULL DEFAULT 'Employee'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE Ticket ADD COLUMN assigned_department TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    finally:
        conn.close()


# ── User helpers ──────────────────────────────────────────────────────────────

def create_user(name: str, email: str, password: str, role: str = "Employee") -> dict[str, Any] | None:
    """
    Create a new user with a hashed password.

    Returns the user dict on success, or None if the email already exists.
    """
    hashed = generate_password_hash(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO User (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email.lower().strip(), hashed, role, now),
        )
        conn.commit()
        user = conn.execute(
            "SELECT id, name, email, role, created_at FROM User WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        # Duplicate email
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """
    Verify credentials.

    Returns user dict (id, name, email, role, created_at) on success, or None.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, email, password_hash, role, created_at FROM User WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            return {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "role": row["role"],
                "created_at": row["created_at"]
            }
        return None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    """Fetch a single user by primary key."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, email, role, created_at FROM User WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Ticket helpers ────────────────────────────────────────────────────────────

def save_ticket(
    user_id: int,
    title: str,
    description: str,
    priority: str,
    category: str,
    department: str,
    deadline: str | None,
) -> dict[str, Any]:
    """Insert a new ticket and return its full dict."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO Ticket
                (user_id, title, description, predicted_priority,
                 predicted_category, predicted_department, assigned_department, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
            """,
            (user_id, title, description, priority, category, department, department, deadline or "—", now),
        )
        conn.commit()
        ticket_id = cur.lastrowid
        row = conn.execute("SELECT * FROM Ticket WHERE id = ?", (ticket_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_user_tickets(user_id: int) -> list[dict[str, Any]]:
    """Return all tickets for a user, newest first."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM Ticket WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_department_tickets(department: str) -> list[dict[str, Any]]:
    """Return all tickets assigned to a specific department, newest first."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM Ticket WHERE assigned_department = ? ORDER BY created_at DESC",
            (department,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_user_ticket_stats(user_id: int) -> dict[str, int]:
    """Return KPI counts for a user's tickets."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT predicted_priority, status FROM Ticket WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        total = len(rows)
        open_count = sum(1 for r in rows if r["status"] == "Open")
        high_count = sum(1 for r in rows if r["predicted_priority"] == "High")
        resolved = sum(1 for r in rows if r["status"] == "Resolved")
        return {"total": total, "open": open_count, "high": high_count, "resolved": resolved}
    finally:
        conn.close()


def update_ticket_status(ticket_id: int, status: str) -> bool:
    """Update status of a ticket."""
    conn = _get_connection()
    try:
        conn.execute("UPDATE Ticket SET status = ? WHERE id = ?", (status, ticket_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

