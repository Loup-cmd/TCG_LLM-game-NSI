"""
generer_donnees.py -- fabrique donnees.sql à partir de modeles.csv.

  modeles.csv  : 24 modèles de langage avec leurs benchmarks (relevé du 2 novembre 2026)
  donnees.sql  : instructions INSERT (raretés, catégories, cartes) lues ensuite par creer_bdd.py

Pour mettre à jour le jeu avec de nouveaux benchmarks : modifier modeles.csv, puis lancer
    python generer_donnees.py
    python creer_bdd.py        (efface et recrée la base)
Usage :  python generer_donnees.py
"""
import csv
import os
import modele

FICHIER_CSV = os.path.join(modele.DOSSIER, "modeles.csv")
FICHIER_SQL = os.path.join(modele.DOSSIER, "donnees.sql")

RARETES = [(1, "Commune", "#6b7280", 60), (2, "Rare", "#1d6fd8", 25),
           (3, "Épique", "#8a3ffc", 12), (4, "Légendaire", "#c77700", 3)]
CATEGORIES = [(1, "Frontier"), (2, "Poids ouverts"), (3, "Compact")]


def lire_modeles(chemin=FICHIER_CSV):
    """lit le fichier CSV : renvoie une liste de dictionnaires (un par modèle)"""
    modeles = []
    with open(chemin, encoding="utf-8", newline="") as f:
        for ligne in csv.DictReader(f, delimiter=";"):
            ligne["indice"] = float(ligne["indice"])
            ligne["tokens_s"] = int(ligne["tokens_s"])
            modeles.append(ligne)
    return modeles


def preparer_cartes(modeles):
    """
    
    c:omplète chaque modèle : puissance, vitesse, id_rarete, id_categorie, illustration.
    la rareté dépend du rang du modèle DANS SA CATÉGORIE (classement par score global)"""
    par_categorie = {}
    for m in modeles:
        if m["categorie"] not in par_categorie:
            par_categorie[m["categorie"]] = []
        par_categorie[m["categorie"]].append(m)

    id_categories = {}
    for id_categorie, nom in CATEGORIES:
        id_categories[nom] = id_categorie

    cartes = []
    for m in modeles:
        groupe = par_categorie[m["categorie"]]
        rang = modele.rangs_dans_categorie(groupe)[m["nom"]]
        puissance, vitesse = modele.calculer_stats(m["indice"], m["tokens_s"])
        carte = dict(m)
        carte["puissance"] = puissance
        carte["vitesse"] = vitesse
        carte["rang"] = rang
        carte["id_rarete"] = modele.rarete_du_rang(rang, len(groupe))
        carte["id_categorie"] = id_categories[m["categorie"]]
        carte["illustration"] = modele.nom_fichier_illustration(m["nom"])
        cartes.append(carte)
    return cartes


def texte_sql(texte):
    """Texte entre apostrophes, avec les apostrophes doublées."""
    return "'" + texte.replace("'", "''") + "'"


def construire_sql(modeles):
    """
    Renvoie le contenu complet de donnees.sql."""
    lignes = ["-- Fichier GÉNÉRÉ par generer_donnees.py à partir de modeles.csv : ne pas modifier à la main.",
              "-- Benchmarks : Artificial Analysis Intelligence Index v5.0 et vitesse médiane (jetons/s), relevé du 2 novembre 2026.",
              "",
              "INSERT INTO Rarete (id_rarete, nom, couleur, poids_tirage) VALUES"]
    valeurs = []
    for id_rarete, nom, couleur, poids in RARETES:
        valeurs.append("    (" + str(id_rarete) + ", " + texte_sql(nom) + ", " + texte_sql(couleur) + ", " + str(poids) + ")")
    lignes.append(",\n".join(valeurs) + ";")
    lignes.append("")
    lignes.append("INSERT INTO Categorie (id_categorie, nom) VALUES")
    valeurs = []
    for id_categorie, nom in CATEGORIES:
        valeurs.append("    (" + str(id_categorie) + ", " + texte_sql(nom) + ")")
    lignes.append(",\n".join(valeurs) + ";")
    lignes.append("")
    lignes.append("INSERT INTO Carte (id_carte, nom, editeur, description, indice, tokens_s, puissance, vitesse,")
    lignes.append("                   illustration, id_rarete, id_categorie) VALUES")
    valeurs = []
    numero = 0
    for c in preparer_cartes(modeles):
        numero = numero + 1
        valeurs.append("    (" + str(numero) + ", " + texte_sql(c["nom"]) + ", " + texte_sql(c["editeur"]) + ", "
                       + texte_sql(c["description"]) + ", " + str(c["indice"]) + ", " + str(c["tokens_s"]) + ", "
                       + str(c["puissance"]) + ", " + str(c["vitesse"]) + ", " + texte_sql(c["illustration"]) + ", "
                       + str(c["id_rarete"]) + ", " + str(c["id_categorie"]) + ")")
    lignes.append(",\n".join(valeurs) + ";")
    return "\n".join(lignes) + "\n"


if __name__ == "__main__":
    sql = construire_sql(lire_modeles())
    with open(FICHIER_SQL, "w", encoding="utf-8") as f:
        f.write(sql)
    print("donnees.sql généré :", len(lire_modeles()), "cartes.")
