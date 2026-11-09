"""
modele.py -- accès à la base de données et règles du jeu.

En gros, vu qu'on a vu la programmation objet, je me suis dit qu'on pourrait tout mettre dans un fichier, comme ça il
est indépendant de flask, et on peut faire des tests vicieux
  TOUTES les requêtes utilisent des paramètres "?" (jamais de f-string dans le SQL)
ce qui protège contre les injections SQL

"""
import os
import random
import sqlite3
# hachage des mots de passe (outil fourni avec Flask)
#   generate_password_hash(mdp)  -> "empreinte" à sens unique (calculée avec un sel aléatoire) : c'est elle
#                                   qu'on stocke
#   check_password_hash(empreinte, mdp) -> True si le mot de passe saisi redonne la même empreinte.
from werkzeug.security import generate_password_hash, check_password_hash

DOSSIER = os.path.dirname(os.path.abspath(__file__)) #donne le chemin absolu du fichier
NOM_BDD = os.path.join(DOSSIER, "cartes.db")

PRIX_BOOSTER = 50
NB_CARTES_BOOSTER = 3
NOM_CARTE_DEPART = "DeepSeek V4 Pro"   #carte offerte à l'inscription ( deep seek V4.1 flash mog btw )
RECOMPENSE_VICTOIRE = 20
RECOMPENSE_EGALITE = 5  

# passage des benchmarks aux caractéristiques d'une carte (voir docs/BENCHMARKS.md)
INDICE_PAR_POINT = 6       # 1 point de puissance = 6 points d'indice d'intelligence 
TOKENS_PAR_POINT = 25      # 1 point de vitesse = 25 jetons par seconde 
COEF_PUISSANCE = 7         # score global = 7 x puissance + 3 x vitesse
COEF_VITESSE = 3
BASE_ESQUIVE = 15           # combat : dégâts = puissance x (15 - vitesse adverse)

#requête de base réutilisée pour afficher des cartes (3 tables jointes)
REQUETE_CARTES = """
    SELECT c.id_carte, c.nom, c.editeur, c.description, c.indice, c.tokens_s, c.puissance, c.vitesse,
           c.illustration, r.nom AS rarete, r.couleur, cat.nom AS categorie
    FROM Carte AS c
    JOIN Rarete AS r ON c.id_rarete = r.id_rarete
    JOIN Categorie AS cat ON c.id_categorie = cat.id_categorie
"""


# ----------------------------------------------------------------------------
# 1. Accès à la base
# ----------------------------------------------------------------------------
def connexion():
    """Ouvre une connexion. Les lignes lues s'utilisent comme des dictionnaires : ligne["nom"]."""
    con = sqlite3.connect(NOM_BDD)
    #row_factory = sqlite3.Row = on lit une colonne par son nom (ligne["nom"])
    # au lieu de son numéro (ligne[1]).
    con.row_factory = sqlite3.Row
    #      SQLite ne vérifie PAS les clés étrangères tant qu'on n'active pas cette option
    # (à refaire pour chaque connexion). Sans elle Virgile a réussis à récup une carte qui n'existe pas
    con.execute("PRAGMA foreign_keys = ON")
    return con


def lire(sql, params=()):
    """Exécute un SELECT et renvoie la liste de toutes les lignes."""
    con = connexion()
    #petite pythonnerie : try / finally. le bloc finally s'exécute TOUJOURS, même si la requête provoque
    # une erreur (contrainte violée...) La connexion est donc toujours fermée ; fermer sans commit()
    # annule la modification en cours Sans ça la base restait verrouillée ("database is locked")
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def lire_une(sql, params=()):
    """Exécute un SELECT et renvoie la première ligne (ou None s'il n'y a aucun résultat)."""
    con = connexion()
    try:
        return con.execute(sql, params).fetchone()
    finally:
        con.close()


def ecrire(sql, params=()):
    """Exécute un INSERT / UPDATE / DELETE, valide la modification et renvoie l'id de la ligne insérée."""
    con = connexion()

    try:
        curseur = con.execute(sql, params)
        con.commit()
        return curseur.lastrowid
    finally:
        con.close()



def verifier_pseudo(pseudo):
    """renvoie un message d'erreur, ou None si le pseudo est valide."""
    if not (3 <= len(pseudo) <= 20):
        return "Le pseudo doit contenir entre 3 et 20 caractères."
    if not pseudo.isalnum():
        return "Le pseudo ne doit contenir que des lettres et des chiffres."
    return None


def verifier_mdp(mdp):
    """renvoie un message d'erreur, ou None si le mot de passe est valide."""
    if len(mdp) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères."
    return None




def calculer_stats(indice, tokens_s):
    """transforme les benchmarks d'un modèle en caractéristiques de jeu (entiers de 0 à 10).
    indice   : Intelligence Index (puissance générale)  -> puissance = indice / 6, arrondi, plafonné à 10
    tokens_s : vitesse de génération en jetons/seconde -> vitesse   = tokens_s / 25, arrondi, plafonné à 10
    """
    puissance = min(10, int(indice / INDICE_PAR_POINT + 0.5))
    vitesse = min(10, int(tokens_s / TOKENS_PAR_POINT + 0.5))
    return puissance, vitesse

def score_global(puissance, vitesse):
    """note sur 100 qui mesure la puissance AVEC la vitesse : 7 x puissance + 3 x vitesse."""
    return COEF_PUISSANCE * puissance + COEF_VITESSE * vitesse


def cle_rang(modele):
    """cclé de tri d'un modèle : meilleur score global d'abord, puis meilleur indice, puis ordre alphabétique."""
    puissance, vitesse = calculer_stats(modele["indice"], modele["tokens_s"])
    return (-score_global(puissance, vitesse), -modele["indice"], modele["nom"])


def rangs_dans_categorie(modeles):
    """modeles : liste de dictionnaires (nom, indice, tokens_s) d'UNE SEULE catégorie.
    Renvoie un dictionnaire {nom : rang}, le rang 1 étant le meilleur."""
    classement = sorted(modeles, key=cle_rang)
    rangs = {}
    for position in range(len(classement)):
        rangs[classement[position]["nom"]] = position + 1
    return rangs


def rarete_du_rang(rang, nb_modeles):
    """rareté d'après le rang dans la catégorie : le meilleur huitième est Légendaire (4), les
    2 huitièmes suivants Épiques (3), les 2 suivants Rares (2), le reste Communes (1).
    Avec 8 modèles : rang 1 -> 4 ; rangs 2-3 -> 3 ; rangs 4-5 -> 2 ; rangs 6-8 -> 1."""
    if rang * 8 <= nb_modeles:
        return 4
    if rang * 8 <= 3 * nb_modeles:
        return 3
    if rang * 8 <= 5 * nb_modeles:
        return 2
    return 1


def nom_fichier_illustration(nom):
    """nom du fichier image d'un modèle : minuscules, tout caractère non alphanumérique devient '-'.
    Exemple : 'GPT-6.1 Sol' -> 'gpt-6-1-sol.svg'."""
    morceaux = []
    precedent_est_tiret = True            # évite un tiret au début et les tirets doubles
    for caractere in nom.lower():
        if caractere.isalnum():
            morceaux.append(caractere)
            precedent_est_tiret = False
        elif not precedent_est_tiret:
            morceaux.append("-")
            precedent_est_tiret = True
    if len(morceaux) > 0 and morceaux[-1] == "-":
        morceaux.pop()
    return "".join(morceaux) + ".svg"


def resoudre_combat(carte_att, carte_def):
    """règle du jeu
    Dégâts infligés par une carte = sa puissance x (15 - vitesse de la carte adverse) :
    plus l'adversaire est rapide, plus il est difficile à toucher (dégâts multipliés par 5 au minimum, 14 au maximum).
    Renvoie 1 si l'attaquant gagne, 2 si le défenseur gagne, 0 en cas d'égalité."""
    puissance1, vitesse1 = carte_att
    puissance2, vitesse2 = carte_def
    degats_sur_defenseur = puissance1 * (BASE_ESQUIVE - vitesse2)
    degats_sur_attaquant = puissance2 * (BASE_ESQUIVE - vitesse1)
    if degats_sur_defenseur > degats_sur_attaquant:
        return 1
    if degats_sur_defenseur < degats_sur_attaquant:
        return 2
    return 0




def creer_joueur(pseudo, mdp, est_admin=0):
    """Inscrit un joueur. Renvoie (id_joueur, None) ou (None, message d'erreur)."""
    erreur = verifier_pseudo(pseudo)
    if erreur is None:
        erreur = verifier_mdp(mdp)
    if erreur is not None:
        return None, erreur
    if lire_une("SELECT id_joueur FROM Joueur WHERE pseudo = ?", (pseudo,)) is not None:
        return None, "Ce pseudo est déjà pris."

    con = connexion()
    try:
        curseur = con.execute("INSERT INTO Joueur (pseudo, mdp_hash, est_admin) VALUES (?, ?, ?)",
                              (pseudo, generate_password_hash(mdp), est_admin))
        id_joueur = curseur.lastrowid
        depart = con.execute("SELECT id_carte FROM Carte WHERE nom = ?", (NOM_CARTE_DEPART,)).fetchone()
        if depart is not None:
            con.execute("INSERT INTO Possession (id_joueur, id_carte, quantite) VALUES (?, ?, 1)",
                        (id_joueur, depart["id_carte"]))
        con.commit()
    finally:
        con.close()
    return id_joueur, None


def verifier_connexion(pseudo, mdp):
    """renvoie l'id du joueur si pseudo et mot de passe sont corrects, sinon None."""
    ligne = lire_une("SELECT id_joueur, mdp_hash FROM Joueur WHERE pseudo = ?", (pseudo,))
    if ligne is None:
        return None
    if check_password_hash(ligne["mdp_hash"], mdp):
        return ligne["id_joueur"]
    return None


def lire_joueur(id_joueur):
    return lire_une("""SELECT id_joueur, pseudo, pieces, est_admin, date_inscription
                       FROM Joueur WHERE id_joueur = ?""", (id_joueur,))


def liste_joueurs(sauf=None):
    """tous les joueurs (pour une liste déroulante), sauf éventuellement celui dont l'id est donné."""
    if sauf is None:
        return lire("SELECT id_joueur, pseudo FROM Joueur ORDER BY pseudo")
    return lire("SELECT id_joueur, pseudo FROM Joueur WHERE id_joueur <> ? ORDER BY pseudo", (sauf,))


def changer_pseudo(id_joueur, nouveau_pseudo):
    """UPDATE du pseudo. Renvoie un message d'erreur ou None."""
    erreur = verifier_pseudo(nouveau_pseudo)
    if erreur is not None:
        return erreur
    autre = lire_une("SELECT id_joueur FROM Joueur WHERE pseudo = ? AND id_joueur <> ?",
                     (nouveau_pseudo, id_joueur))
    if autre is not None:
        return "Ce pseudo est déjà pris."
    ecrire("UPDATE Joueur SET pseudo = ? WHERE id_joueur = ?", (nouveau_pseudo, id_joueur))
    return None


def changer_mdp(id_joueur, ancien, nouveau):
    """UPDATE du mot de passe (après vérification de l'ancien). Renvoie un message d'erreur ou None."""
    ligne = lire_une("SELECT mdp_hash FROM Joueur WHERE id_joueur = ?", (id_joueur,))
    if ligne is None or not check_password_hash(ligne["mdp_hash"], ancien):
        return "L'ancien mot de passe est incorrect."
    erreur = verifier_mdp(nouveau)
    if erreur is not None:
        return erreur
    ecrire("UPDATE Joueur SET mdp_hash = ? WHERE id_joueur = ?", (generate_password_hash(nouveau), id_joueur))
    return None





def liste_raretes():
    return lire("SELECT id_rarete, nom FROM Rarete ORDER BY id_rarete")


def liste_categories():
    return lire("SELECT id_categorie, nom FROM Categorie ORDER BY id_categorie")


def id_carte_par_nom(nom):
    """renvoie l'id de la carte portant ce nom, ou None."""
    ligne = lire_une("SELECT id_carte FROM Carte WHERE nom = ?", (nom,))
    if ligne is None:
        return None
    return ligne["id_carte"]


def catalogue(id_rarete=None, id_categorie=None):
    """cartes du catalogue, avec filtres facultatifs. Le SQL est construit morceau par morceau,
    mais les valeurs passent toujours par des paramètres '?'."""
    sql = REQUETE_CARTES + " WHERE 1 = 1"
    params = []
    if id_rarete is not None:
        sql = sql + " AND c.id_rarete = ?"
        params.append(id_rarete)
    if id_categorie is not None:
        sql = sql + " AND c.id_categorie = ?"
        params.append(id_categorie)
    sql = sql + " ORDER BY c.id_categorie, c.id_rarete DESC, c.puissance DESC, c.nom"
    return lire(sql, params)


def ajouter_carte(nom, editeur, description, indice, tokens_s, id_rarete, id_categorie):
    """INSERT dans Carte (table avec 2 clés étrangères). La puissance et la vitesse sont calculées
    à partir des benchmarks. Renvoie (id_carte, None) ou (None, message d'erreur)."""
    nom = nom.strip()
    editeur = editeur.strip()
    if nom == "" or editeur == "":
        return None, "Le nom et l'éditeur sont obligatoires."
    if indice is None or not (0 <= indice <= 100):
        return None, "L'indice d'intelligence doit être un nombre entre 0 et 100."
    if tokens_s is None or not (1 <= tokens_s <= 5000):
        return None, "La vitesse doit être un entier entre 1 et 5000 jetons par seconde."
    if lire_une("SELECT id_carte FROM Carte WHERE nom = ?", (nom,)) is not None:
        return None, "Une carte porte déjà ce nom."
    if lire_une("SELECT id_rarete FROM Rarete WHERE id_rarete = ?", (id_rarete,)) is None:
        return None, "Rareté inconnue."
    if lire_une("SELECT id_categorie FROM Categorie WHERE id_categorie = ?", (id_categorie,)) is None:
        return None, "Catégorie inconnue."
    puissance, vitesse = calculer_stats(indice, tokens_s)
    id_carte = ecrire("""INSERT INTO Carte (nom, editeur, description, indice, tokens_s, puissance, vitesse,
                                            id_rarete, id_categorie)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (nom, editeur, description, indice, tokens_s, puissance, vitesse, id_rarete, id_categorie))
    return id_carte, None


def statistiques():
    """chiffres affichés sur la page d'accueil."""
    nb_cartes = lire_une("SELECT COUNT(*) AS n FROM Carte")["n"]
    nb_joueurs = lire_une("SELECT COUNT(*) AS n FROM Joueur")["n"]
    nb_combats = lire_une("SELECT COUNT(*) AS n FROM Combat")["n"]
    return {"nb_cartes": nb_cartes, "nb_joueurs": nb_joueurs, "nb_combats": nb_combats}


# ----------------------------------------------------------------------------
# 5. Inventaire et boosters
# ----------------------------------------------------------------------------
def inventaire(id_joueur):
    """Cartes possédées par un joueur (jointure de 4 tables)."""
    return lire("""
        SELECT c.id_carte, c.nom, c.editeur, c.puissance, c.vitesse, c.illustration, p.quantite,
               r.nom AS rarete, r.couleur, cat.nom AS categorie
        FROM Possession AS p
        JOIN Carte AS c ON p.id_carte = c.id_carte
        JOIN Rarete AS r ON c.id_rarete = r.id_rarete
        JOIN Categorie AS cat ON c.id_categorie = cat.id_categorie
        WHERE p.id_joueur = ?
        ORDER BY r.id_rarete DESC, c.puissance DESC, c.nom
    """, (id_joueur,))


def stats_collection(id_joueur):
    """renvoie (nombre de cartes différentes possédées, nombre total d'exemplaires, taille du catalogue)."""
    differentes = lire_une("SELECT COUNT(*) AS n FROM Possession WHERE id_joueur = ?", (id_joueur,))["n"]
    total = lire_une("SELECT SUM(quantite) AS n FROM Possession WHERE id_joueur = ?", (id_joueur,))["n"]
    if total is None:          # SUM d'un ensemble vide vaut NULL
        total = 0
    taille_catalogue = lire_une("SELECT COUNT(*) AS n FROM Carte")["n"]
    return differentes, total, taille_catalogue


def tirer_rarete(raretes, tirage):
    """choisit une rareté selon son poids.
    raretes : liste de couples (id_rarete, poids) ; tirage : entier entre 1 et la somme des poids.
    Exemple : [(1, 60), (2, 25), (3, 12), (4, 3)] -> tirage 1 à 60 : 1 ; 61 à 85 : 2 ; 86 à 97 : 3 ; 98 à 100 : 4."""
    cumul = 0
    for id_rarete, poids in raretes:
        cumul = cumul + poids
        if tirage <= cumul:
            return id_rarete
    return raretes[-1][0]      # par sécurité, si le tirage dépasse le total


def ajouter_a_inventaire(con, id_joueur, id_carte):
    """ajoute un exemplaire : crée la ligne de Possession ou augmente la quantité."""
    ligne = con.execute("SELECT quantite FROM Possession WHERE id_joueur = ? AND id_carte = ?",
                        (id_joueur, id_carte)).fetchone()
    if ligne is None:
        con.execute("INSERT INTO Possession (id_joueur, id_carte, quantite) VALUES (?, ?, 1)",
                    (id_joueur, id_carte))
    else:
        con.execute("UPDATE Possession SET quantite = quantite + 1 WHERE id_joueur = ? AND id_carte = ?",
                    (id_joueur, id_carte))


def acheter_booster(id_joueur):
    """débite PRIX_BOOSTER pièces et ajoute NB_CARTES_BOOSTER cartes tirées au hasard.
    Renvoie la liste des cartes obtenues, ou None si le joueur n'a pas assez de pièces.
    Tout se fait dans UNE transaction : si une étape échoue, rien n'est enregistré."""
    con = connexion()
    # [IA] try / finally : voir lire()
    try:
        joueur = con.execute("SELECT pieces FROM Joueur WHERE id_joueur = ?", (id_joueur,)).fetchone()
        if joueur is None or joueur["pieces"] < PRIX_BOOSTER:
            return None

        raretes = []
        for ligne in con.execute("SELECT id_rarete, poids_tirage FROM Rarete ORDER BY id_rarete"):
            raretes.append((ligne["id_rarete"], ligne["poids_tirage"]))
        total_poids = 0
        for _, poids in raretes:
            total_poids = total_poids + poids

        obtenues = []
        for _ in range(NB_CARTES_BOOSTER):
            id_rarete = tirer_rarete(raretes, random.randint(1, total_poids))
            candidates = con.execute("SELECT id_carte FROM Carte WHERE id_rarete = ?", (id_rarete,)).fetchall()
            if len(candidates) == 0:                   # aucune carte de cette rareté : on prend n'importe laquelle
                candidates = con.execute("SELECT id_carte FROM Carte").fetchall()
            id_carte = random.choice(candidates)["id_carte"]
            ajouter_a_inventaire(con, id_joueur, id_carte)
            obtenues.append(con.execute(REQUETE_CARTES + " WHERE c.id_carte = ?", (id_carte,)).fetchone())

        con.execute("UPDATE Joueur SET pieces = pieces - ? WHERE id_joueur = ?", (PRIX_BOOSTER, id_joueur))
        con.commit()
        return obtenues
    finally:
        con.close()


# ----------------------------------------------------------------------------
# 6. Combats entre joueurs
# ----------------------------------------------------------------------------
def jouer_combat(id_attaquant, id_defenseur, id_carte_att, id_carte_def):
    """Résout le combat, l'enregistre dans Combat et verse les récompenses. Renvoie un dictionnaire."""
    requete_carte = "SELECT nom, editeur, puissance, vitesse, illustration FROM Carte WHERE id_carte = ?"
    carte_att = lire_une(requete_carte, (id_carte_att,))
    carte_def = lire_une(requete_carte, (id_carte_def,))
    issue = resoudre_combat((carte_att["puissance"], carte_att["vitesse"]),
                            (carte_def["puissance"], carte_def["vitesse"]))
    if issue == 1:
        id_vainqueur = id_attaquant
    elif issue == 2:
        id_vainqueur = id_defenseur
    else:
        id_vainqueur = None

    con = connexion()
    # [IA] try / finally : voir lire()
    try:
        curseur = con.execute("""INSERT INTO Combat (id_attaquant, id_defenseur, id_carte_att, id_carte_def, id_vainqueur)
                                 VALUES (?, ?, ?, ?, ?)""",
                              (id_attaquant, id_defenseur, id_carte_att, id_carte_def, id_vainqueur))
        if id_vainqueur is None:
            recompense = RECOMPENSE_EGALITE
            for id_joueur in (id_attaquant, id_defenseur):
                con.execute("UPDATE Joueur SET pieces = pieces + ? WHERE id_joueur = ?", (recompense, id_joueur))
        else:
            recompense = RECOMPENSE_VICTOIRE
            con.execute("UPDATE Joueur SET pieces = pieces + ? WHERE id_joueur = ?", (recompense, id_vainqueur))
        con.commit()
        id_combat = curseur.lastrowid
    finally:
        con.close()

    pseudo_vainqueur = None
    if id_vainqueur is not None:
        pseudo_vainqueur = lire_joueur(id_vainqueur)["pseudo"]
    return {"id_combat": id_combat, "issue": issue, "id_vainqueur": id_vainqueur,
            "pseudo_att": lire_joueur(id_attaquant)["pseudo"], "pseudo_def": lire_joueur(id_defenseur)["pseudo"],
            "pseudo_vainqueur": pseudo_vainqueur, "carte_att": carte_att, "carte_def": carte_def,
            "recompense": recompense}


def lancer_combat(id_attaquant, id_defenseur, id_carte_att):
    """vérifie la demande, tire au hasard la carte du défenseur parmi les siennes, puis joue le combat.
    renvoie (résultat, None) ou (None, message d'erreur)."""
    if id_attaquant == id_defenseur:
        return None, "Tu ne peux pas te défier toi-même."
    if lire_joueur(id_defenseur) is None:
        return None, "Adversaire inconnu."
    if lire_une("SELECT id_carte FROM Possession WHERE id_joueur = ? AND id_carte = ?",
                (id_attaquant, id_carte_att)) is None:
        return None, "Tu ne possèdes pas cette carte."
    cartes_defenseur = lire("SELECT id_carte FROM Possession WHERE id_joueur = ?", (id_defenseur,))
    if len(cartes_defenseur) == 0:
        return None, "Ton adversaire ne possède aucune carte."
    id_carte_def = random.choice(cartes_defenseur)["id_carte"]
    return jouer_combat(id_attaquant, id_defenseur, id_carte_att, id_carte_def), None


def historique_combats(limite=20):
    """derniers combats (jointure de 5 tables : Combat, Joueur x2, Carte x2, avec alias)."""
    return lire("""
        SELECT co.id_combat, co.date_combat, co.id_attaquant, co.id_vainqueur,
               a.pseudo AS attaquant, d.pseudo AS defenseur,
               ca.nom AS carte_att, cd.nom AS carte_def
        FROM Combat AS co
        JOIN Joueur AS a  ON co.id_attaquant = a.id_joueur
        JOIN Joueur AS d  ON co.id_defenseur = d.id_joueur
        JOIN Carte  AS ca ON co.id_carte_att = ca.id_carte
        JOIN Carte  AS cd ON co.id_carte_def = cd.id_carte
        ORDER BY co.id_combat DESC
        LIMIT ?
    """, (limite,))


def cle_classement(ligne):
    """clé de tri : plus de victoires d'abord, puis moins de combats joués, puis ordre alphabétique."""
    return (-ligne["victoires"], ligne["combats"], ligne["pseudo"].lower())


def classement():
    """classement des joueurs. (Version avancée possible avec GROUP BY, mais ici on reste
    sur COUNT + WHERE + un tri en Python.)"""
    resultat = []
    for joueur in lire("SELECT id_joueur, pseudo FROM Joueur"):
        id_joueur = joueur["id_joueur"]
        victoires = lire_une("SELECT COUNT(*) AS n FROM Combat WHERE id_vainqueur = ?", (id_joueur,))["n"]
        combats = lire_une("SELECT COUNT(*) AS n FROM Combat WHERE id_attaquant = ? OR id_defenseur = ?",
                           (id_joueur, id_joueur))["n"]
        resultat.append({"pseudo": joueur["pseudo"], "victoires": victoires, "combats": combats})
    return sorted(resultat, key=cle_classement)
