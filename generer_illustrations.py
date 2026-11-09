"""
generer_illustrations.py -- fabrique l'illustration de chaque carte (fichiers SVG dans static/cartes/).

[IA] TOUT CE FICHIER EST HORS PROGRAMME de NSI : les illustrations sont GÉNÉRÉES PAR UNE IA (Claude).
  - SVG : format d'image vectorielle écrit en texte (balises <rect>, <circle>, <line>...) que le navigateur dessine.
  - random.Random(nom) : générateur pseudo-aléatoire initialisé avec le nom du modèle :
    le même nom redonne toujours le même dessin, et deux modèles n'ont jamais le même.
Chaque dessin est une petite "constellation de neurones" qui traduit les caractéristiques de la carte :
    nombre de neurones par couche = puissance ; nombre de traits de vitesse = vitesse ;
    couleur du cadre et étoiles = rareté ; couleur du fond = catégorie.
Aucune illustration ne reprend de logo ni de marque. Chaque image porte la mention "illustration IA".

Usage :  python generer_illustrations.py
"""
import os
import random
import generer_donnees
import modele

DOSSIER_IMAGES = os.path.join(modele.DOSSIER, "static", "cartes")
LARGEUR = 240
HAUTEUR = 160
FONDS = {"Frontier": ("#16215e", "#6a2fa8"),
         "Poids ouverts": ("#07463a", "#1f9d73"),
         "Compact": ("#7a2e00", "#e08a1e"),
         "defaut": ("#2b2f3a", "#5b6475")}
COULEURS_RARETE = {}
for _id, _nom, _couleur, _poids in generer_donnees.RARETES:
    COULEURS_RARETE[_id] = _couleur
NB_ETOILES = {1: 0, 2: 1, 3: 2, 4: 4}      # plus la carte est rare, plus elle brille


def echapper(texte):
    """Remplace les caractères spéciaux du XML."""
    return texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def etoile(cx, cy, r):
    """Étoile à 4 branches (polygone à 8 sommets)."""
    sommets = [(cx, cy - r), (cx + r * 0.25, cy - r * 0.25), (cx + r, cy), (cx + r * 0.25, cy + r * 0.25),
               (cx, cy + r), (cx - r * 0.25, cy + r * 0.25), (cx - r, cy), (cx - r * 0.25, cy - r * 0.25)]
    points = " ".join("%.1f,%.1f" % (x, y) for x, y in sommets)
    return '<polygon points="' + points + '" fill="#ffe08a"/>'


def dessiner(nom, categorie, puissance, vitesse, id_rarete):
    """Renvoie le texte SVG de l'illustration d'une carte."""
    hasard = random.Random(nom)
    haut, bas = FONDS[categorie]
    couleur_cadre = COULEURS_RARETE[id_rarete]
    elements = []

    # 1. Traits de vitesse : un trait par point de vitesse
    for _ in range(vitesse):
        y = 14 + hasard.random() * 120
        x = hasard.random() * 70
        longueur = 30 + 6 * vitesse + hasard.random() * 40
        elements.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ffffff" stroke-opacity="0.28" '
                        'stroke-width="2" stroke-linecap="round"/>' % (x, y, x + longueur, y))

    # 2. Réseau de neurones : 3 couches de (1 + puissance // 2) neurones
    nb = 1 + puissance // 2
    couches = []
    for x in (60, 120, 180):
        couche = []
        for k in range(nb):
            if nb == 1:
                y = 80
            else:
                y = 32 + k * (96 / (nb - 1))
            couche.append((x + hasard.uniform(-6, 6), y + hasard.uniform(-5, 5)))
        couches.append(couche)
    for c in range(len(couches) - 1):
        for x1, y1 in couches[c]:
            for x2, y2 in couches[c + 1]:
                if hasard.random() < 0.7:
                    elements.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ffffff" '
                                    'stroke-opacity="0.35" stroke-width="1"/>' % (x1, y1, x2, y2))
    for couche in couches:
        for x, y in couche:
            elements.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffffff" fill-opacity="0.92"/>'
                            % (x, y, 3 + hasard.random() * 2.5))
    vedette_x, vedette_y = couches[1][hasard.randrange(nb)]     # un neurone "vedette" avec un halo
    elements.append('<circle cx="%.1f" cy="%.1f" r="12" fill="%s" fill-opacity="0.35"/>' % (vedette_x, vedette_y, couleur_cadre))
    elements.append('<circle cx="%.1f" cy="%.1f" r="5.5" fill="%s" stroke="#ffffff" stroke-width="1.5"/>'
                    % (vedette_x, vedette_y, couleur_cadre))

    # 3. Étoiles selon la rareté
    for _ in range(NB_ETOILES[id_rarete]):
        elements.append(etoile(14 + hasard.random() * 212, 12 + hasard.random() * 120, 5 + hasard.random() * 4))

    titre = "Illustration générée par IA : " + echapper(nom)
    description = ("Réseau de %d neurones par couche (puissance %d sur 10) et %d traits de vitesse (vitesse %d sur 10)."
                   % (nb, puissance, vitesse, vitesse))
    morceaux = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="t d">'
                % (LARGEUR, HAUTEUR, LARGEUR, HAUTEUR),
                '<title id="t">' + titre + '</title>',
                '<desc id="d">' + description + '</desc>',
                '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/>'
                '<stop offset="1" stop-color="%s"/></linearGradient>'
                '<clipPath id="c"><rect x="0" y="0" width="%d" height="%d" rx="12"/></clipPath></defs>'
                % (haut, bas, LARGEUR, HAUTEUR),
                '<g clip-path="url(#c)">',
                '<rect width="%d" height="%d" fill="url(#g)"/>' % (LARGEUR, HAUTEUR)]
    morceaux = morceaux + elements
    morceaux.append('</g>')
    morceaux.append('<rect x="2.5" y="2.5" width="%d" height="%d" rx="11" fill="none" stroke="%s" stroke-width="5"/>'
                    % (LARGEUR - 5, HAUTEUR - 5, couleur_cadre))
    morceaux.append('<rect x="146" y="138" width="84" height="15" rx="7.5" fill="#000000" fill-opacity="0.6"/>')
    morceaux.append('<text x="188" y="148.5" text-anchor="middle" fill="#ffffff" font-size="9" '
                    'font-family="system-ui, Arial, sans-serif">illustration IA</text>')
    morceaux.append('</svg>')
    return "\n".join(morceaux) + "\n"


def generer_tout():
    """Écrit une image par carte, plus l'image par défaut (cartes ajoutées par l'administrateur)."""
    if not os.path.exists(DOSSIER_IMAGES):
        os.makedirs(DOSSIER_IMAGES)
    fichiers = []
    for c in generer_donnees.preparer_cartes(generer_donnees.lire_modeles()):
        svg = dessiner(c["nom"], c["categorie"], c["puissance"], c["vitesse"], c["id_rarete"])
        fichiers.append((c["illustration"], svg))
    fichiers.append(("defaut.svg", dessiner("defaut", "defaut", 5, 5, 1)))
    for nom_fichier, svg in fichiers:
        with open(os.path.join(DOSSIER_IMAGES, nom_fichier), "w", encoding="utf-8") as f:
            f.write(svg)
    return len(fichiers)


if __name__ == "__main__":
    print(generer_tout(), "illustrations générées dans", DOSSIER_IMAGES)
