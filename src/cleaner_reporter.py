# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import logging

class CleanerReporter:
    """Génère un rapport Markdown (.md) détaillé du nettoyage des données."""
    
    def __init__(self, profiler, logger, source_file_path=None):
        self.profiler = profiler
        self.logger = logger
        self.source_file_path = source_file_path
        self.report_title = "Rapport de Nettoyage des Données"
    
    def _get_header(self) -> str:
        """Crée l'en-tête Markdown avec la date."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.source_file_path:
            source_filename = Path(self.source_file_path).name
            return f"# {self.report_title}\n\n" \
                   f"**Date de génération :** {timestamp}\n\n" \
                   f"**Fichier source :** `{source_filename}`\n\n"
        else:
            return f"# {self.report_title}\n\n" \
                   f"**Date de génération :** {timestamp}\n\n" \
                   f"**Fichier source :** `Inconnu`\n\n"
    
    def _get_summary_section(self) -> str:
        """Résumé des métriques globales (Avant/Après)."""
        try:
            # On récupère les résultats de l'analyse déjà effectuée
            profile_results = self.profiler.profile_results
            
            if not profile_results:
                return "## Résumé Global\n\n*Aucun profilage disponible.*\n\n"
            
            # Extraction des métriques disponibles
            shape = profile_results.get('shape', {})
            nb_lignes_avant = shape.get('nb_lignes', 'N/A')
            nb_colonnes = shape.get('nb_colonnes', 'N/A')
            nb_doublons = profile_results.get('nb_doublons', 0)
            
            # Pour les valeurs manquantes
            missing_values = profile_results.get('missing_values', {})
            total_missing = sum(missing_values.get('count', {}).values()) if missing_values else 0
            
            return f"""## 1. Résumé des Métriques
| Statistique | Valeur |
| :--- | :---: |
| Lignes totales (avant) | {nb_lignes_avant} |
| Colonnes totales | {nb_colonnes} |
| Doublons trouvés | {nb_doublons} |
| Valeurs manquantes totales | {total_missing} |
"""
        except Exception as e:
            return f"## Résumé des Métriques\n\n*Erreur lors de la récupération des métriques : {str(e)}*\n\n"
    
    def _get_operations_table(self, stats) -> str:
        """Transforme les statistiques de nettoyage en tableau Markdown détaillé."""
        if not stats:
            return "## 2. Détail des Opérations\n\n*Aucune opération enregistrée.*\n\n"
        
        try:
            # Construction du tableau avec les informations de nettoyage
            table_content = "## 2. Détail des Opérations\n\n"
            
            # Colonnes vides supprimées
            if 'empty_cols_dropped' in stats and stats['empty_cols_dropped'] > 0:
                table_content += f"### Colonnes vides supprimées\n\n"
                table_content += f"Total de colonnes supprimées : {stats['empty_cols_dropped']}\n\n"
            
            # Espaces nettoyés
            if 'whitespace_cleaned' in stats and stats['whitespace_cleaned'] > 0:
                table_content += f"### Espaces nettoyés\n\n"
                table_content += f"Total d'espaces nettoyés : {stats['whitespace_cleaned']}\n\n"
                
            # Doublons supprimés
            if 'duplicates_removed' in stats and stats['duplicates_removed'] > 0:
                table_content += f"### Doublons supprimés\n\n"
                table_content += f"Total de doublons supprimés : {stats['duplicates_removed']}\n\n"
                
            # Conversions de types
            if 'types_converted' in stats and stats['types_converted']:
                table_content += f"### Conversions de types\n\n"
                table_content += f"Total de conversions effectuées : {len(stats['types_converted'])}\n\n"
                table_content += "| Type converti | Colonnes concernées |\n"
                table_content += "| :--- | :--- |\n"
                for type_name, columns in stats['types_converted'].items():
                    # Si c'est une chaîne de caractères qui contient les colonnes
                    if isinstance(columns, list):
                        table_content += f"| {type_name} | {', '.join(columns)} |\n"
                    else:
                        # Sinon on affiche le type converti comme colonne concernée
                        table_content += f"| {type_name} | - |\n"
                table_content += "\n"
                
            # Valeurs manquantes comblées
            if 'missing_filled' in stats and stats['missing_filled']:
                table_content += f"### Valeurs manquantes comblées\n\n"
                # Calcul du total (somme des counts)
                total_missing = 0
                try:
                    total_missing = sum([v['count'] if isinstance(v, dict) else v for v in stats['missing_filled'].values()])
                except TypeError:
                    total_missing = "N/A"
                table_content += f"Total de valeurs manquantes comblées : {total_missing}\n\n"
                table_content += "| Colonne | Nombre de valeurs comblées | Méthode utilisée |\n"
                table_content += "| :--- | :---: | :--- |\n"
                for col, info in stats['missing_filled'].items():
                    if isinstance(info, dict):
                        count = info['count']
                        method = info['method']
                    else:
                        count = info
                        method = "inconnue"
                    table_content += f"| {col} | {count} | {method} |\n"
                table_content += "\n"
                
            # Valeurs aberrantes corrigées
            if 'outliers_corrected' in stats and stats['outliers_corrected']:
                table_content += f"### Valeurs aberrantes corrigées\n\n"
                # On fait une somme uniquement si les valeurs sont numériques
                total_outliers = 0
                try:
                    total_outliers = sum(stats['outliers_corrected'].values())
                except TypeError:
                    # Si ce n'est pas numérique, on ne compte pas
                    total_outliers = "N/A"
                table_content += f"Total de valeurs aberrantes corrigées : {total_outliers}\n\n"
                table_content += "| Colonne | Nombre de valeurs aberrantes corrigées |\n"
                table_content += "| :--- | :---: |\n"
                for col, count in stats['outliers_corrected'].items():
                    try:
                        # Vérifier si c'est un nombre
                        int(count)
                        table_content += f"| {col} | {count} |\n"
                    except (ValueError, TypeError):
                        # Si ce n'est pas un nombre, on affiche le type de valeur
                        table_content += f"| {col} | {count} (type: {type(count).__name__}) |\n"
                table_content += "\n"
                
            if not table_content.endswith("## 2. Détail des Opérations\n\n"):
                return table_content
            else:
                return "## 2. Détail des Opérations\n\n*Aucune opération enregistrée.*\n\n"
                
        except Exception as e:
            return f"## 2. Détail des Opérations\n\n*Erreur lors de la génération du tableau : {str(e)}*\n\n"
    
    def generate_with_stats(self, output_path: str, stats: dict = None) -> str:
        """Génère le fichier Markdown complet avec les statistiques."""
        try:
            content = (self._get_header() + 
                      self._get_summary_section() + 
                      self._get_operations_table(stats))
            
            path_obj = Path(output_path)
            # Vérification du répertoire parent
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(content, encoding="utf-8")
            self.logger.info(f"Rapport généré avec succès : {path_obj.absolute()}")
            return str(path_obj.absolute())
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport : {str(e)}")
            raise RuntimeError(f"Erreur lors de la génération du rapport : {str(e)}")
    
    def generate(self, output_path: str = "cleaning_report.md") -> str:
        """Génère le fichier Markdown complet (ancienne version)."""
        return self.generate_with_stats(output_path, {})

def generate_enhanced_report(profiler, logger, reports_dir, input_file, stats):
    """Fonction utilitaire pour générer le rapport amélioré."""
    try:
        # Initialisation du reporter avec le chemin du fichier source
        reporter = CleanerReporter(profiler, logger, source_file_path=str(input_file))
        
        # Nom du rapport final avec timestamp
        final_report_filename = reports_dir / f"cleaning_report_{input_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        # Génération du rapport final avec les stats
        report_path = reporter.generate_with_stats(str(final_report_filename), stats)
        print(f"📝 Rapport de nettoyage généré : {report_path}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du rapport final : {e}")