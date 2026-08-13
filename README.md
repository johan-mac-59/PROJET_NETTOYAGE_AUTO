PROJET consistant à créer des outils intéractifs de nettoyage automatique de fichier .CSV, .JSON

*** PROJET EN COURS ***



=================================================================================  

### ⚙️ Capacités du Pipeline de Nettoyage

Le projet est conçu comme une suite de modules spécialisés, orchestrés pour transformer des données brutes et incertaines en datasets propres et exploitables :

* **`file_loader`** : **Intelligence de lecture.** Détecte automatiquement le format (CSV/Excel), l'encodage (UTF-8, Latin1) et le séparateur (`,` , `;` ou `\t`) pour garantir un chargement sans erreur.
* **`data_profiler`** : **Inspection & Diagnostic.** Génère un rapport Markdown détaillé des données brutes (types, valeurs manquantes, statistiques clés, aperçu) avant le nettoyage. Idéal pour un audit rapide de la qualité des données.
* **`cleaner_engine`** : **Moteur de transformation intelligent.** Automatise les tâches critiques : suppression des doublons, gestion des valeurs manquantes, et surtout **normalisation avancée des formats monétaires** (suppression des symboles €, $, £) et **correction des types numériques** (passage du type float instable au type `Int64` robuste).
* **`cleaner_logger`** : **Audit & Traçabilité.** Génère un rapport détaillé après chaque passage, permettant de visualiser l'impact précis du nettoyage (nombre de lignes traitées, statistiques post-nettoyage).
* **`cleaner_reporter`** : **Audit & Reporting Professionnel.** Transforme les logs et les profils en un document d'audit Markdown structuré. Il permet de comparer l'état "Avant" vs "Après" nettoyage (KPIs) tout en garantissant la sécurité du rapport via une sanitisation des caractères spéciaux.

---

### 📖 Exemple d'utilisation rapide

```python
# Exécution complète : Chargement -> Nettoyage -> Rapport de synthèse
main()
```

*(Note : `main()` utilisera par défaut les chemins définis dans le script, ou tu pourras plus tard ajouter des arguments en ligne de commande si tu souhaites personnaliser les entrées/sorties.)*

### ⚠️ Gestion des Erreurs

Le module est conçu pour être robuste et lever des exceptions claires si le fichier n'est pas exploitable :
- FileNotFoundError : Si le chemin du fichier est incorrect.  
- ValueError : Si l'extension du fichier est inconnue (ex: .txt).  
- Cas limite (Fichier vide) : Si le fichier fait 0 octet ou contient uniquement des sauts de ligne, la fonction retourne calmement un DataFrame vide (`pd.DataFrame()`) au lieu de planter.  

### 🔧 Bonnes pratiques implémentées
- **Robustesse des types (Int64)** : Utilisation de types entiers "nullables" pour préserver l'intégrité des colonnes numériques contenant des valeurs manquantes.
- **Intelligence monétaire** : Capacité à normaliser et convertir des formats complexes (ex: `"1 200,50 €"` $\rightarrow$ `1200.50`).
- **Support multi-encodage** : Pas de crash avec les fichiers exportés par Excel ou systèmes anciens (Latin1/CP1252).
- **Détection automatique** : Utilise l'heuristique d'échantillonnage pour identifier le séparateur et la structure dès les premières lignes.
- **Séparation des responsabilités (SRP)** : Architecture modulaire où chaque composant a une responsabilité unique, facilitant les tests unitaires et l'évolution. 

---

### 📁 Arborescence :

```text
mon_projet_nettoyage/
├── data/
│   ├── processed/              # Fichiers propres générés par les scripts
│   └── raw/                    # Données brutes (lecture seule)
├── src/
│   ├── __init__.py
│   ├── cleaner_engine.py       # Moteur principal de nettoyage des données
│   ├── cleaner_logger.py       # Génération de rapports après traitement
│   ├── cleaner_reporter.py     # Génération du fichier markdown de rapports
│   ├── data_profiler.py        # Module d'inspection et génération de rapports Markdown
│   └── file_loader.py          # Chargement intelligent (détection auto format/encodage)
├── tests/
│   ├── test_cleaner_engine.py
│   ├── test_cleaner_logger.py
│   ├── test_cleaner_reporter.py
│   ├── test_data_profiler.py
│   └── test_file_loader.py
├── améliorations_futures.md    # Planification des évolutions du projet
├── DEROULEMENT_PROJET.md       # Journal de bord technique et historique des développements
├── main.py                     # Point d'entrée principal de l'application
├── pyproject.toml              # Configuration du projet et des dépendances (uv)
├── README.md                   # Documentation principale et présentation du projet
└── uv.lock                     # Verrouillage précis des versions des dépendances

====================================================================================  

### Technologies utilisées :
Python, Pandas, POO, fonctions

====================================================================================