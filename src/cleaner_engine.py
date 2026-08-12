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

def clean_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Convertit automatiquement les types de colonnes en toute sécurité."""
    if df.empty:
        return df.copy(), {} 
    
    conversions = {}
    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        # Si déjà numeric/datetime on passe
        if pd.api.types.is_numeric_dtype(df_cleaned[col]) or pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
            continue

        # On force en string pour uniformiser le traitement des "objets"
        if df_cleaned[col].dtype == 'object':
            df_cleaned[col] = df_cleaned[col].astype('string')

        # --- Tentative Numeric ---
        numeric_data = pd.to_numeric(df_cleaned[col], errors='coerce')
        
        # Seuil à 90% de validité
        if numeric_data.notna().sum() / len(numeric_data) > 0.9: 
            non_na_values = numeric_data.dropna()
            
            # Vérification robuste pour les entiers (corrigé)
            is_likely_int = (
                len(non_na_values) > 0 and 
                (non_na_values == non_na_values.astype(int)).all() and
                not non_na_values.isna().any()
            )
            
            if is_likely_int:
                # On passe en numpy int64 standard pour correspondre aux attentes des tests classiques
                df_cleaned[col] = numeric_data.astype(np.int64) 
                conversions[col] = 'object -> int'
            else:
                # On passe en numpy float64 standard
                df_cleaned[col] = numeric_data.astype(np.float64)
                conversions[col] = 'object -> float'

        # --- Tentative Date (corrigé pour éviter les avertissements) ---
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
                    'method': f"fill_median_{median_val}" if pd.api.types.is_numeric_dtype(df_cleaned[col]) else f"fill_mode_{str(mode_val)}"
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

def run_all_cleaning_steps(df: pd.DataFrame, max_iterations: int = 5) -> Tuple[pd.DataFrame, dict]:
    """
    Applique les nettoyages de manière itérative et ordonnée.
    
    Ordre stratégique pour éviter les erreurs en cascade :
    1. Forme (espaces) -> Pour préparer la conversion de types
    2. Types -> Pour pouvoir faire des calculs statistiques
    3. Structure (doublons/vides) -> Une fois qu'on connaît les vrais types
    4. Stats (Missing/Outliers) -> En dernier, sur des données propres
    """
    stats = {
        'empty_cols_dropped': 0,
        'whitespace_cleaned': 0,
        'types_converted': {},
        'duplicates_removed': 0,
        'missing_filled': {},
        'outliers_corrected': {}
    }

    current_df = df.copy()
    
    for i in range(max_iterations):
        any_change = False

        # 1. Nettoyage Forme (AVANT les types ! " 45" doit devenir 45)
        current_df, n_spaces = clean_whitespace(current_df)
        if n_spaces > 0:
            stats['whitespace_cleaned'] += n_spaces
            any_change = True

        # 2. Conversion Types (CRITIQUE : on transforme " 45" en int/float maintenant)
        current_df, conversions = clean_types(current_df)
        if conversions:
            stats['types_converted'].update(conversions)
            any_change = True

        # 3. Nettoyage Structurel (Colonnes vides)
        # On ne le fait qu'au premier tour ou si on a besoin de réévaluer suite à un type change ?
        # Pour simplifier et être sûr, on laisse la logique "si jamais" dans clean_empty_columns
        # mais ici on l'appelle systématiquement au début pour purger avant les stats.
        current_df, n_dropped = clean_empty_columns(current_df)
        if n_dropped > 0:
            stats['empty_cols_dropped'] += n_dropped
            any_change = True

        # 4. Doublons (Avant IQR/Median pour ne pas fausser les bornes)
        current_df, n_dups = clean_duplicates(current_df)
        if n_dups > 0:
            stats['duplicates_removed'] += n_dups
            any_change = True

        # 5. Missing Values (Remplissage)
        current_df, fillings = clean_missing_values(current_df)
        if fillings:
            stats['missing_filled'].update(fillings)
            any_change = True

        # Si rien n'a changé, on arrête (convergence)
        if not any_change:
            break
    
    # 6. Outliers IQR (En dernier, sur données numérées et propres) 
    current_df, outliers = clip_outliers(current_df)
    if outliers:
        for col, count in outliers.items():
            stats['outliers_corrected'][col] = stats['outliers_corrected'].get(col, 0) + count
        any_change = True

    return current_df, stats