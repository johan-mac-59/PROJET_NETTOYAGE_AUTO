# PROJET consistant à créer des outils intéractifs de nettoyage automatique de fichier .CSV, .JSON

*** PROJET EN COURS ***

## ⚙️ Capacités du Pipeline de Nettoyage

Le projet est conçu comme une suite de modules spécialisés, orchestrés par `main.py`, pour transformer des données brutes et incertaines en datasets propres et exploitables :

* **`file_loader`** : Intelligence de lecture. Détecte automatiquement le format (CSV/Excel/JSON), l'encodage (UTF-8, Latin1) et le séparateur (`,` , `;` ou `\t`) pour garantir un chargement sans erreur.
* **`data_profiler`** : Inspection & Diagnostic. Génère des rapports détaillés des données brutes et nettoyées. Capable de produire :
    *   Un fichier **Markdown** structuré avec aperçu, statistiques et qualité des lignes.
    *   Un fichier **HTML** reprenant le profilage complet avec graphiques intégrés (histogrammes, boxplots, barplots) pour une visualisation avancée de la distribution des données.
* **`cleaner_engine`** : Moteur de transformation intelligent. Automatise les tâches critiques : suppression des doublons, gestion des valeurs manquantes et aberrantes, et normalisation avancée des formats monétaires (suppression des symboles €, $, £) et correction des types numériques (passage du type float instable au type `Int64` robuste).
* **`cleaner_logger`** : Audit & Traçabilité. Génère un rapport détaillé après chaque passage, permettant de visualiser l'impact précis du nettoyage (nombre de lignes traitées, statistiques post-nettoyage). Disponible dans le projet, appelé par les fonctions orchestrateurs.
* **`cleaner_reporter`** : Reporting Professionnel. Transforme les logs et les profils en document d'audit Markdown structuré avec comparaison "Avant" vs "Après" nettoyage (KPIs).

## 🛠️ Ordonnancement du Pipeline (main.py)

L'application suit un flux itératif conçu pour intégrer le contrôle utilisateur à chaque étape critique :

1.  **Chargement intelligent** : Détection auto du format et de l'encodage.
2.  **Profiling initial** : Génération d'un rapport d'inspection des données brutes (au format Markdown ou HTML au choix, avec graphiques pour le HTML).
3.  **Nettoyage adaptatif** :
    *   Corrections automatiques (types, doublons, espaces).
    *   Interrogation de l'utilisateur sur les outliers et valeurs manquantes pour décider de la marche à suivre.
4.  **Reporting Terminal** : Affichage résumé des opérations effectuées (gain en lignes/colonnes, types modifiés).
5.  **Sauvegarde** : Export du dataset nettoyé vers `data/processed/`.
6.  **(Prochainement) Nouveau profilage post-nettoyage** : Comparaison automatique "Avant/Après" pour valider la qualité finale.

## 📖 Exemple d'utilisation rapide

```python
# Lancement du pipeline interactif avec chemins par défaut
main()
```
*(Note : `main()` utilisera par défaut les chemins définis dans le script. Pour personnaliser les entrées/sorties, tu pourras plus tard ajouter des arguments en ligne de commande.)*

## ⚠️ Gestion des Erreurs

Le module est conçu pour être robuste et lever des exceptions claires si le fichier n'est pas exploitable :
- **FileNotFoundError** : Si le chemin du fichier est incorrect.  
- **ValueError** : Si l'extension du fichier est inconnue (ex: `.txt`).  
- **Cas limite (Fichier vide)** : Le module `file_loader` retourne calmement un DataFrame vide (`pd.DataFrame()`). Cependant, le profilage (`data_profiler`) nécessite des données réelles pour fonctionner.

## 🔧 Bonnes pratiques implémentées

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
```
---

### Technologies utilisées :
Python, Pandas, Matplotlib, Seaborn, POO, fonctions