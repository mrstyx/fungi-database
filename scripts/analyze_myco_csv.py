"""
analyze_myco_csv.py
===================
Reads ``data/raw/mycoCSV.csv`` and produces a comprehensive data-quality
report at ``data/processed/analysis_report.txt``.

Usage::

    python scripts/analyze_myco_csv.py

Output
------
* ``data/processed/analysis_report.txt``  – full quality report
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
RAW_CSV = REPO_ROOT / "data" / "raw" / "mycoCSV.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
REPORT_FILE = PROCESSED_DIR / "analysis_report.txt"

# Columns considered "empty" as well as truly blank
NULL_LIKE: set[str] = {"", "not provided", "unknown", "n/a", "none"}


def load_csv(path: Path) -> pd.DataFrame:
    """Load the CSV, dropping unnamed/empty header columns left over from Excel."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    # pandas renames blank headers to "Unnamed: N" – drop all such columns
    unnamed = [c for c in df.columns if str(c).strip() == "" or str(c).startswith("Unnamed:")]
    if unnamed:
        df = df.drop(columns=unnamed)
    return df


def is_empty(value: str) -> bool:
    """Return True when a value is blank or a known placeholder."""
    return str(value).strip().lower() in NULL_LIKE


def column_analysis(df: pd.DataFrame) -> list[dict]:
    """Return per-column statistics."""
    results = []
    for col in df.columns:
        series = df[col].astype(str)
        null_count = series.apply(is_empty).sum()
        unique_vals = series[~series.apply(is_empty)].nunique()
        top_values = (
            series[~series.apply(is_empty)]
            .value_counts()
            .head(5)
            .to_dict()
        )
        results.append(
            {
                "column": col,
                "total": len(series),
                "null_like": int(null_count),
                "filled": int(len(series) - null_count),
                "fill_pct": round(100 * (len(series) - null_count) / len(series), 1),
                "unique": int(unique_vals),
                "top_values": top_values,
            }
        )
    return results


def identification_analysis(df: pd.DataFrame) -> dict:
    """Analyse the three identification columns."""
    total = len(df)

    def count_filled(col: str) -> int:
        return int(df[col].astype(str).apply(lambda v: not is_empty(v)).sum())

    has_identification = count_filled("Identification")
    has_binomial = count_filled("Binomial")
    has_first_pass = count_filled("First Pass ID")

    # Records where ALL three are empty/unknown
    no_id = df[
        df["Identification"].apply(is_empty)
        & df["Binomial"].apply(is_empty)
        & df["First Pass ID"].apply(is_empty)
    ]

    seq_success = int((df["Seq. Status"].str.strip() == "Successful").sum())
    seq_failed = int((df["Seq. Status"].str.strip() == "Failed").sum())

    return {
        "total": total,
        "has_identification": has_identification,
        "has_binomial": has_binomial,
        "has_first_pass": has_first_pass,
        "no_id_at_all": len(no_id),
        "seq_successful": seq_success,
        "seq_failed": seq_failed,
    }


def duplicate_analysis(df: pd.DataFrame) -> dict:
    """Find potential duplicate records."""
    id_cols = ["Identification", "Binomial", "First Pass ID", "Brand", "Barcode"]
    available = [c for c in id_cols if c in df.columns]
    dup_mask = df.duplicated(subset=available, keep=False)
    dup_df = df[dup_mask]
    return {
        "duplicate_rows": int(dup_mask.sum()),
        "duplicate_groups": int(dup_df.groupby(available).ngroups) if not dup_df.empty else 0,
    }


def completeness(df: pd.DataFrame) -> dict:
    """Overall data completeness as a percentage."""
    total_cells = df.size
    filled_cells = int(
        df.apply(lambda col: col.astype(str).apply(lambda v: not is_empty(v))).sum().sum()
    )
    return {
        "total_cells": total_cells,
        "filled_cells": filled_cells,
        "completeness_pct": round(100 * filled_cells / total_cells, 1),
    }


def unimportable_records(df: pd.DataFrame) -> pd.DataFrame:
    """Return records that cannot be imported (scientific_name cannot be derived)."""
    return df[
        df["Identification"].apply(is_empty)
        & df["Binomial"].apply(is_empty)
        & df["First Pass ID"].apply(is_empty)
    ]


def write_report(
    df: pd.DataFrame,
    col_stats: list[dict],
    id_stats: dict,
    dup_stats: dict,
    comp_stats: dict,
    unimportable: pd.DataFrame,
    path: Path,
) -> None:
    """Write the full analysis report to *path*."""
    lines: list[str] = []

    def h1(title: str) -> None:
        lines.append("=" * 72)
        lines.append(f" {title}")
        lines.append("=" * 72)

    def h2(title: str) -> None:
        lines.append("")
        lines.append(f"--- {title} ---")

    lines.append("FUNGI DATABASE – mycoCSV.csv DATA QUALITY REPORT")
    lines.append(f"Generated from: {RAW_CSV}")
    lines.append("")

    # ---- Overview ----------------------------------------------------------
    h1("1. OVERVIEW")
    lines.append(f"Total records : {len(df)}")
    lines.append(f"Total columns : {len(df.columns)}")
    lines.append(f"Column names  : {list(df.columns)}")
    lines.append("")
    lines.append(f"Overall data completeness : {comp_stats['completeness_pct']}%")
    lines.append(
        f"  ({comp_stats['filled_cells']} / {comp_stats['total_cells']} cells filled)"
    )

    # ---- Column analysis ---------------------------------------------------
    h1("2. COLUMN-BY-COLUMN ANALYSIS")
    for s in col_stats:
        h2(s["column"])
        lines.append(f"  Filled      : {s['filled']} / {s['total']}  ({s['fill_pct']}%)")
        lines.append(f"  Null/Unknown: {s['null_like']}")
        lines.append(f"  Unique vals : {s['unique']}")
        if s["top_values"]:
            lines.append("  Top values  :")
            for val, cnt in s["top_values"].items():
                lines.append(f"    {cnt:>5}x  {val!r}")

    # ---- Identification analysis -------------------------------------------
    h1("3. IDENTIFICATION FIELD ANALYSIS")
    lines.append(f"Total records            : {id_stats['total']}")
    lines.append(f"Have 'Identification'    : {id_stats['has_identification']}")
    lines.append(f"Have 'Binomial'          : {id_stats['has_binomial']}")
    lines.append(f"Have 'First Pass ID'     : {id_stats['has_first_pass']}")
    lines.append(f"No ID at all             : {id_stats['no_id_at_all']}")
    lines.append("")
    lines.append(f"Seq. Status – Successful : {id_stats['seq_successful']}")
    lines.append(f"Seq. Status – Failed     : {id_stats['seq_failed']}")
    lines.append("")
    importable = id_stats["total"] - id_stats["no_id_at_all"]
    lines.append(
        f"Records importable (scientific_name derivable): {importable} "
        f"({round(100 * importable / id_stats['total'], 1)}%)"
    )

    # ---- Edibility ---------------------------------------------------------
    h1("4. EDIBILITY INFERENCE")
    lines.append(
        "The CSV contains no explicit edibility column. All records will be "
        "assigned the default value 'unknown' during import."
    )
    lines.append(
        "Product Type distribution (Food vs. Medicinal/Tea) is available and "
        "could inform downstream classification."
    )
    if "Product Type" in df.columns:
        pt = df["Product Type"].value_counts().to_dict()
        for k, v in pt.items():
            lines.append(f"  {v:>5}x  {k!r}")

    # ---- Duplicates --------------------------------------------------------
    h1("5. DUPLICATE DETECTION")
    lines.append(f"Duplicate rows (same key fields) : {dup_stats['duplicate_rows']}")
    lines.append(f"Duplicate groups                 : {dup_stats['duplicate_groups']}")

    # ---- Unimportable records ----------------------------------------------
    h1("6. RECORDS THAT CANNOT BE IMPORTED")
    lines.append(
        f"Records with no Identification, Binomial, OR First Pass ID: "
        f"{len(unimportable)}"
    )
    if not unimportable.empty:
        lines.append("")
        lines.append("Sample Location values for unimportable records:")
        for loc in unimportable.get("Sample Location", pd.Series(dtype=str)).tolist():
            lines.append(f"  - {loc}")

    # ---- Summary -----------------------------------------------------------
    h1("7. SUMMARY & RECOMMENDATIONS")
    lines.append("• At least one name field is available for the majority of records.")
    lines.append("• DNA sequencing ('Seq. Status') indicates ID reliability.")
    lines.append("• No explicit edibility data – use 'unknown' as default.")
    lines.append("• Check duplicate records before import to avoid redundancy.")
    lines.append(
        "• Run cleanse_myco_data.py to generate a cleaned CSV ready for import."
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not RAW_CSV.exists():
        print(f"Error: CSV file not found: {RAW_CSV}")
        sys.exit(1)

    print(f"Loading {RAW_CSV} …")
    df = load_csv(RAW_CSV)
    print(f"Loaded {len(df)} records with {len(df.columns)} columns.")

    col_stats = column_analysis(df)
    id_stats = identification_analysis(df)
    dup_stats = duplicate_analysis(df)
    comp_stats = completeness(df)
    unimportable = unimportable_records(df)

    write_report(df, col_stats, id_stats, dup_stats, comp_stats, unimportable, REPORT_FILE)
    print(f"Report written to {REPORT_FILE}")


if __name__ == "__main__":
    main()
