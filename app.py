"""
voir docs/UTILISATION_IA.md pour ce qui est pas de moi ou Curzio
"""
from flask import Flask, render_template, request, redirect, url_for, session
import modele

app = Flask(__name__)
# Fait avec IA pour les comptes, `session` se comporte comme un dictionnaire conservé dans un cookie du navigateur.
# le cookie est signé avec secret_key : le joueur peut le lire mais pas le modifier sans connaître la clé'
# grâce à lui le serveur reconnaît le joueur d'une requête à l'autre (HTTP ne garde aucune mémoire)
app.secret_key = "cle-secrete-a-changer"


def joueur_connecte():
    """Renvoie la ligne Joueur du joueur connecté, ou None s'il n'est pas connecté."""
    if "id_joueur" in session:
        return modele.lire_joueur(session["id_joueur"])
    return None


# petite pythonerie : le décorateur enregistre une fonction dont le résultat (ici `joueur`) est ajouté
# automatiquement à TOUS les templates pour pas avoir à écrire joueur=... dans chaque render_template
@app.context_processor
def ajouter_joueur_aux_pages():
    """Rend la variable `joueur` disponible dans tous les templates (barre de navigation)"""
    return {"joueur": joueur_connecte()}


@app.route("/")
def accueil():
    return render_template("accueil.html", stats=modele.statistiques())


@app.route("/cartes")
def cartes():
    """catalogue avec filtres (formulaire GET : les choix sont dans l'URL)"""
    # type=int convertit le paramètre en entier ; on obtient None s'il est absent ou inval
    id_rarete = request.args.get("rarete", type=int)
    id_categorie = request.args.get("categorie", type=int)
    return render_template("cartes.html",
                           cartes=modele.catalogue(id_rarete, id_categorie),
                        raretes=modele.liste_raretes(), categories=modele.liste_categories(),
                           rarete_choisie=id_rarete, categorie_choisie=id_categorie)


@app.route("/classement")
def classement():
    return render_template("classement.html", lignes=modele.classement())


@app.route("/combats")
def combats():
    return render_template("combats.html", combats=modele.historique_combats())


@app.route("/regles")
def regles():
    """page d'explication : benchmarks, caractéristiques d'une carte, rareté, combat, booster"""
    return render_template("regles.html", indice_par_point=modele.INDICE_PAR_POINT,
                        tokens_par_point=modele.TOKENS_PAR_POINT, coef_puissance=modele.COEF_PUISSANCE,
                    coef_vitesse=modele.COEF_VITESSE, base_esquive=modele.BASE_ESQUIVE,
                           prix=modele.PRIX_BOOSTER, nb_cartes_booster=modele.NB_CARTES_BOOSTER,
                        victoire=modele.RECOMPENSE_VICTOIRE, egalite=modele.RECOMPENSE_EGALITE,
                           carte_depart=modele.NOM_CARTE_DEPART)


@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    erreur = None
    if request.method == "POST":
        pseudo = request.form.get("pseudo", "").strip()
        mdp = request.form.get("mdp", "")
        mdp2 = request.form.get("mdp2", "")
        if mdp != mdp2:
            erreur = "Les deux mots de passe sont différents."
        else:
            id_joueur, erreur = modele.creer_joueur(pseudo, mdp)
            if erreur is None:
                session["id_joueur"] = id_joueur          # connexion automatique
                return redirect(url_for("inventaire"))
    return render_template("inscription.html", erreur=erreur)


# pareil sauf qu'on vérifie au lieu d'enregistrer
@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    erreur = None
    if request.method == "POST":
        pseudo = request.form.get("pseudo", "").strip()
        mdp = request.form.get("mdp", "")
        id_joueur = modele.verifier_connexion(pseudo, mdp)
        if id_joueur is None:
            erreur = "Pseudo ou mot de passe incorrect."
        else:
            session["id_joueur"] = id_joueur
            return redirect(url_for("inventaire"))
    return render_template("connexion.html", erreur=erreur)


@app.route("/deconnexion")
def deconnexion():
    session.clear()
    return redirect(url_for("accueil"))


@app.route("/profil", methods=["GET", "POST"])
def profil():
    joueur = joueur_connecte()
    if joueur is None:
        return redirect(url_for("connexion"))
    message = None
    erreur = None
    if request.method == "POST":
        if request.form.get("action") == "pseudo":
            erreur = modele.changer_pseudo(joueur["id_joueur"], request.form.get("pseudo", "").strip())
            if erreur is None:
                message = "Pseudo modifié."
        elif request.form.get("action") == "mdp":
            erreur = modele.changer_mdp(joueur["id_joueur"], request.form.get("ancien", ""),
                                        request.form.get("nouveau", ""))
            if erreur is None:
                message = "Mot de passe modifié."
    return render_template("profil.html", message=message, erreur=erreur)




@app.route("/inventaire")
def inventaire():
    joueur = joueur_connecte()
    if joueur is None:
        return redirect(url_for("connexion"))
    differentes, total, taille_catalogue = modele.stats_collection(joueur["id_joueur"])
    return render_template("inventaire.html", cartes=modele.inventaire(joueur["id_joueur"]), 
                differentes=differentes, total=total, taille_catalogue=taille_catalogue)


@app.route("/booster", methods=["GET", "POST"])
def booster():
    joueur = joueur_connecte()
    if joueur is None:
        return redirect(url_for("connexion"))
    nouvelles_cartes = None
    erreur = None
    if request.method == "POST":
        nouvelles_cartes = modele.acheter_booster(joueur["id_joueur"])
        if nouvelles_cartes is None:
            erreur = "Tu n'as pas assez de pièces pour ouvrir un booster."
    return render_template("booster.html", prix=modele.PRIX_BOOSTER,
                           nouvelles_cartes=nouvelles_cartes, erreur=erreur)


@app.route("/combat", methods=["GET", "POST"])
def combat():
    joueur = joueur_connecte()
    if joueur is None:
        return redirect(url_for("connexion"))
    resultat = None
    erreur = None
    if request.method == "POST":
        id_defenseur = request.form.get("adversaire", type=int)
        id_carte = request.form.get("carte", type=int)
        if id_defenseur is None or id_carte is None:
            erreur = "Choisis un adversaire et une de tes cartes."
        else:
            resultat, erreur = modele.lancer_combat(joueur["id_joueur"], id_defenseur, id_carte)
    return render_template("combat.html", adversaires=modele.liste_joueurs(sauf=joueur["id_joueur"]),
                           mes_cartes=modele.inventaire(joueur["id_joueur"]),
                           resultat=resultat, erreur=erreur)


@app.route("/admin/carte", methods=["GET", "POST"])
def admin_carte():
    joueur = joueur_connecte()
    if joueur is None:
        return redirect(url_for("connexion"))
    if joueur["est_admin"] != 1:
        # très stylé, on peut renvoyer deux arguments et on choisis le type d'erreure + le message
        return "Accès réservé à l'administrateur.", 403
    message = None
    erreur = None
    if request.method == "POST":
        id_carte, erreur = modele.ajouter_carte(
            request.form.get("nom", ""), request.form.get("editeur", ""), request.form.get("description", "").strip(),
            request.form.get("indice", type=float), request.form.get("tokens_s", type=int),
            request.form.get("rarete", type=int), request.form.get("categorie", type=int))
        if erreur is None:
            message = "Carte ajoutée au catalogue (n° " + str(id_carte) + ")."
    return render_template("admin_carte.html", raretes=modele.liste_raretes(),
                           categories=modele.liste_categories(), message=message, erreur=erreur)


if __name__ == "__main__":
    # sqlite_master = la table interne de SQLite qui liste les tables existantes
    # on vérifie que la base a bien été créée pour afficher un message clair plutôt qu'une erreur 500.
    tables = modele.lire("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'Carte'")
    if len(tables) == 0:
        print("La base de données est absente ou vide sale hamar apprends à coder.")
        print("Il faut d'abors lancer  python creer_bdd.py   (depuis le dossier du projet)  c'est IMPORTANT")
    else:
        app.run(debug=True)
