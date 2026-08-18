# tests/test_file_loader.py
import os
import pandas as pd
import pytest
from unittest.mock import patch, mock_open
import json

# Importation du module à tester
from src.file_loader import load_file, _load_csv, _load_excel, _load_json, _load_jsonl, _load_json_manual, _detect_and_load_format, _detect_encoding, _detect_delimiter


class TestFileLoader:
    """Tests unitaires pour le module file_loader.py"""
    
    def test_load_file_csv_nominal(self, tmp_path):
        """Test de chargement d'un fichier CSV nominal"""
        # Création d'un fichier CSV de test
        csv_content = "col1,col2,col3\n1,2,3\n4,5,6"
        file_path = tmp_path / "test.csv"
        file_path.write_text(csv_content)
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2', 'col3']
    
    def test_load_file_xlsx_nominal(self, tmp_path):
        """Test de chargement d'un fichier Excel nominal"""
        # Création d'un fichier Excel de test
        df_test = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        file_path = tmp_path / "test.xlsx"
        
        # Sauvegarde du DataFrame en Excel
        with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
            df_test.to_excel(writer, index=False)
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['A', 'B']
    
    def test_load_file_json_nominal(self, tmp_path):
        """Test de chargement d'un fichier JSON nominal"""
        json_content = '{"col1": [1, 2], "col2": [3, 4]}'
        file_path = tmp_path / "test.json"
        file_path.write_text(json_content)
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_file_jsonl_nominal(self, tmp_path):
        """Test de chargement d'un fichier JSONL nominal"""
        jsonl_content = '{"col1": 1, "col2": 2}\n{"col1": 3, "col2": 4}'
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(jsonl_content)
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_file_not_found(self):
        """Test de gestion d'erreur pour fichier introuvable"""
        with pytest.raises(FileNotFoundError):
            load_file("fichier_inexistant.csv")
    
    def test_load_file_empty_csv(self, tmp_path):
        """Test de chargement d'un fichier CSV vide"""
        file_path = tmp_path / "empty.csv"
        file_path.write_text("")
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_file_empty_json(self, tmp_path):
        """Test de chargement d'un fichier JSON vide"""
        file_path = tmp_path / "empty.json"
        file_path.write_text("")
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_file_empty_jsonl(self, tmp_path):
        """Test de chargement d'un fichier JSONL vide"""
        file_path = tmp_path / "empty.jsonl"
        file_path.write_text("")
        
        # Chargement du fichier
        df = load_file(str(file_path))
        
        # Vérification des résultats
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_file_corrupted_json(self, tmp_path):
        """Test de gestion d'erreur pour JSON corrompu"""
        json_content = '{"col1": [1, 2], "col2": [3, 4}'
        file_path = tmp_path / "corrupted.json"
        file_path.write_text(json_content)
        
        # Le fichier devrait être chargé manuellement et échouer
        with pytest.raises(ValueError):
            load_file(str(file_path))
    
    def test_load_file_invalid_jsonl(self, tmp_path):
        """Test de gestion d'erreur pour JSONL invalide"""
        jsonl_content = '{"col1": 1, "col2": 2}\n{"col1": 3, "col2":}'
        file_path = tmp_path / "invalid.jsonl"
        file_path.write_text(jsonl_content)
        
        # Chargement du fichier - devrait ignorer la ligne invalide
        df = load_file(str(file_path))
        
        # Vérification que le fichier est chargé malgré une ligne invalide
        assert isinstance(df, pd.DataFrame)
    
    def test_load_csv_with_different_delimiters(self, tmp_path):
        """Test de détection automatique du séparateur CSV"""
        # Test avec point-virgule
        csv_content = "col1;col2;col3\n1;2;3\n4;5;6"
        file_path = tmp_path / "test_semicolon.csv"
        file_path.write_text(csv_content)
        
        df = _load_csv(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2', 'col3']
    
    def test_load_csv_empty_file(self, tmp_path):
        """Test de chargement d'un fichier CSV vide"""
        file_path = tmp_path / "empty.csv"
        file_path.write_text("")
        
        df = _load_csv(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_excel_empty_file(self, tmp_path):
        """Test de chargement d'un fichier Excel vide"""
        df_test = pd.DataFrame()
        file_path = tmp_path / "empty.xlsx"
        
        # Sauvegarde du DataFrame vide en Excel
        with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
            df_test.to_excel(writer, index=False)
        
        df = _load_excel(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
    
    def test_load_json_empty_file(self, tmp_path):
        """Test de chargement d'un fichier JSON vide"""
        file_path = tmp_path / "empty.json"
        file_path.write_text("")
        
        df = _load_json(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_jsonl_empty_file(self, tmp_path):
        """Test de chargement d'un fichier JSONL vide"""
        file_path = tmp_path / "empty.jsonl"
        file_path.write_text("")
        
        df = _load_jsonl(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_json_manual_list_of_dicts(self, tmp_path):
        """Test de chargement JSON manuel avec liste de dictionnaires"""
        json_content = '[{"col1": 1, "col2": 2}, {"col1": 3, "col2": 4}]'
        file_path = tmp_path / "manual.json"
        file_path.write_text(json_content)
        
        df = _load_json_manual(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_json_manual_single_dict(self, tmp_path):
        """Test de chargement JSON manuel avec dictionnaire simple"""
        json_content = '{"col1": [1, 2], "col2": [3, 4]}'
        file_path = tmp_path / "manual.json"
        file_path.write_text(json_content)
        
        df = _load_json_manual(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_detect_encoding_utf8(self, tmp_path):
        """Test de détection d'encodage UTF-8"""
        content = "col1,col2\n1,2"
        file_path = tmp_path / "test.csv"
        file_path.write_text(content, encoding='utf-8')
        
        encoding = _detect_encoding(str(file_path))
        
        assert encoding == 'utf-8'
    
    def test_detect_delimiter_semicolon(self, tmp_path):
        """Test de détection du séparateur point-virgule"""
        content = "col1;col2;col3\n1;2;3\n4;5;6"
        
        delimiter = _detect_delimiter(content)
        
        assert delimiter == ';'
    
    def test_detect_delimiter_tab(self, tmp_path):
        """Test de détection du séparateur tabulation"""
        content = "col1\tcol2\tcol3\n1\t2\t3\n4\t5\t6"
        
        delimiter = _detect_delimiter(content)
        
        assert delimiter == '\t'
    
    def test_detect_delimiter_comma(self, tmp_path):
        """Test de détection du séparateur virgule (fallback)"""
        content = "col1,col2,col3\n1,2,3\n4,5,6"
        
        delimiter = _detect_delimiter(content)
        
        assert delimiter == ','
    
    def test_detect_and_load_format_json(self, tmp_path):
        """Test de détection automatique et chargement de format JSON"""
        json_content = '{"col1": [1, 2], "col2": [3, 4]}'
        file_path = tmp_path / "test.unknown"
        file_path.write_text(json_content)
        
        # Mocker os.path.getsize pour simuler un fichier non vide
        with patch('os.path.getsize', return_value=100):
            with patch('os.path.splitext', return_value=('', '.unknown')):
                df = _detect_and_load_format(str(file_path))
                
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 2
    
    def test_detect_and_load_format_invalid(self, tmp_path):
        """Test de détection automatique pour format invalide"""
        content = "non json content"
        file_path = tmp_path / "test.unknown"
        file_path.write_text(content)
        
        # Mocker os.path.getsize pour simuler un fichier non vide
        with patch('os.path.getsize', return_value=100):
            with pytest.raises(ValueError, match="Format de fichier non supporté"):
                _detect_and_load_format(str(file_path))
    
    def test_load_file_with_different_encodings(self, tmp_path):
        """Test de chargement avec différents encodages"""
        # Test avec Latin-1
        csv_content = "col1,col2\n1,2"
        file_path = tmp_path / "test_latin1.csv"
        file_path.write_text(csv_content, encoding='latin1')
        
        df = load_file(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_file_with_nan_values(self, tmp_path):
        """Test de chargement avec valeurs NaN"""
        csv_content = "col1,col2\n1,\n,3"
        file_path = tmp_path / "test_nan.csv"
        file_path.write_text(csv_content)
        
        df = load_file(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_file_with_missing_columns(self, tmp_path):
        """Test de chargement avec colonnes manquantes"""
        csv_content = "col1,col2\n1,2\n3"
        file_path = tmp_path / "test_missing_cols.csv"
        file_path.write_text(csv_content)
        
        df = load_file(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_file_with_special_characters(self, tmp_path):
        """Test de chargement avec caractères spéciaux"""
        csv_content = "col1,col2\ncafé,naïf\nrésumé,piñata"
        file_path = tmp_path / "test_special_chars.csv"
        file_path.write_text(csv_content, encoding='utf-8')
        
        df = load_file(str(file_path))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_file_unsupported_format_with_json_content(self, tmp_path):
        """Test de gestion d'erreur pour format non supporté avec contenu JSON valide"""
        # Création d'un fichier avec extension non supportée mais contenu JSON valide
        json_content = '{"col1": [1, 2], "col2": [3, 4]}'
        file_path = tmp_path / "test.txt"
        file_path.write_text(json_content)
        
        # Mock de os.path.exists et d'autres fonctions pour simuler un fichier valide
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=100):
                # Le fichier devrait être détecté comme JSON et chargé correctement
                df = load_file(str(file_path))
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 2
    
    def test_load_file_unsupported_format_with_invalid_content(self, tmp_path):
        """Test de gestion d'erreur pour format non supporté avec contenu invalide"""
        # Création d'un fichier avec extension non supportée et contenu non JSON
        content = "non json content"
        file_path = tmp_path / "test.txt"
        file_path.write_text(content)
        
        # Mock des fonctions pour simuler un fichier valide
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=100):
                with pytest.raises(ValueError, match="Format de fichier non supporté"):
                    load_file(str(file_path))