# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import logging

class CleanerReporter:
    """Génère un rapport Markdown (.md) détaillé du nettoyage des données."""
    
    def __init__(self, profiler, logger):
        self.profiler = profiler
        self.logger = logger
        self.report_title = "Rapport de Nettoyage des Données"
    
    def _get_header(self) -> str:
        """Crée l'en-tête Markdown avec la date."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        """Transforme les statistiques de nettoyage en tableau Markdown."""
        if not stats:
            return "## 2. Détail des Opérations\n\n*Aucune opération enregistrée.*\n\n"
        
        try:
            # Construction du tableau avec les informations de nettoyage
            table_content = "## 2. Détail des Opérations\n\n"
            table_content += "| Opération | Nombre | Détails |\n"
            table_content += "| :--- | :---: | :--- |\n"
            
            # Ajout des statistiques de nettoyage
            if 'empty_cols_dropped' in stats and stats['empty_cols_dropped'] > 0:
                table_content += f"| Colonnes vides supprimées | {stats['empty_cols_dropped']} | - |\n"
            
            if 'whitespace_cleaned' in stats and stats['whitespace_cleaned'] > 0:
                table_content += f"| Espaces nettoyés | {stats['whitespace_cleaned']} | - |\n"
                
            if 'duplicates_removed' in stats and stats['duplicates_removed'] > 0:
                table_content += f"| Doublons supprimés | {stats['duplicates_removed']} | - |\n"
                
            if 'types_converted' in stats and stats['types_converted']:
                table_content += f"| Conversions de types | {len(stats['types_converted'])} | {', '.join(list(stats['types_converted'].keys()))} |\n"
                
            if 'missing_filled' in stats and stats['missing_filled']:
                table_content += f"| Valeurs manquantes comblées | {len(stats['missing_filled'])} | {', '.join(list(stats['missing_filled'].keys()))} |\n"
                
            if 'outliers_corrected' in stats and stats['outliers_corrected']:
                outliers_info = []
                for col, count in stats['outliers_corrected'].items():
                    outliers_info.append(f"{col}({count})")
                table_content += f"| Valeurs aberrantes corrigées | {len(stats['outliers_corrected'])} | {', '.join(outliers_info)} |\n"
                
            if not table_content.endswith("| Opération | Nombre | Détails |\n| :--- | :---: | :--- |\n"):
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
        # Initialisation du reporter
        reporter = CleanerReporter(profiler, logger)
        
        # Nom du rapport final avec timestamp
        final_report_filename = reports_dir / f"cleaning_report_{input_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        # Génération du rapport final avec les stats
        report_path = reporter.generate_with_stats(str(final_report_filename), stats)
        print(f"📝 Rapport de nettoyage généré : {report_path}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du rapport final : {e}")