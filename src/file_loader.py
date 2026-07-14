import pandas as pd
import os
from typing import Union
    

def load_file(file_path: str) -> pd.DataFrame:
    """Charge un fichier dans un DataFrame selon son extension.

    Args:
        file_path: Chemin vers le fichier à charger.

    Returns:
        Un DataFrame pandas chargé depuis le fichier.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si l'extension du fichier n'est pas supportée.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} est introuvable.")

    # On prend l'extension en minuscule pour être robuste
    ext = os.path.splitext(file_path)[1].lower()

    print(f"📂 Chargement du fichier : {file_path}")
    
    try:
        if ext == '.csv':
            return _load_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            return _load_excel(file_path)
        # On peut ajouter plus tard :
        # elif ext == '.json':
        #     return pd.read_json(file_path)
        else:
            raise ValueError(f"Format de fichier non supporté : {ext}")
            
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        raise


def _load_csv(file_path: str) -> pd.DataFrame:
    """Charge un CSV en détectant automatiquement l'encodage et le séparateur."""
    # 1. Détection de l'encodage
    encoding = _detect_encoding(file_path)
    
    # 2. Lecture d'un échantillon pour détecter le séparateur
    with open(file_path, 'r', encoding=encoding) as f:
        sample_text = f.read(4096)
    
    delimiter = _detect_delimiter(sample_text)
    print(f"   -> Séparateur : '{delimiter}' | Encodage : {encoding}")

    # 3. Chargement complet du DataFrame
    return pd.read_csv(file_path, sep=delimiter, encoding=encoding)


def _load_excel(file_path: str) -> pd.DataFrame:
    """Charge un fichier Excel."""
    print(f"   -> Format Excel détecté.")
    # Par défaut on prend la première feuille
    return pd.read_excel(file_path, engine='openpyxl')


def _detect_encoding(file_path: str) -> str:
    """Détecte l'encodage en testant les plus courants."""
    encodings = ['utf-8', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(4096)
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8'


def _detect_delimiter(sample_text: str) -> str:
    """Détecte le séparateur d'un fichier CSV semi-structuré."""
    delimiters = [';', ',', '\t', '|']
    for delim in delimiters:
        lines = sample_text.strip().split('\n')[:3]
        # Si chaque ligne contient le délimiteur et a le même nombre de colonnes
        if all(delim in line for line in lines):
            parts = [line.split(delim) for line in lines]
            if len(set(len(p) for p in parts)) == 1:
                return delim
    # Fallback sur la virgule si rien ne matche parfaitement
    return ','