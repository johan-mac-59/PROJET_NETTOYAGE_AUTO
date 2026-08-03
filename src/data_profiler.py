# src/data_profiler.py
import os
import pandas as pd
from typing import Dict, Any

class DataProfiler:
    """Analyse descriptive d'un DataFrame avec génération de rapport Markdown."""

    def __init__(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("L'objet fourni n'est pas un DataFrame pandas.")
        self.df = df.copy()
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
        self.profile_results['duplicates_count'] = int(self.df.duplicated().sum())

        # 3. Stats Numériques
        numeric_cols = self.df.select_dtypes(include=['number'])
        if not numeric_cols.empty:
            self.profile_results['describe_numeric'] = numeric_cols.describe().to_dict()

        # 4. Top Catégorielles (pour ne pas afficher 1000 lignes de texte)
        categorical_cols = self.df.select_dtypes(include=['str','object', 'category'])
        if not categorical_cols.empty:
            self.profile_results['describe_categorical'] = {
                col: self.df[col].value_counts().head(3).to_dict() for col in categorical_cols.columns
            }

        # 5. Aperçu
        self.profile_results['sample_preview'] = self.df.head().to_markdown(index=False) if not self.df.empty else "Pas de données"
        
        return self.profile_results

    def _generate_markdown_report(self) -> str:
        """Convertit les résultats en Markdown structuré."""
        md = [f"# 📊 Rapport d'Inspection des Données ({pd.Timestamp.now().strftime('%Y-%m-%d')})\n", "---\n"]
        
        shape = self.profile_results['shape']
        # Vue d'ensemble
        md.append("## 🧱 Structure\n")
        for k, v in {**shape, **{'duplicates_count': self.profile_results.get('duplicates_count', 0)}}.items():
            md.append(f"- **{k}**: {v}")
        
        # Types (tableau simple)
        md.append("\n## 🏷️ Colonnes et Types\n")
        for col, dtype in self.profile_results['dtypes'].items():
            md.append(f"| {col} | {dtype} |")
        md.insert(-1, "| --- | --- |") 

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