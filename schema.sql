-- Schéma de la base cartes.db (SQLite) correspond au schéma relationnel de docs/MCD_et_SR.md
PRAGMA foreign_keys = ON;


-- Curzio regarde ça c pas dans le programme mais il faut utilise : 
--   CHECK (condition)                        la base refuse toute ligne qui ne respecte pas la condition
--   COLLATE NOCASE                              comparaison sans tenir compte des majuscules ("Alice" = "alice")
--   DEFAULT CURRENT_DATE / CURRENT_TIMESTAMP  date du jour inscrite automatiquement
--   PRAGMA foreign_keys                 active la vérification des clés étrangères (voir modele.py)

-- On supprime d'abord les tables "enfants" (celles qui contiennent des clés étrangères)
DROP TABLE IF EXISTS Combat;
DROP TABLE IF EXISTS Possession;
DROP TABLE IF EXISTS Carte;
DROP TABLE IF EXISTS Categorie;
DROP TABLE IF EXISTS Rarete;
DROP TABLE IF EXISTS Joueur;

-- Tables SANS clé étrangère ---------------------------------------------------
CREATE TABLE Joueur (
    id_joueur        INTEGER PRIMARY KEY AUTOINCREMENT,
    pseudo           TEXT    NOT NULL UNIQUE COLLATE NOCASE,   -- "Alice" = "alice"
    mdp_hash         TEXT    NOT NULL,                         -- jamais le mot de passe en clair !
    pieces           INTEGER NOT NULL DEFAULT 100 CHECK (pieces >= 0),
    est_admin        INTEGER NOT NULL DEFAULT 0 CHECK (est_admin IN (0, 1)),
    date_inscription TEXT    NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE Rarete (
    id_rarete    INTEGER PRIMARY KEY,
    nom          TEXT    NOT NULL UNIQUE,
    couleur      TEXT    NOT NULL,                             -- code couleur CSS pour l'affichage
    poids_tirage INTEGER NOT NULL CHECK (poids_tirage > 0)     -- chances de sortie dans un booster
);

CREATE TABLE Categorie (                                       -- Frontier, Poids ouverts, Compact
    id_categorie INTEGER PRIMARY KEY,
    nom          TEXT NOT NULL UNIQUE
);

-- Tables AVEC clés étrangères -------------------------------------------------
-- Une carte = un modèle de langage On garde les benchmarks bruts (indice, tokens_s) pour l'affichage,
-- et les caractéristiques de jeu (puissance, vitesse) calculées une fois pour toutes à partir d'eux :
-- les cartes déjà possédées ne changent donc pas quand les benchmarks évoluent.
CREATE TABLE Carte (
    id_carte     INTEGER PRIMARY KEY AUTOINCREMENT,
    nom          TEXT    NOT NULL UNIQUE,
    editeur      TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    indice       REAL    NOT NULL CHECK (indice >= 0),         -- Intelligence Index (puissance générale)
    tokens_s     INTEGER NOT NULL CHECK (tokens_s > 0),        -- vitesse de génération (jetons par seconde)
    puissance    INTEGER NOT NULL CHECK (puissance BETWEEN 0 AND 10),
    vitesse      INTEGER NOT NULL CHECK (vitesse BETWEEN 0 AND 10),
    illustration TEXT    NOT NULL DEFAULT 'defaut.svg',        -- fichier de static/cartes/ (généré par IA)
    id_rarete    INTEGER NOT NULL,
    id_categorie INTEGER NOT NULL,
    FOREIGN KEY (id_rarete)    REFERENCES Rarete(id_rarete),
    FOREIGN KEY (id_categorie) REFERENCES Categorie(id_categorie)
);

-- Association N-N (Joueur, Carte) portant l'attribut "quantite"
CREATE TABLE Possession (
    id_joueur INTEGER NOT NULL,
    id_carte  INTEGER NOT NULL,
    quantite  INTEGER NOT NULL DEFAULT 1 CHECK (quantite >= 1),
    PRIMARY KEY (id_joueur, id_carte),
    FOREIGN KEY (id_joueur) REFERENCES Joueur(id_joueur),
    FOREIGN KEY (id_carte)  REFERENCES Carte(id_carte)
);

CREATE TABLE Combat (
    id_combat    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_attaquant INTEGER NOT NULL,
    id_defenseur INTEGER NOT NULL,
    id_carte_att INTEGER NOT NULL,
    id_carte_def INTEGER NOT NULL,
    id_vainqueur INTEGER,                                      -- NULL = égalité
    date_combat  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (id_attaquant <> id_defenseur),
    FOREIGN KEY (id_attaquant) REFERENCES Joueur(id_joueur),
    FOREIGN KEY (id_defenseur) REFERENCES Joueur(id_joueur),
    FOREIGN KEY (id_carte_att) REFERENCES Carte(id_carte),
    FOREIGN KEY (id_carte_def) REFERENCES Carte(id_carte),
    FOREIGN KEY (id_vainqueur) REFERENCES Joueur(id_joueur)
);
