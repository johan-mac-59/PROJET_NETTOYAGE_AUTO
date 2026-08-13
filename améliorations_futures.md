# 🚀 Roadmap du Projet

## 🛠️ Développement Technique (En cours)
- **Module `validator`** : Création d'un moteur de vérification des contraintes (types, formats, plages de valeurs).
- **Documentation API** : Rédaction d'un document technique détaillé décrivant l'interface et les paramètres de chaque fonction.
- **rendre optionnelle l'écrètage des outliers** : permettre à l'utilisateur ou rendre automatique le besoin d'écrèter ou non les valeurs aberrantes
- **rendre flexible le loader** : permettre à l'utilisateur de choisir le fichier
- **enrichir le DataProfiler** : renseigner le fichier source, mettre des graphiques (répartition, heatmap, dispersion, outliers...)

## 📊 Améliorations Fonctionnelles
- **Support JSON** : Implémentation du chargement des fichiers .json via l'intégration de pd.read_json() dans le module file_loader.
- **enrichir le rapport** : ajouter un nouveau DataProfiler à la suite du nettoyage
- **améliorer la détection des dates** : être plus explicite sur le format 
- **Séparer profiling et cleaning** : permettre de lancer un nettoyage des données après avoir pris le temps d'analyser la structure du dataset



# 📋 Cahier des Charges : Améliorations du DataProfiler (V2)

## 1. Objectif Principal
Transformer le profilage des données d'une simple statistique descriptive en un **outil d'aide à la décision** pour le nettoyage (Data Cleaning). Le livrable final doit être un rapport unique, autonome et lisible.

## 2. Décisions Architecturelles & Techniques

### 📄 Format du Rapport
*   **Choix :** Génération d'un fichier `.html` unique et autonome.
*   **Justification :** 
    *   Support natif des graphiques sans dépendances externes (pas de dossiers `images/`).
    *   Portabilité totale : un seul fichier à partager, s'affiche dans tout navigateur.
    *   Utilisation de l'encodage **Base64** pour intégrer les images (`<img src="data:image/png;base64...">`) directement dans le flux HTML.

### 📂 Métadonnées & Contexte Source
Le rapport doit inclure en haut :
*   Nom du fichier source original.
*   Chemin d'accès complet.
*   Date et heure de génération du rapport.
*   Hash du fichier (optionnel futur) pour détection de modification.

### 🧠 Intelligence des Colonnes (Classification Dynamique)
Nous ne traitons plus les données comme "juste num/obj", mais selon leur pertinence analytique via une **limite de cardinalité relative**.

*   **Logique de classification :**
    *   Calcul du ratio : `n_unique_values / total_rows`.
    *   **Seuil à définir (ex: 0.5 ou 0.8) :**
        *   Si `ratio > seuil` : La colonne est considérée comme **"Identifiant Unique"** (ID, Email, Téléphone). Exclue des graphiques de distribution standard.
        *   Si `ratio <= seuil` : La colonne est considérée comme **"Catégorielle"**.

## 3. Métriques et Statistiques Dédiées

### 📊 Pour les Colonnes Numériques
*   Stats classiques (Moyenne, Médiane, Quartiles).
*   **Détection d'Outliers :** Calcul des bornes IQR ($Q1 - 1.5 \times IQR$, $Q3 + 1.5 \times IQR$) et % de points aberrants.

### 📊 Pour les Colonnes Catégorielles (Validées par le seuil)
*   **Cardinalité Absolue et Relative.**
*   **Sparsity Ratio :** Taux de valeurs manquantes spécifique.
*   **Skewness de Fréquence :** Pourcentage détenu par la catégorie majoritaire. Si > 90%, alerter sur la faible variance.
*   **Qualité du Format :** Détection d'hétérogénéité (majuscules/minuscules, espaces).

### 📉 Analyse Ligne par Ligne (Nouveau)
*   Calcul du pourcentage de valeurs manquantes par ligne (`pct_null_in_row`).
*   **Alertes contextuelles :** 
    *   `row_full_empty` (> 90% vide) : "À supprimer".
    *   `row_partially_empty` (30-90% vide) : "À inspecter manuellement".

## 4. Stratégie de Visualisation (Graphiques)
Pour éviter un rapport illisible, les graphiques ne sont générés **que si** `len(df) < 100,000` lignes.

*   **Si Numérique :**
    *   **Boxplot (Moustaches) :** Visualisation des outliers.
    *   **Histogramme / KDE :** Forme de la distribution.
*   **Si Catégorielle :**
    *   **Top-N Bar Chart :** Top 10 catégories les plus fréquentes + segment "Autres".
*   **Vue Globale (Optionnelle) :**
    *   Heatmap de corrélation des manquants.

## 5. Prochaines Étapes d'Implémentation
1.  Implémenter `run_analysis` avec le calcul du ratio de cardinalité et la séparation des colonnes (`numeric`, `categorical`, `skipped_unique`).
2.  Calculer les métriques catégorielles spécifiques (Skewness fréquence, Sparsity).
3.  Créer `generate_html_report` :
    *   Utiliser `matplotlib`/`seaborn` en mémoire (`io.BytesIO`).
    *   Encoder les figures en Base64.
    *   Injecter le HTML/CSS et les images dans un template propre.