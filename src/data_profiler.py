# src/data_profiler.py
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

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
        
        # 3. Lignes peu remplies
        self.profile_results['row_quality'] = self._analyze_row_quality()

        # 4. Stats Numériques
        numeric_cols = self.df.select_dtypes(include=['number'])
        if not numeric_cols.empty:
            self.profile_results['describe_numeric'] = numeric_cols.describe().to_dict()
            # Ajout de la détection des outliers
            self.profile_results['outliers'] = self._detect_outliers(numeric_cols)

        # 5. Stats Catégorielles
        categorical_cols = self.df.select_dtypes(include=['str','object', 'category'])
        if not categorical_cols.empty:
            self.profile_results['describe_categorical'] = self._analyze_categorical_columns(categorical_cols)

        # 6. Aperçu
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
            top_categories = value_counts.head(10).to_dict()
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
    
    def _analyze_row_quality(self) -> Dict[str, Any]:
        """Analyse la qualité des lignes en fonction du pourcentage de valeurs manquantes."""
        # Calcul du pourcentage de valeurs manquantes par ligne
        row_null_counts = self.df.isnull().sum(axis=1)
        row_null_percentages = (row_null_counts / len(self.df.columns) * 100).round(2)
        
        # Classification des lignes
        row_full_empty = (row_null_percentages > 90).sum()
        row_partially_empty = ((row_null_percentages >= 30) & (row_null_percentages <= 90)).sum()
        
        # Identification des index des lignes problématiques
        problematic_rows = {
            'full_empty': row_null_percentages[row_null_percentages > 90].index.tolist(),
            'partially_empty': row_null_percentages[(row_null_percentages >= 30) & (row_null_percentages <= 90)].index.tolist()
        }
        
        # Génération des alertes
        alerts = []
        if row_full_empty > 0:
            alerts.append({
                'type': 'row_full_empty',
                'count': int(row_full_empty),
                'message': "À supprimer"
            })
        
        # Pour les lignes partiellement vides, on identifie les pourcentages spécifiques
        if row_partially_empty > 0:
            # Regrouper par pourcentage de valeurs manquantes
            percentage_groups = row_null_percentages[(row_null_percentages >= 30) & (row_null_percentages <= 90)].value_counts().sort_index(ascending=False)
            
            # Ne pas afficher plus de 10 lignes au total
            displayed_rows = 0
            for pct, count in percentage_groups.items():
                if displayed_rows >= 10:
                    break
                    
                # Afficher uniquement les lignes avec au moins 25% de manquants
                if pct >= 25:
                    # Trouver les index des lignes avec ce pourcentage spécifique
                    rows_with_pct = row_null_percentages[row_null_percentages == pct].index.tolist()
                    
                    # Limiter à 10 index max par groupe
                    rows_to_show = rows_with_pct[:10]
                    
                    # Message différent si plus de 10 lignes dans le groupe
                    if len(rows_with_pct) > 10:
                        message = f"À inspecter manuellement (affichées 10 premières sur {len(rows_with_pct)})"
                    else:
                        message = "À inspecter manuellement"
                    
                    alerts.append({
                        'type': 'row_partially_empty',
                        'count': int(count),
                        'percentage': float(pct),
                        'rows': rows_to_show,
                        'message': message
                    })
                    
                    displayed_rows += len(rows_to_show)
        
        return {
            'row_null_percentages': row_null_percentages.to_dict(),
            'problematic_rows': problematic_rows,
            'alerts': alerts
        }

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

        # --- CORRECTION ICI : Section Valeurs Manquantes ---
        md.append("\n## ⚠️ Valeurs Manquantes\n")
        
        missing_values_data = self.profile_results.get('missing_values', {})
        missing_found = False
        
        if missing_values_data:
            for col, pct in missing_values_data.get('percent', {}).items():
                if pct > 0:
                    count = missing_values_data['count'][col]
                    md.append(f"- **{col}**: {pct:.2f}% ({count} lignes)")
                    missing_found = True
        
        # Si aucune valeur manquante n'a été détectée, on affiche une confirmation claire
        if not missing_found:
            md.append("✅ **Aucune valeur manquante détectée.** Les données sont saines sur ce critère.")

        # Qualité des lignes (seulement si alertes existent)
        if 'row_quality' in self.profile_results and self.profile_results['row_quality']['alerts']:
            md.append("\n## 🚩 Qualité des Lignes\n")
            for alert in self.profile_results['row_quality']['alerts']:
                if alert['type'] == 'row_full_empty':
                    md.append(f"- **{alert['count']} lignes** avec > 90% de valeurs manquantes : {alert['message']}")
                elif alert['type'] == 'row_partially_empty':
                    if 'percentage' in alert:
                        md.append(f"- **{alert['count']} lignes** avec {alert['percentage']}% de valeurs manquantes : {alert['message']}")
                        # Afficher les index des lignes si elles existent
                        if 'rows' in alert and alert['rows']:
                            md.append(f"  - Index des lignes : {', '.join(map(str, alert['rows']))}")

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
                md.append(f"- **Skewness Frequency | Asymétrie de distribution** : {stats['skewness_frequency']}%")

                # Catégories les plus fréquentes (Uniquement si la cardinalité est raisonnable < 100)
                # On affiche toujours le TOP 10, quoi qu'il arrive dans cette plage
                if stats['cardinality_absolute'] > 0 and stats['cardinality_absolute'] <= 100:
                    md.append("\n- **Top 10 Catégories les plus fréquentes** :")
                    
                    # On s'assure de ne prendre que les 10 premiers (même si le profilage en a envoyé plus par erreur)
                    top_10 = list(stats['top_categories'].items())[:10]

                    for category, count in top_10:
                        total_non_null = len(self.df) - self.df[col].isnull().sum()
                        if total_non_null > 0:
                            percentage = (count / total_non_null * 100).round(2)
                        else:
                            percentage = 0
                        md.append(f"  - {category} ({percentage}%)")
                elif stats['cardinality_absolute'] > 100:
                    # Pour les listes très longues (ex: IDs), on affiche juste le compteur pour confirmer la diversité
                    pass 
                
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

    def generate_md_report(self, output_filename: str = "data/processed/data_profiling_report.md") -> str:
        """Sauvegarde le rapport Markdown."""
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        if not self.profile_results:
            self.run_analysis()
            
        report_content = self._generate_markdown_report()
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"📄 Rapport sauvegardé : {output_filename}")
        return output_filename

    def generate_visualizations(self, output_dir: str = "data/processed/") -> None:
        """Génère des visualisations et les sauvegarde dans un dossier."""
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Histogrammes pour les colonnes numériques
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            try:
                plt.figure(figsize=(8, 4))
                sns.histplot(self.df[col].dropna(), kde=True)
                plt.title(f"Distribution de {col}")
                plt.tight_layout()
                plt.savefig(Path(output_dir) / f"{col}_hist.png")
                plt.close()
            except Exception as e:
                print(f"⚠️ Erreur lors de la génération du histogramme pour {col}: {e}")

        # 2. Boxplots pour les colonnes numériques (outliers)
        for col in numeric_cols:
            try:
                plt.figure(figsize=(6, 3))
                sns.boxplot(y=self.df[col].dropna())
                plt.title(f"Boxplot de {col}")
                plt.tight_layout()
                plt.savefig(Path(output_dir) / f"{col}_boxplot.png")
                plt.close()
            except Exception as e:
                print(f"⚠️ Erreur lors de la génération du boxplot pour {col}: {e}")

        # 3. Graphiques pour les colonnes catégorielles
        categorical_cols = self.df.select_dtypes(include=['str','object', 'category']).columns
        for col in categorical_cols:
            try:
                plt.figure(figsize=(10, 6))
                value_counts = self.df[col].value_counts().head(10)  # Top 10 catégories
                sns.barplot(x=value_counts.values, y=value_counts.index)
                plt.title(f"Répartition de {col}")
                plt.xlabel("Nombre de occurrences")
                plt.tight_layout()
                plt.savefig(Path(output_dir) / f"{col}_barplot.png")
                plt.close()
            except Exception as e:
                print(f"⚠️ Erreur lors de la génération du barplot pour {col}: {e}")

    def _generate_html_report(self) -> str:
        """Convertit les résultats en HTML avec graphiques intégrés."""
        # En-tête HTML
        html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Rapport d'Inspection des Données</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #2c3e50; }
                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                img { max-width: 100%; height: auto; margin: 10px 0; }
                ul { margin-top: 5px; margin-bottom: 5px; }
            </style>
        </head>
        <body>
            <h1>📊 Rapport d'Inspection des Données</h1>
            <hr>

            <!-- Métadonnées -->
            <h2>📂 Métadonnées & Contexte Source</h2>
        """

        # Ajout des métadonnées
        if self.source_file_path:
            source_filename = Path(self.source_file_path).name
            html += f"<p><strong>Nom du fichier source</strong> : {source_filename}</p>"
            html += f"<p><strong>Chemin d'accès complet</strong> : {self.source_file_path}</p>"
        html += f"<p><strong>Date et heure de génération</strong> : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"

        # Structure
        shape = self.profile_results['shape']
        html += "<h2>🧱 Structure</h2>"
        for k, v in {**shape, **{'nb_doublons': self.profile_results.get('nb_doublons', 0)}}.items():
            html += f"<p><strong>{k}</strong>: {v}</p>"

        # Types
        html += "<h2>🏷️ Colonnes et Types</h2>"
        html += "<table border='1'><tr><th>Colonne</th><th>Type</th></tr>"
        for col, dtype in self.profile_results['dtypes'].items():
            html += f"<tr><td>{col}</td><td>{dtype}</td></tr>"
        html += "</table>"

        # Valeurs manquantes (Correction pour afficher si vide)
        html += "<h2>⚠️ Valeurs Manquantes</h2>"
        
        missing_values_data = self.profile_results.get('missing_values', {})
        missing_found = False
        
        if missing_values_data:
            for col, pct in missing_values_data.get('percent', {}).items():
                if pct > 0:
                    count = missing_values_data['count'][col]
                    html += f"<p><strong>{col}</strong>: {pct:.2f}% ({count} lignes)</p>"
                    missing_found = True
        
        # Si aucune valeur manquante, on confirme l'état sain
        if not missing_found:
            html += "<p>✅ <strong>Aucune valeur manquante détectée.</strong> Les données sont saines sur ce critère.</p>"

        # Qualité des lignes
        if 'row_quality' in self.profile_results and self.profile_results['row_quality']['alerts']:
            html += "<h2>🚩 Qualité des Lignes</h2>"
            for alert in self.profile_results['row_quality']['alerts']:
                if alert['type'] == 'row_full_empty':
                    html += f"<p><strong>{alert['count']} lignes</strong> avec > 90% de valeurs manquantes : {alert['message']}</p>"
                elif alert['type'] == 'row_partially_empty':
                    html += f"<p><strong>{alert['count']} lignes</strong> avec {alert['percentage']}% de valeurs manquantes : {alert['message']}</p>"
                    # Afficher les index des lignes si elles existent
                    if 'rows' in alert and alert['rows']:
                        html += f"<p>Index des lignes : {', '.join(map(str, alert['rows']))}</p>"

        # Stats numériques
        if 'describe_numeric' in self.profile_results:
            desc_df = pd.DataFrame(self.profile_results['describe_numeric'])
            html += "<h2>📈 Statistiques Numériques</h2>"
            html += desc_df.round(2).to_html()

        # Outliers
        if 'outliers' in self.profile_results and self.profile_results['outliers']:
            html += "<h2>🚩 Valeurs Aberrantes (Outliers)</h2>"
            html += "<table border='1'><tr><th>Colonne</th><th>Nombre d'outliers</th><th>Limite inférieure</th><th>Limite supérieure</th></tr>"
            for col, info in self.profile_results['outliers'].items():
                html += f"<tr><td>{col}</td><td>{info['count']}</td><td>{info['lower_bound']:.2f}</td><td>{info['upper_bound']:.2f}</td></tr>"
            html += "</table>"

        # Stats Catégorielles (Corrigées pour afficher toujours le Top 10 si pertinent)
        if 'describe_categorical' in self.profile_results:
            html += "<h2>📊 Analyse des Colonnes Catégorielles</h2>"
            
            for col, stats in self.profile_results['describe_categorical'].items():
                html += f"<h3>{col}</h3>"
                
                # Informations de base
                html += f"<p><strong>Cardinalité absolue</strong> : {stats['cardinality_absolute']}</p>"
                html += f"<p><strong>Cardinalité relative</strong> : {stats['cardinality_relative']}%</p>"
                html += f"<p><strong>Sparsity Ratio | Taux de remplissage</strong> : {stats['sparsity_ratio']}%</p>"
                
                # Skewness de fréquence (Affichage neutre)
                if stats['is_high_skewness']:
                    html += f"<p><strong>Skewness Frequency | Asymétrie de distribution</strong> : {stats['skewness_frequency']}%</p>"
                else:
                    html += f"<p><strong>Skewness Frequency | Asymétrie de distribution</strong> : {stats['skewness_frequency']}%</p>"

                # Catégories les plus fréquentes (Uniquement si cardinalité <= 100 pour rester lisible)
                if stats['cardinality_absolute'] > 0 and stats['cardinality_absolute'] <= 100:
                    html += "<p><strong>Top 10 Catégories les plus fréquentes</strong> :</p>"
                    html += "<ul>"
                    top_10 = list(stats['top_categories'].items())
                    
                    for category, count in top_10:
                        total_non_null = len(self.df) - self.df[col].isnull().sum()
                        if total_non_null > 0:
                            percentage = (count / total_non_null * 100).round(2)
                        else:
                            percentage = 0
                        html += f"<li>{category} ({percentage}%)</li>"
                    html += "</ul>"

                # Qualité du format
                if stats['format_anomalies']:
                    html += "<p><strong>⚠️ Anomalies de format détectées</strong> :</p>"
                    html += "<ul>"
                    for issue in stats['format_anomalies']:
                        html += f"<li>{issue}</li>"
                    html += "</ul>"
                else:
                    html += "<p><strong>✅ Format conforme</strong></p>"

        # Visualisations intégrées
        html += "<h2>📊 Graphiques</h2>"
        
        # Générer les graphiques directement dans le HTML
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            html += f"<h3>{col}</h3>"
            
            # Histogramme
            try:
                plt.figure(figsize=(8, 4))
                sns.histplot(self.df[col].dropna(), kde=True)
                plt.title(f"Distribution de {col}")
                plt.tight_layout()
                
                # Convertir le graphique en base64
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                plt.close()
                
                html += f'<img src="data:image/png;base64,{img_base64}" alt="{col} histogram" width="400">'
            except Exception as e:
                html += f"<p>Erreur lors de la génération de l'histogramme pour {col}: {e}</p>"
            
            # Boxplot
            try:
                plt.figure(figsize=(6, 3))
                sns.boxplot(y=self.df[col].dropna())
                plt.title(f"Boxplot de {col}")
                plt.tight_layout()
                
                # Convertir le graphique en base64
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                plt.close()
                
                html += f'<img src="data:image/png;base64,{img_base64}" alt="{col} boxplot" width="400">'
            except Exception as e:
                html += f"<p>Erreur lors de la génération du boxplot pour {col}: {e}</p>"

        # Graphiques catégoriels
        categorical_cols = self.df.select_dtypes(include=['str','object', 'category']).columns
        for col in categorical_cols:
            html += f"<h3>{col}</h3>"
            try:
                plt.figure(figsize=(10, 6))
                value_counts = self.df[col].value_counts().head(10)  # Top 10 catégories
                sns.barplot(x=value_counts.values, y=value_counts.index)
                plt.title(f"Répartition de {col}")
                plt.xlabel("Nombre de occurrences")
                plt.tight_layout()
                
                # Convertir le graphique en base64
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                plt.close()
                
                html += f'<img src="data:image/png;base64,{img_base64}" alt="{col} barplot" width="400">'
            except Exception as e:
                html += f"<p>Erreur lors de la génération du barplot pour {col}: {e}</p>"

        # Aperçu
        html += "<h2>👀 Aperçu</h2>"
        try:
            # Utiliser directement le DataFrame pour générer un tableau HTML propre
            preview_df = self.df.head(10)
            html += preview_df.to_html(index=False, table_id='preview-table', escape=False)
        except Exception as e:
            # Fallback si conversion échoue
            html += "<p>Erreur lors de l'affichage de l'aperçu</p>"
            # Afficher le texte brut en dernier recours
            if self.profile_results['sample_preview']:
                html += f"<pre>{self.profile_results['sample_preview']}</pre>"

        html += "</body></html>"
        return html
    
    def generate_html_report(self, output_filename: str = "data/processed/data_profiling_report.html") -> str:
        """Génère un rapport HTML avec graphiques intégrés."""
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        if not self.profile_results:
            self.run_analysis()
            
        # Générer le rapport HTML avec graphiques intégrés
        report_content = self._generate_html_report()
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"📄 Rapport HTML sauvegardé : {output_filename}")
        return output_filename

    def interactive_report_choice(self, reports_dir, input_file):
        """Permet de choisir le format de rapport de manière interactive"""
        print("\n--- 📊 Choix du Format de Rapport d'analyse ---")
        print("Souhaitez-vous un rapport en format Markdown (.md) ou HTML avec graphiques ?")
        print("1. Markdown (.md)")
        print("2. HTML avec graphiques")
        
        import datetime
        
        choice = input("⏳ Votre choix (1 ou 2) : ").strip()
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
        
        if choice == "1":
            report_filename = reports_dir / f"profiling_{input_file.stem}_{timestamp}.md"
            self.generate_md_report(str(report_filename))
        elif choice == "2":
            report_filename = reports_dir / f"profiling_{input_file.stem}_{timestamp}.html"
            self.generate_html_report(str(report_filename))
        else:
            print("❌ Choix non valide. Génération par défaut en Markdown.")
            report_filename = reports_dir / f"profiling_{input_file.stem}_{timestamp}.md"
            self.generate_md_report(str(report_filename))

            