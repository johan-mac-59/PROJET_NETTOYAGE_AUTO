import pandas as pd
import os    
import json

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
        elif ext == '.json':
            return _load_json(file_path)
        elif ext == '.jsonl':
            return _load_jsonl(file_path)
        else:
            # Tentative de détection automatique du format
            return _detect_and_load_format(file_path)
            
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        raise


def _load_json(file_path: str) -> pd.DataFrame:
    """Charge un fichier JSON standard."""
    # Vérification de base que le fichier n'est pas vide
    if os.path.getsize(file_path) == 0:
        print(f"   -> ⚠️ Fichier JSON vide détecté")
        return pd.DataFrame()
    
    try:
        # Utilisation directe de pandas pour charger le JSON
        df = pd.read_json(file_path)
        print(f"   -> Format JSON détecté et chargé avec succès.")
        return df
    except Exception as e:
        # Si pandas échoue, on essaie une approche manuelle plus robuste
        print(f"   -> Échec du chargement avec pandas, tentative de lecture manuelle : {e}")
        return _load_json_manual(file_path)


def _load_jsonl(file_path: str) -> pd.DataFrame:
    """Charge un fichier JSON Lines (chaque ligne est un objet JSON valide)."""
    # Vérification de base que le fichier n'est pas vide
    if os.path.getsize(file_path) == 0:
        print(f"   -> ⚠️ Fichier JSONL vide détecté")
        return pd.DataFrame()
    
    try:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():  # Ignorer les lignes vides
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"   -> Erreur de décodage JSON à la ligne {line_num}: {e}")
                        continue  # On ignore les lignes invalides
        
        if not records:
            print(f"   -> Aucun enregistrement valide trouvé dans le fichier JSONL")
            return pd.DataFrame()
            
        df = pd.DataFrame(records)
        print(f"   -> Format JSONL détecté et chargé avec succès ({len(records)} enregistrements).")
        return df
        
    except Exception as e:
        print(f"   -> Erreur lors du chargement du fichier JSONL : {e}")
        raise ValueError(f"Impossible de charger le fichier JSONL : {e}")


def _load_json_manual(file_path: str) -> pd.DataFrame:
    """Charge un fichier JSON manuellement en cas d'échec de pd.read_json."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validation complète du JSON avant traitement
        data = json.loads(content)
        
        # Si c'est une liste de dictionnaires, on peut directement créer le DataFrame
        if isinstance(data, list) and len(data) > 0:
            # Vérifier si tous les éléments sont des dictionnaires
            if all(isinstance(item, dict) for item in data):
                return pd.DataFrame(data)
            else:
                # Si ce n'est pas une liste de dicts, on traite différemment
                return pd.DataFrame([data] if not isinstance(data, list) else data)
        
        # Si c'est un seul dictionnaire, on le transforme en DataFrame avec une ligne
        elif isinstance(data, dict):
            # Pour les structures complexes, on essaie de trouver les données tabulaires
            # On cherche les clés qui contiennent des listes (typiquement des colonnes)
            df_data = []
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Si c'est une liste de valeurs simples, on peut l'utiliser
                    if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                        df_data.append({key: value})
            
            if df_data:
                # Fusionner les listes en un seul DataFrame
                return pd.DataFrame({k: v for d in df_data for k, v in d.items()})
            else:
                # Sinon, on crée une ligne avec toutes les clés
                return pd.DataFrame([data])
        else:
            print(f"   -> Format JSON non reconnu : {type(data)}")
            return pd.DataFrame()
            
    except json.JSONDecodeError as e:
        print(f"   -> Erreur de décodage JSON : {e}")
        raise ValueError(f"Format JSON invalide : {e}")
    except Exception as e:
        print(f"   -> Erreur lors du chargement manuel JSON : {e}")
        raise ValueError(f"Impossible de charger le fichier JSON : {e}")


def _detect_and_load_format(file_path: str) -> pd.DataFrame:
    """Tente de détecter automatiquement le format si l'extension n'est pas supportée."""
    # Lecture d'un échantillon pour déterminer le format
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)  # Lire un peu plus que nécessaire pour détecter JSON
    except UnicodeDecodeError:
        # Si on ne peut pas lire en UTF-8, essayer d'autres encodages
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                sample = f.read(1024)
        except Exception:
            raise ValueError("Impossible de déterminer le format du fichier")
    
    # Vérification si c'est probablement du JSON (contient des accolades ou crochets)
    sample_stripped = sample.strip()
    
    # Test plus robuste : vérifier si c'est un JSON valide
    if sample_stripped.startswith('{') or sample_stripped.startswith('['):
        try:
            json.loads(sample_stripped)
            print(f"   -> Format JSON détecté automatiquement.")
            return _load_json(file_path)
        except json.JSONDecodeError:
            # Si ce n'est pas un JSON valide, on laisse le traitement échouer
            pass
    
    raise ValueError(f"Format de fichier non supporté : {os.path.splitext(file_path)[1]}")


def _load_csv(file_path: str) -> pd.DataFrame:
    """Charge un CSV en détectant automatiquement l'encodage et le séparateur."""

    # --- Gestion du fichier vide ---
    if os.path.getsize(file_path) == 0:
        print(f"   -> ⚠️ Fichier vide détecté")
        return pd.DataFrame() # On retourne un DataFrame vide sans lever d'erreur

    # 1. Détection de l'encodage
    encoding = _detect_encoding(file_path)
    
    # 2. Lecture d'un échantillon pour détecter le séparateur
    with open(file_path, 'r', encoding=encoding) as f:
        sample_text = f.read(4096)
    
    delimiter = _detect_delimiter(sample_text)
    print(f"   -> Séparateur : '{delimiter}' | Encodage : {encoding}")

    # 3. Chargement complet du DataFrame (avec gestion spécifique de EmptyDataError si besoin)
    try:
        return pd.read_csv(file_path, sep=delimiter, encoding=encoding)
    except pd.errors.EmptyDataError:
        # Au cas où le fichier n'est pas strictement vide mais sans colonnes valables
        return pd.DataFrame()


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