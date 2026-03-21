-- Fungi Species Database Schema
-- SQLite-compatible SQL schema for managing fungi species data

-- Species table: core taxonomic and descriptive information
CREATE TABLE IF NOT EXISTS species (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT    UNIQUE NOT NULL,
    common_name    TEXT,
    family         TEXT,
    genus          TEXT,
    order_name     TEXT,   -- 'order' is a reserved SQL keyword
    class_name     TEXT,   -- 'class' is a reserved SQL keyword
    phylum         TEXT,
    edibility      TEXT    CHECK (edibility IN ('edible', 'poisonous', 'inedible', 'unknown')),
    toxicity       TEXT,
    description    TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table: geographic and habitat information
CREATE TABLE IF NOT EXISTS locations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,
    latitude     REAL,
    longitude    REAL,
    habitat_type TEXT,
    elevation    REAL,
    region       TEXT,
    country      TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Observations table: individual sighting records linking species and locations
CREATE TABLE IF NOT EXISTS observations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id         INTEGER REFERENCES species(id),
    location_id        INTEGER REFERENCES locations(id),
    observation_date   DATE,
    habitat            TEXT,
    substrate          TEXT,
    weather_conditions TEXT,
    observer           TEXT,
    notes              TEXT,
    photo_url          TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Characteristics table: morphological and sensory traits per species
CREATE TABLE IF NOT EXISTS characteristics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id        INTEGER REFERENCES species(id),
    cap_shape         TEXT,
    cap_color         TEXT,
    cap_diameter_cm   REAL,
    gill_attachment   TEXT,
    gill_color        TEXT,
    stem_height_cm    REAL,
    stem_diameter_cm  REAL,
    spore_print_color TEXT,
    odor              TEXT,
    taste             TEXT,
    notes             TEXT
);

-- Indexes for performance on common queries
CREATE INDEX IF NOT EXISTS idx_species_scientific_name ON species (scientific_name);
CREATE INDEX IF NOT EXISTS idx_observations_species_id  ON observations (species_id);
CREATE INDEX IF NOT EXISTS idx_observations_location_id ON observations (location_id);
CREATE INDEX IF NOT EXISTS idx_observations_date        ON observations (observation_date);
CREATE INDEX IF NOT EXISTS idx_characteristics_species  ON characteristics (species_id);
