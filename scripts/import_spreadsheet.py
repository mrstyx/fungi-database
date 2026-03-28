"""
import_spreadsheet.py
=====================
Imports data from an Excel or CSV spreadsheet into the fungi SQLite database.

Usage examples:
    # Basic import – table name inferred from file name
    python scripts/import_spreadsheet.py data/raw/species.xlsx

    # Specify target table and sheet
    python scripts/import_spreadsheet.py data/raw/mydata.xlsx \\
        --table-name species --sheet-name Sheet1

    # Preview data without writing to the database
    python scripts/import_spreadsheet.py data/raw/species.csv --dry-run

Supported file formats: .xlsx, .xls, .csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import sqlalchemy

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "database" / "fungi.db"

# Required columns for each known table (empty set means no enforcement)
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "species": ["scientific_name"],
    "observations": ["species_id"],
    "locations": [],
    "characteristics": ["species_id"],
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Import spreadsheet data into the fungi SQLite database.",
        epilog=(
            "Examples:\n"
            "  python scripts/import_spreadsheet.py data/raw/species.xlsx\n"
            "  python scripts/import_spreadsheet.py data/raw/obs.csv "
            "--table-name observations\n"
            "  python scripts/import_spreadsheet.py data/raw/species.xlsx --dry-run"
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
        default=None,
        help=(
            "Target database table name. "
            "Defaults to the file stem (e.g. 'species' from 'species.xlsx')."
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


def validate_columns(df: pd.DataFrame, table_name: str) -> None:
    """Check that required columns are present in the DataFrame."""
    required = REQUIRED_COLUMNS.get(table_name, [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Required column(s) missing for table '{table_name}': "
            + ", ".join(missing)
        )


def import_data(df: pd.DataFrame, table_name: str) -> None:
    """Write the DataFrame to the SQLite database table."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Run 'python scripts/create_database.py' first."
        )

    engine = sqlalchemy.create_engine(f"sqlite:///{DB_PATH}")
    with engine.begin() as conn:
        df.to_sql(
            table_name,
            con=conn,
            if_exists="append",  # append rows; never overwrite the table
            index=False,
        )
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

    # Determine target table name
    table_name: str = args.table_name or file_path.stem.lower().replace("-", "_")
    print(f"Source file : {file_path}")
    print(f"Target table: {table_name}")

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
        validate_columns(df, table_name)
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
