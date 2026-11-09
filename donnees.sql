-- Fichier GÉNÉRÉ par generer_donnees.py à partir de modeles.csv : ne pas modifier à la main.
-- Benchmarks : Artificial Analysis Intelligence Index v5.0 et vitesse médiane (jetons/s), relevé du 2 novembre 2026.

INSERT INTO Rarete (id_rarete, nom, couleur, poids_tirage) VALUES
    (1, 'Commune', '#6b7280', 60),
    (2, 'Rare', '#1d6fd8', 25),
    (3, 'Épique', '#8a3ffc', 12),
    (4, 'Légendaire', '#c77700', 3);

INSERT INTO Categorie (id_categorie, nom) VALUES
    (1, 'Frontier'),
    (2, 'Poids ouverts'),
    (3, 'Compact');

INSERT INTO Carte (id_carte, nom, editeur, description, indice, tokens_s, puissance, vitesse,
                   illustration, id_rarete, id_categorie) VALUES
    (1, 'Gemini 4 Carbon', 'Google', 'Tête de l''indice d''intelligence au 2 novembre 2026 (sortie le 28/10/2026).', 59.4, 95, 10, 4, 'gemini-4-carbon.svg', 4, 1),
    (2, 'Claude Opus 5.5', 'Anthropic', 'À un point du premier du classement, pour une vitesse comparable (sortie le 22/09/2026).', 58.4, 96, 10, 4, 'claude-opus-5-5.svg', 3, 1),
    (3, 'GPT-6 Astra', 'OpenAI', 'Le modèle le plus puissant d''OpenAI dans ce relevé, mais plus lent (sortie le 03/09/2026).', 56.9, 72, 9, 3, 'gpt-6-astra.svg', 2, 1),
    (4, 'GPT-6.1 Sol', 'OpenAI', 'Proche du sommet pour un coût d''évaluation bien plus faible (sortie le 29/09/2026).', 54.5, 87, 9, 3, 'gpt-6-1-sol.svg', 1, 1),
    (5, 'Claude Sonnet 5.5', 'Anthropic', 'Très proche de la tête du classement et nettement plus rapide que les modèles du haut (sortie le 28/09/2026).', 54.2, 137, 9, 5, 'claude-sonnet-5-5.svg', 3, 1),
    (6, 'Gemini 4 Argon', 'Google', 'Deuxième modèle de la gamme Gemini 4 de ce relevé (sortie le 30/09/2026).', 50.4, 83, 8, 3, 'gemini-4-argon.svg', 1, 1),
    (7, 'Kimi K3.1 Pro', 'Moonshot AI', 'Puissant mais lent : 31 jetons par seconde seulement (sortie le 23/10/2026).', 46.0, 31, 8, 1, 'kimi-k3-1-pro.svg', 1, 1),
    (8, 'Muse Wonder', 'Meta', 'Un modèle de haut niveau qui génère très vite (sortie le 12/10/2026).', 43.3, 192, 7, 8, 'muse-wonder.svg', 2, 1),
    (9, 'DeepSeek V4.1 Flash', 'DeepSeek', 'Le meilleur modèle à poids ouverts du classement (sortie le 17/10/2026).', 32.5, 171, 5, 7, 'deepseek-v4-1-flash.svg', 4, 2),
    (10, 'GLM-5.3', 'Z AI', 'Modèle à poids ouverts de Z AI (sortie le 18/08/2026).', 31.6, 89, 5, 4, 'glm-5-3.svg', 2, 2),
    (11, 'MiMo-V2.6-Pro', 'Xiaomi', 'Modèle à poids ouverts de Xiaomi, plutôt lent : 44 jetons par seconde.', 29.9, 44, 5, 2, 'mimo-v2-6-pro.svg', 1, 2),
    (12, 'MiniMax-M3.1-Flash', 'MiniMax', 'Version Flash à poids ouverts, rapide (sortie le 19/10/2026).', 28.9, 136, 5, 5, 'minimax-m3-1-flash.svg', 2, 2),
    (13, 'Step 5 Preview', 'StepFun', 'Aperçu à poids ouverts de StepFun, rapide : 146 jetons par seconde.', 28.5, 146, 5, 6, 'step-5-preview.svg', 3, 2),
    (14, 'Muse Spark Open', 'Meta', 'Modèle à poids ouverts de Meta, très rapide : 193 jetons par seconde.', 24.7, 193, 4, 8, 'muse-spark-open.svg', 3, 2),
    (15, 'DeepSeek V4 Pro', 'DeepSeek', 'Version Pro à poids ouverts de DeepSeek (sortie le 13/08/2026).', 23.1, 94, 4, 4, 'deepseek-v4-pro.svg', 1, 2),
    (16, 'Qwen3.8 27B', 'Alibaba', 'Modèle à poids ouverts de 27 milliards de paramètres.', 20.1, 41, 3, 2, 'qwen3-8-27b.svg', 1, 2),
    (17, 'Claude Haiku 5.5', 'Anthropic', 'Le modèle compact le plus puissant de la sélection, à 235 jetons par seconde.', 36.2, 235, 6, 9, 'claude-haiku-5-5.svg', 4, 3),
    (18, 'Gemini 3.8 Flash', 'Google', 'Version Flash de Google : un bon équilibre entre puissance et vitesse.', 30.6, 131, 5, 5, 'gemini-3-8-flash.svg', 2, 3),
    (19, 'GPT-6 Luna', 'OpenAI', 'Petit modèle d''OpenAI, très économique (0,10 $ le million de jetons en entrée).', 27.8, 117, 5, 5, 'gpt-6-luna.svg', 2, 3),
    (20, 'K2 Horizon 375B A23B', 'Institute of Foundation Models', 'Le modèle le plus rapide du classement : 720 jetons par seconde, mais peu puissant.', 17.8, 720, 3, 10, 'k2-horizon-375b-a23b.svg', 3, 3),
    (21, 'Beam 1.0', 'Reflection', 'Modèle à poids ouverts très rapide : 361 jetons par seconde.', 17.7, 361, 3, 10, 'beam-1-0.svg', 3, 3),
    (22, 'Gemini 3.5 Flash-Lite', 'Google', 'Version Flash-Lite de Google : 423 jetons par seconde.', 11.7, 423, 2, 10, 'gemini-3-5-flash-lite.svg', 1, 3),
    (23, 'Nemotron 3.5 Lightning', 'NVIDIA', 'Modèle NVIDIA ultra-rapide (295 jetons par seconde) mais peu puissant.', 5.5, 295, 1, 10, 'nemotron-3-5-lightning.svg', 1, 3),
    (24, 'Mistral Small 4', 'Mistral', 'Petit modèle à poids ouverts de Mistral AI, éditeur français.', 4.3, 158, 1, 6, 'mistral-small-4.svg', 1, 3);
