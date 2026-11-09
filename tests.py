"""
tests.py -- batterie de tests (assert) du projet.

Lancer :   python tests.py        (ou :  pytest tests.py)

Chaque test repart d'une base NEUVE (temporaire) remplie par creer_bdd.py :
  admin/admin1234, alice/alice1234, bob/bob12345, 24 cartes de modèles de langage, 2 combats.
Les vrais fichiers du projet (cartes.db) ne sont jamais touchés.

[IA] Seuls les `assert` sont du programme. Le reste est HORS PROGRAMME (code proposé par une IA, relu et compris) :
 tempfile (fichier temporaire), app.test_client() (simule un navigateur sans lancer
le serveur), sqlite3.IntegrityError (erreur levée quand une contrainte est violée), globals() (retrouve les tests).
"""
import os
import sqlite3
import tempfile

import modele
import creer_bdd
import generer_donnees
import generer_illustrations
from app import app

app.config["TESTING"] = True
FICHIERS_TEMP = []


# ----------------------------------------------------------------------------
# Outils
# ----------------------------------------------------------------------------
def preparer():
    """Branche le projet sur une base temporaire neuve."""
    descripteur, chemin = tempfile.mkstemp(suffix=".db")
    os.close(descripteur)
    FICHIERS_TEMP.append(chemin)
    modele.NOM_BDD = chemin
    creer_bdd.creer_bdd()


def id_de(pseudo):
    return modele.lire_une("SELECT id_joueur FROM Joueur WHERE pseudo = ?", (pseudo,))["id_joueur"]


def pieces_de(pseudo):
    return modele.lire_une("SELECT pieces FROM Joueur WHERE pseudo = ?", (pseudo,))["pieces"]


def carte(nom):
    """La ligne complète de la table Carte pour un modèle donné."""
    return modele.lire_une("SELECT * FROM Carte WHERE nom = ?", (nom,))


def nb_combats():
    return modele.lire_une("SELECT COUNT(*) AS n FROM Combat")["n"]


def est_refuse(sql, params=()):
    """True si la base REFUSE la requête (violation de contrainte)."""
    try:
        modele.ecrire(sql, params)
    except sqlite3.IntegrityError:
        return True
    return False


def connecter(client, pseudo, mdp):
    return client.post("/connexion", data={"pseudo": pseudo, "mdp": mdp})


def texte(reponse):
    return reponse.get_data(as_text=True)


# ----------------------------------------------------------------------------
# 1. Fonctions pures (sans base de données)
# ----------------------------------------------------------------------------
def test_verifier_pseudo():
    assert modele.verifier_pseudo("alice") is None
    assert modele.verifier_pseudo("abc") is None
    assert modele.verifier_pseudo("a" * 20) is None
    assert modele.verifier_pseudo("ab") is not None            # trop court
    assert modele.verifier_pseudo("a" * 21) is not None        # trop long
    assert modele.verifier_pseudo("al ice") is not None        # espace interdit
    assert modele.verifier_pseudo("x'; DROP TABLE Joueur;--") is not None


def test_verifier_mdp():
    assert modele.verifier_mdp("12345678") is None
    assert modele.verifier_mdp("1234567") is not None
    assert modele.verifier_mdp("") is not None


def test_tirer_rarete():
    raretes = [(1, 60), (2, 25), (3, 12), (4, 3)]
    assert modele.tirer_rarete(raretes, 1) == 1
    assert modele.tirer_rarete(raretes, 60) == 1
    assert modele.tirer_rarete(raretes, 61) == 2
    assert modele.tirer_rarete(raretes, 85) == 2
    assert modele.tirer_rarete(raretes, 86) == 3
    assert modele.tirer_rarete(raretes, 97) == 3
    assert modele.tirer_rarete(raretes, 98) == 4
    assert modele.tirer_rarete(raretes, 100) == 4
    assert modele.tirer_rarete([(7, 5)], 3) == 7               # une seule rareté


def test_calculer_stats():
    """Passage des benchmarks (indice, jetons/s) aux caractéristiques (puissance, vitesse)."""
    assert modele.calculer_stats(59.4, 95) == (10, 4)          # Gemini 4 Carbon
    assert modele.calculer_stats(54.2, 137) == (9, 5)          # Claude Sonnet 5.5
    assert modele.calculer_stats(36.2, 235) == (6, 9)          # Claude Haiku 5.5
    assert modele.calculer_stats(4.3, 158) == (1, 6)           # Mistral Small 4
    assert modele.calculer_stats(17.8, 720) == (3, 10)         # K2 Horizon : la vitesse est plafonnée à 10
    assert modele.calculer_stats(100, 5000) == (10, 10)        # la puissance aussi
    assert modele.calculer_stats(0, 1) == (0, 0)
    assert modele.calculer_stats(2.9, 12) == (0, 0)            # juste en dessous de l'arrondi
    assert modele.calculer_stats(3.0, 13) == (1, 1)            # juste au-dessus


def test_score_global():
    assert modele.score_global(10, 4) == 82
    assert modele.score_global(1, 6) == 25
    assert modele.score_global(0, 0) == 0
    assert modele.score_global(10, 10) == 100


def test_rarete_du_rang():
    assert [modele.rarete_du_rang(rang, 8) for rang in range(1, 9)] == [4, 3, 3, 2, 2, 1, 1, 1]
    assert [modele.rarete_du_rang(rang, 24) for rang in (1, 3, 4, 9, 10, 15, 16, 24)] == [4, 4, 3, 3, 2, 2, 1, 1]


def test_rangs_dans_categorie():
    modeles = [{"nom": "F", "indice": 57.5, "tokens_s": 97},    # (10, 4) -> score 82
               {"nom": "B", "indice": 30, "tokens_s": 500},     # (5, 10) -> score 65
               {"nom": "D", "indice": 59.4, "tokens_s": 95},    # (10, 4) -> score 82
               {"nom": "C", "indice": 54, "tokens_s": 30},      # (9, 1)  -> score 66
               {"nom": "E", "indice": 58.4, "tokens_s": 96}]    # (10, 4) -> score 82
    rangs = modele.rangs_dans_categorie(modeles)
    assert rangs == {"D": 1, "E": 2, "F": 3, "C": 4, "B": 5}    # D, E, F à égalité de score : meilleur indice d'abord
    assert modele.rangs_dans_categorie([{"nom": "seul", "indice": 10, "tokens_s": 10}]) == {"seul": 1}


def test_nom_fichier_illustration():
    assert modele.nom_fichier_illustration("GPT-6.1 Sol") == "gpt-6-1-sol.svg"
    assert modele.nom_fichier_illustration("Gemini 3.5 Flash-Lite") == "gemini-3-5-flash-lite.svg"
    assert modele.nom_fichier_illustration("K2 Horizon 375B A23B") == "k2-horizon-375b-a23b.svg"
    assert modele.nom_fichier_illustration("  Claude   Opus 5.5 ") == "claude-opus-5-5.svg"
    assert modele.nom_fichier_illustration("Step 5 Preview") == "step-5-preview.svg"


def test_resoudre_combat():
    """Dégâts = puissance x (15 - vitesse adverse)."""
    assert modele.resoudre_combat((10, 4), (5, 7)) == 1        # 10 x 8 = 80 contre 5 x 11 = 55
    assert modele.resoudre_combat((5, 7), (10, 4)) == 2        # 55 contre 80
    assert modele.resoudre_combat((5, 5), (5, 5)) == 0         # égalité
    assert modele.resoudre_combat((9, 3), (9, 3)) == 0
    assert modele.resoudre_combat((6, 9), (9, 3)) == 1         # Haiku 5.5 bat GPT-6.1 Sol : 6 x 12 = 72 contre 9 x 6 = 54
    assert modele.resoudre_combat((7, 2), (7, 9)) == 2         # à puissance égale, le plus rapide gagne
    assert modele.resoudre_combat((10, 4), (1, 10)) == 1       # un modèle ultra-rapide ne suffit pas s'il est trop faible


def test_resoudre_combat_symetrie():
    """Échanger les deux cartes doit échanger le résultat (1 <-> 2) et laisser l'égalité (0)."""
    inverse = {0: 0, 1: 2, 2: 1}
    for p1 in range(0, 11, 2):
        for v1 in range(0, 11, 2):
            for p2 in range(0, 11, 2):
                for v2 in range(0, 11, 2):
                    r1 = modele.resoudre_combat((p1, v1), (p2, v2))
                    r2 = modele.resoudre_combat((p2, v2), (p1, v1))
                    assert r1 in (0, 1, 2)
                    assert r2 == inverse[r1]


# ----------------------------------------------------------------------------
# 2. Schéma et contraintes d'intégrité
# ----------------------------------------------------------------------------
def test_tables_presentes():
    preparer()
    noms = {ligne["name"] for ligne in modele.lire("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"Joueur", "Rarete", "Categorie", "Carte", "Possession", "Combat"} <= noms


def test_cles_etrangeres_actives():
    preparer()
    sonnet = carte("Claude Sonnet 5.5")["id_carte"]
    assert est_refuse("INSERT INTO Possession (id_joueur, id_carte, quantite) VALUES (?, ?, 1)", (id_de("alice"), 999))
    assert est_refuse("INSERT INTO Possession (id_joueur, id_carte, quantite) VALUES (?, ?, 1)", (999, sonnet))
    assert est_refuse("""INSERT INTO Carte (nom, editeur, indice, tokens_s, puissance, vitesse, id_rarete, id_categorie)
                         VALUES ('Fantome', 'X', 1.0, 1, 1, 1, 99, 1)""")
    assert est_refuse("""INSERT INTO Combat (id_attaquant, id_defenseur, id_carte_att, id_carte_def)
                         VALUES (?, 999, ?, ?)""", (id_de("alice"), sonnet, sonnet))


def test_contraintes_check_et_unique():
    preparer()
    sonnet = carte("Claude Sonnet 5.5")["id_carte"]
    assert est_refuse("UPDATE Joueur SET pieces = -5 WHERE pseudo = 'alice'")
    assert est_refuse("UPDATE Possession SET quantite = 0 WHERE id_joueur = ?", (id_de("alice"),))
    assert est_refuse("""INSERT INTO Carte (nom, editeur, indice, tokens_s, puissance, vitesse, id_rarete, id_categorie)
                         VALUES ('Trop fort', 'X', 1.0, 1, 11, 1, 1, 1)""")
    assert est_refuse("INSERT INTO Joueur (pseudo, mdp_hash) VALUES ('ALICE', 'x')")   # pseudo unique sans tenir compte de la casse
    assert est_refuse("""INSERT INTO Combat (id_attaquant, id_defenseur, id_carte_att, id_carte_def)
                         VALUES (?, ?, ?, ?)""", (id_de("alice"), id_de("alice"), sonnet, sonnet))   # on ne se défie pas soi-même
    assert est_refuse("INSERT INTO Possession (id_joueur, id_carte) VALUES (?, ?)", (id_de("alice"), sonnet))   # clé primaire composée déjà utilisée


def test_donnees_de_depart():
    preparer()
    assert modele.statistiques() == {"nb_cartes": 24, "nb_joueurs": 3, "nb_combats": 2}
    assert pieces_de("alice") == 100 and pieces_de("bob") == 100      # les récompenses de démonstration sont remises à zéro


# ----------------------------------------------------------------------------
# 3. Les cartes : benchmarks, catégories, raretés, illustrations
# ----------------------------------------------------------------------------
def test_donnees_sql_a_jour():
    """donnees.sql doit être exactement ce que produit generer_donnees.py à partir de modeles.csv."""
    attendu = generer_donnees.construire_sql(generer_donnees.lire_modeles())
    with open(generer_donnees.FICHIER_SQL, encoding="utf-8") as f:
        assert f.read() == attendu


def test_24_cartes_8_par_categorie():
    preparer()
    assert len(modele.catalogue()) == 24
    for id_categorie in (1, 2, 3):
        assert len(modele.catalogue(id_categorie=id_categorie)) == 8
    assert [c["nom"] for c in modele.liste_categories()] == ["Frontier", "Poids ouverts", "Compact"]


def test_repartition_des_raretes():
    preparer()
    nombres = [len(modele.catalogue(id_rarete=i)) for i in (1, 2, 3, 4)]
    assert nombres == [9, 6, 6, 3]                                     # Commune, Rare, Épique, Légendaire
    for id_categorie in (1, 2, 3):
        assert len(modele.catalogue(id_rarete=4, id_categorie=id_categorie)) == 1   # un seul Légendaire par catégorie


def test_stats_coherentes_avec_les_benchmarks():
    """Pour chaque carte, puissance et vitesse sont bien calculées à partir de l'indice et des jetons/s."""
    preparer()
    for ligne in modele.lire("SELECT nom, indice, tokens_s, puissance, vitesse FROM Carte"):
        assert (ligne["puissance"], ligne["vitesse"]) == modele.calculer_stats(ligne["indice"], ligne["tokens_s"]), ligne["nom"]


def test_rare_veut_dire_bon_dans_sa_categorie():
    """Dans une même catégorie, une carte plus rare n'a JAMAIS un score global inférieur à une carte moins rare."""
    preparer()
    lignes = modele.lire("SELECT nom, puissance, vitesse, id_rarete, id_categorie FROM Carte")
    for a in lignes:
        for b in lignes:
            if a["id_categorie"] == b["id_categorie"] and a["id_rarete"] > b["id_rarete"]:
                assert modele.score_global(a["puissance"], a["vitesse"]) >= modele.score_global(b["puissance"], b["vitesse"]), (a["nom"], b["nom"])


def test_cartes_connues():
    preparer()
    legendaires = {c["categorie"]: c["nom"] for c in modele.catalogue(id_rarete=4)}
    assert legendaires == {"Frontier": "Gemini 4 Carbon", "Poids ouverts": "DeepSeek V4.1 Flash", "Compact": "Claude Haiku 5.5"}
    assert carte("Gemini 4 Carbon")["indice"] == 59.4 and carte("Gemini 4 Carbon")["tokens_s"] == 95
    k2 = carte("K2 Horizon 375B A23B")
    assert k2["vitesse"] == 10 and k2["puissance"] == 3                # le plus rapide, mais peu puissant
    # La rareté est relative à la catégorie : le Légendaire Compact est moins puissant qu'un Frontier Commun
    sol = carte("GPT-6.1 Sol")
    haiku = carte("Claude Haiku 5.5")
    assert sol["id_rarete"] == 1 and haiku["id_rarete"] == 4
    assert sol["puissance"] > haiku["puissance"] and haiku["vitesse"] > sol["vitesse"]
    # Chaque éditeur et chaque catégorie sont renseignés
    for ligne in modele.lire("SELECT editeur, description FROM Carte"):
        assert ligne["editeur"] != "" and ligne["description"] != ""


def test_illustrations_generees_par_ia():
    """Chaque carte a son image SVG, et chaque image porte la mention 'illustration IA'."""
    preparer()
    fichiers_vus = set()
    for ligne in modele.lire("SELECT nom, illustration FROM Carte"):
        assert ligne["illustration"] == modele.nom_fichier_illustration(ligne["nom"])
        assert ligne["illustration"] not in fichiers_vus               # une image différente par carte
        fichiers_vus.add(ligne["illustration"])
        chemin = os.path.join(generer_illustrations.DOSSIER_IMAGES, ligne["illustration"])
        assert os.path.exists(chemin), chemin
        with open(chemin, encoding="utf-8") as f:
            svg = f.read()
        assert svg.startswith("<?xml") and "<svg" in svg
        assert "illustration IA" in svg                                # mention visible dans l'image
        assert "Illustration générée par IA" in svg                    # et dans le titre (accessibilité)
    defaut = os.path.join(generer_illustrations.DOSSIER_IMAGES, "defaut.svg")
    assert os.path.exists(defaut)                                      # image des cartes ajoutées par l'admin


def test_illustrations_reproductibles():
    """Le même modèle donne toujours le même dessin ; deux modèles différents, deux dessins différents."""
    a1 = generer_illustrations.dessiner("Beam 1.0", "Compact", 3, 10, 2)
    a2 = generer_illustrations.dessiner("Beam 1.0", "Compact", 3, 10, 2)
    b = generer_illustrations.dessiner("Kimi K3.1 Pro", "Frontier", 8, 1, 1)
    assert a1 == a2
    assert a1 != b


# ----------------------------------------------------------------------------
# 4. Comptes joueurs
# ----------------------------------------------------------------------------
def test_creer_joueur():
    preparer()
    id_joueur, erreur = modele.creer_joueur("charlie", "motdepasse")
    assert erreur is None and id_joueur is not None
    assert pieces_de("charlie") == 100
    ligne = modele.lire_une("SELECT mdp_hash, est_admin FROM Joueur WHERE id_joueur = ?", (id_joueur,))
    assert ligne["mdp_hash"] != "motdepasse"                   # mot de passe jamais stocké en clair
    assert ligne["est_admin"] == 0
    cartes = modele.inventaire(id_joueur)
    assert len(cartes) == 1 and cartes[0]["nom"] == modele.NOM_CARTE_DEPART   # carte de départ
    assert cartes[0]["rarete"] == "Commune"


def test_creer_joueur_refuses():
    preparer()
    avant = modele.statistiques()["nb_joueurs"]
    for pseudo, mdp in [("alice", "motdepasse"), ("ALICE", "motdepasse"),   # déjà pris (même casse différente)
                        ("ab", "motdepasse"), ("charlie", "court")]:
        id_joueur, erreur = modele.creer_joueur(pseudo, mdp)
        assert id_joueur is None and erreur is not None
    assert modele.statistiques()["nb_joueurs"] == avant


def test_verifier_connexion():
    preparer()
    assert modele.verifier_connexion("alice", "alice1234") == id_de("alice")
    assert modele.verifier_connexion("ALICE", "alice1234") == id_de("alice")    # insensible à la casse
    assert modele.verifier_connexion("alice", "mauvais") is None
    assert modele.verifier_connexion("alice", "") is None
    assert modele.verifier_connexion("inconnu", "alice1234") is None


def test_injection_sql():
    preparer()
    assert modele.verifier_connexion("' OR '1'='1", "x") is None
    assert modele.verifier_connexion("alice' --", "x") is None
    assert modele.verifier_connexion("alice", "' OR '1'='1") is None
    id_joueur, erreur = modele.creer_joueur("x'); DROP TABLE Joueur;--", "motdepasse")
    assert id_joueur is None and erreur is not None
    assert modele.statistiques()["nb_joueurs"] == 3            # la table Joueur existe toujours
    assert len(modele.catalogue(id_rarete="1 OR 1=1")) == 0    # une valeur n'est jamais interprétée comme du SQL


def test_changer_pseudo():
    preparer()
    alice = id_de("alice")
    assert modele.changer_pseudo(alice, "alicia") is None
    assert modele.lire_joueur(alice)["pseudo"] == "alicia"
    assert modele.changer_pseudo(alice, "bob") is not None     # pris par un autre joueur
    assert modele.changer_pseudo(alice, "BOB") is not None
    assert modele.changer_pseudo(alice, "x") is not None       # invalide
    assert modele.changer_pseudo(alice, "ALICIA") is None      # on peut changer la casse de son propre pseudo
    assert modele.lire_joueur(alice)["pseudo"] == "ALICIA"


def test_changer_mdp():
    preparer()
    alice = id_de("alice")
    assert modele.changer_mdp(alice, "faux", "nouveaumdp1") is not None
    assert modele.changer_mdp(alice, "alice1234", "court") is not None
    assert modele.verifier_connexion("alice", "alice1234") == alice       # rien n'a changé
    assert modele.changer_mdp(alice, "alice1234", "nouveaumdp1") is None
    assert modele.verifier_connexion("alice", "alice1234") is None
    assert modele.verifier_connexion("alice", "nouveaumdp1") == alice


# ----------------------------------------------------------------------------
# 5. Catalogue
# ----------------------------------------------------------------------------
def test_catalogue_et_filtres():
    preparer()
    assert modele.catalogue()[0]["nom"] == "Gemini 4 Carbon"               # tri : catégorie, puis rareté décroissante
    assert len(modele.catalogue(id_rarete=4)) == 3
    assert {c["nom"] for c in modele.catalogue(id_rarete=2, id_categorie=1)} == {"Muse Wonder", "GPT-6 Astra"}
    assert {c["nom"] for c in modele.catalogue(id_categorie=3, id_rarete=1)} == \
        {"Gemini 3.5 Flash-Lite", "Nemotron 3.5 Lightning", "Mistral Small 4"}
    assert modele.catalogue(id_rarete=99) == []


def test_ajouter_carte():
    preparer()
    id_carte, erreur = modele.ajouter_carte("GPT Nano", "Testeur", "Un petit modèle.", 30.0, 100, 2, 3)
    assert erreur is None and id_carte == 25
    assert len(modele.catalogue()) == 25
    ligne = carte("GPT Nano")
    assert (ligne["editeur"], ligne["indice"], ligne["tokens_s"]) == ("Testeur", 30.0, 100)
    assert (ligne["puissance"], ligne["vitesse"]) == (5, 4)                # calculées par calculer_stats
    assert (ligne["id_rarete"], ligne["id_categorie"]) == (2, 3)
    assert ligne["illustration"] == "defaut.svg"                           # image par défaut
    refus = [("GPT Nano", "X", "", 30.0, 100, 2, 3),        # nom déjà pris
             ("   ", "X", "", 30.0, 100, 2, 3),             # nom vide
             ("Test", "  ", "", 30.0, 100, 2, 3),           # éditeur vide
             ("Test", "X", "", 101, 100, 2, 3),             # indice hors bornes
             ("Test", "X", "", -1, 100, 2, 3),
             ("Test", "X", "", None, 100, 2, 3),            # valeur non numérique reçue du formulaire
             ("Test", "X", "", 30.0, 0, 2, 3),              # vitesse hors bornes
             ("Test", "X", "", 30.0, 6000, 2, 3),
             ("Test", "X", "", 30.0, None, 2, 3),
             ("Test", "X", "", 30.0, 100, 99, 3),           # rareté inconnue
             ("Test", "X", "", 30.0, 100, None, 3),
             ("Test", "X", "", 30.0, 100, 2, 99)]           # catégorie inconnue
    for arguments in refus:
        id_carte, erreur = modele.ajouter_carte(*arguments)
        assert id_carte is None and erreur is not None
    assert len(modele.catalogue()) == 25


# ----------------------------------------------------------------------------
# 6. Inventaire et boosters
# ----------------------------------------------------------------------------
def test_inventaire_et_stats():
    preparer()
    alice = id_de("alice")
    noms = {c["nom"] for c in modele.inventaire(alice)}
    assert noms == {"DeepSeek V4 Pro", "Claude Sonnet 5.5", "GPT-6.1 Sol", "Muse Spark Open", "Gemini 3.8 Flash"}
    assert modele.stats_collection(alice) == (5, 5, 24)
    assert modele.stats_collection(id_de("admin")) == (1, 1, 24)
    assert modele.inventaire(999) == []
    assert modele.stats_collection(999) == (0, 0, 24)          # SUM vide -> 0 et non None


def test_ajouter_a_inventaire():
    preparer()
    alice = id_de("alice")
    con = modele.connexion()
    modele.ajouter_a_inventaire(con, alice, carte("Claude Sonnet 5.5")["id_carte"])    # déjà possédée -> quantité 2
    modele.ajouter_a_inventaire(con, alice, carte("Gemini 4 Carbon")["id_carte"])      # nouvelle ligne
    con.commit()
    con.close()
    quantites = {c["nom"]: c["quantite"] for c in modele.inventaire(alice)}
    assert quantites["Claude Sonnet 5.5"] == 2
    assert quantites["Gemini 4 Carbon"] == 1


def test_acheter_booster():
    preparer()
    alice = id_de("alice")
    _, total_avant, _ = modele.stats_collection(alice)
    cartes = modele.acheter_booster(alice)
    assert cartes is not None and len(cartes) == modele.NB_CARTES_BOOSTER
    for c in cartes:
        assert 1 <= c["id_carte"] <= 24
        assert c["rarete"] in ("Commune", "Rare", "Épique", "Légendaire")
        assert c["categorie"] in ("Frontier", "Poids ouverts", "Compact")
        assert c["illustration"].endswith(".svg")
    assert pieces_de("alice") == 100 - modele.PRIX_BOOSTER
    assert modele.stats_collection(alice)[1] == total_avant + 3
    assert modele.acheter_booster(alice) is not None           # deuxième booster : il reste 50 pièces
    assert pieces_de("alice") == 0
    assert modele.acheter_booster(alice) is None               # plus assez de pièces
    assert pieces_de("alice") == 0
    assert modele.stats_collection(alice)[1] == total_avant + 6


def test_booster_fonds_insuffisants():
    preparer()
    alice = id_de("alice")
    modele.ecrire("UPDATE Joueur SET pieces = 49 WHERE id_joueur = ?", (alice,))
    total_avant = modele.stats_collection(alice)[1]
    assert modele.acheter_booster(alice) is None
    assert pieces_de("alice") == 49                            # rien n'a été débité
    assert modele.stats_collection(alice)[1] == total_avant    # aucune carte ajoutée
    assert modele.acheter_booster(999) is None                 # joueur inconnu


# ----------------------------------------------------------------------------
# 7. Combats
# ----------------------------------------------------------------------------
def test_jouer_combat_victoire_attaquant():
    preparer()
    alice, bob = id_de("alice"), id_de("bob")
    resultat = modele.jouer_combat(alice, bob, carte("Claude Sonnet 5.5")["id_carte"], carte("Beam 1.0")["id_carte"])
    assert resultat["issue"] == 1 and resultat["id_vainqueur"] == alice      # 9 x (15-10) = 45 contre 3 x (15-5) = 30
    assert resultat["pseudo_vainqueur"] == "alice"
    assert resultat["carte_att"]["nom"] == "Claude Sonnet 5.5" and resultat["carte_def"]["nom"] == "Beam 1.0"
    assert pieces_de("alice") == 100 + modele.RECOMPENSE_VICTOIRE
    assert pieces_de("bob") == 100
    ligne = modele.lire_une("SELECT * FROM Combat WHERE id_combat = ?", (resultat["id_combat"],))
    assert (ligne["id_attaquant"], ligne["id_defenseur"], ligne["id_vainqueur"]) == (alice, bob, alice)
    assert nb_combats() == 3


def test_jouer_combat_victoire_defenseur():
    preparer()
    alice, bob = id_de("alice"), id_de("bob")
    depart = carte(modele.NOM_CARTE_DEPART)["id_carte"]
    resultat = modele.jouer_combat(alice, bob, depart, carte("Claude Haiku 5.5")["id_carte"])
    assert resultat["issue"] == 2 and resultat["id_vainqueur"] == bob        # 4 x (15-9) = 24 contre 6 x (15-4) = 66
    assert pieces_de("bob") == 100 + modele.RECOMPENSE_VICTOIRE
    assert pieces_de("alice") == 100


def test_jouer_combat_egalite():
    preparer()
    alice, bob = id_de("alice"), id_de("bob")
    depart = carte(modele.NOM_CARTE_DEPART)["id_carte"]
    resultat = modele.jouer_combat(alice, bob, depart, depart)               # même carte des deux côtés
    assert resultat["issue"] == 0 and resultat["id_vainqueur"] is None
    assert resultat["pseudo_vainqueur"] is None
    assert pieces_de("alice") == 100 + modele.RECOMPENSE_EGALITE
    assert pieces_de("bob") == 100 + modele.RECOMPENSE_EGALITE
    ligne = modele.lire_une("SELECT id_vainqueur FROM Combat WHERE id_combat = ?", (resultat["id_combat"],))
    assert ligne["id_vainqueur"] is None                       # NULL en base


def test_lancer_combat_erreurs():
    preparer()
    alice, bob, admin = id_de("alice"), id_de("bob"), id_de("admin")
    sonnet = carte("Claude Sonnet 5.5")["id_carte"]
    carbone = carte("Gemini 4 Carbon")["id_carte"]
    for arguments in [(alice, alice, sonnet),   # se défier soi-même
                      (alice, 999, sonnet),     # adversaire inconnu
                      (alice, bob, carbone)]:   # alice ne possède pas Gemini 4 Carbon
        resultat, erreur = modele.lancer_combat(*arguments)
        assert resultat is None and erreur is not None
    modele.ecrire("DELETE FROM Possession WHERE id_joueur = ?", (admin,))
    resultat, erreur = modele.lancer_combat(alice, admin, sonnet)   # adversaire sans carte
    assert resultat is None and erreur is not None
    assert nb_combats() == 2                                   # aucun combat enregistré


def test_lancer_combat_ok():
    preparer()
    alice, bob = id_de("alice"), id_de("bob")
    sonnet = carte("Claude Sonnet 5.5")["id_carte"]
    cartes_bob = {c["nom"] for c in modele.inventaire(bob)}
    for essai in range(15):                                    # le défenseur est tiré au hasard : on répète
        resultat, erreur = modele.lancer_combat(alice, bob, sonnet)
        assert erreur is None
        assert resultat["carte_att"]["nom"] == "Claude Sonnet 5.5"
        assert resultat["carte_def"]["nom"] in cartes_bob
        assert resultat["issue"] in (0, 1, 2)
        gagnant = {0: None, 1: alice, 2: bob}[resultat["issue"]]
        assert resultat["id_vainqueur"] == gagnant
    assert nb_combats() == 2 + 15


def test_historique_combats():
    preparer()
    historique = modele.historique_combats()
    assert len(historique) == 2
    dernier = historique[0]                                    # le plus récent d'abord
    assert dernier["attaquant"] == "bob" and dernier["defenseur"] == "alice"
    assert dernier["carte_att"] == "Claude Haiku 5.5" and dernier["carte_def"] == "GPT-6.1 Sol"
    assert dernier["id_vainqueur"] == id_de("bob")             # 6 x (15-3) = 72 contre 9 x (15-9) = 54 : la vitesse l'emporte
    assert len(modele.historique_combats(limite=1)) == 1


def test_classement():
    preparer()
    lignes = modele.classement()
    assert [(l["pseudo"], l["victoires"], l["combats"]) for l in lignes] == \
        [("alice", 1, 2), ("bob", 1, 2), ("admin", 0, 0)]
    alice, bob = id_de("alice"), id_de("bob")
    haiku = carte("Claude Haiku 5.5")["id_carte"]
    depart = carte(modele.NOM_CARTE_DEPART)["id_carte"]
    modele.jouer_combat(bob, alice, haiku, depart)             # Haiku bat DeepSeek V4 Pro
    modele.jouer_combat(bob, alice, haiku, depart)
    lignes = modele.classement()
    assert lignes[0]["pseudo"] == "bob" and lignes[0]["victoires"] == 3
    assert lignes[1]["pseudo"] == "alice" and lignes[1]["victoires"] == 1
    assert lignes[2]["pseudo"] == "admin"


# ----------------------------------------------------------------------------
# 8. Application Flask (routes, formulaires, session)
# ----------------------------------------------------------------------------
def test_pages_publiques():
    preparer()
    client = app.test_client()
    for url in ["/", "/cartes", "/regles", "/classement", "/combats", "/inscription", "/connexion"]:
        assert client.get(url).status_code == 200, url
    page = texte(client.get("/cartes"))
    assert "Gemini 4 Carbon" in page and "Claude Haiku 5.5" in page and "Mistral Small 4" in page
    page = texte(client.get("/cartes?rarete=4"))
    assert "Gemini 4 Carbon" in page and "Claude Haiku 5.5" in page and "Mistral Small 4" not in page
    page = texte(client.get("/cartes?rarete=4&categorie=3"))
    assert "Claude Haiku 5.5" in page and "Gemini 4 Carbon" not in page
    assert client.get("/cartes?rarete=abc").status_code == 200          # paramètre invalide ignoré
    assert "alice" in texte(client.get("/classement"))
    assert client.get("/page-qui-n-existe-pas").status_code == 404


def test_illustrations_signalees_ia_dans_les_pages():
    preparer()
    client = app.test_client()
    page = texte(client.get("/cartes"))
    assert "Illustration générée par IA : Gemini 4 Carbon" in page      # texte alternatif de chaque image
    assert "gemini-4-carbon.svg" in page
    assert page.count("<img") == 24                                     # une image par carte
    for url in ["/", "/cartes", "/regles", "/classement", "/inscription"]:
        assert "générées par IA" in texte(client.get(url)), url          # mention dans le pied de page de toutes les pages
    reponse = client.get("/static/cartes/gemini-4-carbon.svg")
    assert reponse.status_code == 200 and "illustration IA" in texte(reponse)


def test_page_regles_coherente_avec_le_code():
    preparer()
    page = texte(app.test_client().get("/regles"))
    assert "15" in page and str(modele.PRIX_BOOSTER) in page and modele.NOM_CARTE_DEPART in page
    assert "Frontier" in page and "Poids ouverts" in page and "Compact" in page


def test_pages_protegees_redirigent():
    preparer()
    client = app.test_client()
    for url in ["/inventaire", "/booster", "/combat", "/profil", "/admin/carte"]:
        reponse = client.get(url)
        assert reponse.status_code == 302, url
        assert "/connexion" in reponse.headers["Location"], url
    assert client.post("/booster").status_code == 302                   # même en POST


def test_inscription_http():
    preparer()
    client = app.test_client()
    reponse = client.post("/inscription", data={"pseudo": "charlie", "mdp": "motdepasse", "mdp2": "motdepasse"})
    assert reponse.status_code == 302 and reponse.headers["Location"].endswith("/inventaire")
    page = texte(client.get("/inventaire"))                             # connecté automatiquement
    assert modele.NOM_CARTE_DEPART in page and "charlie" in page
    assert pieces_de("charlie") == 100
    # cas d'erreur, avec un client "neuf"
    autre = app.test_client()
    page = texte(autre.post("/inscription", data={"pseudo": "dave", "mdp": "motdepasse", "mdp2": "autrechose"}))
    assert "différents" in page
    page = texte(autre.post("/inscription", data={"pseudo": "alice", "mdp": "motdepasse", "mdp2": "motdepasse"}))
    assert "déjà pris" in page
    page = texte(autre.post("/inscription", data={"pseudo": "x", "mdp": "motdepasse", "mdp2": "motdepasse"}))
    assert "entre 3 et 20" in page
    assert modele.statistiques()["nb_joueurs"] == 4                     # seul charlie a été créé
    assert autre.get("/inventaire").status_code == 302                  # dave n'est pas connecté


def test_connexion_deconnexion_http():
    preparer()
    client = app.test_client()
    reponse = connecter(client, "alice", "mauvais")
    assert reponse.status_code == 200 and "incorrect" in texte(reponse)
    assert client.get("/inventaire").status_code == 302
    reponse = connecter(client, "alice", "alice1234")
    assert reponse.status_code == 302
    page = texte(client.get("/inventaire"))
    assert "Claude Sonnet 5.5" in page and "GPT-6.1 Sol" in page
    assert "Illustration générée par IA : Claude Sonnet 5.5" in page
    assert client.get("/deconnexion").status_code == 302
    assert client.get("/inventaire").status_code == 302                 # session effacée


def test_profil_http():
    preparer()
    client = app.test_client()
    connecter(client, "bob", "bob12345")
    page = texte(client.post("/profil", data={"action": "pseudo", "pseudo": "robert"}))
    assert "Pseudo modifié" in page and "robert" in page
    assert modele.lire_joueur(id_de("robert"))["pseudo"] == "robert"
    page = texte(client.post("/profil", data={"action": "pseudo", "pseudo": "alice"}))
    assert "déjà pris" in page
    page = texte(client.post("/profil", data={"action": "mdp", "ancien": "faux", "nouveau": "nouveaumdp1"}))
    assert "incorrect" in page
    page = texte(client.post("/profil", data={"action": "mdp", "ancien": "bob12345", "nouveau": "nouveaumdp1"}))
    assert "Mot de passe modifié" in page
    assert modele.verifier_connexion("robert", "nouveaumdp1") == id_de("robert")


def test_booster_http():
    preparer()
    client = app.test_client()
    connecter(client, "alice", "alice1234")
    assert "50 pièces" in texte(client.get("/booster"))
    page = texte(client.post("/booster"))
    assert "Tu as obtenu 3 cartes" in page
    assert page.count("Illustration générée par IA") == 3               # une image par carte tirée
    assert pieces_de("alice") == 50
    client.post("/booster")
    assert pieces_de("alice") == 0
    page = texte(client.post("/booster"))
    assert "assez de pièces" in page and "Tu as obtenu" not in page
    assert pieces_de("alice") == 0


def test_combat_http():
    preparer()
    client = app.test_client()
    connecter(client, "alice", "alice1234")
    bob = id_de("bob")
    sonnet = carte("Claude Sonnet 5.5")["id_carte"]
    page = texte(client.get("/combat"))
    assert "bob" in page and "Claude Sonnet 5.5" in page
    assert "Gemini 4 Carbon" not in page                                # alice ne l'a pas
    page = texte(client.post("/combat", data={"adversaire": bob, "carte": sonnet}))
    assert "contre" in page and "Claude Sonnet 5.5" in page
    assert page.count("Illustration générée par IA") == 2               # les deux cartes du duel sont illustrées
    assert nb_combats() == 3
    assert "Choisis un adversaire" in texte(client.post("/combat", data={"adversaire": "", "carte": sonnet}))
    carbone = carte("Gemini 4 Carbon")["id_carte"]
    assert "ne possèdes pas" in texte(client.post("/combat", data={"adversaire": bob, "carte": carbone}))
    assert "toi-même" in texte(client.post("/combat", data={"adversaire": id_de("alice"), "carte": sonnet}))
    assert nb_combats() == 3                                            # les 3 demandes invalides n'ont rien enregistré
    assert "alice" in texte(client.get("/combats"))


def test_admin_http():
    preparer()
    simple = app.test_client()
    connecter(simple, "bob", "bob12345")
    assert simple.get("/admin/carte").status_code == 403
    assert simple.post("/admin/carte", data={"nom": "Pirate", "editeur": "X", "indice": 10, "tokens_s": 50,
                                             "rarete": 1, "categorie": 1}).status_code == 403
    assert len(modele.catalogue()) == 24                                # le joueur simple n'a rien pu ajouter

    admin = app.test_client()
    connecter(admin, "admin", "admin1234")
    page = texte(admin.get("/admin/carte"))
    assert "Épique" in page and "Compact" in page                       # listes déroulantes remplies depuis la base
    donnees = {"nom": "GPT Nano", "editeur": "Testeur", "description": "Petit mais costaud", "indice": 30,
               "tokens_s": 100, "rarete": 2, "categorie": 3}
    assert "Carte ajoutée" in texte(admin.post("/admin/carte", data=donnees))
    assert len(modele.catalogue()) == 25
    assert "GPT Nano" in texte(admin.get("/cartes"))
    assert "déjà ce nom" in texte(admin.post("/admin/carte", data=donnees))
    donnees["nom"] = "Autre"
    donnees["indice"] = 150
    assert "entre 0 et 100" in texte(admin.post("/admin/carte", data=donnees))
    donnees["indice"] = 30
    donnees["rarete"] = 99
    assert "Rareté inconnue" in texte(admin.post("/admin/carte", data=donnees))
    assert len(modele.catalogue()) == 25


# ----------------------------------------------------------------------------
# Lanceur (sans pytest) : python tests.py
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    reussis = 0
    echecs = 0
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_") and callable(fonction):
            try:
                fonction()
                print("OK     ", nom)
                reussis += 1
            except AssertionError as e:
                import traceback
                print("ECHEC  ", nom)
                traceback.print_exc()
                echecs += 1
    for chemin in FICHIERS_TEMP:
        if os.path.exists(chemin):
            os.remove(chemin)
    print()
    print(reussis, "test(s) réussi(s),", echecs, "échec(s).")
    raise SystemExit(1 if echecs > 0 else 0)
