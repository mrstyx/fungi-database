"""
import_spreadsheet.py
=====================
Imports data from an Excel or CSV spreadsheet into the fungi MariaDB database.

The script connects to the same MariaDB instance used by the Flask web app.
Ensure MariaDB is running (e.g. via ``docker compose up -d``) before importing.

Connection is configured via environment variables:

    DB_HOST      MariaDB host         (default: localhost)
    DB_PORT      MariaDB port         (default: 3306)
    DB_USER      MariaDB user         (default: fungi)
    DB_PASSWORD  MariaDB password     (default: empty string)
    DB_NAME      MariaDB database     (default: fungi_db)

Usage examples:
    # Basic import into the fungi table
    python scripts/import_spreadsheet.py data/raw/fungi.xlsx

    # Specify a sheet name
    python scripts/import_spreadsheet.py data/raw/mydata.xlsx \\
        --sheet-name Sheet1

    # Preview data without writing to the database
    python scripts/import_spreadsheet.py data/raw/fungi.csv --dry-run

Supported file formats: .xlsx, .xls, .csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import sqlalchemy

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# MariaDB connection settings (mirrors app.py)
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "fungi")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "fungi_db")

# Target table and required / optional columns (matches the fungi table in app.py)
TARGET_TABLE = "fungi"
REQUIRED_COLUMNS: list[str] = ["scientific_name"]
OPTIONAL_COLUMNS: list[str] = [
    "common_name",
    "family",
    "habitat",
    "edibility",
    "description",
    "notes",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Import spreadsheet data into the fungi MariaDB database.",
        epilog=(
            "Examples:\n"
            "  python scripts/import_spreadsheet.py data/raw/fungi.xlsx\n"
            "  python scripts/import_spreadsheet.py data/raw/fungi.csv --dry-run\n"
            "  python scripts/import_spreadsheet.py data/raw/mydata.xlsx "
            "--sheet-name Sheet1"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the spreadsheet file (.xlsx, .xls, or .csv).",
    )
    parser.add_argument(
        "--sheet-name",
        default=0,
        help="Sheet name or index for Excel files (default: first sheet).",
    )
    parser.add_argument(
        "--table-name",
        default=TARGET_TABLE,
        help=(
            f"Target database table name (default: '{TARGET_TABLE}')."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the data without writing to the database.",
    )
    return parser.parse_args()


def read_spreadsheet(file_path: Path, sheet_name) -> pd.DataFrame:
    """Read an Excel or CSV file and return a DataFrame."""
    suffix = file_path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    elif suffix == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise ValueError(
            f"Unsupported file format '{suffix}'. Use .xlsx, .xls, or .csv."
        )
    return df


def validate_columns(df: pd.DataFrame) -> None:
    """Check that required columns are present in the DataFrame."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "Required column(s) missing from spreadsheet: "
            + ", ".join(missing)
        )


def import_data(df: pd.DataFrame, table_name: str) -> None:
    """Write the DataFrame to the MariaDB database table."""
    connection_url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    try:
        engine = sqlalchemy.create_engine(connection_url)
        with engine.begin() as conn:
            df.to_sql(
                table_name,
                con=conn,
                if_exists="append",  # append rows; never overwrite the table
                index=False,
            )
    except Exception as exc:
        raise ConnectionError(
            f"Could not connect to MariaDB at {DB_HOST}:{DB_PORT}/{DB_NAME}. "
            "Ensure MariaDB is running (e.g. 'docker compose up -d') and "
            "that the DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME "
            f"environment variables are set correctly.\nDetail: {exc}"
        ) from exc
    print(f"Successfully imported {len(df)} rows into '{table_name}'.")


def main() -> None:
    """Entry point."""
    args = parse_args()

    # Resolve the file path
    file_path: Path = args.file
    if not file_path.is_absolute():
        file_path = REPO_ROOT / file_path
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    table_name: str = args.table_name
    print(f"Source file : {file_path}")
    print(f"Target table: {table_name}")
    print(f"Database    : {DB_HOST}:{DB_PORT}/{DB_NAME}")

    # Read the spreadsheet
    try:
        df = read_spreadsheet(file_path, sheet_name=args.sheet_name)
    except Exception as exc:
        print(f"Error reading spreadsheet: {exc}")
        sys.exit(1)

    print(f"Rows read   : {len(df)}")
    print(f"Columns     : {list(df.columns)}")
    print("\nData preview (first 5 rows):")
    print(df.head().to_string(index=False))
    print()

    # Validate required columns
    try:
        validate_columns(df)
    except ValueError as exc:
        print(f"Validation error: {exc}")
        sys.exit(1)

    if args.dry_run:
        print("Dry-run mode – no data written to the database.")
        return

    # Import into the database
    try:
        import_data(df, table_name)
    except Exception as exc:
        print(f"Import error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
