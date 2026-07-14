import pytest
import pandas as pd
import os
from pathlib import Path
import tempfile
# On importe les fonctions que l'on souhaite tester depuis ton module
from src.file_loader import load_file, _detect_encoding, _detect_delimiter


# ==========================================
# FIXTURES : Fichiers temporaires simulés
# ==========================================

@pytest.fixture
def temp_dir(tmp_path):
    """Crée un dossier temporaire pour les tests."""
    return tmp_path

@pytest.fixture
def valid_csv(temp_dir):
    """Génère un fichier CSV valide (séparateur ;)"""
    file = temp_dir / "valid_data.csv"
    content = "nom;age\nAlice;25\nBob;30\nCharlie;35"
    file.write_text(content, encoding='utf-8')
    return file

@pytest.fixture
def comma_csv(temp_dir):
    """Génère un fichier CSV valide (séparateur ,)"""
    file = temp_dir / "comma_data.csv"
    content = "nom;age\nAlice;25\nBob;30" # On garde le contenu, la fixture change juste le nom pour simuler un autre type
    # Pour ce test précis, on s'assure que le séparateur est détecté
    file.write_text("nom,age\nAlice,25\nBob,30", encoding='utf-8')
    return file

@pytest.fixture
def empty_csv(temp_dir):
    """Génère un fichier CSV vide."""
    file = temp_dir / "empty_data.csv"
    file.write_text("", encoding='utf-8')
    return file

# ==========================================
# TESTS NOMINAUX (Cas simples)
# ==========================================

class TestLoadFile:
    def test_chargement_csv_nominal(self, valid_csv):
        """Test nominal : le fichier existe et est un CSV valide."""
        df = load_file(str(valid_csv))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3 # 3 lignes de données
        assert list(df.columns) == ['nom', 'age']

    def test_chargement_excel(self, temp_dir):
        """Test nominal : charge un fichier Excel (si on en ajoute un plus tard)."""
        # Note: Pour l'instant on ne teste que le CSV. 
        # Quand tu auras implémenté Excel, on testera ici.
        pass 

    def test_detection_separateur_virgule(self, comma_csv):
        """Vérifie que le loader détecte bien la virgule comme séparateur."""
        # On ne peut pas tester _detect_delimiter directement sans l'ouvrir 
        # mais load_file s'en charge. Vérifions que les colonnes sont bien splitées.
        df = load_file(str(comma_csv))
        assert list(df.columns) == ['nom', 'age']

# ==========================================
# TESTS LIMITES (Edge Cases & Erreurs)
# ==========================================

class TestLoadFileErrors:
    def test_fichier_inexistant(self, temp_dir):
        """Cas limite : Le fichier n'existe pas -> doit lever FileNotFoundError."""
        fake_path = str(temp_dir / "cest_pas_la.csv")
        
        with pytest.raises(FileNotFoundError, match="introuvable"):
            load_file(fake_path)

    def test_format_non_soutenu(self, temp_dir):
        """Cas limite : Extension non supportée -> doit lever ValueError."""
        file = temp_dir / "data.txt"
        file.write_text("Je ne suis pas un CSV")
        
        with pytest.raises(ValueError, match="Format de fichier non supporté"):
            load_file(str(file))

    def test_fichier_vide(self, empty_csv):
        """Cas limite : Fichier CSV vide."""
        # Cela peut parfois renvoyer un DataFrame vide (0 colonnes) sans erreur
        df = load_file(str(empty_csv))
        assert len(df) == 0


class TestHelpers:
    def test_detect_encoding_utf8(self, valid_csv):
        """Vérifie que l'encodage est bien détecté."""
        enc = _detect_encoding(str(valid_csv))
        # On s'attend à 'utf-8' par défaut pour nos fichiers récents
        assert enc in ['utf-8', 'latin1']

    def test_detect_delimiter_semicolon(self):
        """Vérifie la fonction interne de détection du séparateur."""
        text = "col1;col2\nval1;val2"
        delimiter = _detect_delimiter(text)
        assert delimiter == ';'

    def test_detect_delimiter_tab(self):
        """Vérifie la détection du séparateur Tabulation."""
        text = "col1\tcol2\nval1\tval2"
        delimiter = _detect_delimiter(text)
        assert delimiter == '\t'

    def test_detect_delimiter_default(self):
        """Si le texte est bizarre, ça devrait tomber sur la virgule par défaut."""
        text = "lignes sans délimiteur obvious\njuste du texte"
        delimiter = _detect_delimiter(text)
        assert delimiter == ','