"""
cleanse_myco_data.py
====================
Reads ``data/raw/mycoCSV.csv``, applies all data-cleansing and mapping rules,
and writes:

* ``data/processed/myco_cleaned.csv``  – import-ready CSV
* ``data/processed/cleansing_log.txt`` – full transformation log

Column mappings (CSV → fungi table)
------------------------------------
scientific_name  : "Identification" → "Binomial" → "First Pass ID" + " sp."
common_name      : "Identification Per FDA Label" → "Name of Product"
family           : "First Pass ID"
habitat          : "Country of Origin" + "Product Type"
edibility        : always 'unknown' (no source data)
description      : "Brand" + "Manufacturer/Distributor" + "Preservation Method"
notes            : "Comments" + "GenBank#" + "Seq. Status" + "Multiple species?"

Usage::

    python scripts/cleanse_myco_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
RAW_CSV = REPO_ROOT / "data" / "raw" / "mycoCSV.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
CLEANED_CSV = PROCESSED_DIR / "myco_cleaned.csv"
LOG_FILE = PROCESSED_DIR / "cleansing_log.txt"

# MariaDB VARCHAR(255) limit
VARCHAR_LIMIT = 255

# Values treated as missing
NULL_LIKE: set[str] = {"", "not provided", "unknown", "n/a", "none"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_empty(value: object) -> bool:
    """Return True when *value* is blank or a known placeholder."""
    return str(value).strip().lower() in NULL_LIKE


def coalesce(*values: object) -> str:
    """Return the first non-empty value, or empty string."""
    for v in values:
        if not is_empty(v):
            return str(v).strip()
    return ""


def truncate(text: str, limit: int = VARCHAR_LIMIT, log_lines: list[str] | None = None,
             field: str = "", row_idx: int = 0) -> str:
    """Truncate *text* to *limit* characters, logging a warning if needed."""
    if len(text) > limit:
        truncated = text[:limit]
        if log_lines is not None:
            log_lines.append(
                f"  [WARNING] Row {row_idx}: field '{field}' truncated from "
                f"{len(text)} to {limit} chars."
            )
        return truncated
    return text


# ---------------------------------------------------------------------------
# Field mappers
# ---------------------------------------------------------------------------

def map_scientific_name(row: pd.Series, idx: int, log: list[str]) -> str:
    """Derive scientific_name with three-level fallback."""
    identification = row.get("Identification", "")
    binomial = row.get("Binomial", "")
    first_pass = row.get("First Pass ID", "")

    if not is_empty(identification):
        name = str(identification).strip()
        source = "Identification"
    elif not is_empty(binomial):
        name = str(binomial).strip()
        source = "Binomial"
    elif not is_empty(first_pass):
        name = str(first_pass).strip() + " sp."
        source = "First Pass ID (+ sp.)"
    else:
        log.append(
            f"  [SKIP] Row {idx}: no scientific_name derivable – record excluded."
        )
        return ""

    log.append(f"  [MAP] Row {idx}: scientific_name={name!r}  (from {source})")
    return truncate(name, log_lines=log, field="scientific_name", row_idx=idx)


def map_common_name(row: pd.Series, idx: int, log: list[str]) -> str:
    fda_label = row.get("Identification Per FDA Label", "")
    product_name = row.get("Name of Product", "")
    name = coalesce(fda_label, product_name)
    if name:
        return truncate(name, log_lines=log, field="common_name", row_idx=idx)
    return ""


def map_family(row: pd.Series) -> str:
    first_pass = row.get("First Pass ID", "")
    if is_empty(first_pass):
        return ""
    return truncate(str(first_pass).strip())


def map_habitat(row: pd.Series, idx: int, log: list[str]) -> str:
    origin = row.get("Country of Origin", "")
    product_type = row.get("Product Type", "")
    parts: list[str] = []
    if not is_empty(origin):
        parts.append(f"Country of origin: {origin.strip()}")
    if not is_empty(product_type):
        parts.append(f"Product type: {product_type.strip()}")
    return "; ".join(parts)


def map_description(row: pd.Series, idx: int, log: list[str]) -> str:
    brand = row.get("Brand", "")
    manufacturer = row.get("Manufacturer/Distributor", "")
    preservation = row.get("Preservation Method", "")
    parts: list[str] = []
    if not is_empty(brand):
        parts.append(f"Brand: {brand.strip()}")
    if not is_empty(manufacturer):
        parts.append(f"Manufacturer/Distributor: {manufacturer.strip()}")
    if not is_empty(preservation):
        parts.append(f"Preservation method: {preservation.strip()}")
    return "; ".join(parts)


def map_notes(row: pd.Series, idx: int, log: list[str]) -> str:
    comments = row.get("Comments", "")
    genbank = row.get("GenBank#", "")
    seq_status = row.get("Seq. Status", "")
    multiple = row.get("Multiple species?", "")

    parts: list[str] = []
    if not is_empty(comments):
        parts.append(str(comments).strip())
    if not is_empty(genbank):
        parts.append(f"GenBank#: {genbank.strip()}")
    if not is_empty(seq_status):
        label = "DNA sequencing status"
        if str(seq_status).strip() == "Failed":
            label = "DNA sequencing FAILED"
        parts.append(f"{label}: {seq_status.strip()}")
    if str(multiple).strip().upper() == "Y":
        parts.append("Note: product contains multiple species")

    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Main cleansing logic
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    # pandas renames blank headers to "Unnamed: N" – drop all such columns
    unnamed = [c for c in df.columns if str(c).strip() == "" or str(c).startswith("Unnamed:")]
    if unnamed:
        df = df.drop(columns=unnamed)
    return df


def cleanse(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Apply all transformations; return (cleaned_df, log_lines)."""
    log: list[str] = [
        "CLEANSING LOG – mycoCSV.csv",
        f"Input records : {len(df)}",
        "",
    ]

    records: list[dict] = []
    skipped = 0

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # +2: 1-based + header row

        sci_name = map_scientific_name(row, row_num, log)
        if not sci_name:
            skipped += 1
            continue

        common = map_common_name(row, row_num, log)
        family = map_family(row)
        habitat = map_habitat(row, row_num, log)
        description = map_description(row, row_num, log)
        notes = map_notes(row, row_num, log)

        records.append(
            {
                "scientific_name": sci_name,
                "common_name": common or None,
                "family": family or None,
                "habitat": habitat or None,
                "edibility": "unknown",
                "description": description or None,
                "notes": notes or None,
            }
        )

    log.append("")
    log.append(f"Records processed : {len(df)}")
    log.append(f"Records skipped   : {skipped}  (missing all name fields)")
    log.append(f"Records cleaned   : {len(records)}")
    log.append(
        f"Success rate      : "
        f"{round(100 * len(records) / len(df), 1)}%  "
        f"({len(records)} / {len(df)})"
    )

    cleaned_df = pd.DataFrame(records)
    return cleaned_df, log


def main() -> None:
    if not RAW_CSV.exists():
        print(f"Error: CSV not found: {RAW_CSV}")
        sys.exit(1)

    print(f"Loading {RAW_CSV} …")
    df = load_csv(RAW_CSV)
    print(f"Loaded {len(df)} records.")

    cleaned_df, log_lines = cleanse(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_df.to_csv(CLEANED_CSV, index=False, encoding="utf-8")
    print(f"Cleaned CSV  → {CLEANED_CSV}  ({len(cleaned_df)} records)")

    LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"Cleansing log → {LOG_FILE}")


if __name__ == "__main__":
    main()
