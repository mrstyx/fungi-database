"""
generate_import_sql.py
======================
Reads ``data/processed/myco_cleaned.csv`` and writes a self-contained SQL
script of INSERT statements to ``data/processed/import_statements.sql``.

The generated file can be executed directly with the MariaDB client::

    mysql -u fungi -p fungi_db < data/processed/import_statements.sql

Usage::

    python scripts/generate_import_sql.py

Output
------
* ``data/processed/import_statements.sql``
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
CLEANED_CSV = REPO_ROOT / "data" / "processed" / "myco_cleaned.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
SQL_FILE = PROCESSED_DIR / "import_statements.sql"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sql_escape(value: object) -> str:
    """Return a SQL-safe representation of *value*.

    NULL is produced for None / NaN / empty strings; otherwise the value is
    single-quoted with internal single-quotes doubled.
    """
    if value is None:
        return "NULL"
    text = str(value)
    if text.strip() == "" or text.lower() in ("nan", "none", "nat"):
        return "NULL"
    # Use quote-doubling (SQL standard) rather than backslash escaping
    escaped = text.replace("'", "''")
    return f"'{escaped}'"


# ---------------------------------------------------------------------------
# Generation logic
# ---------------------------------------------------------------------------

def load_cleaned_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=True)
    df = df.where(pd.notnull(df), other=None)
    return df


def generate_sql(df: pd.DataFrame) -> list[str]:
    """Return a list of SQL statement strings."""
    lines: list[str] = [
        "-- Fungi Database – Generated INSERT statements",
        f"-- Source: {CLEANED_CSV.name}",
        f"-- Records: {len(df)}",
        "--",
        "-- Execute with:",
        "--   mysql -u <user> -p <database> < data/processed/import_statements.sql",
        "",
        "SET NAMES utf8mb4;",
        "",
        "INSERT INTO fungi",
        "    (scientific_name, common_name, family, habitat, edibility, description, notes)",
        "VALUES",
    ]

    value_rows: list[str] = []
    for _, row in df.iterrows():
        parts = ", ".join(
            [
                sql_escape(row.get("scientific_name")),
                sql_escape(row.get("common_name")),
                sql_escape(row.get("family")),
                sql_escape(row.get("habitat")),
                sql_escape(row.get("edibility")),
                sql_escape(row.get("description")),
                sql_escape(row.get("notes")),
            ]
        )
        value_rows.append(f"    ({parts})")

    lines.append(",\n".join(value_rows) + ";")
    lines.append("")
    lines.append(f"-- {len(df)} row(s) inserted.")
    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not CLEANED_CSV.exists():
        print(f"Error: cleaned CSV not found: {CLEANED_CSV}")
        print("Run cleanse_myco_data.py first.")
        sys.exit(1)

    print(f"Loading {CLEANED_CSV} …")
    df = load_cleaned_csv(CLEANED_CSV)
    print(f"Loaded {len(df)} records.")

    sql_lines = generate_sql(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SQL_FILE.write_text("\n".join(sql_lines) + "\n", encoding="utf-8")
    print(f"SQL file written to {SQL_FILE}  ({len(df)} INSERT rows)")


if __name__ == "__main__":
    main()
