# src/data_profiler.py
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any

class DataProfiler:
    """Analyse descriptive d'un DataFrame avec génération de rapport Markdown."""

    def __init__(self, df: pd.DataFrame, source_file_path: str = None):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("L'objet fourni n'est pas un DataFrame pandas.")
        self.df = df.copy()
        self.source_file_path = source_file_path
        self.profile_results: Dict[str, Any] = {}

    def run_analysis(self) -> Dict[str, Any]:
        """Orchestre toutes les analyses."""
        if len(self.df) == 0:
            raise ValueError("Impossible de profiler un DataFrame vide.")

        # 1. Structure et Types
        nb_lignes, nb_colonnes = self.df.shape
        # On stocke le shape sous forme de dictionnaire pour faciliter l'affichage Markdown
        self.profile_results['shape'] = {
            'nb_lignes': nb_lignes, 
            'nb_colonnes': nb_colonnes
        }
        self.profile_results['dtypes'] = {col: str(dtype) for col, dtype in self.df.dtypes.items()}

        # 2. Qualité (NaN & Doublons)
        null_counts = self.df.isnull().sum()
        self.profile_results['missing_values'] = {
            'count': null_counts.to_dict(), 
            'percent': (null_counts / len(self.df) * 100).round(2).to_dict()
        }
        self.profile_results['nb_doublons'] = int(self.df.duplicated().sum())

        # 3. Stats Numériques
        numeric_cols = self.df.select_dtypes(include=['number'])
        if not numeric_cols.empty:
            self.profile_results['describe_numeric'] = numeric_cols.describe().to_dict()
            # Ajout de la détection des outliers
            self.profile_results['outliers'] = self._detect_outliers(numeric_cols)

        # 4. Stats Catégorielles
        categorical_cols = self.df.select_dtypes(include=['str','object', 'category'])
        if not categorical_cols.empty:
            self.profile_results['describe_categorical'] = self._analyze_categorical_columns(categorical_cols)

        # 5. Aperçu
        self.profile_results['sample_preview'] = self.df.head(10).to_markdown(index=False) if not self.df.empty else "Pas de données"
        
        return self.profile_results

    def _detect_outliers(self, numeric_df: pd.DataFrame) -> Dict[str, Any]:
        """Détecte les outliers pour chaque colonne numérique en utilisant la méthode IQR."""
        outliers_info = {}
        
        for col in numeric_df.columns:
            if col in numeric_df.columns:
                series = numeric_df[col].dropna()
                if len(series) > 0:
                    # Calcul des quartiles
                    Q1 = series.quantile(0.25)
                    Q3 = series.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    # Limites pour les outliers
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # Identification des outliers
                    outliers = series[(series < lower_bound) | (series > upper_bound)]
                    
                    if len(outliers) > 0:
                        outliers_info[col] = {
                            'count': len(outliers),
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound),
                            'outlier_values': outliers.tolist()
                        }
        
        return outliers_info

    def _analyze_categorical_columns(self, categorical_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse approfondie des colonnes catégorielles avec synthèse des anomalies."""
        categorical_stats = {}
        
        for col in categorical_df.columns:
            series = categorical_df[col]
            
            # Cardinalité
            unique_count = series.nunique()
            cardinality_absolute = unique_count
            cardinality_relative = round((unique_count / len(series) * 100), 2)
            
            # Sparsity Ratio (taux de remplissage)
            null_count = series.isnull().sum()
            sparsity_ratio = round(((len(series) - null_count) / len(series) * 100), 2)
            
            # Fréquence des catégories
            value_counts = series.value_counts()
            total_non_null = len(series) - null_count
            
            # Skewness de fréquence (pourcentage détenu par la catégorie majoritaire)
            if len(value_counts) > 0:
                max_frequency = value_counts.iloc[0]
                skewness_frequency = round((max_frequency / total_non_null * 100), 2)
                is_high_skewness = skewness_frequency > 90
            else:
                skewness_frequency = 0
                is_high_skewness = False
            
            # Qualité du format (détection d'hétérogénéité)
            # Vérification des majuscules/minuscules et espaces
            detected_anomalies = []
            has_whitespace_issue = False
            has_case_issue = False

            if len(value_counts) > 0:
                # Vérifier les valeurs avec des espaces en début/fin
                for value in value_counts.index:
                    if isinstance(value, str):
                        if value != value.strip():
                            has_whitespace_issue = True
                        if value != value.lower() and value != value.upper():
                            has_case_issue = True
            
            if has_whitespace_issue:
                detected_anomalies.append("Présence d'espaces superflus (début/fin)")
            if has_case_issue:
                detected_anomalies.append("Variations de casse (Maj/Min)")

            # Gestion du nombre de valeurs à afficher
            if len(value_counts) <= 20:
                top_categories = value_counts.to_dict()
            else:
                top_categories = value_counts.head(5).to_dict()
            
            categorical_stats[col] = {
                'cardinality_absolute': cardinality_absolute,
                'cardinality_relative': cardinality_relative,
                'sparsity_ratio': sparsity_ratio,
                'skewness_frequency': skewness_frequency,
                'is_high_skewness': is_high_skewness,
                'top_categories': top_categories,
                'format_anomalies': detected_anomalies
            }
        
        return categorical_stats

    def _generate_markdown_report(self) -> str:
        """Convertit les résultats en Markdown structuré."""
        # Préambule avec métadonnées de source
        md = [f"# 📊 Rapport d'Inspection des Données\n", "---\n"]
        
        # Ajout des métadonnées de source
        md.append("## 📂 Métadonnées & Contexte Source\n")
        if self.source_file_path:
            source_filename = Path(self.source_file_path).name
            md.append(f"- **Nom du fichier source** : {source_filename}")
            md.append(f"- **Chemin d'accès complet** : {self.source_file_path}")
        md.append(f"- **Date et heure de génération** : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        shape = self.profile_results['shape']
        # Vue d'ensemble
        md.append("## 🧱 Structure\n")
        for k, v in {**shape, **{'nb_doublons': self.profile_results.get('nb_doublons', 0)}}.items():
            md.append(f"- **{k}**: {v}")
        
        # Types (tableau simple)
        md.append("\n## 🏷️ Colonnes et Types\n")

        # On récupère les clés pour faire l'en-tête dynamiquement
        columns = list(self.profile_results['dtypes'].keys())
        if columns:
            # Création dynamique de l'en-tête (pour 2 colonnes fixées)
            header = f"| {'Colonne':<15} | {'Type':<10} |"
            separator = "| " + "-"*13 + " | " + "-"*8 + " |"
            
            md.append(header)
            md.append(separator)

        for col, dtype in self.profile_results['dtypes'].items():
            md.append(f"| {col} | {dtype} |")

        # Missing Values (seulement si > 0)
        md.append("\n## ⚠️ Valeurs Manquantes\n")
        for col, pct in self.profile_results['missing_values']['percent'].items():
            if pct > 0:
                count = self.profile_results['missing_values']['count'][col]
                md.append(f"- **{col}**: {pct:.2f}% ({count} lignes)")

        # Stats Numériques (si présentes)
        if 'describe_numeric' in self.profile_results:
            desc_df = pd.DataFrame(self.profile_results['describe_numeric'])
            md.append("\n## 📈 Statistiques Numériques\n")
            md.append(desc_df.round(2).to_markdown())

        # Outliers (si présents)
        if 'outliers' in self.profile_results and self.profile_results['outliers']:
            md.append("\n## 🚩 Valeurs Aberrantes (Outliers)\n")
            md.append("| Colonne | Nombre d'outliers | Limite inférieure | Limite supérieure |")
            md.append("|---------|-------------------|-------------------|-------------------|")
            for col, info in self.profile_results['outliers'].items():
                md.append(f"| {col} | {info['count']} | {info['lower_bound']:.2f} | {info['upper_bound']:.2f} |")

        # Stats Catégorielles (si présentes)
        if 'describe_categorical' in self.profile_results:
            md.append("\n## 📊 Analyse des Colonnes Catégorielles\n")
            
            for col, stats in self.profile_results['describe_categorical'].items():
                md.append(f"\n### {col}\n")
                
                # Informations de base
                md.append(f"- **Cardinalité absolue** : {stats['cardinality_absolute']}")
                md.append(f"- **Cardinalité relative** : {stats['cardinality_relative']}%")
                md.append(f"- **Sparsity Ratio | Taux de remplissage** : {stats['sparsity_ratio']}%")
                
                # Skewness de fréquence
                if stats['is_high_skewness']:
                    md.append(f"- ⚠️ **Skewness Frequency | Asymétrie de distribution** : {stats['skewness_frequency']}% (⚠️ Faible variance)")
                else:
                    # Ne pas afficher une faible variance si la colonne est très riche
                    if stats['cardinality_absolute'] > 10:  # Si plus de 10 catégories, c'est un cas normal
                        md.append(f"- **Skewness Frequency | Asymétrie de distribution** : {stats['skewness_frequency']}%")
                    else:
                        # Pour les colonnes avec peu de valeurs, on n'affiche pas la valeur faible
                        md.append(f"- **Skewness Frequency | Asymétrie de distribution** : {stats['skewness_frequency']}% (⚠️ Peu de catégories)")

                # Catégories les plus fréquentes
                md.append("\n- **Catégories les plus fréquentes** :")
                for category, count in stats['top_categories'].items():
                    percentage = (count / (len(self.df) - self.df[col].isnull().sum()) * 100).round(2)
                    md.append(f"  - {category} ({percentage}%)")
                
                # Qualité du format
                if stats['format_anomalies']:
                    md.append("\n- **⚠️ Anomalies de format détectées** :")
                    for issue in stats['format_anomalies']:
                        md.append(f"  - {issue}")
                else:
                    md.append("\n- **✅ Format conforme**")

        # Aperçu final
        md.append("\n## 👀 Aperçu\n")
        md.append(self.profile_results['sample_preview'])

        return "\n".join(md)

    def generate_report(self, output_filename: str = "data/processed/data_profiling_report.md") -> str:
        """Sauvegarde le rapport Markdown."""
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        if not self.profile_results:
            self.run_analysis()
            
        report_content = self._generate_markdown_report()
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"📄 Rapport sauvegardé : {output_filename}")
        return output_filename

    # --- Future méthode d'alertes ---
    def detect_quality_issues(self) -> Dict[str, str]:
        """Préparation pour les futures préconisations de nettoyage."""
        issues = {}
        for col, dtype in self.profile_results.get('dtypes', {}).items():
            if 'float' in dtype and col in self.df.columns:
                # Exemple : si une colonne float a beaucoup de NaN, c'est un problème potentiel
                pass 
        return issues