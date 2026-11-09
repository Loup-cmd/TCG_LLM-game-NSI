# Benchmarks : d'où viennent les cartes

Les 24 cartes sont de vrais modèles de langage. Leurs caractéristiques viennent de deux mesures publiques, relevées **au 2 novembre 2026** et stockées dans `modeles.csv`.

## 1. Les deux mesures

| Mesure | Ce que c'est | Colonne |
|---|---|---|
| **Indice d'intelligence** | Note composite d'Artificial Analysis (Intelligence Index v5.0) qui regroupe des tests d'agents, de code, de sciences et de connaissances. Plus c'est haut, plus le modèle est « puissant » en général. | `indice` |
| **Vitesse de génération** | Nombre médian de jetons produits par seconde sur l'API de l'éditeur. | `tokens_s` |

Le relevé a été fait sur la page <https://thebestsuperintelligence.io/llm-leaderboard> (données du 2 novembre 2026), qui reprend l'indice d'Artificial Analysis (<https://artificialanalysis.ai/models>). Les modèles de tête et leurs valeurs ont été recoupés avec deux autres agrégateurs (<https://modelgrep.com/leaderboard> et <https://www.sevenlab.ai/ai-leaderboard>) : l'ordre des modèles de tête est le même et les indices diffèrent d'au plus un point. Les vitesses, en revanche, varient davantage d'une source à l'autre.

## 2. Précautions à connaître

- **L'indice dépend du niveau de raisonnement demandé** (par exemple, pour Claude Opus 5.5 : 58,4 en « max », 51,7 en « high », 34,5 en « low »). On a retenu pour chaque modèle la variante la plus haute publiée.
- **La vitesse varie fortement selon la source et le moment** (par exemple Gemini 4 Carbon : 89 à 95 jetons/s selon les sites, GPT-6 Astra : 51 à 72). On a utilisé une seule source, de façon cohérente.
- **Les chiffres changent chaque mois.** C'est pourquoi les caractéristiques sont figées dans la base : une carte déjà possédée ne change pas quand les benchmarks évoluent.
- La page source indique qu'elle n'a pas détaillé l'origine de chaque colonne : avant de réutiliser ces chiffres ailleurs, les vérifier sur artificialanalysis.ai.
- Un benchmark ne mesure qu'une partie de ce qu'un modèle sait faire. Le classement est un jeu, pas un verdict.
- Les noms de modèles appartiennent à leurs éditeurs et sont utilisés ici à titre descriptif. Les illustrations ne reprennent aucun logo.

## 3. Du benchmark à la carte

1. `puissance = min(10, arrondi(indice / 6))` : un indice de 60 donne 10.
2. `vitesse = min(10, arrondi(jetons par seconde / 25))` : 250 jetons/s donnent 10.
3. `score global = 7 x puissance + 3 x vitesse` (sur 100) : la puissance compte davantage, mais pas sans la vitesse.
4. Dans chaque catégorie, les 8 modèles sont classés par score global (en cas d'égalité : meilleur indice, puis ordre alphabétique).
5. La **rareté dépend du rang dans la catégorie** : rang 1 = Légendaire, rangs 2 et 3 = Épique, rangs 4 et 5 = Rare, rangs 6 à 8 = Commune.

Exemple : Claude Haiku 5.5 (indice 36,2 ; 235 jetons/s) donne puissance 6 et vitesse 9, soit un score de 69. C'est le meilleur des modèles Compact, donc une carte Légendaire, alors que GPT-6.1 Sol (puissance 9, vitesse 3) n'est qu'une carte Commune dans la catégorie Frontier, beaucoup plus disputée.

Ces fonctions sont dans `modele.py` (`calculer_stats`, `score_global`, `rangs_dans_categorie`, `rarete_du_rang`) et testées dans `tests.py`.

## 4. Les 24 cartes

Catégories (choix éditorial, la colonne `categorie` de `modeles.csv`) :

- **Frontier** : les modèles propriétaires haut de gamme ;
- **Poids ouverts** : modèles dont les poids sont publiés ;
- **Compact** : versions légères et rapides, propriétaires ou ouvertes.

Sélection : 8 modèles par catégorie, au plus 2 par éditeur dans une catégorie, uniquement des modèles dont la vitesse est publiée. Des modèles connus sont donc absents : GPT-6.1 Terra (51,0) et Claude Fable 5.1 (49,0) à cause de la limite de 2 par éditeur, Grok 4.7 et Qwen3.8 Max (poids fermés mais indice inférieur à 40, donc difficiles à classer dans nos trois catégories), Mistral Large 4 (pas de vitesse publiée). On peut les ajouter en modifiant le CSV.

| Catégorie | Rang | Modèle | Éditeur | Indice | Jetons/s | Puissance | Vitesse | Score | Rareté |
|---|---|---|---|---|---|---|---|---|---|
| Frontier | 1 | Gemini 4 Carbon | Google | 59.4 | 95 | 10 | 4 | 82 | Légendaire |
| Frontier | 2 | Claude Opus 5.5 | Anthropic | 58.4 | 96 | 10 | 4 | 82 | Épique |
| Frontier | 3 | Claude Sonnet 5.5 | Anthropic | 54.2 | 137 | 9 | 5 | 78 | Épique |
| Frontier | 4 | Muse Wonder | Meta | 43.3 | 192 | 7 | 8 | 73 | Rare |
| Frontier | 5 | GPT-6 Astra | OpenAI | 56.9 | 72 | 9 | 3 | 72 | Rare |
| Frontier | 6 | GPT-6.1 Sol | OpenAI | 54.5 | 87 | 9 | 3 | 72 | Commune |
| Frontier | 7 | Gemini 4 Argon | Google | 50.4 | 83 | 8 | 3 | 65 | Commune |
| Frontier | 8 | Kimi K3.1 Pro | Moonshot AI | 46.0 | 31 | 8 | 1 | 59 | Commune |
| Poids ouverts | 1 | DeepSeek V4.1 Flash | DeepSeek | 32.5 | 171 | 5 | 7 | 56 | Légendaire |
| Poids ouverts | 2 | Step 5 Preview | StepFun | 28.5 | 146 | 5 | 6 | 53 | Épique |
| Poids ouverts | 3 | Muse Spark Open | Meta | 24.7 | 193 | 4 | 8 | 52 | Épique |
| Poids ouverts | 4 | MiniMax-M3.1-Flash | MiniMax | 28.9 | 136 | 5 | 5 | 50 | Rare |
| Poids ouverts | 5 | GLM-5.3 | Z AI | 31.6 | 89 | 5 | 4 | 47 | Rare |
| Poids ouverts | 6 | MiMo-V2.6-Pro | Xiaomi | 29.9 | 44 | 5 | 2 | 41 | Commune |
| Poids ouverts | 7 | DeepSeek V4 Pro | DeepSeek | 23.1 | 94 | 4 | 4 | 40 | Commune |
| Poids ouverts | 8 | Qwen3.8 27B | Alibaba | 20.1 | 41 | 3 | 2 | 27 | Commune |
| Compact | 1 | Claude Haiku 5.5 | Anthropic | 36.2 | 235 | 6 | 9 | 69 | Légendaire |
| Compact | 2 | K2 Horizon 375B A23B | Institute of Foundation Models | 17.8 | 720 | 3 | 10 | 51 | Épique |
| Compact | 3 | Beam 1.0 | Reflection | 17.7 | 361 | 3 | 10 | 51 | Épique |
| Compact | 4 | Gemini 3.8 Flash | Google | 30.6 | 131 | 5 | 5 | 50 | Rare |
| Compact | 5 | GPT-6 Luna | OpenAI | 27.8 | 117 | 5 | 5 | 50 | Rare |
| Compact | 6 | Gemini 3.5 Flash-Lite | Google | 11.7 | 423 | 2 | 10 | 44 | Commune |
| Compact | 7 | Nemotron 3.5 Lightning | NVIDIA | 5.5 | 295 | 1 | 10 | 37 | Commune |
| Compact | 8 | Mistral Small 4 | Mistral | 4.3 | 158 | 1 | 6 | 25 | Commune |

## 5. Mettre à jour les benchmarks

1. Modifier `modeles.csv` (une ligne par modèle : nom, éditeur, catégorie, indice, jetons/s, description).
2. `python generer_donnees.py` : recalcule puissance, vitesse, rang et rareté, et réécrit `donnees.sql`.
3. `python generer_illustrations.py` : régénère les images (la description visuelle suit les nouvelles caractéristiques).
4. `python creer_bdd.py` : recrée la base (efface les données existantes).
5. `python tests.py` : le test `test_donnees_sql_a_jour` signale un oubli de l'étape 2. Si le nombre de modèles par catégorie change, adapter les tests qui comptent les cartes (24, 8 par catégorie, répartition 9 / 6 / 6 / 3).
