"""
create_database.py
==================
Creates the SQLite fungi database by executing the SQL schema file.

Usage:
    python scripts/create_database.py

The database is created at data/database/fungi.db relative to the
repository root.  Run this script once before importing any data.
"""

import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to the repository root, not the script location)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "database" / "fungi.db"
SCHEMA_PATH = REPO_ROOT / "schema" / "schema.sql"


def create_database() -> None:
    """Create the SQLite database and initialise all tables from schema.sql."""

    # Ensure the database directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read the SQL schema
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    print(f"Reading schema from: {SCHEMA_PATH}")
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    # Connect to (or create) the SQLite database
    print(f"Creating database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Enable foreign key enforcement for this connection
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Execute the full schema script
        conn.executescript(schema_sql)
        conn.commit()

        # Report which tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables created: {', '.join(tables)}")
        print("Database created successfully.")
    except sqlite3.Error as exc:
        print(f"Database error: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
