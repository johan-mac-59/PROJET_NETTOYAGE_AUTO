# DEROULEMENT_PROJET.MD

## Contexte du Projet

**Objectif principal** : Créer un script Python capable de détecter automatiquement les problèmes courants dans un fichier CSV et d'y remédier sans connaître à l'avance le contenu ni la structure du fichier.

**Contraintes clés** :
- Ne pas savoir comment est le fichier initialement (encodage, séparateur, types...)
- Manipuler des données sous forme de DataFrame pandas
- Fournir un rapport détaillé des transformations effectuées

---

## Étape 1 : Analyse des besoins et planification

### Problématiques identifiées dans les CSV bruts :
1. **Encodage** : UTF-8, Latin1, CP1252... (caractères spéciaux mal affichés)
2. **Séparateur** : Point-virgule (;), virgule (,), tabulation (\t), pipe (|)...
3. **Valeurs manquantes** : NaN, vides, "NA"...
4. **Doubons exacts** : lignes identiques
5. **Types incohérents** : dates/numéros stockés en texte, espaces superflus...
6. **Colonnes vides** : >95% de valeurs manquantes
7. **Valeurs aberrantes (outliers)** : écarts importants dans les données numériques

### Solutions envisagées :
- Créer des fonctions dédiées pour chaque problème
- Ordonner intelligemment les nettoyages (ordre logique)
- Détecter automatiquement encodage et séparateur
- Fournir un rapport exhaustif

---

## Étape 2 : Conception du cleaner automatique

### Architecture choisie

```
cleaner_auto.py
├── detect_delimiter()     → Détecte le séparateur (; , \t |)
├── detect_encoding()      → Détecte l'encodage (UTF-8, Latin1...)
├── clean_empty_columns()  → Supprime les colonnes >95% vides
├── clean_whitespace()     → Nettoie espaces superflus
├── clean_types()          → Convertit automatique string→num/datetime
├── clean_duplicates()     → Supprime doublons exacts
├── clean_missing_values() → Remplit NaN (médiane/mode)
├── clean_outliers()       → Corrige valeurs aberrantes (IQR)
└── clean_csv_file()       → Fonction principale qui orchestre tout
```

### Logique d'orchestration (ordre du nettoyage)

1. **Suppression colonnes vides** → Réduire le bruit dès le début
2. **Nettoyage espaces** → Préparer les textes avant tout traitement
3. **Conversion types** → Numérique et dates à leurs bons formats
4. **Suppression doublons** → Éviter de fausser les stats après conversion
5. **Valeurs manquantes** → Remplir avec médiane (num) ou mode (text)
6. **Traitement outliers** → En dernier pour ne pas fausser les calculs

---

## Étape 3 : Implémentation - Détails techniques

### Fonction `detect_delimiter()`
- Teste les séparateurs courants (;, ,, \t, |)
- Vérifie que le nombre de colonnes est cohérent sur plusieurs lignes
- Retourne ',' par défaut si rien ne correspond

### Fonction `detect_encoding()`
- Essaie successivement UTF-8, Latin1, CP1252
- Si l'encodage marche (lecture sans erreur) → c'est le bon
- Ne nécessite pas de dépendance externe (pas de chardet nécessaire)
- Fallback sur UTF-8 si tout échoue

### Fonction `clean_missing_values()`
- **Colonnes numériques** → Médiane (plus robuste que la moyenne face aux outliers)
- **Colonnes textuelles** → Mode (valeur la plus fréquente)
- Supprime les colonnes si >50% de NaN restants

### Fonction `clean_types()`
- **Numérique** : Essaie `pd.to_numeric()`, vérifie que les valeurs sont cohérentes
- **Date** : Essaie `pd.to_datetime()`, accepte si >80% des valeurs converties correctement
- Garde le texte inchangé sinon (éviter de fausser codes postaux, numéros de téléphone...)

### Fonction `clean_outliers()`
- Utilise la méthode **IQR (Interquartile Range)**
- Bornes = Q1 - 1.5*IQR et Q3 + 1.5*IQR
- Remplace les valeurs par les bornes (winsorization)
- Appliqué en dernier pour ne pas influencer les autres calculs

### Fonction `clean_duplicates()`
- Utilise `drop_duplicates()` de pandas
- Retourne le nombre exact de lignes supprimées

### Fonction `clean_empty_columns()`
- Supprime les colonnes avec ≥95% de valeurs manquantes
- Garde les données avec au moins 5% d'information

---

## Étape 4 : Fonction principale `clean_csv_file()`

Cette fonction est le point d'entrée qui :
1. **Charge** le fichier en détectant automatiquement séparateur et encodage
2. **Applique** les nettoyages dans l'ordre logique
3. **Sauvegarde** le résultat propre
4. **Retourne un rapport** avec toutes les transformations effectuées

### Exemple d'utilisation :

```python
# Dans le terminal ou IDLE :
python src/cleaner_auto.py

# Output attendu :
# 📂 Chargement : data/raw/reservation_rivage_brut.csv
#    Séparateur : ';' | Encodage : latin-1
#
# 🧹 Nettoyage en cours...
# ✓ Colonnes vides supprimées
# ✓ Espaces nettoyés
# ✓ Types convertis
# ✓ 42 doublons supprimés
# ✓ Valeurs manquantes traitées
# ✓ Outliers corrigés
#
# ✅ Fichier sauvegardé : data/processed/reservation_nettoye.csv
# 📊 Résultat : 1500→1458 lignes, 12→10 colonnes
```

---

## Étape 5 : Concepts techniques abordés

### Typing (from typing import Tuple)
- Permet d'annoter les types des paramètres et retours
- Améliore la lisibilité et aide à détecter les erreurs avant l'exécution

### DataFrame pandas
- Structure de données tabulaire au cœur du traitement
- Méthodes clés : `isnull().sum()`, `drop_duplicates()`, `fillna()`, `to_numeric()`, `to_datetime()`

### Gestion des encodages
- UTF-8 : standard moderne
- Latin1/CP1252 : courants sur fichiers Windows/Excel européens
- Détecter automatiquement évite les caractères bizarres

### Méthode IQR pour les outliers
- Q1 = 25e percentile, Q3 = 75e percentile
- IQR = Q3 - Q1
- Bornes : Q1 - 1.5*IQR et Q3 + 1.5*IQR
- Standard en statistiques pour détecter les valeurs aberrantes

---

## Étape 6 : Limitations et améliorations futures

### Limitations actuelles :
- **One-pass** : le script ne s'exécute qu'une fois (risque de passer à côté de problèmes résiduels)
- **Détection des dates** : heuristique simple (>80% convertis), peut échouer sur des formats rares
- **Outliers** : méthode IQR standard (1.5x), peut être trop agressive ou pas assez selon le cas
- **Pas de validation post-nettoyage** : on ne vérifie pas si le résultat est réellement propre

### Améliorations possibles :
1. **Validation post-nettoyage** : vérifier qu'il n'y a plus de problèmes critiques
2. **Mode multi-passes** : exécuter plusieurs fois jusqu'à stabilisation
3. **Détection de format de date plus robuste** (regex avancée)
4. **Filtrage paramétrable** des outliers selon le contexte métier
5. **Support multi-format** (JSON, Excel, Parquet...)

---

## Récapitulatif final

### Fichiers créés :
- `src/cleaner_auto.py` → Script principal avec toutes les fonctions de nettoyage automatique
- `DEROULEMENT_PROJET.md` → Ce fichier de documentation du projet

### Commande pour tester :
```bash
# Dans le dossier PROJET_NETTOYAGE_AUTO
python src/cleaner_auto.py
```

### Résultats attendus :
Un fichier CSV nettoyé automatiquement avec un rapport détaillé des transformations effectuées. Le script est générique et fonctionne sur n'importe quel CSV sans connaissance préalable du contenu.

---

*Projet en cours de développement - Bootcamp Data Analyst Wild Code School*



---

## Étape 7 : Refactoring et Architecture Modulaire (En cours)

Dans une version plus avancée et professionnelle, nous avons refactorisé le projet pour le rendre plus robuste et maintenable. 

### Nouvelle architecture du projet
Au lieu d'un seul fichier monolithique (`cleaner_auto.py`), le projet est maintenant découpé en modules distincts :

```
src/
├── __init__.py          → Marque le dossier comme un package Python
├── file_loader.py       → Chargement et détection (encodage, séparateur)
├── cleaner_engine.py    → Moteur de nettoyage (logique pure)
├── report_generator.py  → Génération des rapports
└── main.py              → Orchestrateur principal (point d'entrée)
```

### Apports de la modularité

1.  **Détachement du chargement (`file_loader`)** :
    *   Permet de supporter plusieurs formats (CSV, Excel, JSON) sans toucher à la logique de nettoyage.
    *   Utilise `os.path` importé globalement pour respecter les bonnes pratiques d'importation Python.

2.  **Séparation des responsabilités** :
    *   Le `cleaner_engine.py` manipule uniquement des `DataFrames`. Il ne sait pas d'où viennent les données ni où elles vont. C'est une fonction pure.
    *   Le `report_generator.py` s'occupe de la présentation, sans effectuer de calculs lourds sur les données brutes.

3.  **Orchestration via `main.py`** :
    *   Le script principal devient très lisible et orienté "workflow" : Charger → Nettoyer → Sauvegarder → Rapporter.
    *   Facilite les tests unitaires : on peut tester le moteur de nettoyage sans avoir besoin d'un fichier CSV physique.

### Commandes pour la version modulaire

```bash
# Pour exécuter le projet refactored
python src/main.py

# Résultat attendu (extrait du rapport généré) :
# ============================================================
# RAPPORT DE NETTOYAGE DE DONNÉES
# ============================================================
# 📊 Lignes: 1500 → 1458 (-42)
# 📑 Colonnes: 12 → 10 (+2)
# 🗑️ Colonnes supprimées (vides): 1
# ... etc
```

### Notes pour l'entretien technique
*   **Pourquoi avoir refactorisé ?** Pour respecter le principe de responsabilité unique (SRP - Single Responsibility Principle). Chaque fichier a une tâche précise.
*   **Gestion des imports :** Attention à toujours importer les dépendances au début du fichier (`import os`, `import pandas`) et non dans les fonctions, pour garantir la lisibilité et l'ordre d'exécution.
*   **Évolutivité :** Cette structure permet d'ajouter le support de JSON (via `pd.read_json`) ou d'une base SQL très facilement sans casser le cœur du programme.

---

## Récapitulatif final (Version Modulaire)

### Fichiers créés :
- `src/file_loader.py` → Chargement intelligent (CSV/Excel), détection encodage/séparateur.
- `src/cleaner_engine.py` → Moteur de transformation des données (Nettoyage pur).
- `src/report_generator.py` → Moteur d'affichage des résultats (Rapports textuels).
- `src/main.py` → Point d'entrée qui lie le tout.

### Commande pour tester :
```bash
# Dans le dossier PROJET_NETTOYAGE_AUTO
python src/main.py
```

*Projet en cours de développement - Bootcamp Data Analyst Wild Code School*

---

## Étape 8 : Optimisations récentes et corrections critiques (En cours)

Dans les dernières itérations, nous avons corrigé des bugs structurels et optimisé l'ordre logique des opérations pour garantir la fiabilité du nettoyage.

### 1. Correction de la structure du Pipeline (`run_pipeline.py`)
*   **Problème :** L'indentation dans le bloc `try/except` de la sauvegarde CSV était erronée, risquant de faire planter le script.
*   **Solution :** Structuration propre avec des chemins dynamiques via `pathlib`. Le pipeline orchestre maintenant clairement : Chargement → Nettoyage → Sauvegarde → Rapport.

### 2. Révision critique de l'ordre des tâches (Le "Golden Path")
L'ordre d'exécution a été redéfini pour éviter les faux négatifs en Data Science :
1.  **`clean_empty_columns`** : On retire le bruit dès le début.
2.  **`clean_whitespace`** : Crucial avant toute comparaison (ex: " Paris" vs "Paris").
3.  **`clean_types`** : **Point clé !** Les conversions doivent avoir lieu *avant* de chercher les doublons. Sans ça, " 10.5" et "10.5" seraient vus comme différents.
4.  **`clean_duplicates`** : Maintenant que les types sont homogènes, la détection est fiable.
5.  **`clean_missing_values`** : On remplit les trous une fois la structure figée.
6.  **`clean_outliers`** : En dernier pour ne pas fausser les calculs de bornes ou de stats.

### 3. Renforcement de `clean_types` dans `cleaner_engine.py`
*   **Robustesse accrue :** Utilisation de `errors='coerce'` dans `pd.to_numeric` et `pd.to_datetime`. Cela permet de transformer les erreurs en `NaN` plutôt que de faire planter le script.
*   **Protection des IDs :** Ajout d'une heuristique pour éviter de convertir des numéros de téléphone ou ID clients longs (>= 1e6) en float, ce qui entraînerait une perte de précision (ex: fin du nombre transformée en `.0`).
*   **Détection Date/Floating Point :** Une colonne n'est convertie en date que si >80% des valeurs sont valides.

### Impact sur le projet
Ces ajustements rendent le script "Data Analyst" beaucoup plus résilient face à des fichiers réels, sales et mal formatés (comme ceux qu'on trouve souvent en entreprise). Le pipeline ne "plante" plus silencieusement sur des formats inattendus.

---

## Étape 9 : Structuration du Projet et Début des Tests Unitaires

Dans cette phase, nous avons professionnalisé l'architecture du projet et commencé à garantir sa fiabilité grâce aux tests automatisés.

### 1. Résolution des conflits d'environnement (uv) pour les tests
Pour que pytest puisse importer nos modules correctement, deux ajustements cruciaux ont été faits :
*   **Configuration de `pyproject.toml`** : Ajout de la section `[tool.pytest.ini_options]` avec `pythonpath = ["."]`. Cela dit explicitement à Python de regarder dans le dossier racine pour trouver les dossiers `src` et `tests`.
*   **Nettoyage des fichiers markers** : Le fichier `src/__init__.py` (qui n'est qu'un marqueur de package) a été vidé. Il ne doit contenir aucun code, seulement indiquer à Python que le dossier est importable.

### 2. Organisation du système de tests
Nous utilisons **pytest**, la référence en matière de tests Python. 
*   **Dossier `tests/`** : Tous les fichiers de test (`test_*.py`) sont isolés dans ce dossier.
*   **Tests sur `file_loader.py`** : Nous avons créé des tests pour valider les fonctions de base :
    *   Chargement nominal (CSV et Excel).
    *   Détection automatique du séparateur et de l'encodage.
    *   Gestion des erreurs (fichier inexistant, format non supporté).

Résultats des tests sur file_loader
Les tests ont permis de valider plusieurs points clés :

Chargement CSV : Le fichier est bien lu et les colonnes détectées.
Chargement Excel : Support du format .xlsx intégré.
Gestion d'erreurs : Si on passe un fichier inexistant ou un format non supporté (ex: .txt), la fonction renvoie une erreur claire (FileNotFoundError ou ValueError) au lieu de planter le script silencieusement.
tests/test_file_loader.py::TestLoadFile::test_chargement_csv_nominal PASSED            [ 10%]
tests/test_file_loader.py::TestLoadFile::test_chargement_excel PASSED                  [ 20%]
tests/test_file_loader.py::TestLoadFile::test_detection_separateur_virgule PASSED      [ 30%]
tests/test_file_loader.py::TestLoadFileErrors::test_fichier_inexistant PASSED          [ 40%]
tests/test_file_loader.py::TestLoadFileErrors::test_format_non_soutenu PASSED          [ 50%]
tests/test_file_loader.py::TestLoadFileErrors::test_fichier_vide FAILED                [ 60%]
tests/test_file_loader.py::TestHelpers::test_detect_encoding_utf8 PASSED               [ 70%]
tests/test_file_loader.py::TestHelpers::test_detect_delimiter_semicolon PASSED         [ 80%]
tests/test_file_loader.py::TestHelpers::test_detect_delimiter_tab PASSED               [ 90%]
tests/test_file_loader.py::TestHelpers::test_detect_delimiter_default PASSED           [100%]


### 3. Résolution du bug sur les fichiers vides (`test_fichier_vide FAILED`)

**Problème initial :**
Le test échouait car `pd.read_csv()` levait une exception `EmptyDataError` non capturée dès que le fichier était vide (0 octet ou seulement des sauts de ligne). Cela bloquait le chargement.

**Correctif appliqué dans `file_loader.py` :**
1.  **Vérification proactive :** Ajout d'un contrôle `os.path.getsize(file_path) == 0` au tout début de la fonction pour détecter les fichiers vides instantanément.
2.  **Sécurité supplémentaire (try/except) :** Enveloppons l'appel à `pd.read_csv()` dans un bloc de capture spécifique :
    ```python
    try:
        df = pd.read_csv(file_path, sep=delimiter, encoding=encoding)
    except pd.errors.EmptyDataError:
        # Retourne un DataFrame vide proprement au lieu de planter
        return pd.DataFrame()
    ```

**Résultat final :** 
La fonction `load_file` ne plante plus. Si le fichier est vide, elle retourne calmement un objet `pd.DataFrame()` vide (qui fait 0 ligne et 0 colonne). Le test passe donc avec succès.

---

## Récapitulatif final (V1.0 - Stable)

## Étape 10 : Stabilisation du Moteur de Nettoyage et Passage aux Tests Unitaires

Cette étape est cruciale car elle marque le passage d'un "script qui fonctionne" à un "programme robuste et testé".

### 1. Résolution des bugs dans `cleaner_engine.py`
Nous avons corrigé plusieurs erreurs logiques persistantes :

*   **Bug sur la `median` (Médiane)** : Le `fillna` de la médiane pour les colonnes numériques n'était pas appliqué directement au DataFrame (`df_cleaned`). Nous avons rectifié en écrivant explicitement `df_cleaned[col] = df_cleaned[col].fillna(median_val)`.
*   **Bug sur le `mode` (Mode)** : La variable `col_mode` était parfois mal indentée ou non définie dans la boucle. Nous avons clarifié la logique pour que les colonnes de type "texte" (comme `'email'`) soient bien détectées, calculées via `.mode()[0]`, et ensuite remplies proprement avec `fillna`.
*   **Gestion des types (`StringDtype`)** : Une colonne contenant du texte dans un fichier moderne Pandas n'est pas toujours de type `'object'`. Nous avons ajusté la logique pour que les conversions numériques (comme `'10.5'` → `float`) se fassent correctement en utilisant `pd.to_numeric()`.

### 2. Premiers Tests Unitaires (`pytest`)
Nous avons commencé à intégrer des tests automatisés pour garantir qu'un changement de code ne "casse" pas les fonctionnalités existantes (régression).

**Résultats des tests sur le moteur de nettoyage (`cleaner_engine`)** :
*   **Clean Missing Values** ✅ : Les fonctions de remplissage par la médiane et le mode fonctionnent.
*   **Clean Types** ✅ : La détection automatique de colonnes à convertir (String → Numérique) est fiable.
*   **Clean Duplicates** ✅ : Le nombre de doublons supprimés est correct.

### 3. Impact sur l'architecture
Grâce aux tests, nous pouvons désormais refactoriser le code en toute sécurité. 
Le fichier `DEROULEMENT_PROJET.md` devient notre source de vérité technique, documentant chaque erreur rencontrée et sa solution.

---

### 4. Résolution des derniers bugs critiques dans cleaner_engine.py
 ⚠️
Le pipeline fonctionnait globalement mais restait bloqué par 3 erreurs de type ("TypeErrors" ou "Logique"). Voici comment elles ont été résolues pour garantir la compatibilité avec les versions récentes de pandas (2.x et 3.x) :

Erreur sur les Types (
clean_types
) :

Problème : Int64 est le type nullable de pandas, mais le test cherchait np.int64. Le test plantait.
Solution : On a adapté la logique pour que les colonnes converties soient compatibles avec les vérifications de types standards tout en gardant la gestion des NaN.
Erreur sur les Doubles (
clean_duplicates
) :

Problème : Le test test_doublons_exact échouait (le DataFrame n'était pas modifié). C'était un problème d'ordre de nettoyage ou de copie du DataFrame.
Solution : On a sécurisé l'appel avec .copy() et vérifié que les colonnes étaient bien traitées avant de supprimer les doublons.
Erreur sur les Outliers (
clean_outliers
) :

Problème : Tentative d'écriture de valeurs à virgule (la borne IQR) dans des colonnes entières (int64), ce qui provoque une erreur LossySetitemError.
Solution : On convertit systématiquement les colonnes numériques en Float64 (qui accepte les NaN et les virgules) avant d'appliquer la logique IQR.

### 5. Stabilisation du Pipeline et Passage aux Tests Unitaires 🛡️
Nous avons maintenant un ensemble de tests automatisés qui s'assurent que chaque brique du nettoyage fonctionne individuellement :

clean_empty_columns
 ✅ : Supprime les colonnes avec >95% de NaN.
clean_whitespace
 ✅ : Nettoie les espaces superflus sans casser les données.
clean_types
 ✅ : Transforme automatiquement les strings en numbers/dates quand c'est pertinent.
clean_duplicates
 ✅ : Gère correctement les lignes identiques.
clean_missing_values
 ✅ : Remplit les trous avec la médiane (pour les chiffres) ou le mode (pour le texte).


### 6. Tentative d'automatisation du nettoyage des Outliers (Boucle IQR itérative)

**Pourquoi cette fonctionnalité ?**
Le test de régression (`test_correction_iqr`) a révélé une faille critique de l'algorithme IQR simple sur les petits échantillons. 
*   *Le problème :* Si on a `[0, 1, 2, -999]`, Q1 est à 0 (ou 0.25). La borne inférieure devient $0 - 1.5 \times 1.2 = -1.8$. Or, **-999 est plus grand que -1.8**. L'algorithme pense donc que le "monstre" est valide.

**Ce qu'on essaie de faire :**
Au lieu d'appliquer les bornes une seule fois (One-pass), nous implémentons une fonction `clean_outliers_robust` qui :
1.  Calcule les bornes IQR actuelles.
2.  Repère si des valeurs se trouvent à l'extérieur de ces bornes.
3.  Si c'est le cas, **remplace** temporairement ces valeurs aberrantes par la borne la plus proche (winsorisation stricte).
4.  Recommence le calcul des bornes sur les nouvelles données "assainies".
5.  Boucle tant que toutes les valeurs sont comprises dans les bornes ou qu'on a atteint un seuil de sécurité (10 itérations max pour éviter les boucles infinies).

**État actuel :** En cours d'intégration avec des tests unitaires spécifiques (`test_iqr_multi_pass`).

 ---

## Étape 11 : Analyse de Régression et Tests Unitaires (`pytest`)

### Contexte
En lançant les tests unitaires (`pytest`) pour valider l'architecture modulaire, nous avons constaté une régression inattendue. Le script principal (`main.py`) fonctionne car il utilise correctement le retour des fonctions (assignation), mais les fonctions isolées dans `cleaner_engine.py` posent problème dans un contexte de test pur.

### Résultats des tests (14 collectés)
- **11 Passed** ✅ (La logique globale et le pipeline d'intégration passent).
- **3 Failed** ❌ (Des anomalies persistantes dans les fonctions isolées).

### 1. Échec sur `clean_duplicates` (`test_doublons_exact`)
*   **Symptôme :** Le test s'attend à ce que la longueur du DataFrame passe de 4 à 3, mais elle reste à 4.
*   **Analyse technique :** Cette fonction est une "fonction pure" : elle retourne un tuple `(df_cleaned, count)` mais ne modifie pas le DataFrame d'origine. Dans `main.py`, l'appel est correct (`df = clean(df)[0]`), mais dans le test unitaire, il faut impérativement récupérer le premier élément du retour.
*   **Leçon :** L'intégration via `main.py` masque parfois les erreurs si on n'affecte pas bien la variable de retour.

### 2. Échec sur `clean_outliers` (`test_correction_iqr`)
*   **Symptôme :** La valeur aberrante `-999` est toujours présente dans le DataFrame nettoyé.
*   **Analyse technique :** L'algorithme IQR calcule des bornes basées sur Q1 et Q3. Avec un échantillon très petit (3 ou 4 points) et une outlier si extrême, les quartiles sont décalés. La borne inférieure calculée est parfois *plus basse* que -999 (ex: Q1=-600), rendant la valeur "valide" aux yeux du script.
*   **Piste de correction :** Ajouter un filtre préalable ou une logique de détection par écart-type si le DataFrame est trop petit pour être représentatif des quartiles.

### 3. Échec sur `clean_types` (`test_conversion_object_vers_numeric`)
*   **Symptôme :** Assertion échouée : `assert df['col'].dtype in [np.float64, np.int64]` retourne `Int64Dtype()`.
*   **Analyse technique :** Pandas 2.x utilise par défaut le type `Int64` (int nullable avec support des NaN) plutôt que le standard NumPy `np.int64`. Les données sont correctes, mais la vérification du test est trop rigide.
*   **Correction requise :** Utiliser `pd.api.types.is_integer_dtype()` ou vérifier que le type appartient aux types pandas (`Int64`, `Float64`) et non uniquement à NumPy.

### Résultat final de l'étape
Le pipeline global (`test_pipeline_complet`) valide que si l'orchestrateur fait bien son travail, les données finales sont propres. Cependant, pour garantir la robustesse du moteur (`cleaner_engine`), il faut corriger ces 3 points dans les tests unitaires.

## Étape 12 : Correction des Tests Unitaires et Résolution des "Fausses" Négatives 🐛🛠️

Dans cette étape critique, nous avons identifié pourquoi certains tests échouaient malgré un pipeline fonctionnel en production. Les erreurs provenaient de la rigidité des fixtures de test et du comportement mathématique de pandas sur de petits échantillons.

### 1. Analyse de l'échec `test_doublons_exact`
*   **Symptôme :** Le test échouait car le DataFrame retenu contenait toujours 4 lignes.
*   **Analyse technique :** Le DataFrame initial (`dirty_df`) contenait des lignes avec le même ID (2) mais des noms différents ("Bob" et "Alice"). `drop_duplicates()` de pandas considère que ce sont deux lignes *distinctes* car elles ne sont pas identiques caractère pour caractère.
*   **Correctif appliqué :** 
    1. Nous avons créé une fixture dédiée (`dirty_df_with_exact_doublons`) contenant des répétitions parfaites de toutes les colonnes.
    2. Cette approche garantit que le test valide bien la logique de suppression de doublons sans être faussé par d'autres données.

### 2. Analyse de l'échec `test_correction_iqr`
*   **Symptôme :** La valeur -999 n'était pas supprimée/correctement traitée.
*   **Analyse technique :** 
    *   L'algorithme IQR nécessite des colonnes de type numérique pur (`np.number`). Si la présence de NaN ou d'espaces laisse pandas interpréter la colonne comme `object` (string), le calcul `quantile()` échoue silencieusement ou renvoie des valeurs par défaut incohérentes.
    *   De plus, sur un échantillon minuscule (ex: `[25, NaN, 35]`), l'IQR est très faible, rendant la borne inférieure (`Q1 - 1.5*IQR`) autour de 20. La valeur -999 étant bien en dessous, elle est détectée comme aberrante.
*   **Correctif appliqué :** 
    *   Ajout d'une étape explicite `pd.to_numeric(errors='coerce')` avant le calcul des bornes dans `clean_outliers`.
    *   Utilisation de `.fillna(median())` sur une copie temporaire du DataFrame pour calculer les quartiles sans perdre l'information des indices originaux.

---

## Étape 13 : Préparation à la présentation (Audit de professionnalisme)

Dans cette phase finale, l'objectif est de transformer un projet technique en un produit prêt pour une présentation professionnelle (Candidature). L'accent a été mis sur la communication, la clart_ de la documentation et la suppression des traces de travail "brouillon".

### 1. Audit de cohérence structurelle
* **Objectif** : S'assurer que le `README.md` ne promet rien que le code ne puisse réaliser (évitement du syndrome du "Feature Creep" non documenté).
* **Action** : Vérification systématique entre les modules présents dans `src/` et les fonctionnalités annoncées au lecteur.
* **Résultat** : Alignement total de la documentation sur les capacités réelles du pipeline (retrait des mentions de modules inexistants comme `validator`).

### 2. Professionnalisation de la documentation technique
* **Élimination des "traces de chantier"** : Suppression des commentaires de développement, des notes personnelles et des rappels d'erreurs passées à l'intérieur du code source (`src/file_loader.py`) pour ne laisser que une documentation API propre (Docstrings).
* **Refonte de la communication des capacités** : Passage d'une liste de fonctions techniques à une présentation par "Capacités Métier" (ex: "Intelligence de lecture", "Audit & Traçabilité"). L'idée est de mettre en avant la valeur ajoutée pour un utilisateur Data.

### 3. Stratégie de communication sur l'IA (AI-Augmented Engineering)
* **Positionnement** : Transformation de la méthode de travail (utilisation d'agents LLM) en une compétence stratégique : l'orchestration d'intelligence artificielle pour accéliter le cycle de développement et la robustesse du code.
* **Valorisation de l'expertise humaine** : Mise en avant du rôle critique de l'humain dans l'architecture, la conception des processus de convergence (itérations sur les types) et l'audit final du pipeline.

### Résumé de la maturité du projet au terme de cette étape
Le projet est passé d'un script de nettoyage expérimentale à un **systle de pipeline de données structuré, testé et prêt pour une présentation professionnelle**, capable de démontrer à la fois des compétences en Python avancé, en manipulation de données (Pandas/Numpy) et en gestion moderne du cycle de vie logiciel.





---

## Étape 14 : Développement du module de Profilage (`data_profiler`) 📊

Dans cette étape, nous avons ajouté une brique essentielle au pipeline : **la phase d'inspection**. Avant même de penser à nettoyer, il est impératif de comprendre la structure et la qualité des données brutes.

### 1. Objectif du module `DataProfiler`
Créer un outil autonome (`src/data_profiler.py`) capable de produire un rapport structuré (format Markdown) sans dépendre de lourdes librairies tierces comme `ydata-profiling`. 

**Pourquoi "from scratch" ?**
*   **Légèreté :** Aucune dépendance externe complexe (matplotlib, scipy...) à gérer.
*   **Transparence :** Comprendre les statistiques de base (IQR, médiane, top-N) est une compétence clé d'analyste.
*   **Intégration facile :** Le rapport `.md` peut être consulté directement sur GitHub ou GitLab pour un partage rapide des findings.

### 2. Fonctionnalités implémentées
Le moteur `DataProfiler` analyse le DataFrame et génère les sections suivantes :

1.  **🧱 Vue d'ensemble** : Dimensions (Lignes/Colonnes) et poids estimé.
2.  **🏷️ Types de colonnes** : Identification précise des types (`Int64`, `Float64`, `object`...) pour anticiper les conversions nécessaires.
3.  **⚠️ Matrice de Qualité (NaN)** : 
    *   Calcul du compte et du pourcentage de valeurs manquantes par colonne.
    *   Focalisation sur les colonnes critiques (> 0%).
4.  **📈 Statistiques Numériques** :
    *   Utilisation de `describe()` pour les min, max, moyennes et percentiles (Q1, Q3).
    *   Cela permet d'identifier visuellement les outliers potentiels avant même le nettoyage.
5.  **🔤 Top Catégorielles** :
    *   Pour les colonnes texte/categ, on affiche le "Top 3" des valeurs les plus fréquentes (au lieu de tout lister, ce qui serait illisible).
6.  **👀 Aperçu Brut** : Les 5 premières lignes formatées en tableau Markdown.

### 3. Tests Pytest
3 ok et 13 erreurs, essentiellement dues à un module absente mais nécessaire : Tabulate
après installation de ce module, 5 KO sur 16 : un même problème car je faisais une opération sur un Tuple
après correction de cette anomalie, une nouvelle mais unique erreur est apparue suite un correctif dans le fichier de tests
après mise à jour du fichier de tests par l'agent testeur, tous les tests sont OK
je corrige néanmoins les alertes de Pandas

### 4. Intégration au Pipeline
Le flux de travail devient maintenant :
1.  **Chargement** (`file_loader`)
2.  **Profiling** (`data_profiler`) ➡️ *Nouveau* : Génère `data/processed/report_profile.md`
3.  **Nettoyage** (`cleaner_engine`)
4.  **Sauvegarde & Rapport Final** (`cleaner_logger`)

**Défis techniques résolus aujourd'hui :**
*   **Gestion des chemins relatifs :** Utilisation de `Path(__file__).parent.parent` pour que le script fonctionne depuis n'importe quel répertoire (racine ou sous-dossier `src/`).
*   **Correction des imports dynamiques :** Ajout de `sys.path.insert(0, ...)` dans le fichier orchestrator pour éviter les `ModuleNotFoundError` quand le script est lancé depuis l'intérieur d'un package.

### 4. Préparer le terrain pour les futures alertes
La classe `DataProfiler` inclut désormais une méthode预留 (`detect_quality_issues`). Cette structure est prête à accueillir nos prochaines règles métier (ex: "Si une colonne 'Age' a des valeurs < 0, alerter l'utilisateur").

---