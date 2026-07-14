import pandas as pd
import numpy as np
from typing import Tuple, List

def clean_empty_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Supprime les colonnes avec >95% de valeurs manquantes."""
    if df.empty:
        return df, 0
    cols_to_drop = [col for col in df.columns if df[col].isnull().sum() / len(df) >= 0.95]
    n_dropped = len(cols_to_drop)
    df_cleaned = df.drop(columns=cols_to_drop)
    return df_cleaned, n_dropped

def clean_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Nettoie les espaces superflus dans les colonnes de type string."""
    if df.empty:
        return df, 0
    
    n_modified = 0
    df_cleaned = df.copy()
    
    # Utilisation de 'string' pour éviter les warnings pandas 3.x
    cols_to_process = df_cleaned.select_dtypes(include=['object', 'string']).columns

    for col in cols_to_process:
        original_values = df_cleaned[col].copy()
        
        cleaned_values = df_cleaned[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
        
        # On compare les valeurs nettoyées aux originales (en ignorant la casse des types)
        changed_mask = (original_values != cleaned_values) | (original_values.isna() != cleaned_values.isna())
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
        # On passe d'abord tout ce qui est object en string pour uniformiser le traitement
        if df_cleaned[col].dtype == 'object':
            df_cleaned[col] = df_cleaned[col].astype('string')
        
        if df_cleaned[col].dtype.kind not in ['O', 'U']: # Si ce n'est pas une chaîne (Object/Unicode)
            continue

        # --- Tentative Numeric ---
        # errors='coerce' transforme ce qui n'est pas un nombre en NaN
        numeric_data = pd.to_numeric(df_cleaned[col], errors='coerce')
        valid_numeric_rate = numeric_data.notna().sum() / len(numeric_data)
        
        if valid_numeric_rate > 0.9: 
            non_na_values = numeric_data.dropna()
            
            # Vérification plus robuste pour les entiers
            is_likely_int = (len(non_na_values) > 0) and (non_na_values == non_na_values.astype(int)).all()
            
            if is_likely_int:
                # On utilise 'Int64' (nullable integer de pandas) au lieu de 'int64' standard
                df_cleaned[col] = numeric_data.astype('Int64')
                conversions[col] = 'object -> int'
            else:
                # On utilise 'Float64' (nullable float de pandas)
                df_cleaned[col] = numeric_data.astype('Float64')
                conversions[col] = 'object -> float'

        # --- Tentative Date ---
        if col not in conversions:
             date_data = pd.to_datetime(df_cleaned[col], errors='coerce')
             valid_date_rate = date_data.notna().sum() / len(date_data)
             
             if valid_date_rate > 0.8:
                 df_cleaned[col] = date_data
                 conversions[col] = 'object -> datetime'

    return df_cleaned, conversions

def clean_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Supprime les doublons exacts."""
    if df.empty:
        return df, 0
    
    df_cleaned = df.copy() # Sûr pour éviter les SettingWithCopyWarning
    n_before = len(df_cleaned)
    
    # keep='first' est la valeur par défaut : on garde la première occurrence
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
        null_count = df_cleaned[col].isnull().sum()
        if null_count > 0:
            # Si c'est une colonne de nombres (int ou float)
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                median_val = df_cleaned[col].median()
                df_cleaned[col] = df_cleaned[col].fillna(median_val)
                actions[col] = f"fill_median_{median_val}"
            
            # Si c'est une colonne de type objet/string
            else:
                mode_val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Inconnu'
                # On force le type string pour éviter les erreurs lors du fillna
                df_cleaned[col] = df_cleaned[col].astype('string').fillna(str(mode_val))
                actions[col] = f"fill_mode_{str(mode_val)}"

    return df_cleaned, actions

def clean_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Corrige les valeurs aberrantes avec la méthode IQR."""
    if df.empty:
        return df.copy(), {}
    
    corrections = {}
    # On sélectionne les colonnes qui sont numériques
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        # On ne traite pas si la colonne est vide ou n'a qu'une seule valeur unique
        non_null_data = df[col].dropna()
        if non_null_data.empty or len(non_null_data.unique()) <= 1:
            continue

        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        if IQR == 0:
            continue

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        n_outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()

        if n_outliers > 0:
            # CORRECTION MAJEURE : On convertit la colonne en Float64 avant de l'assigner
            # car les bornes IQR sont des nombres à virgule.
            df_cleaned_col = df[col].astype('Float64')
            
            # On applique la borne inférieure
            mask_lower = df_cleaned_col < lower_bound
            df_cleaned_col.loc[mask_lower] = lower_bound
            
            # On applique la borne supérieure
            mask_upper = df_cleaned_col > upper_bound
            df_cleaned_col.loc[mask_upper] = upper_bound
            
            # On met à jour le DataFrame principal (si on voulait travailler en copy, on ferait df[col] = df_cleaned_col)
            df[col] = df_cleaned_col 
            corrections[col] = int(n_outliers)

    return df, corrections

def run_all_cleaning_steps(df: pd.DataFrame, max_iterations: int = 5) -> Tuple[pd.DataFrame, dict]:
    """
    Applique les nettoyages de manière itérative et ordonnée.
    
    Garde-fous :
    - Max iterations pour éviter les boucles infinies.
    - Cumul des stats (on ne remplace pas le dict par dessus).
    - Ordre stratégique : Types d'abord, puis stats/doublons.
    """
    # Initialisation des accumulateurs
    stats = {
        'empty_cols_dropped': 0,
        'whitespace_cleaned': 0,
        'types_converted': {},
        'duplicates_removed': 0,
        'missing_filled': {},
        'outliers_corrected': {}
    }

    current_df = df.copy()
    
    # On boucle tant que des changements sont détectés
    for i in range(max_iterations):
        any_change = False

        # 1. Nettoyage structurel (toujours en premier)
        if 'empty_cols_dropped' not in stats or stats['empty_cols_dropped'] == 0:
            current_df, n_dropped = clean_empty_columns(current_df)
            if n_dropped > 0:
                stats['empty_cols_dropped'] += n_dropped
                any_change = True

        # 2. Nettoyage forme (espaces)
        current_df, n_spaces = clean_whitespace(current_df)
        if n_spaces > 0:
            stats['whitespace_cleaned'] += n_spaces
            any_change = True

        # 3. Conversion de types (CRITIQUE : à faire AVANT les calculs numériques)
        current_df, conversions = clean_types(current_df)
        if conversions:
            # On fusionne avec les dict existants
            stats['types_converted'].update(conversions)
            any_change = True

        # 4. Doublons (à faire avant IQR/Median pour ne pas fausser les stats)
        current_df, n_dups = clean_duplicates(current_df)
        if n_dups > 0:
            stats['duplicates_removed'] += n_dups
            any_change = True

        # 5. Missing Values (nécessite des types corrects)
        current_df, fillings = clean_missing_values(current_df)
        if fillings:
            stats['missing_filled'].update(fillings)
            any_change = True

        # 6. Outliers (nécessite des types numériques et pas de doublons) 
        current_df, outliers = clean_outliers(current_df)
        if outliers:
            for col, count in outliers.items():
                stats['outliers_corrected'][col] = stats['outliers_corrected'].get(col, 0) + count
            any_change = True

        # Si rien n'a changé lors de ce tour complet, on arrête (convergence)
        if not any_change:
            break

    return current_df, stats