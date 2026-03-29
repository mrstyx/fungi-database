#!/usr/bin/env bash
# run_pipeline.sh
# ===============
# Master pipeline script for the mycoCSV data analysis and import workflow.
#
# Runs scripts in order:
#   1. analyze_myco_csv.py    – data quality report
#   2. cleanse_myco_data.py   – data cleansing and transformation
#   3. generate_import_sql.py – SQL INSERT statements
#   4. import_to_mariadb.py   – database import (only with --import flag)
#
# Usage:
#   bash scripts/run_pipeline.sh            # analyse, cleanse, generate SQL
#   bash scripts/run_pipeline.sh --import   # also import into MariaDB

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-python3}"

RUN_IMPORT=false
for arg in "$@"; do
    if [[ "$arg" == "--import" ]]; then
        RUN_IMPORT=true
    fi
done

log() {
    echo ""
    echo "============================================================"
    echo "  $*"
    echo "============================================================"
}

cd "$REPO_ROOT"

# ---------------------------------------------------------------------------
# Step 1 – Analyse
# ---------------------------------------------------------------------------
log "Step 1/4 – Analysing mycoCSV.csv …"
$PYTHON scripts/analyze_myco_csv.py

# ---------------------------------------------------------------------------
# Step 2 – Cleanse
# ---------------------------------------------------------------------------
log "Step 2/4 – Cleansing data …"
$PYTHON scripts/cleanse_myco_data.py

# ---------------------------------------------------------------------------
# Step 3 – Generate SQL
# ---------------------------------------------------------------------------
log "Step 3/4 – Generating SQL import file …"
$PYTHON scripts/generate_import_sql.py

# ---------------------------------------------------------------------------
# Step 4 – Import (optional)
# ---------------------------------------------------------------------------
if $RUN_IMPORT; then
    log "Step 4/4 – Importing into MariaDB …"
    $PYTHON scripts/import_to_mariadb.py --execute
else
    log "Step 4/4 – Skipped (pass --import to enable database import)"
    echo "  To preview the import run:"
    echo "    $PYTHON scripts/import_to_mariadb.py"
    echo "  To execute the import run:"
    echo "    $PYTHON scripts/import_to_mariadb.py --execute"
fi

log "Pipeline complete."
echo "  Output files are in: $REPO_ROOT/data/processed/"
