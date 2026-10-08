DROP TABLE IF EXISTS offre_competence CASCADE;
DROP TABLE IF EXISTS fait_offres CASCADE;
DROP TABLE IF EXISTS dim_temps CASCADE;
DROP TABLE IF EXISTS dim_lieu CASCADE;
DROP TABLE IF EXISTS dim_entreprise CASCADE;
DROP TABLE IF EXISTS dim_competence CASCADE;
DROP TABLE IF EXISTS dim_contrat CASCADE;

CREATE TABLE dim_temps (
    id_temps      SERIAL PRIMARY KEY,
    date_complete DATE NOT NULL UNIQUE,
    jour          INT,
    mois          INT,
    trimestre     INT,
    annee         INT
);

CREATE TABLE dim_lieu (
    id_lieu SERIAL PRIMARY KEY,
    ville   VARCHAR(100),
    pays    VARCHAR(100) DEFAULT 'Tunisie',
    UNIQUE(ville, pays)
);

CREATE TABLE dim_entreprise (
    id_entreprise SERIAL PRIMARY KEY,
    nom           VARCHAR(255) UNIQUE,
    secteur       VARCHAR(100)
);

CREATE TABLE dim_contrat (
    id_contrat   SERIAL PRIMARY KEY,
    type_contrat VARCHAR(50) UNIQUE,
    mode_travail VARCHAR(50)
);

CREATE TABLE dim_competence (
    id_competence SERIAL PRIMARY KEY,
    nom           VARCHAR(100) UNIQUE,
    categorie     VARCHAR(50)
);

CREATE TABLE fait_offres (
    id_offre       SERIAL PRIMARY KEY,
    source_id      VARCHAR(100) UNIQUE,
    titre          VARCHAR(500),
    id_entreprise  INT REFERENCES dim_entreprise(id_entreprise),
    id_lieu        INT REFERENCES dim_lieu(id_lieu),
    id_contrat     INT REFERENCES dim_contrat(id_contrat),
    id_temps       INT REFERENCES dim_temps(id_temps),
    experience_min INT,
    experience_max INT,
    niveau_etudes  VARCHAR(50),
    langues        VARCHAR(255),
    description    TEXT,
    url            VARCHAR(500),
    scraped_at     TIMESTAMP
);

CREATE TABLE offre_competence (
    id_offre      INT REFERENCES fait_offres(id_offre) ON DELETE CASCADE,
    id_competence INT REFERENCES dim_competence(id_competence) ON DELETE CASCADE,
    PRIMARY KEY (id_offre, id_competence)
);

CREATE INDEX idx_fait_entreprise ON fait_offres(id_entreprise);
CREATE INDEX idx_fait_lieu       ON fait_offres(id_lieu);
CREATE INDEX idx_fait_temps      ON fait_offres(id_temps);