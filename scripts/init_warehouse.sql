-- Schéma en étoile : 1 table de faits, 2 dimensions.
-- Compatible PostgreSQL. Rejouable : IF NOT EXISTS partout.

CREATE TABLE IF NOT EXISTS dim_ville (
    id_ville   SERIAL PRIMARY KEY,
    nom        TEXT NOT NULL,
    pays       TEXT NOT NULL,
    latitude   DOUBLE PRECISION NOT NULL,
    longitude  DOUBLE PRECISION NOT NULL,
    UNIQUE (nom, pays)
);

CREATE TABLE IF NOT EXISTS dim_temps (
    id_temps      SERIAL PRIMARY KEY,
    date          DATE NOT NULL,
    heure         SMALLINT NOT NULL CHECK (heure BETWEEN 0 AND 23),
    jour_semaine  SMALLINT NOT NULL CHECK (jour_semaine BETWEEN 0 AND 6), -- 0 = lundi
    est_weekend   BOOLEAN NOT NULL,
    mois          SMALLINT NOT NULL CHECK (mois BETWEEN 1 AND 12),
    annee         SMALLINT NOT NULL,
    UNIQUE (date, heure)
);

-- Table de faits : uniquement des mesures + des clés étrangères.
-- Pas de nom de ville, pas de date lisible ici (règle du cours respectée).
CREATE TABLE IF NOT EXISTS fait_qualite_air (
    id_ville  INTEGER NOT NULL REFERENCES dim_ville(id_ville),
    id_temps  INTEGER NOT NULL REFERENCES dim_temps(id_temps),
    aqi       SMALLINT NOT NULL CHECK (aqi BETWEEN 1 AND 5),
    co        DOUBLE PRECISION,
    no        DOUBLE PRECISION,
    no2       DOUBLE PRECISION,
    o3        DOUBLE PRECISION,
    so2       DOUBLE PRECISION,
    pm2_5     DOUBLE PRECISION,
    pm10      DOUBLE PRECISION,
    nh3       DOUBLE PRECISION,
    PRIMARY KEY (id_ville, id_temps)
);

CREATE INDEX IF NOT EXISTS idx_fait_temps ON fait_qualite_air(id_temps);
CREATE INDEX IF NOT EXISTS idx_fait_ville ON fait_qualite_air(id_ville);
