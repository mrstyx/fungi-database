"""
create_database.py  –  DEPRECATED
===================================
This script is no longer needed.

The MariaDB schema (``fungi`` table) is now created automatically by
``app.py``'s ``init_db()`` function when the Flask application starts.
The database is managed by the MariaDB service defined in
``docker-compose.yml``.

To set up the database, simply start the services with Docker Compose::

    docker compose up --build -d

The ``fungi`` table will be created on first run.  See the README for
full setup instructions.
"""

import sys

if __name__ == "__main__":
    print(
        "create_database.py is deprecated.\n"
        "The MariaDB schema is automatically created by app.py on startup.\n"
        "Start the services with: docker compose up --build -d"
    )
    sys.exit(0)
