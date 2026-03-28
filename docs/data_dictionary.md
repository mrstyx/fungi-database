# Fungi Species Database – Data Dictionary

## Introduction

This document describes the structure and meaning of every field in the fungi
species database. The database consists of four tables: **species**,
**locations**, **observations**, and **characteristics**. Each table is
documented below with field definitions, data types, constraints, and example
values.

---

## Species Table

**Purpose:** Stores core taxonomic and descriptive information about each
fungal species. This is the central reference table to which observations and
characteristics are linked.

| Field           | Type      | Constraints              | Description                                                        | Example                       |
|-----------------|-----------|--------------------------|-------------------------------------------------------------------|-------------------------------|
| id              | INTEGER   | PRIMARY KEY, AUTOINCREMENT | Unique identifier for the species record.                        | `1`                           |
| scientific_name | TEXT      | UNIQUE, NOT NULL         | Full binomial Latin name.                                         | `Amanita muscaria`            |
| common_name     | TEXT      | –                        | Vernacular name(s) in English.                                    | `Fly Agaric`                  |
| family          | TEXT      | –                        | Taxonomic family.                                                 | `Amanitaceae`                 |
| genus           | TEXT      | –                        | Taxonomic genus.                                                  | `Amanita`                     |
| order_name      | TEXT      | –                        | Taxonomic order (column named `order_name` to avoid SQL keyword). | `Agaricales`                  |
| class_name      | TEXT      | –                        | Taxonomic class (column named `class_name` to avoid SQL keyword). | `Agaricomycetes`              |
| phylum          | TEXT      | –                        | Taxonomic phylum.                                                 | `Basidiomycota`               |
| edibility       | TEXT      | CHECK (controlled vocab) | Safety classification – see Controlled Vocabularies below.        | `poisonous`                   |
| toxicity        | TEXT      | –                        | Description of known toxins or toxic effects.                     | `Contains ibotenic acid`      |
| description     | TEXT      | –                        | Free-text description of the species.                             | `Iconic red cap with white…`  |
| created_at      | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Row creation timestamp (UTC).                                    | `2024-06-01 10:30:00`         |
| updated_at      | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Row last-updated timestamp (UTC).                                | `2024-06-15 14:00:00`         |

---

## Locations Table

**Purpose:** Stores geographic and environmental context for where
observations take place. A single location can be associated with many
observations.

| Field        | Type      | Constraints              | Description                                          | Example                 |
|--------------|-----------|--------------------------|------------------------------------------------------|-------------------------|
| id           | INTEGER   | PRIMARY KEY, AUTOINCREMENT | Unique identifier for the location.                | `1`                     |
| name         | TEXT      | –                        | Human-readable name for the site.                    | `Sherwood Forest North` |
| latitude     | REAL      | –                        | Latitude in decimal degrees (WGS 84). See Formats.   | `53.2050`               |
| longitude    | REAL      | –                        | Longitude in decimal degrees (WGS 84). See Formats.  | `-1.0650`               |
| habitat_type | TEXT      | –                        | General habitat category.                            | `Deciduous woodland`    |
| elevation    | REAL      | –                        | Elevation above sea level in metres.                 | `85.0`                  |
| region       | TEXT      | –                        | Sub-national region or county.                       | `Nottinghamshire`       |
| country      | TEXT      | –                        | Country name.                                        | `United Kingdom`        |
| created_at   | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Row creation timestamp (UTC).                       | `2024-06-01 10:30:00`   |

---

## Observations Table

**Purpose:** Records individual sightings of a species at a location on a
specific date. Links the **species** and **locations** tables in a many-to-many
relationship.

| Field              | Type      | Constraints                          | Description                                              | Example                        |
|--------------------|-----------|--------------------------------------|----------------------------------------------------------|--------------------------------|
| id                 | INTEGER   | PRIMARY KEY, AUTOINCREMENT           | Unique identifier for the observation.                   | `1`                            |
| species_id         | INTEGER   | FOREIGN KEY → species(id)            | Reference to the observed species.                       | `3`                            |
| location_id        | INTEGER   | FOREIGN KEY → locations(id)          | Reference to the observation location.                   | `7`                            |
| observation_date   | DATE      | –                                    | Date of the observation (YYYY-MM-DD).                    | `2024-09-15`                   |
| habitat            | TEXT      | –                                    | Specific micro-habitat at the time of observation.       | `Under birch trees`            |
| substrate          | TEXT      | –                                    | Material the fungus was growing on.                      | `Dead wood`, `Leaf litter`     |
| weather_conditions | TEXT      | –                                    | Weather at the time of observation.                      | `Overcast, 14°C, recent rain`  |
| observer           | TEXT      | –                                    | Name or identifier of the person who made the record.    | `J. Smith`                     |
| notes              | TEXT      | –                                    | Free-text field for additional information.              | `Large cluster of 12 fruiting` |
| photo_url          | TEXT      | –                                    | URL or relative path to a photograph.                    | `photos/obs_001.jpg`           |
| created_at         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP            | Row creation timestamp (UTC).                            | `2024-09-15 18:45:00`          |

---

## Characteristics Table

**Purpose:** Stores morphological and sensory attributes for each species.
A species may have multiple characteristic records (e.g. for different growth
stages or regional variations).

| Field             | Type    | Constraints               | Description                                     | Example                       |
|-------------------|---------|---------------------------|-------------------------------------------------|-------------------------------|
| id                | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier for the characteristics row. | `1`                           |
| species_id        | INTEGER | FOREIGN KEY → species(id) | Reference to the species these traits belong to.| `3`                           |
| cap_shape         | TEXT    | –                         | Shape of the cap – see Controlled Vocabularies. | `convex`                      |
| cap_color         | TEXT    | –                         | Cap colour description.                         | `scarlet red`                 |
| cap_diameter_cm   | REAL    | –                         | Cap diameter in centimetres.                    | `12.5`                        |
| gill_attachment   | TEXT    | –                         | How gills attach to the stem – see vocab.       | `free`                        |
| gill_color        | TEXT    | –                         | Colour of the gills.                            | `white`                       |
| stem_height_cm    | REAL    | –                         | Stem height in centimetres.                     | `15.0`                        |
| stem_diameter_cm  | REAL    | –                         | Stem diameter in centimetres.                   | `2.0`                         |
| spore_print_color | TEXT    | –                         | Colour of the spore print.                      | `white`                       |
| odor              | TEXT    | –                         | Smell description.                              | `faint, musty`                |
| taste             | TEXT    | –                         | Taste description (use with caution).           | `mild`                        |
| notes             | TEXT    | –                         | Additional morphological notes.                 | `Ring present, warty patches` |

---

## Relationships

```
species ──┬── characteristics (species.id = characteristics.species_id)
          └── observations   (species.id = observations.species_id)
                               │
locations ──────────────────── observations (locations.id = observations.location_id)
```

- **species → observations**: One species can have many observations.
- **locations → observations**: One location can have many observations.
- **species → characteristics**: One species can have many characteristic
  records (e.g. multiple growth stages).

---

## Data Formats

| Data             | Format                                                        |
|------------------|---------------------------------------------------------------|
| Dates            | ISO 8601: `YYYY-MM-DD` (e.g. `2024-09-15`)                   |
| Timestamps       | ISO 8601: `YYYY-MM-DD HH:MM:SS` UTC                          |
| Coordinates      | Decimal degrees, WGS 84 (e.g. `53.2050`, `-1.0650`)          |
| Measurements     | Centimetres (cm) for cap/stem dimensions; metres (m) for elevation |
| Text encoding    | UTF-8                                                         |

---

## Controlled Vocabularies

### edibility (species table)

| Value       | Meaning                                                   |
|-------------|-----------------------------------------------------------|
| `edible`    | Recognised as safe to eat when properly prepared.         |
| `poisonous`  | Contains toxins; may cause illness or death.             |
| `inedible`  | Not toxic but not suitable for eating (e.g. too tough).   |
| `unknown`   | Safety has not been established.                          |

### cap_shape (characteristics table)

Common values: `convex`, `flat`, `umbonate`, `depressed`, `funnel-shaped`,
`bell-shaped` (campanulate), `egg-shaped` (ovate), `irregular`.

### gill_attachment (characteristics table)

Common values: `free`, `adnate`, `adnexed`, `decurrent`, `sinuate`, `none`
(for pore-bearing or smooth-hymenium species).

---

## Data Entry Guidelines

1. **Scientific names** must follow the binomial nomenclature standard and
   should be verified against a recognised taxonomic resource (e.g. MycoBank,
   Index Fungorum).
2. **Coordinates** should be recorded to at least four decimal places
   (~11 m precision).
3. **Dates** must always be stored in `YYYY-MM-DD` format.
4. **Edibility** must be one of the four controlled vocabulary values; do not
   leave blank – use `unknown` if unsure.
5. **Observer** should be a consistent identifier (full name or username) to
   allow aggregation of records by contributor.
6. **Location privacy**: avoid recording precise coordinates for sensitive or
   protected sites; use regional-level data only when necessary.
7. Leave optional fields blank (`NULL`) rather than entering placeholder text
   such as "N/A" or "unknown" for non-edibility fields.
