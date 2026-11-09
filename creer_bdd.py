"""
creer_bdd.py -- (ré)initialise la base cartes.db :
  1. crée les tables (schema.sql)
  2. remplit raretés, catégories et les 24 cartes de modèles de langage (donnees.sql,
     fabriqué à partir de modeles.csv par generer_donnees.py)
  3. ajoute des comptes et des combats de démonstration

"""
import os
import sqlite3
import modele


def creer_bdd():
    con = sqlite3.connect(modele.NOM_BDD)
    for fichier in ("schema.sql", "donnees.sql"):
        chemin = os.path.join(modele.DOSSIER, fichier)
        with open(chemin, encoding="utf-8") as f:
            con.executescript(f.read())
    con.commit()
    con.close()

    # comptes de démonstration (le hachage du mot de passe est fait par modele.creer_joueur)
    id_admin, _ = modele.creer_joueur("admin", "admin1234", est_admin=1)
    id_alice, _ = modele.creer_joueur("alice", "alice1234")
    id_bob, _ = modele.creer_joueur("bob", "bob12345")

    # quelques cartes supplémentaires (chacun a déjà la carte de départ, offerte à l'inscription)
    cartes_alice = ["Claude Sonnet 5.5", "GPT-6.1 Sol", "Muse Spark Open", "Gemini 3.8 Flash"]
    cartes_bob = ["DeepSeek V4.1 Flash", "Beam 1.0", "Gemini 4 Argon", "Kimi K3.1 Pro", "Claude Haiku 5.5"]
    for nom in cartes_alice:
        modele.ecrire("INSERT INTO Possession (id_joueur, id_carte, quantite) VALUES (?, ?, 1)",
                      (id_alice, modele.id_carte_par_nom(nom)))
    for nom in cartes_bob:
        modele.ecrire("INSERT INTO Possession (id_joueur, id_carte, quantite) VALUES (?, ?, 1)",
                      (id_bob, modele.id_carte_par_nom(nom)))

    # Deux combats déjà joués, pour que l'historique et le classement ne soient pas vides.
    # sonnet 5.5 (9/5) d'alice contre Beam 1.0 (3/10) de bob : alice gagne
    modele.jouer_combat(id_alice, id_bob, modele.id_carte_par_nom("Claude Sonnet 5.5"), modele.id_carte_par_nom("Beam 1.0"))
    # aiku 5.5 (6/9) de bob contre GPT-6.1 Sol (9/3) d'alice : bob gagne grâce à sa vitesse
    modele.jouer_combat(id_bob, id_alice, modele.id_carte_par_nom("Claude Haiku 5.5"), modele.id_carte_par_nom("GPT-6.1 Sol"))

    modele.ecrire("UPDATE Joueur SET pieces = 100")


if __name__ == "__main__":
    creer_bdd()
    print("Base", modele.NOM_BDD, "créée.")
    print("Comptes : admin/admin1234  alice/alice1234  bob/bob12345")
