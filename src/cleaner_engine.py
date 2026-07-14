import pandas as pd
import numpy as np
from typing import Tuple, List


def clean_empty_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Supprime les colonnes avec >95% de valeurs manquantes.
    Retourne le DataFrame modifié et le nombre de colonnes supprimées."""
    cols_to_drop = [col for col in df.columns if df[col].isnull().sum() / len(df) >= 0.95]
    n_dropped = len(cols_to_drop)
    df = df.drop(columns=cols_to_drop)
    return df, n_dropped


def clean_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Nettoie les espaces superflus dans les colonnes de type string.
    Retourne le DataFrame modifié et le nombre de valeurs distinctes fusionnées."""
    n_modified = 0
    for col in df.select_dtypes(include=['object']).columns:
        original_unique = df[col].nunique()
        df[col] = df[col].str.strip().str.replace(r'\s+', ' ', regex=True)
        # On compte si la structure a changé (plus d'occurrences uniques après strip/replace)
        if df[col].nunique() != original_unique:
            n_modified += 1 
    return df, n_modified


def clean_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Convertit automatiquement les types de colonnes en toute sécurité.
    
    Logique :
    1. Numeric : Si > 90% des valeurs sont valides numériquement ET que ce n'est pas un ID.
    2. Date : Si > 80% des valeurs sont convertibles en date.
    
    Returns:
        Tuple (DataFrame modifié, dict des conversions effectuées)
    """
    conversions = {}
    
    for col in df.columns:
        if df[col].dtype != 'object':
            continue

        # --- Tentative Numeric ---
        # 'coerce' transforme les erreurs en NaN, on peut donc mesurer le taux de succès
        numeric_data = pd.to_numeric(df[col], errors='coerce')
        valid_numeric_rate = numeric_data.notna().sum() / len(numeric_data)
        
        if valid_numeric_rate > 0.9: 
            # Vérification heuristic : si la plupart sont des entiers et que le max est grand, c'est probablement un ID/Phone
            int_mask = numeric_data == numeric_data.astype(int) 
            is_likely_int = valid_numeric_rate > 0.95 and int_mask.sum() / len(numeric_data) > 0.9
            
            # On évite de convertir les grands entiers en float pour éviter la perte de précision
            if is_likely_int and numeric_data.max() < 1e6: 
                df[col] = numeric_data.astype('float64') # float pour compatibilité avec NaN futurs
                conversions[col] = 'object -> float'
            elif valid_numeric_rate > 0.95:
                df[col] = numeric_data
                conversions[col] = 'object -> numeric'

        # --- Tentative Date (seulement si pas déjà converti) ---
        elif col not in conversions:
             date_data = pd.to_datetime(df[col], errors='coerce')
             valid_date_rate = date_data.notna().sum() / len(date_data)
             
             if valid_date_rate > 0.8:
                 df[col] = date_data
                 conversions[col] = 'object -> datetime'

    return df, conversions


def clean_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Supprime les doublons exacts. Retourne DataFrame et nb lignes supprimées."""
    n_before = len(df)
    df = df.drop_duplicates()
    n_removed = n_before - len(df)
    return df, n_removed


def clean_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Nettoie les valeurs manquantes de manière intelligente.
    Retourne DataFrame et un dict détaillant les actions par colonne."""
    actions = {}
    
    # On travaille sur une copie pour éviter SettingWithCopyWarning si df est un slice
    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        if df_cleaned[col].isnull().sum() > 0:
            if df_cleaned[col].dtype in ['float64', 'int64']:
                median_val = df_cleaned[col].median()
                df_cleaned[col].fillna(median_val, inplace=True)
                actions[col] = f"fill_median_{median_val}"
            elif df_cleaned[col].dtype == 'object':
                mode_val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Inconnu'
                df_cleaned[col].fillna(mode_val, inplace=True)
                actions[col] = f"fill_mode_{mode_val}"

    return df_cleaned, actions


def clean_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Corrige les valeurs aberrantes avec la méthode IQR (remplacement par la borne).
    Retourne DataFrame et un dict des colonnes modifiées avec le nb d'outliers corrigés."""
    corrections = {}
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns

    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        n_outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()

        if n_outliers > 0:
            df.loc[df[col] < lower_bound, col] = lower_bound
            df.loc[df[col] > upper_bound, col] = upper_bound
            corrections[col] = n_outliers

    return df, corrections


def run_all_cleaning_steps(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Ordonne l'application des différentes étapes de nettoyage.
    
    Args:
        df: DataFrame brut
        
    Returns:
        Tuple (DataFrame nettoyé, dict des stats intermédiaires pour le rapport)
    """
    stats = {
        'empty_cols_dropped': 0,
        'whitespace_cleaned': 0,
        'types_converted': {},
        'duplicates_removed': 0,
        'missing_filled': {},
        'outliers_corrected': {}
    }

    df, stats['empty_cols_dropped'] = clean_empty_columns(df)
    df, stats['whitespace_cleaned'] = clean_whitespace(df)
    df, stats['types_converted'] = clean_types(df) 
    df, stats['duplicates_removed'] = clean_duplicates(df) 
    df, stats['missing_filled'] = clean_missing_values(df)
    df, stats['outliers_corrected'] = clean_outliers(df)
    return df, stats