# Fungi Species Database – Data Dictionary

## Introduction

This document describes the structure and meaning of every field in the fungi
species database. The database consists of a single **fungi** table stored in
MariaDB and managed by the Flask web application (`app.py`).

---

## Fungi Table

**Purpose:** Stores core taxonomic and descriptive information about each
fungal species.

| Field           | Type         | Constraints                                      | Description                                                         | Example                      |
|-----------------|--------------|--------------------------------------------------|---------------------------------------------------------------------|------------------------------|
| id              | INT          | PRIMARY KEY, AUTO_INCREMENT                      | Unique identifier for the record.                                   | `1`                          |
| scientific_name | VARCHAR(255) | NOT NULL                                         | Full binomial Latin name.                                           | `Amanita muscaria`           |
| common_name     | VARCHAR(255) | –                                                | Vernacular name(s) in English.                                      | `Fly Agaric`                 |
| family          | VARCHAR(255) | –                                                | Taxonomic family.                                                   | `Amanitaceae`                |
| habitat         | TEXT         | –                                                | Description of typical habitat.                                     | `Deciduous woodland`         |
| edibility       | ENUM         | NOT NULL, DEFAULT 'unknown' (controlled vocab)   | Safety classification – see Controlled Vocabularies below.          | `poisonous`                  |
| description     | TEXT         | –                                                | Free-text description of the species.                               | `Iconic red cap with white…` |
| notes           | TEXT         | –                                                | Additional notes.                                                   | `Ring present`               |
| date_added      | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP                        | Row creation timestamp (UTC).                                       | `2024-06-01 10:30:00`        |

---

## Data Formats

| Data          | Format                                               |
|---------------|------------------------------------------------------|
| Timestamps    | ISO 8601: `YYYY-MM-DD HH:MM:SS` UTC                 |
| Text encoding | UTF-8                                                |

---

## Controlled Vocabularies

### edibility (fungi table)

| Value       | Meaning                                                   |
|-------------|-----------------------------------------------------------|
| `edible`    | Recognised as safe to eat when properly prepared.         |
| `poisonous` | Contains toxins; may cause illness or death.              |
| `inedible`  | Not toxic but not suitable for eating (e.g. too tough).   |
| `unknown`   | Safety has not been established.                          |

---

## Data Entry Guidelines

1. **Scientific names** must follow the binomial nomenclature standard and
   should be verified against a recognised taxonomic resource (e.g. MycoBank,
   Index Fungorum).
2. **Edibility** must be one of the four controlled vocabulary values; do not
   leave blank – use `unknown` if unsure.
3. Leave optional fields blank (`NULL`) rather than entering placeholder text
   such as "N/A".

