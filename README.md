PROJET consistant à créer des outils intéractifs de nettoyage automatique de fichier .CVS, .JSON

*** PROJET EN COURS ***



=================================================================================  

### ⚙️ Capacités du Pipeline de Nettoyage

Le projet est conçu comme une suite de modules spécialisés, orchestrés pour transformer des données brutes et incertaines en datasets propres et exploitables :

* **`file_loader`** : **Intelligence de lecture.** Détecte automatiquement le format (CSV/Excel), l'encodage (UTF-8, Latin1) et le séparateur (`,` , `;` ou `\t`) pour garantir un chargement sans erreur.
* **`data_profiler`** : **Inspection & Diagnostic.** Génère un rapport Markdown détaillé des données brutes (types, valeurs manquantes, statistiques clés, aperçu) avant le nettoyage. Idéal pour un audit rapide de la qualité des données.
* **`cleaner_engine`** : **Moteur de transformation.** Automatise les tâches critiques du nettoyage : suppression des doublons, gestion intelligente des valeurs manquantes et normalisation des types de données.
* **`cleaner_logger`** : **Audit & Traçabilité.** Génère un rapport détaillé après chaque passage, permettant de visualiser l'impact du nettoyage (nombre de lignes traitées, statistiques post-nettoyage).
* **`run_pipeline`** : **Orchestration.** Pilote l'exécution complète du flux, du chargement des données brutes jusqu'à la production des fichiers nettoyés.

---

### 📖 Exemple d'utilisation rapide

```python
from src.run_pipeline import run_cleaning_pipeline

# Exécution complète : Chargement -> Nettoyage -> Rapport de synthèse
run_cleaning_pipeline(input_path="data/raw/mon_fichier.csv", output_path="data/processed/mon_fichier_propre.csv")
```

### ⚠️ Gestion des Erreurs
Le module est conçu pour être robuste et lever des exceptions claires si le fichier n'est pas exploitable :
- FileNotFoundError : Si le chemin du fichier est incorrect.  
- ValueError : Si l'extension du fichier est inconnue (ex: .txt).  
- Cas limite (Fichier vide) : Si le fichier fait 0 octet ou contient uniquement des sauts de ligne, la fonction retourne calmement un DataFrame vide (pd.DataFrame()) au lieu de planter.  
🔧 Bonnes pratiques implémentées
- Support multi-encodage : Pas de crash avec les fichiers exportés par Excel (souvent en latin1).
- Détection automatique : Utilise l'heuristique d'échantillonnage pour identifier le séparateur dès les premières lignes.
- Séparation des responsabilités : Les fonctions privées (_) ne font qu'une seule tâche précise (soit l'encodage, soit le séparateur).  


### Technologies utilisées :
Python, Pandas, POO, fonctions

====================================================================================  

### Arborescense :
```
mon_projet_nettoyage/
├── data/
│   ├── processed/              # Fichiers propres générés par les scripts
│   └── raw/                    # Données brutes (lecture seule)
├── src/
│   ├── __init__.py
│   ├── cleaner_engine.py       # Moteur principal de nettoyage des données
│   ├── clearner_logger.py      # Génération de rapports après traitement
│   ├── data_profiler.py        # Module d'inspection et génération de rapports Markdown
│   ├── file_loader.py          # Chargement intelligent (détection auto format/encodage)
│   └── run_pipeline.py         # Orchestration du flux de travail complet
├── tests/                      # Tests unitaires pour garantir la fiabilité
│   ├── test_cleaner_engine.py
│   ├── test_data_profiler.py
│   └── test_file_loader.py
├── améliorations_futures.md    # Planification des évolutions du projet
├── DEROULEMENT_PROJET.md       # Journal de bord technique et historique des développements
├── main.py                     # Point d'entrée principal de l'application
├── pyproject.toml              # Configuration du projet et des dépendances (uv)
├── README.md                   # Documentation principale et présentation du projet
└── uv.lock                     # Verrouillage précis des versions des dépendances
```