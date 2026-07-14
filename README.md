PROJET consistant à créer des outils intéractifs de nettoyage automatique de fichier .CVS, .JSON

*** PROJET EN COURS ***



=================================================================================
Documentation du module file_loader.py
🎯 Objectif
Ce module est responsable du chargement intelligent des fichiers de données. Il s'occupe de détecter automatiquement le format, l'encodage et le séparateur pour ne jamais avoir à spécifier ces paramètres manuellement lors de l'appel au script principal.

🛠️ Fonctions Disponibles
| Fonction | Description | | :--- | :--- | | 
load_file(file_path)
 | Fonction principale. Détecte le format (CSV/Excel) et charge les données dans un DataFrame pandas. | | 
_load_csv()
 | Chargeur interne pour les fichiers .csv. Gère les encodages variés (utf-8, latin1) et détecte le séparateur. | | 
_load_excel()
 | Chargeur interne pour les fichiers .xlsx ou .xls. Lit la première feuille par défaut. | | 
_detect_encoding()
 | Teste successivement les encodages courants pour éviter les erreurs de caractères spéciaux (accents, symboles). | | 
_detect_delimiter()
 | Analyse un échantillon des 3 premières lignes pour deviner si le séparateur est ;, , ou \t. |

📖 Exemple d'utilisation

```
from src.file_loader import load_file

# Chargement automatique (pas besoin de savoir si c'un csv à point-virgule ou une virgule)
df = load_file("data/mon_donnees.csv")

print(f"Nombre de lignes chargées : {len(df)}")
```

⚠️ Gestion des Erreurs
Le module est conçu pour être robuste et lever des exceptions claires si le fichier n'est pas exploitable :

FileNotFoundError : Si le chemin du fichier est incorrect.
ValueError : Si l'extension du fichier est inconnue (ex: .txt).
Cas limite (Fichier vide) : Si le fichier fait 0 octet ou contient uniquement des sauts de ligne, la fonction retourne calmement un DataFrame vide (pd.DataFrame()) au lieu de planter.
🔧 Bonnes pratiques implémentées
Support multi-encodage : Pas de crash avec les fichiers exportés par Excel (souvent en latin1).
Détection automatique : Utilise l'heuristique d'échantillonnage pour identifier le séparateur dès les premières lignes.
Séparation des responsabilités : Les fonctions privées (_) ne font qu'une seule tâche précise (soit l'encodage, soit le séparateur).
====================================================================================

"" Arborescense :
```
mon-projet-nettoyage/
├── .venv/                  # Ton environnement virtuel géré par uv
├── data/
│   ├── raw/                # Fichiers CSV/JSON d'origine (non modifiés, "lecture seule")
│   └── processed/          # Fichiers propres générés par tes scripts/agents
├── docs_references/        # Si tu y déposes des PDF ou des schémas de données locaux
├── src/
│   ├── __init__.py
│   ├── cleaner.py          # Le script Python principal de nettoyage
│   └── validator.py        # Le script qui contrôle la conformité des données
├── tests/                  # Pour vérifier que le nettoyage n'a pas cassé les types de données

```