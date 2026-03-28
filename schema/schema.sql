-- Fungi Species Database Schema
-- MariaDB-compatible SQL schema (mirrors the table created by app.py's init_db())

CREATE TABLE IF NOT EXISTS fungi (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    scientific_name  VARCHAR(255) NOT NULL,
    common_name      VARCHAR(255),
    family           VARCHAR(255),
    habitat          TEXT,
    edibility        ENUM('edible', 'poisonous', 'inedible', 'unknown') NOT NULL DEFAULT 'unknown',
    description      TEXT,
    notes            TEXT,
    date_added       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
