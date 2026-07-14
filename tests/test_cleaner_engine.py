import pytest
import pandas as pd
import numpy as np
from src.cleaner_engine import (
    clean_empty_columns,
    clean_whitespace,
    clean_types,
    clean_duplicates,
    clean_missing_values,
    clean_outliers,
    run_all_cleaning_steps
)


# ==========================================
# FIXTURES : Données de test simulées
# ==========================================

@pytest.fixture
def perfect_df():
    """Cas nominal : DataFrame propre et complet."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'nom': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35]
    })

@pytest.fixture
def dirty_df():
    """Cas complexe : DataFrame avec trous (NaN), espaces et doublons."""
    data = {
        'id': [1, 2, 2, 4],          # Contient un doublon (2)
        'nom': [' Alice ', 'Bob', 'Alice', 'David'], # Espaces superflus & doublon logique
        'age': [25, np.nan, 35, -999], # NaN et outlier (-999)
        'email': ['a@b.com', None, np.nan, np.nan]   # Plusieurs NaN
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_col_df():
    """Cas limite : DataFrame avec une colonne vide à 100%."""
    return pd.DataFrame({
        'col_pleine': [1, 2],
        'col_vide': [np.nan, np.nan]
    })


# ==========================================
# TESTS NOMINAUX (Cas simples)
# ==========================================

class TestCleanEmptyColumns:
    def test_nominal(self, perfect_df):
        """Aucune colonne à supprimer car aucune n'est pleine de NaN."""
        df_cleaned, count = clean_empty_columns(perfect_df)
        assert len(df_cleaned.columns) == 3 # Les 3 colonnes sont gardées
        assert count == 0

    def test_suppression_colonne_vide(self, empty_col_df):
        """La colonne pleine de NaN doit être supprimée."""
        df_cleaned, count = clean_empty_columns(empty_col_df)
        assert 'col_vide' not in df_cleaned.columns
        assert count == 1


class TestCleanWhitespace:
    def test_nominal(self, perfect_df):
        """Les noms ne contiennent pas d'espaces superflus au départ (sauf si on en ajoute)."""
        # Ici, les données sont propres, le nombre de modifications doit être 0.
        df_cleaned, count = clean_whitespace(perfect_df)
        assert count == 0

    def test_nettoyage_espaces(self, dirty_df):
        """On vérifie que ' Alice ' devient 'Alice'."""
        df_cleaned, _ = clean_whitespace(dirty_df)
        assert df_cleaned.loc[0, 'nom'] == 'Alice', "L'espace avant Alice n'a pas été retiré"


class TestCleanDuplicates:
    def test_doublons_exact(self, dirty_df):
        """La ligne avec id=2 en double doit être retirée (1 doublon exact)."""
        df_cleaned, count = clean_duplicates(dirty_df)
        assert len(df_cleaned) == 3 # 4 lignes initiales - 1 doublon
        assert count == 1

    def test_pas_de_doublons(self, perfect_df):
        """Aucun doublon dans un jeu de données parfait."""
        df_cleaned, count = clean_duplicates(perfect_df)
        assert count == 0


class TestCleanOutliers:
    def test_correction_iqr(self, dirty_df):
        """L'âge '-999' (valeur aberrante) doit être remplacé par la borne inférieure IQR."""
        df_cleaned, corrections = clean_outliers(dirty_df)
        
        # -999 ne devrait plus exister dans 'age' (sauf si c'est une vraie borne mathématique très basse)
        assert -999 not in df_cleaned['age'].values
    
    def test_pas_d_outlier(self, perfect_df):
        """Aucun outlier dans un jeu de données parfait."""
        df_cleaned, corrections = clean_outliers(perfect_df)
        assert len(corrections) == 0


# ==========================================
# TESTS LIMITES (Edge Cases & Intégration)
# ==========================================

class TestCleanTypes:
    def test_conversion_object_vers_numeric(self):
        """Test le passage de string '123' vers int/float."""
        df_test = pd.DataFrame({'val': ['10', '20', '30']})
        df_cleaned, types_conv = clean_types(df_test)
        
        # Vérifie que les valeurs sont bien des nombres et non plus des strings
        assert df_cleaned['val'].dtype in [np.float64, np.int64]

    def test_conversion_dates(self):
        """Test la détection de dates."""
        df_test = pd.DataFrame({'date': ['01/01/2023', '02/01/2023']})
        df_cleaned, types_conv = clean_types(df_test)
        
        # On vérifie le type object -> datetime (souvent <M8[ns] avec pandas)
        assert 'datetime' in str(types_conv.get('date', ''))


class TestCleanMissingValues:
    def test_fill_median(self, dirty_df):
        """Les NaN de la colonne age (float/int) doivent être comblés par la médiane."""
        df_cleaned, actions = clean_missing_values(dirty_df)
        
        # Il ne doit plus y avoir de valeurs None ou np.nan dans 'age'
        assert df_cleaned['age'].isnull().sum() == 0
        
    def test_fill_mode(self, dirty_df):
        """Les NaN de la colonne email doivent être comblés par le mode (valeur fréquente)."""
        df_cleaned, actions = clean_missing_values(dirty_df)
        
        # L'email doit être rempli (on ne sait pas laquelle par défaut mais il ne doit pas être nul)
        assert df_cleaned['email'].isnull().sum() == 0


class TestPipelineEndToEnd:
    def test_pipeline_complet(self, dirty_df):
        """Test du workflow complet : on s'assure que rien ne plante."""
        final_df, stats = run_all_cleaning_steps(dirty_df)
        
        # Vérifications finales sur le résultat global
        assert not final_df.empty 
        assert 'id' in final_df.columns
        
    def test_pipeline_vide(self):
        """Test sur un DataFrame vide (cas limite)."""
        df_empty = pd.DataFrame()
        # On s'assure que ça ne plante pas (ou renvoie un truc gérable)
        final_df, stats = run_all_cleaning_steps(df_empty)
        assert final_df.empty