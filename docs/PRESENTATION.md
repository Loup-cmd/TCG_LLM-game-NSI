# LLM Cards - document de présentation


## 1. L'idée

LLM Cards est un jeu de cartes à collectionner en ligne. **Chaque carte est un vrai modèle de langage**, classé d'après ses résultats aux benchmarks récents : sa puissance (indice d'intelligence) et sa vitesse (jetons par seconde). Une carte rare est un des meilleurs modèles de sa catégorie (Frontier, Poids ouverts ou Compact). Le joueur crée un compte, ouvre des boosters pour compléter sa collection et défie les autres joueurs. Les résultats alimentent un classement.

## 2. Fonctionnalités

| Page | Ce que fait le joueur | Compétence travaillée |
|---|---|---|
| Accueil, règles | Comprendre le jeu et le calcul des cartes | routes Flask (niveau 1) |
| Catalogue | Parcourir et filtrer les 24 cartes avec leur illustration | requête SQL avec jointures, tableau (niveau 4) |
| Inscription, connexion | Créer un compte, se connecter | formulaires POST, INSERT (niveaux 2 et 3) |
| Profil | Changer de pseudo ou de mot de passe | UPDATE d'une table sans clé étrangère (niveau 3) |
| Inventaire | Voir ses cartes et sa progression | SELECT avec 4 tables jointes, tableau HTML (niveau 4) |
| Booster | Acheter 3 cartes tirées au hasard | transaction : UPDATE + INSERT/UPDATE (niveau 5) |
| Combat | Choisir un adversaire et une carte dans des listes déroulantes | INSERT avec clés étrangères (niveau 5) |
| Historique, classement | Consulter les résultats | jointures, COUNT (niveau 4) |
| Ajout de modèle (admin) | Créer une carte avec rareté et catégorie en listes déroulantes | INSERT avec clés étrangères (niveau 5) |


## 3. Des cartes fondées sur des données

Les 24 modèles et leurs mesures sont dans `modeles.csv` (relevé du 2 novembre 2026, indice d'Artificial Analysis et vitesse médiane). Le programme calcule `puissance = indice / 6` et `vitesse = jetons par seconde / 25` (entiers de 0 à 10), puis un score global `7 x puissance + 3 x vitesse`. Dans chaque catégorie, les modèles sont classés par ce score et la **rareté dépend du rang**. Ainsi Claude Haiku 5.5, meilleur modèle compact, est Légendaire, alors que GPT-6.1 Sol, plus puissant mais dans la catégorie Frontier, est Commun. Voir `docs/BENCHMARKS.md`.

## 4. Architecture

Le navigateur (client) envoie des requêtes HTTP au serveur Flask, qui interroge la base SQLite et renvoie une page HTML construite avec Jinja.

- `app.py` : les routes (une fonction par page) ;
- `modele.py` : toutes les requêtes SQL et les règles du jeu, sans dépendance à Flask, donc testables seules ;
- `modeles.csv`, `generer_donnees.py`, `schema.sql`, `donnees.sql`, `creer_bdd.py` : les données et la base ;
- `templates/` et `static/` : l'affichage et les illustrations ;
- `tests.py` : 51 tests automatiques.

## 5. Base de données

6 tables (voir `docs/MCD_et_SR.md` pour le MCD et le schéma relationnel). Le point clé est la table `Possession`, qui relie joueurs et cartes (association plusieurs-à-plusieurs) et porte la quantité d'exemplaires. La table `Carte` garde les mesures brutes (`indice`, `tokens_s`) et les valeurs de jeu qui en découlent (`puissance`, `vitesse`) : les benchmarks changent chaque mois, mais une carte déjà possédée ne doit pas changer.

## 6. Difficultés rencontrées

- **Équilibrer le combat** : la première règle (`puissance - vitesse adverse`) donnait 45 % d'égalités. Nous avons simulé les 552 combats possibles entre les 24 cartes pour comparer plusieurs règles et retenu `puissance x (15 - vitesse adverse)` : 3 % d'égalités, et le taux de victoire augmente avec la rareté. La simulation a aussi montré que la première carte de départ ne gagnait jamais, nous l'avons remplacée.
- **Clés étrangères ignorées** : SQLite ne les vérifie pas par défaut. Solution : `PRAGMA foreign_keys = ON` à chaque connexion ; un test vérifie que l'insertion d'une carte inexistante est refusée.
- **Injections SQL** : une requête construite avec du texte permettrait de se connecter sans mot de passe. Solution : uniquement des requêtes paramétrées (`?`) ; un test tente `' OR '1'='1`.
- **Base verrouillée** après une erreur : la connexion restait ouverte. Solution : `try / finally` pour toujours fermer la connexion.
- **Booster** : si le débit réussit mais pas l'ajout des cartes, le joueur perd ses pièces. Solution : une seule connexion et un seul `commit()` pour tout valider ou tout annuler.
- **Données qui changent** : les benchmarks évoluent et les sources se contredisent légèrement (surtout sur la vitesse). Nous avons figé un relevé daté, avec ses limites, dans `docs/BENCHMARKS.md`.

## 7. Utilisation de l'IA


J'ai utilisé une IA (Claude) **uniquement pour des éléments hors programme** dont on ne trouvais pas de solution tout seul.

| Élément | Ce que j'en ai compris |
|---|---|
| **Illustrations des cartes** | Elles sont **générées par IA** (fichiers SVG fabriqués par `generer_illustrations.py`). Le fond indique la catégorie, le cadre et les étoiles la rareté, le nombre de neurones la puissance, les traits la vitesse. La mention « illustration IA » figure dans chaque image et dans le pied de page. |
| Hachage des mots de passe | La base stocke une empreinte à sens unique (avec un sel aléatoire) ; à la connexion on recalcule l'empreinte et on la compare. |
| Session Flask | Un cookie signé garde l'identifiant du joueur d'une requête à l'autre, car HTTP n'a pas de mémoire. |
| `PRAGMA foreign_keys` | SQLite ne vérifie pas les clés étrangères par défaut. J'ai retiré la ligne et vu le test `test_cles_etrangeres_actives` échouer. |

L'IA m'a aussi aidé à rechercher les benchmarks ; je les ai vérifiés sur plusieurs sites (`docs/BENCHMARKS.md`).

Tout le rest ( surtout les compétences ) a été fait 100% par nous deux à la sueur de notre front.

## 8. Limites et améliorations possibles

Un seul combat à la fois, sans échange de cartes entre joueurs ; la carte du défenseur est tirée au hasard. Pistes : échanges, decks de plusieurs cartes, combats en plusieurs manches, mise à jour automatique des benchmarks, protection contre les attaques CSRF.

## 9. Bilan

Projet bcp trop ambicieux, on a bcp galéré, Loup a pu avancer tout seul quand Curzio avait des problèmes de timing, mais on s'en est sorti à 50/50 ( surtout sur ce qui est évalué, le travail est parfaitement réparti normalement ).