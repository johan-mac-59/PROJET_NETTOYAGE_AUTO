# Amélioration du fichier cleaner_reporter.py
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
        """Crée l'en-tête Markdown avec la date et le nom du fichier."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            file_info = self.profiler.get_file_info()
            # Validation que file_info est bien un dictionnaire
            if not isinstance(file_info, dict):
                file_info = {'path': 'Inconnu'}
        except (AttributeError, TypeError) as e:
            self.logger.warning(f"Erreur lors de la récupération des informations du fichier : {e}")
            file_info = {'path': 'Inconnu'}
        
        return f"# {self.report_title}\n\n" \
               f"**Date de génération :** {timestamp}\n\n" \
               f"**Fichier source :** `{file_info['path']}`\n\n"
    
    def _get_summary_section(self) -> str:
        """Résumé des métriques globales (Avant/Après)."""
        if not self.profiler.has_profile():
            return "## Résumé Global\n\n*Aucun profilage disponible.*\n\n"
        
        try:
            profile = self.profiler.get_profile()
            # Validation du format de profile
            if not isinstance(profile, dict):
                return "## Résumé des Métriques\n\n*Erreur : Format de profil non valide.*\n\n"
                
            # Initialisation correcte des métriques avec des valeurs par défaut
            metrics = {
                'rows_after': 0,
                'missing_after': 0,
                'duplicates_removed': 0
            }
        except (AttributeError, TypeError) as e:
            self.logger.error(f"Erreur lors de la récupération des métriques : {str(e)}")
            return f"## Résumé des Métriques\n\n*Erreur lors de la récupération des métriques : {str(e)}*\n\n"
        
        # Validation et conversion des données
        def safe_get_value(data, key, default='N/A'):
            value = data.get(key, default)
            if value is None:
                return 'N/A'
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                # Pour les nombres, on convertit en chaîne
                if isinstance(value, float) and value.is_integer():
                    return str(int(value))
                return str(value)
            elif isinstance(value, bool):
                return 'Oui' if value else 'Non'
            elif isinstance(value, str):
                return value
            else:
                return str(value)
        
        # Utilisation correcte des données
        total_rows_before = safe_get_value(profile, 'total_rows', 0)
        missing_values_before = safe_get_value(profile, 'missing_values', 0)
        rows_after = safe_get_value(metrics, 'rows_after', 0)
        missing_after = safe_get_value(metrics, 'missing_after', 0)
        duplicates_removed = safe_get_value(metrics, 'duplicates_removed', 0)
        
        return f"""## 1. Résumé des Métriques
| Statistique | Avant Nettoyage | Après Nettoyage |
| :--- | :---: | :---: |
| Lignes totales | {total_rows_before} | {rows_after} |
| Valeurs manquantes | {missing_values_before} | {missing_after} |
| Doublons trouvés | - | {duplicates_removed} |
"""
    
    def _get_operations_table(self) -> str:
        """Transforme le journal des opérations en tableau Markdown."""
        if not hasattr(self.logger, 'operations_log'):
            return "## Opérations de Nettoyage\n\n*Erreur : Logger invalide.*\n\n"
            
        operations_log = getattr(self.logger, 'operations_log', [])
        
        if not isinstance(operations_log, list) or len(operations_log) == 0:
            return "## Opérations de Nettoyage\n\n*Aucune opération enregistrée.*\n\n"
        
        headers = "| Colonne | Opération | Détails | Résultat |\n| :--- | :--- | :--- | :--- |"
        rows = ""
        
        for op in operations_log:
            # Validation du format des opérations
            if not isinstance(op, dict):
                continue
                
            column = op.get('column', 'Inconnu')
            action = op.get('action', 'Inconnue')
            details = op.get('details', 'Aucun détail')
            status = op.get('status', 'Inconnu')
            
            # Nettoyage des valeurs pour éviter les injections MD
            column = str(column).replace('|', '\\|').replace('*', '\\*')
            action = str(action).replace('|', '\\|').replace('*', '\\*')
            details = str(details).replace('|', '\\|').replace('*', '\\*')
            status = str(status).replace('|', '\\|').replace('*', '\\*')
            
            rows += f"| `{column}` | {action} | {details} | {status} |\n"
        
        return f"## 2. Détail des Opérations\n\n{headers}{rows}\n\n"
    
    def generate(self, output_path: str = "cleaning_report.md") -> str:
        """Génère le fichier Markdown complet."""
        try:
            content = (self._get_header() + 
                      self._get_summary_section() + 
                      self._get_operations_table())
            
            path_obj = Path(output_path)
            # Vérification du répertoire parent
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(content, encoding="utf-8")
            self.logger.info(f"Rapport généré avec succès : {path_obj.absolute()}")
            return str(path_obj.absolute())
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport : {str(e)}")
            raise RuntimeError(f"Erreur lors de la génération du rapport : {str(e)}")