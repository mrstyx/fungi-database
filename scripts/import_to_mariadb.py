"""
import_to_mariadb.py
====================
Imports ``data/processed/myco_cleaned.csv`` into the MariaDB fungi database.

Connection is configured via environment variables:

    DB_HOST      MariaDB host         (default: localhost)
    DB_PORT      MariaDB port         (default: 3306)
    DB_USER      MariaDB user         (default: fungi)
    DB_PASSWORD  MariaDB password     (default: empty string)
    DB_NAME      MariaDB database     (default: fungi_db)

Usage::

    # Preview mode (default) – show first 10 records, no DB writes
    python scripts/import_to_mariadb.py

    # Execute mode – actually import into the database
    python scripts/import_to_mariadb.py --execute

    # Use a custom cleaned CSV
    python scripts/import_to_mariadb.py --input data/processed/myco_cleaned.csv

Output
------
* ``data/processed/import_log.txt``
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "myco_cleaned.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
LOG_FILE = PROCESSED_DIR / "import_log.txt"

# ---------------------------------------------------------------------------
# Environment / connection defaults
# ---------------------------------------------------------------------------
load_dotenv(REPO_ROOT / ".env")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "fungi")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "fungi_db")

BATCH_SIZE = 50

INSERT_SQL = """
    INSERT INTO fungi
        (scientific_name, common_name, family, habitat, edibility, description, notes)
    VALUES
        (%(scientific_name)s, %(common_name)s, %(family)s, %(habitat)s,
         %(edibility)s, %(description)s, %(notes)s)
"""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("import_to_mariadb")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8", mode="w")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import myco_cleaned.csv into the MariaDB fungi database.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to cleaned CSV (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write records to the database (default: preview only).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_cleaned_csv(path: Path) -> pd.DataFrame:
    """Load the cleaned CSV and replace NaN with None (NULL in SQL)."""
    df = pd.read_csv(path, dtype=str, keep_default_na=True)
    # Convert pandas NA to Python None for pymysql
    df = df.where(pd.notnull(df), other=None)
    return df


def preview(df: pd.DataFrame, logger: logging.Logger) -> None:
    """Print the first 10 records that would be imported."""
    logger.info("PREVIEW MODE – no data will be written to the database.")
    logger.info(f"Total records ready for import: {len(df)}")
    logger.info("")
    logger.info("First 10 records:")
    preview_df = df.head(10)
    for i, row in preview_df.iterrows():
        logger.info(
            f"  [{i + 1:>3}] scientific_name={row.get('scientific_name')!r}  "
            f"common_name={row.get('common_name')!r}  "
            f"family={row.get('family')!r}  "
            f"edibility={row.get('edibility')!r}"
        )
    logger.info("")
    logger.info("Run with --execute to perform the actual import.")


def execute_import(df: pd.DataFrame, logger: logging.Logger) -> None:
    """Insert all records into MariaDB in batches."""
    logger.info("EXECUTE MODE – connecting to MariaDB …")
    logger.info(f"  Host    : {DB_HOST}:{DB_PORT}")
    logger.info(f"  Database: {DB_NAME}")
    logger.info(f"  User    : {DB_USER}")

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            autocommit=False,
        )
    except pymysql.Error as exc:
        logger.error(f"Cannot connect to MariaDB: {exc}")
        logger.error(
            "Ensure MariaDB is running (e.g. 'docker compose up -d') and "
            "DB_HOST / DB_USER / DB_PASSWORD / DB_NAME are set correctly."
        )
        sys.exit(1)

    total = len(df)
    inserted = 0
    skipped = 0

    try:
        with conn.cursor() as cursor:
            batch: list[dict] = []
            for _, row in df.iterrows():
                batch.append(row.to_dict())
                if len(batch) >= BATCH_SIZE:
                    batch_inserted = _flush_batch(cursor, batch, logger)
                    inserted += batch_inserted
                    skipped += len(batch) - batch_inserted
                    batch = []
                    logger.info(f"  Progress: {inserted}/{total} records inserted.")

            if batch:
                batch_inserted = _flush_batch(cursor, batch, logger)
                inserted += batch_inserted
                skipped += len(batch) - batch_inserted

        conn.commit()
        logger.info(
            f"Import complete: {inserted}/{total} records inserted"
            + (f", {skipped} skipped." if skipped else ".")
        )
    except Exception as exc:
        conn.rollback()
        logger.error(f"Unexpected error – transaction rolled back: {exc}")
        sys.exit(1)
    finally:
        conn.close()


def _flush_batch(cursor, batch: list[dict], logger: logging.Logger) -> int:
    """Execute a batch INSERT; return number of rows successfully inserted."""
    count = 0
    for record in batch:
        try:
            cursor.execute(INSERT_SQL, record)
            count += 1
        except pymysql.Error as exc:
            logger.warning(
                f"  [SKIP] Could not insert record "
                f"scientific_name={record.get('scientific_name')!r}: {exc}"
            )
    return count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    input_path: Path = args.input
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path

    logger = setup_logging(LOG_FILE)
    logger.info(f"Input file : {input_path}")

    if not input_path.exists():
        logger.error(
            f"Cleaned CSV not found: {input_path}\n"
            "Run cleanse_myco_data.py first."
        )
        sys.exit(1)

    df = load_cleaned_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path.name}")

    if args.execute:
        execute_import(df, logger)
    else:
        preview(df, logger)

    logger.info(f"Log written to {LOG_FILE}")


if __name__ == "__main__":
    main()
