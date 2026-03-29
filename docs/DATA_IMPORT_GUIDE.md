# Data Import Guide

## Overview

This guide explains how to analyse the raw `mycoCSV.csv` data, cleanse it,
and import it into the MariaDB fungi database. The pipeline consists of four
Python scripts and one orchestrating Bash script.

```
data/raw/mycoCSV.csv
        │
        ▼
scripts/analyze_myco_csv.py   →  data/processed/analysis_report.txt
        │
        ▼
scripts/cleanse_myco_data.py  →  data/processed/myco_cleaned.csv
                              →  data/processed/cleansing_log.txt
        │
        ├──► scripts/generate_import_sql.py  →  data/processed/import_statements.sql
        │
        └──► scripts/import_to_mariadb.py    →  data/processed/import_log.txt
                                             →  MariaDB fungi table (--execute)
```

---

## Prerequisites

### Python packages

Install the required packages listed in `scripts/requirements.txt`:

```bash
pip install -r scripts/requirements.txt
```

The pipeline also requires `python-dotenv`:

```bash
pip install python-dotenv
```

Or install everything from the top-level `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Environment variables (database import only)

Create a `.env` file in the project root (a template is provided at
`.env.example`):

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=fungi
DB_PASSWORD=your_password
DB_NAME=fungi_db
```

> **Tip:** Start the MariaDB service before running the import scripts:
> ```bash
> docker compose up -d
> ```

---

## Running the Complete Pipeline

```bash
# Analyse + cleanse + generate SQL (no database write)
bash scripts/run_pipeline.sh

# Analyse + cleanse + generate SQL + import into MariaDB
bash scripts/run_pipeline.sh --import
```

---

## Running Individual Scripts

### 1. Analyse the raw CSV

```bash
python scripts/analyze_myco_csv.py
```

Reads `data/raw/mycoCSV.csv` and writes a comprehensive quality report to
`data/processed/analysis_report.txt`.

The report includes:

- Total record count and column list
- Per-column null counts, fill percentages, and top values
- Identification field analysis (how many records have a scientific name)
- DNA sequencing status distribution
- Duplicate detection
- Overall data completeness percentage
- List of records that cannot be imported (no name derivable)

---

### 2. Cleanse and transform the data

```bash
python scripts/cleanse_myco_data.py
```

Reads `data/raw/mycoCSV.csv`, applies all mapping and cleansing rules, and
writes:

- `data/processed/myco_cleaned.csv` – import-ready CSV
- `data/processed/cleansing_log.txt` – full transformation log

---

### 3. Generate SQL INSERT statements

```bash
python scripts/generate_import_sql.py
```

Reads `data/processed/myco_cleaned.csv` and writes a self-contained SQL
script to `data/processed/import_statements.sql`.

Execute it directly with the MariaDB client:

```bash
mysql -u fungi -p fungi_db < data/processed/import_statements.sql
```

---

### 4. Import via Python (preview and execute modes)

```bash
# Preview – show first 10 records, no database writes (default)
python scripts/import_to_mariadb.py

# Execute – actually insert all records
python scripts/import_to_mariadb.py --execute

# Use a custom input file
python scripts/import_to_mariadb.py --input path/to/cleaned.csv --execute
```

Progress and errors are written to both the console and
`data/processed/import_log.txt`.

---

## Data Mapping

The table below shows how each `mycoCSV.csv` column maps to the `fungi`
database table.

| Database field   | Primary source              | Fallback 1          | Fallback 2                   |
|------------------|-----------------------------|---------------------|------------------------------|
| `scientific_name`| `Identification`            | `Binomial`          | `First Pass ID` + ` sp.`     |
| `common_name`    | `Identification Per FDA Label` | `Name of Product` | –                            |
| `family`         | `First Pass ID`             | –                   | –                            |
| `habitat`        | `Country of Origin` + `Product Type` (combined) | – | –               |
| `edibility`      | `'unknown'` (default)       | –                   | –                            |
| `description`    | `Brand` + `Manufacturer/Distributor` + `Preservation Method` (combined) | – | – |
| `notes`          | `Comments` + `GenBank#` + `Seq. Status` + `Multiple species?` (combined) | – | – |

### Notes on field mapping

- **`scientific_name`** is required by the database schema. Records where all
  three source columns are empty or contain only placeholder text (`Unknown`,
  `Not Provided`, etc.) are skipped.
- **`edibility`** defaults to `'unknown'` because the CSV does not contain
  explicit edibility data. Enhance later using external taxonomic resources.
- **Text truncation** – `scientific_name`, `common_name`, and `family` are
  stored as `VARCHAR(255)`. Values longer than 255 characters are truncated
  automatically and logged as warnings.
- **`Seq. Status = "Failed"`** – failed DNA sequencing attempts are flagged in
  the `notes` field so researchers can identify unreliable identifications.

---

## Output Files

| File                               | Description                                  |
|------------------------------------|----------------------------------------------|
| `data/processed/analysis_report.txt` | Data quality report                       |
| `data/processed/myco_cleaned.csv`    | Import-ready cleaned CSV                  |
| `data/processed/cleansing_log.txt`   | Per-record transformation log             |
| `data/processed/import_statements.sql` | SQL INSERT statements for direct import |
| `data/processed/import_log.txt`      | MariaDB import progress and error log     |

---

## Troubleshooting

### `CSV not found` error

Make sure `data/raw/mycoCSV.csv` exists. If you renamed it, update the
`RAW_CSV` path constant at the top of each script.

### `Cannot connect to MariaDB`

1. Ensure MariaDB is running: `docker compose up -d`
2. Verify your `.env` file contains the correct `DB_HOST`, `DB_PORT`,
   `DB_USER`, `DB_PASSWORD`, and `DB_NAME` values.
3. Check that the `fungi_db` database and `fungi` table exist (they are
   created automatically when the Flask app starts).

### `ModuleNotFoundError`

Install all required packages:

```bash
pip install pandas pymysql python-dotenv openpyxl sqlalchemy
```

### Records skipped during cleansing

Records are skipped only when all three name columns (`Identification`,
`Binomial`, `First Pass ID`) are empty or contain placeholder text. Check
`data/processed/cleansing_log.txt` for the specific rows.

---

## Example Output

### `analysis_report.txt` excerpt

```
========================================================================
 1. OVERVIEW
========================================================================
Total records : 237
Total columns : 30
Overall data completeness : 62.3%
  (4413 / 7110 cells filled)
```

### `cleansing_log.txt` excerpt

```
CLEANSING LOG – mycoCSV.csv
Input records : 237

  [MAP] Row 2: scientific_name='Agaricus bisporus'  (from Identification)
  [MAP] Row 3: scientific_name='Agaricus sp.'  (from First Pass ID (+ sp.))
  [WARNING] Row 45: field 'description' truncated from 260 to 255 chars.

Records processed : 237
Records skipped   : 0
Records cleaned   : 237
Success rate      : 100.0%  (237 / 237)
```
