import pandas as pd
from typing import Dict


class CleanLogger:
    """Génère un rapport de nettoyage structuré."""

    def __init__(self, initial_df: pd.DataFrame, stats: Dict):
        """
        Args:
            initial_df: Le DataFrame avant nettoyage.
            stats: Les statistiques retournées par run_all_cleaning_steps.
        """
        self.initial_df = initial_df
        self.stats = stats or {}  # Gestion des stats None
        # On calcule les infos "après" basées sur la différence de forme et la structure
        self.final_shape = None # Sera défini au moment du calcul final
        self.final_columns = None

    def update_final_state(self, final_df: pd.DataFrame):
        """Appelé après le nettoyage pour avoir l'état final."""
        self.final_shape = final_df.shape
        self.final_columns = list(final_df.columns)

    def get_summary(self) -> str:
        """Retourne le résumé textuel du rapport."""
        
        if self.final_shape is None:
            return "⚠️ Rapport non finalisé. Veuillez appeler update_final_state() d'abord."
        
        # 1. Métriques globales
        lines = []
        lines.append("=" * 60)
        lines.append("RAPPORT DE NETTOYAGE DE DONNÉES")
        lines.append("=" * 60)
        lines.append(f"📊 Lignes: {self.initial_df.shape[0]} → {self.final_shape[0]} ({self._format_delta(self.initial_df.shape[0], self.final_shape[0])})")
        lines.append(f"📑 Colonnes: {self.initial_df.shape[1]} → {self.final_shape[1]} ({self._format_delta(self.initial_df.shape[1], self.final_shape[1])})")
        lines.append("-" * 60)

        # 2. Opérations détaillées
        
        # Colonnes supprimées (>95% NaN)
        empty_cols = self.stats.get('empty_cols_dropped', 0)
        if empty_cols and empty_cols > 0:
            lines.append(f"🗑️ Colonnes supprimées (vides): {empty_cols}")

        # Doublons
        duplicates = self.stats.get('duplicates_removed', 0)
        if duplicates and duplicates > 0:
            lines.append(f"🔄 Doublons supprimés: {duplicates}")

        # Types convertis
        types_converted = self.stats.get('types_converted', {})
        if types_converted:
            conv_details = ", ".join([f"{k} ({v})" for k, v in types_converted.items()])
            lines.append(f"🎨 Types convertis: [{conv_details}]")

        # Valeurs manquantes comblées
        missing_filled = self.stats.get('missing_filled', {})
        if missing_filled:
            filled_cols = list(missing_filled.keys())
            lines.append(f"💧 Valeurs manquantes comblées dans: {', '.join(filled_cols)}")

        # Outliers corrigés
        outliers_corrected = self.stats.get('outliers_corrected', {})
        if outliers_corrected:
            outlier_details = ", ".join([f"{k} ({v})" for k, v in outliers_corrected.items()])
            lines.append(f"📈 Outliers corrigés (IQR): [{outlier_details}]")

        # Nettoyage espaces
        whitespace_cleaned = self.stats.get('whitespace_cleaned', 0)
        if whitespace_cleaned and whitespace_cleaned > 0:
            lines.append(f"🧼 Colonnes avec espaces nettoyés: {whitespace_cleaned}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_detailed_table(self, final_df: pd.DataFrame = None) -> pd.DataFrame:
        """Retourne un DataFrame résumé des changements (optionnel, pour affichage tabulaire)."""
        
        # On compare les types avant/après si le DataFrame final est fourni
        type_changes = []
        if final_df is not None:
            for col in self.initial_df.columns:
                if col in final_df.columns:
                    before_type = self.initial_df[col].dtype
                    after_type = final_df[col].dtype
                    if str(before_type) != str(after_type):
                        type_changes.append({
                            'Colonne': col,
                            'Type Avant': before_type,
                            'Type Après': after_type
                        })
        
        return pd.DataFrame(type_changes)

    def _format_delta(self, initial: int, final: int) -> str:
        delta = final - initial
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta}"


def generate_and_print_report(initial_df: pd.DataFrame, stats: Dict, final_df: pd.DataFrame):
    """Fonction utilitaire rapide pour générer et afficher."""
    reporter = CleanLogger(initial_df, stats)
    reporter.update_final_state(final_df)
    print(reporter.get_summary())

