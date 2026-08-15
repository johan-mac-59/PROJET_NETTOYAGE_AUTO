import pandas as pd
import numpy as np
from typing import Tuple

def clean_empty_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Supprime les colonnes avec >95% de valeurs manquantes."""
    if df.empty:
        return df, 0
    # On compte les NA (NaN, None, etc.)
    na_ratio = df.isna().mean()
    cols_to_drop = na_ratio[na_ratio >= 0.95].index.tolist()
    
    n_dropped = len(cols_to_drop)
    if n_dropped > 0:
        df_cleaned = df.drop(columns=cols_to_drop)
    else:
        df_cleaned = df.copy() # Sûr de retourner une copie si rien ne change
        
    return df_cleaned, n_dropped

def clean_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Nettoie les espaces superflus dans les colonnes de type string."""
    if df.empty:
        return df, 0
    
    n_modified = 0
    df_cleaned = df.copy()
    
    # On cible les colonnes string (object ou new StringDtype)
    cols_to_process = df_cleaned.select_dtypes(include=['object', 'string']).columns

    for col in cols_to_process:
        # On convertit temporairement en string pour nettoyer, même si c'est déjà string
        # C'est important pour capturer les NaN qui deviennent le mot "nan" qu'on peut traiter si besoin
        original_str = df_cleaned[col].astype(str)
        
        cleaned_values = original_str.str.strip().str.replace(r'\s+', ' ', regex=True)
        
        # CORRECTION : On compare les versions string pour éviter les pièges des NaN (NaN != NaN est True)
        changed_mask = original_str != cleaned_values
        
        n_modified += changed_mask.sum()
        
        df_cleaned[col] = cleaned_values
        
    return df_cleaned, n_modified

def fix_numeric_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Corrige les colonnes que Pandas a chargées en float à tort (ex: '1.0' au lieu de 1)
    pour les passer en entier nullable si possible.
    """
    conversions = {}
    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        # Si la colonne est déjà un entier standard ou un objet, on ne touche pas
        if pd.api.types.is_integer_dtype(df_cleaned[col]) or df_cleaned[col].dtype == 'object':
            continue
            
        # On cible uniquement les colonnes Float chargées automatiquement
        if not pd.api.types.is_float_dtype(df_cleaned[col]):
            continue

        series = df_cleaned[col]
        
        # Vérifier si toutes les valeurs non nulles sont des entiers (ex: 2.0, 5.0)
        non_na = series.dropna()
        if len(non_na) == 0:
            continue
            
        # Si la partie décimale est toujours 0, c'est un entier déguisé
        if (non_na % 1 == 0).all():
            try:
                # On convertit en Entier Nullable (Int64 avec 'I' majuscule)
                # Ce type accepte les NaN sous forme de <NA>
                df_cleaned[col] = series.astype('Int64')
                conversions[col] = 'float64 -> Int64 (correction Pandas)'
            except Exception as e:
                # Si l'overflow ou autre erreur, on laisse en float
                pass

    return df_cleaned, conversions

def _can_be_numeric(series: pd.Series) -> bool:
    """
    Détermine si une colonne de type string/objet peut être convertie en nombre.
    
    Règles de filtrage (Heuristiques) :
    1. Ignorer les identifiants alphanumériques mixtes (ex: 'R43873', 'AB-12').
       Si le contenu contient des lettres isolées (pas juste dans des mots comme 'euro'), on garde en string.
    2. Ignorer les formats complexes non numériques purs (ex: '4/5', '10%').
       On ne touche que ce qui ressemble strictement à un nombre (chiffres, signes, séparateurs décimaux).
    3. Accepter les nombres avec symboles monétaires (€, $, £) ou espaces de milliers.
    """
    # On ignore les colonnes vides
    valid_data = series.dropna()
    if len(valid_data) == 0:
        return False

    # On prend un échantillon significatif pour la détection (plus rapide et robuste)
    sample = valid_data.head(100) 
    non_numeric_count = 0
    
    for val in sample:
        val_str = str(val).strip()
        
        # Si la valeur est vide après strip, on continue
        if not val_str:
            continue
            
        # Règle 1 : Détection d'ID alphanumérique mixte
        # Si on trouve des lettres qui ne sont pas dans un mot complet (ex 'euro' est OK si c'est rare, 
        # mais 'R43873' non plus. Ici on veut éviter les IDs type 'A12B').
        # On vérifie si la chaine contient à la fois des chiffres et des lettres alphabétiques pures.
        if any(c.isalpha() for c in val_str) and any(c.isdigit() for c in val_str):
            # Est-ce que c'est un mot complet (comme 'euro') ou un mélange ID-like ?
            # On considère qu'un ID mixte est valide si les lettres et chiffres sont collés ou séparés par des tirets simples
            # Mais pour être sûr, on va utiliser une regex simple : si il y a des lettres ET des chiffres, 
            # on vérifie si c'est du type "Lettres+Chiffres" pur.
            if not val_str.replace('-', '').replace('_', '').isalpha() and \
               not val_str.replace('-', '').replace('_', '').isdigit():
                return False

        # Règle 2 : Détection de formats complexes ('/', '%', etc.)
        # On accepte uniquement les caractères autorisés pour un nombre : chiffres, signes, points, virgules, espaces, $, €
        allowed_chars = set("0123456789+-.,;€$£ ")
        if any(c not in allowed_chars for c in val_str):
            return False
            
    # Si on est là, tous les échantillons valides sont "proches" d'un nombre.
    return True

def clean_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Convertit automatiquement les types de colonnes en toute sécurité."""
    if df.empty:
        return df.copy(), {} 
    
    conversions = {}
    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        # 1. Si déjà numeric/datetime on passe (sauf si on veut ré-analyser, mais on suppose que c'est propre)
        if pd.api.types.is_numeric_dtype(df_cleaned[col]) or pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
            continue

        # On force en string pour uniformiser le traitement des "objets"
        if df_cleaned[col].dtype == 'object':
            df_cleaned[col] = df_cleaned[col].astype('string')

        # 2. Filtrage rapide : est-ce que cette colonne a CHANCE d'être numérique ?
        # Si non (ex: notes "4/5", IDs "A12-B"), on passe à la suite sans rien faire.
        if not _can_be_numeric(df_cleaned[col]):
            continue

        # 3. Nettoyage spécifique NUMÉRIQUE AVANT conversion
        # On prépare les données pour que pd.to_numeric fonctionne à 100%
        cleaned_series = df_cleaned[col].copy()
        
        # A. Suppression des symboles monétaires et espaces inutiles (séparateurs de milliers)
        cleaned_series = cleaned_series.str.replace('€', '', regex=False)
        cleaned_series = cleaned_series.str.replace('$', '', regex=False)
        cleaned_series = cleaned_series.str.replace(' ', '', regex=False) # Supprime les espaces de milliers ex: "1 000" -> "1000"
        
        # B. Gestion des séparateurs décimaux européens (virgule) vs anglo-saxons (point)
        # On remplace la virgule par un point pour standardiser, mais on doit faire attention aux séparateurs de milliers 
        # si le format est ex: "1.200,50" (point = milliers, virgule = décimal).
        # Pour simplifier et être robuste :
        # Si il y a des points ET des virgules, on suppose souvent que le dernier séparant est le décimal.
        # Exemple : "1 200,50 €" -> après étape A, ça devient "1200,50". Donc juste remplacer , par .
        
        # Cas particulier : "1.234" (milliers euro) vs "1.234" (décimal). 
        # Les décimales peuvent utiliser la virgule. Les points semblent être des séparateurs de milliers ou des dates mal parsées.
        # Hypothèse : Si on a une virgule, elle est le séparateur décimal.
        
        if cleaned_series.str.contains(',', regex=False).any():
            # Il y a des virgules -> On considère la virgule comme séparateur décimal
            cleaned_series = cleaned_series.str.replace('.', '', regex=False) # Enlève les éventuels séparateurs de milliers (points)
            cleaned_series = cleaned_series.str.replace(',', '.', regex=False) # Transforme le décimal en point standard python/pandas
        else:
            # Pas de virgule. On suppose que le point est soit un séparateur de milliers, soit un décimal.
            # Si on a "1.000" (3 chiffres après le point) -> Séparateur de milliers ? Ou entier ?
            # Pour éviter de perdre des décimales, on garde les points tels quels sauf s'ils semblent être des millers.
            # Une règle simple : si le nombre de points > 1 ou que la partie après le dernier point a plus de 2 chiffres, c'est peut-être un mille.
            # Exemples: "1501,73" (virgule), "1410,10" (virgule), "1274.52" (point).
            # Donc on ne touche rien si pas de virgule, et on laisse pd.to_numeric gérer le point ou l'ignore s'il est illisible.
            pass

        # C. Remplacement des NaN textuels éventuels par np.nan
        cleaned_series = cleaned_series.replace(['', 'nan', 'None', 'NULL'], np.nan)

        # 4. Tentative de conversion numérique
        numeric_data = pd.to_numeric(cleaned_series, errors='coerce')
        
        # Seuil à 90% de validité sur les données ORIGINALES (pas nettoyées) pour valider que la colonne est "numérique"
        # Mais on utilise les données NETTOYÉES pour le calcul final
        original_valid_rate = df_cleaned[col].notna().sum() / len(df_cleaned[col])
        
        # Si après nettoyage, on a encore trop de NaN, c'est que la colonne n'était pas si numérique que ça (peut-être des erreurs de format)
        cleaned_valid_rate = numeric_data.notna().sum() / len(numeric_data)
        
        if cleaned_valid_rate > 0.9: 
            non_na_values = numeric_data.dropna()
            
            # Vérification robuste pour les entiers : sont-ce vraiment des entiers ?
            is_likely_int = (
                len(non_na_values) > 0 and 
                # Les valeurs sont égales à leur version entière
                (non_na_values == non_na_values.astype(int)).all() and
                # Pas de NaN restants après conversion int (rare mais possible si overflow ou erreur)
                not numeric_data.isna().any() 
            )
            
            if is_likely_int:
                # ON GARDE DES INTS SI POSSIBLE
                df_cleaned[col] = numeric_data.astype(np.int64) 
                conversions[col] = 'object -> int'
            else:
                # SINON FLOAT
                df_cleaned[col] = numeric_data.astype(np.float64)
                conversions[col] = 'object -> float'

        # --- Tentative Date (seulement si la colonne n'a PAS été convertie en nombre) ---
        if col not in conversions:
            try:
                # Spécifier explicitement le format pour éviter les avertissements
                date_data = pd.to_datetime(df_cleaned[col], format='%d/%m/%Y', errors='coerce')
                valid_date_rate = date_data.notna().sum() / len(date_data)
                 
                if valid_date_rate > 0.8:
                    df_cleaned[col] = date_data
                    conversions[col] = 'object -> datetime'
            except (ValueError, TypeError):
                # Si le format échoue, on passe à l'approche par défaut
                try:
                    date_data = pd.to_datetime(df_cleaned[col], errors='coerce')
                    valid_date_rate = date_data.notna().sum() / len(date_data)
                     
                    if valid_date_rate > 0.8:
                        df_cleaned[col] = date_data
                        conversions[col] = 'object -> datetime'
                except Exception:
                    continue

    # Pour garder trace des colonnes concernées dans les conversions
    conversions_with_cols = {}
    for col, conv_type in conversions.items():
        if col not in conversions_with_cols:
            conversions_with_cols[col] = []
        conversions_with_cols[col].append(conv_type)

    return df_cleaned, conversions_with_cols

def clean_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Supprime les doublons exacts."""
    if df.empty:
        return df, 0
    
    df_cleaned = df.copy() 
    n_before = len(df_cleaned)
    
    # On garde la première occurrencee
    df_cleaned = df_cleaned.drop_duplicates(keep='first')
    
    n_removed = n_before - len(df_cleaned)
    return df_cleaned, n_removed

def clean_case_sensitivity(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Unifie la casse des colonnes catégorielles (texte) en minuscules.
    IGNORE les valeurs manquantes pour éviter de transformer 'NaN' en 'nan'.
    """
    if df.empty:
        return df.copy(), {}
    
    df_cleaned = df.copy()
    corrections = {}
    
    # On cible les colonnes textuelles (object ou string)
    text_cols = df_cleaned.select_dtypes(include=['object', 'string']).columns
    
    for col in text_cols:
        # 1. Créer un masque des valeurs NON manquantes
        # .notna() fonctionne même sur les strings 'nan' si le dtype est object/string
        valid_mask = df_cleaned[col].notna()
        
        if not valid_mask.any():
            continue
            
        sample = df_cleaned[col][valid_mask].head(10)
        
        # FILTRES EXISTANTS (ID mixte, etc.)
        is_id_like = False
        for val in sample:
            val_str = str(val)
            if any(c.isalpha() for c in val_str) and any(c.isdigit() for c in val_str):
                if len(val_str) < 10: 
                    is_id_like = True
                    break 
        
        if is_id_like:
            continue

        # Si l'échantillon valide ne contient aucune lettre, on skip.
        # On convertit en string pour chercher des lettres
        has_letters = sample.astype(str).str.contains('[a-zA-Z]').any()
        if not has_letters:
            continue

        # 2. Appliquer lower() UNIQUEMENT sur les valeurs valides (non NaN)
        # C'est important de ne pas toucher aux NaN pour ne pas créer de faux positifs
        original_valid = df_cleaned[col][valid_mask].astype(str)
        
        lowered = original_valid.str.lower()
        
        # On compare : original != lowered
        # Mais attention : "NaN" -> "nan" est techniquement un changement de string, mais pas de casse "réelle" pour une donnée manquante.
        # Pour être propre, on ignore les changements qui ne concernent que la transformation 'NaN' -> 'nan'
        changed_mask = original_valid != lowered
        
        # On retire les faux positifs liés aux NaN textuels
        # Si la valeur originale est "NaN" ou "nan" et devient "nan", on considère que c'est pas une correction de casse "métier"
        nan_text_mask = original_valid.str.lower().isin(['nan', 'none', 'na', 'null'])
        
        # On retire les NaN textuels des changements comptés si ils ne changent pas de sens (juste minuscule standard)
        # En fait, le plus simple est de vérifier : la valeur a-t-elle DES LETTRES MINUSCULES qui étaient MAJUSCULES ?
        # Une heuristique plus robuste : on garde le changement seulement si il contient des lettres alphabétiques visibles
        real_change_mask = changed_mask & (original_valid.str.contains('[a-zA-Z]').fillna(False))

        n_changes = real_change_mask.sum()
        
        if n_changes > 0:
            # On applique la correction uniquement sur les valeurs valides qui ont réellement changé
            df_cleaned.loc[df_cleaned[col].notna(), col] = lowered.where(real_change_mask, df_cleaned[col][valid_mask])
            corrections[col] = int(n_changes)
    
    return df_cleaned, corrections

def clean_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Nettoie les valeurs manquantes de manière intelligente."""
    if df.empty:
        return df.copy(), {}
    
    actions = {}
    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        null_count = df_cleaned[col].isna().sum()
        if null_count > 0:
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                median_val = df_cleaned[col].median()
                # On remplit uniquement les NaN, sans changer le type de la colonne
                mask = df_cleaned[col].isna()
                df_cleaned.loc[mask, col] = median_val
                actions[col] = {
                    'count': null_count,
                    'method': f"fill_median_{median_val}"  # Correction : on n'utilise pas mode_val ici
    }
            
            else:
                mode_val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Inconnu'
                # On force le type string pour éviter les erreurs lors du fillna
                mask = df_cleaned[col].isna()
                df_cleaned.loc[mask, col] = str(mode_val)
                actions[col] = {
                    'count': null_count,
                    'method': f"fill_mode_{str(mode_val)}"
                }

    return df_cleaned, actions

def clip_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Corrige les valeurs aberrantes avec la méthode IQR (Cliping)."""
    if df.empty:
        return df.copy(), {}
    
    corrections = {}
    # On s'assure de prendre uniquement les colonnes numériques actives
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        non_null_data = df[col].dropna()
        
        # Cas limite : si on a trop peu de données, l'IQR n'est pas fiable
        if non_null_data.empty or len(non_null_data) < 2: 
            continue
            
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        # Si l'IQR est 0 (toutes les valeurs sont identiques), on ne peut pas calculer de borne standard
        if IQR == 0:
            continue

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        n_outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()

        if n_outliers > 0:
            # Utilisation de clip()
            df_cleaned_col = df[col].clip(lower=lower_bound, upper=upper_bound)
            
            # Mise à jour en préservant le type numérique standard si possible
            if df_cleaned_col.dtype != df[col].dtype:
                df[col] = df_cleaned_col.astype(np.float64)
            else:
                df[col] = df_cleaned_col
            
            corrections[col] = int(n_outliers)

    return df, corrections

def ask_user_outlier_correction(df: pd.DataFrame, stats: dict, profiler_results: dict = None) -> bool:
    """
    Demande à l'utilisateur s'il veut corriger les outliers.
    
    Args:
        df: DataFrame à nettoyer
        stats: Dictionnaire contenant les statistiques de nettoyage actuelles
        profiler_results: Résultats du DataProfiler pour connaître les outliers détectés
        
    Returns:
        bool: True si l'utilisateur veut corriger, False sinon
    """
    print("\n" + "="*60)
    print("⚠️  Gestion des Valeurs Aberrantes (Outliers)")
    print("="*60)
    
    # Récupération des outliers détectés dans le profiler
    outlier_cols = {}
    
    if profiler_results and 'outliers' in profiler_results:
        outlier_cols = profiler_results['outliers']
    elif 'outliers_corrected' in stats:
        # Si on a déjà les outliers corrigés, on les récupère
        outlier_cols = stats['outliers_corrected']
    
    # Si on n'a pas d'outliers détectés
    if not outlier_cols or (isinstance(outlier_cols, dict) and len(outlier_cols) == 0):
        print("✅ Aucune valeur aberrante détectée dans les données.")
        return False
    
    # Afficher les outliers détectés
    print(f"🔍 {len(outlier_cols)} colonne(s) contient(ent) des valeurs aberrantes :")
    
    # Si c'est un dict avec le format de sortie du profiler
    if isinstance(outlier_cols, dict):
        for col, info in outlier_cols.items():
            if isinstance(info, dict) and 'count' in info:
                print(f"   • {col}: {info['count']} outliers détectés")
            else:
                # Format pour les anciens résultats
                print(f"   • {col}: {info} outliers détectés")
    else:
        # Format simplifié
        print(f"   • Détectés dans {len(outlier_cols)} colonnes")
    
    print("\nLes valeurs aberrantes sont corrigées par la méthode IQR (clipping).")
    print("Cela peut modifier les bornes statistiques et altérer les distributions.")
    print("Souhaitez-vous corriger ces valeurs aberrantes ?")
    print("(Répondez par 'y' (oui) ou 'n' (non). Par défaut : 'n')")
    
    while True:
        reponse = input("⏳ Votre choix [y/n, entrée par défaut 'n'] : ").strip().lower()
        
        # Réponse par défaut si l'utilisateur appuie juste sur Entrée
        if reponse == "":
            print("❌ Choix par défaut : Ne pas corriger les outliers")
            return False
            
        if reponse in ['y', 'yes', 'o', 'oui']:
            print("✅ Vous avez choisi de corriger les valeurs aberrantes.")
            return True
        elif reponse in ['n', 'no', 'non']:
            print("❌ Vous avez choisi de ne pas corriger les outliers.")
            return False
        else:
            print("⚠️ Veuillez répondre par 'y' (oui) ou 'n' (non).")
            print("⏳  Appuyez sur Entrée pour choisir 'n' par défaut.")

def ask_user_missing_values_correction(df: pd.DataFrame, stats: dict, profiler_results: dict = None) -> bool:
    """
    Demande à l'utilisateur s'il veut combler les valeurs manquantes.
    
    Args:
        df: DataFrame à nettoyer
        stats: Dictionnaire contenant les statistiques de nettoyage actuelles
        profiler_results: Résultats du DataProfiler pour connaître les valeurs manquantes
        
    Returns:
        bool: True si l'utilisateur veut combler, False sinon
    """
    print("\n" + "="*60)
    print("⚠️  Gestion des Valeurs Manquantes")
    print("="*60)
    
    # Compter les valeurs manquantes totales
    total_missing = df.isnull().sum().sum()
    
    if total_missing == 0:
        print("✅ Aucune valeur manquante détectée dans les données.")
        return False
    
    print(f"🔍 {total_missing} valeurs manquantes détectées dans l'ensemble du dataset")
    
    # Afficher le nombre par colonne
    missing_by_col = df.isnull().sum()
    missing_by_col = missing_by_col[missing_by_col > 0]
    
    if len(missing_by_col) > 0:
        print("Répartition par colonne :")
        for col, count in missing_by_col.items():
            percentage = (count / len(df)) * 100
            print(f"   • {col}: {count} ({percentage:.1f}%)")
    
    print("\nLes valeurs manquantes sont comblées automatiquement :")
    print("- Pour les colonnes numériques : médiane")
    print("- Pour les colonnes catégorielles : mode")
    print("Souhaitez-vous combler ces valeurs manquantes ?")
    print("(Répondez par 'y' (oui) ou 'n' (non). Par défaut : 'n')")
    
    while True:
        reponse = input("⏳ Votre choix [y/n, entrée par défaut 'n'] : ").strip().lower()
        
        # Réponse par défaut si l'utilisateur appuie juste sur Entrée
        if reponse == "":
            print("✅ Choix par défaut : Na pas combler les valeurs manquantes")
            return False
            
        if reponse in ['y', 'yes', 'o', 'oui']:
            print("✅ Vous avez choisi de combler les valeurs manquantes.")
            return True
        elif reponse in ['n', 'no', 'non']:
            print("❌ Vous avez choisi de ne pas combler les valeurs manquantes.")
            return False
        else:
            print("⚠️ Veuillez répondre par 'y' (oui) ou 'n' (non).")
            print("⏳  Appuyez sur Entrée pour choisir 'y' par défaut.")

def run_all_cleaning_steps(df: pd.DataFrame, max_iterations: int = 5, correct_outliers: bool = True, fill_missing: bool = True) -> Tuple[pd.DataFrame, dict]:
    """
    Applique les nettoyages de manière itérative et ordonnée.
    
    Args:
        df: DataFrame à nettoyer
        max_iterations: Nombre maximum d'itérations
        correct_outliers: Booléen pour décider si on corrige les outliers
        fill_missing: Booléen pour décider si on remplit les valeurs manquantes
    
    Ordre stratégique pour éviter les erreurs en cascade :
    1. Forme (espaces) -> Pour préparer la conversion de types
    2. Types fixes (Pandas Trap) -> Pour corriger les float64 -> Int64 si possible
    3. Conversion Types stricte -> Pour pouvoir faire des calculs statistiques
    4. Structure (doublons/vides) -> Une fois qu'on connaît les vrais types
    5. Stats (Missing/Outliers) -> En dernier, sur des données propres
    """
    stats = {
        'empty_cols_dropped': 0,
        'whitespace_cleaned': 0,
        'case_normalized': {},
        'types_fixed_pandas': {},
        'types_converted': {},
        'duplicates_removed': 0,
        'missing_filled': {},
        'outliers_corrected': {}
    }

    current_df = df.copy()
    
    # Boucle de nettoyage automatique (sans interaction utilisateur)
    for iteration in range(max_iterations):
        print(f"\n🔄 Itération {iteration + 1}/{max_iterations}")
        
        # Sauvegarder l'état avant le nettoyage
        previous_shape = current_df.shape
        
        # 1. Nettoyage Forme (AVANT les types ! " 45" doit devenir 45)
        current_df, n_spaces = clean_whitespace(current_df)
        if n_spaces > 0:
            stats['whitespace_cleaned'] += n_spaces

        # 2. Correction des types "Pandas Trap" 
        current_df, fix_stats = fix_numeric_types(current_df)
        if fix_stats:
            stats['types_fixed_pandas'].update(fix_stats)

        # 3. Conversion Types (CRITIQUE : on transforme " 45" en int/float maintenant)
        current_df, conversions = clean_types(current_df)
        if conversions:
            stats['types_converted'].update(conversions)

        # 4. Nettoyage Structurel (Colonnes vides)
        current_df, n_dropped = clean_empty_columns(current_df)
        if n_dropped > 0:
            stats['empty_cols_dropped'] += n_dropped

        # 5. Nettoyage de la casse (à faire après espaces et types mais avant doublons)
        current_df, case_corrections = clean_case_sensitivity(current_df)
        if case_corrections:
            stats['case_normalized'].update(case_corrections)

        # 6. Doublons (Avant IQR/Median pour ne pas fausser les bornes)
        current_df, n_dups = clean_duplicates(current_df)
        if n_dups > 0:
            stats['duplicates_removed'] += n_dups

        # 7. Vérification si on continue ou non
        # Si aucune modification n'a été faite (ni ligne ni colonne ni type), on arrête
        current_shape = current_df.shape
        
        # Vérifier s'il y a eu des changements dans la structure
        changes_detected = (
            n_spaces > 0 or 
            len(fix_stats) > 0 or 
            len(conversions) > 0 or 
            n_dropped > 0 or 
            sum(case_corrections.values()) > 0 or 
            n_dups > 0 or
            current_shape != previous_shape  # Si le nombre de lignes ou colonnes a changé
        )
        
        if not changes_detected:
            print("✅ Aucune modification détectée. Arrêt anticipé du nettoyage.")
            break
    
    # 8. Missing Values (Remplissage) - Exécuté ici de manière explicite
    if fill_missing:
        current_df, fillings = clean_missing_values(current_df)
        if fillings:
            stats['missing_filled'].update(fillings)
        else:
            # Si le traitement est actif mais qu'il n'y avait pas de valeurs à combler, 
            # on garde un dictionnaire vide (cohérent avec le cas où il y en avait)
            pass 
    else:
        print("⚠️ Remplissage des valeurs manquantes ignoré par l'utilisateur.")
        # Format cohérent : on indique explicitement que c'est ignoré
        stats['missing_filled'] = {'ignored': True}

    # 9. Outliers IQR (En dernier, sur données numérées et propres) 
    if correct_outliers:
        current_df, outliers = clip_outliers(current_df)
        if outliers:
            for col, count in outliers.items():
                stats['outliers_corrected'][col] = stats['outliers_corrected'].get(col, 0) + count
    else:
        print("⚠️ Correction des outliers ignorée par l'utilisateur.")
        # On indique simplement dans les stats que c'est ignoré avec un format cohérent
        stats['outliers_corrected'] = {'ignored': True}  # Format cohérent
    
    return current_df, stats