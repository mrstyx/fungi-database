# fungi-database
Mycology repository of all things fungi — a database system for managing fungi species data converted from spreadsheets, plus a MariaDB-backed web application for recording and browsing fungal species.

## Features

- Add, view, edit, and delete fungi entries
- Fields: scientific name, common name, family, habitat, edibility, description, notes
- Clean web interface served by Flask
- Persistent data stored in MariaDB

## Quick Start (Docker Compose)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1. **Copy the environment file and set your passwords:**

   ```bash
   cp .env.example .env
   # Edit .env to set secure values for MARIADB_ROOT_PASSWORD, MARIADB_PASSWORD, and SECRET_KEY
   ```

2. **Build and start all services:**

   ```bash
   docker compose up --build -d
   ```

3. **Open the app in your browser:**

   ```
   http://localhost:5000
   ```

4. **Stop the services:**

   ```bash
   docker compose down
   ```

   To also remove the database volume (deletes all data):

   ```bash
   docker compose down -v
   ```

## Local Development (without Docker)

### Prerequisites
- Python 3.12+
- A running MariaDB or MySQL instance

### Steps

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (or create a `.env` file and export them):

   ```bash
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_USER=fungi
   export DB_PASSWORD=fungipassword
   export DB_NAME=fungi_db
   export SECRET_KEY=change-me
   ```

3. **Create the database** in MariaDB:

   ```sql
   CREATE DATABASE fungi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'fungi'@'localhost' IDENTIFIED BY 'fungipassword';
   GRANT ALL PRIVILEGES ON fungi_db.* TO 'fungi'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. **Run the app** (it will create the table automatically on first run):

   ```bash
   python app.py
   ```

5. **Open** `http://localhost:5000`

## Spreadsheet-to-Database Import

If you have existing fungi data in Excel or CSV spreadsheets, you can import
them directly into a lightweight SQLite database.

### Set up the SQLite database

```bash
# Install the import dependencies
pip install -r scripts/requirements.txt

# Create the database and all tables
python scripts/create_database.py
```

The database is created at `data/database/fungi.db`.

### Import a spreadsheet

```bash
# Place your file in data/raw/ then run:
python scripts/import_spreadsheet.py data/raw/species.xlsx

# Specify a sheet name and target table explicitly
python scripts/import_spreadsheet.py data/raw/mydata.xlsx \
    --sheet-name Sheet1 --table-name species

# Preview without writing to the database
python scripts/import_spreadsheet.py data/raw/species.csv --dry-run
```

Run `python scripts/import_spreadsheet.py --help` for full usage details.

### Database schema overview

| Table            | Description                                             |
|------------------|---------------------------------------------------------|
| species          | Taxonomic and descriptive data for each fungal species  |
| locations        | Geographic and habitat information for observation sites |
| observations     | Individual sighting records linking species and locations |
| characteristics  | Morphological traits (cap, gills, stem, spores, etc.)   |

See [`schema/schema.sql`](schema/schema.sql) for the full schema and
[`docs/data_dictionary.md`](docs/data_dictionary.md) for detailed field
descriptions, data formats, and controlled vocabularies.

### Data privacy

Precise GPS coordinates for sensitive or protected sites should not be
committed to a public repository. Use regional-level data, or add
`data/database/` to `.gitignore` if your database contains sensitive
location records.

## Contributing

1. Fork the repository and create a feature branch.
2. Keep raw spreadsheet files in `data/raw/` (they are git-ignored by default
   if large).
3. Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
4. Open a pull request describing your changes.

## Future Enhancements

- Web interface for querying and browsing the SQLite database
- Automated data-cleaning pipeline for common spreadsheet inconsistencies
- Export to Darwin Core / CSV for sharing with iNaturalist or GBIF
- Photo gallery linked to observation records

## Project Structure

```
fungi-database/
├── app.py                        # Flask web application (MariaDB)
├── templates/
│   ├── base.html                 # Shared layout
│   ├── index.html                # Entry listing
│   ├── form.html                 # Add / edit form
│   └── detail.html               # Single entry view
├── data/
│   ├── raw/                      # Original spreadsheet files
│   ├── processed/                # Cleaned CSV files
│   └── database/                 # SQLite database file
├── scripts/
│   ├── create_database.py        # Creates the SQLite database
│   ├── import_spreadsheet.py     # Imports spreadsheet data
│   └── requirements.txt          # Python dependencies for scripts
├── schema/
│   └── schema.sql                # SQLite database schema
├── docs/
│   └── data_dictionary.md        # Field definitions and guidelines
├── Dockerfile
├── docker-compose.yml
├── requirements.txt              # Flask app dependencies
└── .env.example
```
