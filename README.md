# fungi-database
Mycology repository of all things fungi — a simple MariaDB-backed web application for recording and browsing fungal species.

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

## Project Structure

```
fungi-database/
├── app.py                # Flask application
├── templates/
│   ├── base.html         # Shared layout
│   ├── index.html        # Entry listing
│   ├── form.html         # Add / edit form
│   └── detail.html       # Single entry view
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
