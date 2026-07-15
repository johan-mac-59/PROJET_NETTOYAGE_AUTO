# src/run_pipeline.py
import pandas as pd
from pathlib import Path
from src.file_loader import load_file  # Import du Loader dédié
from src.cleaner_engine import run_all_cleaning_steps
from src.report_generator import generate_and_print_report, CleanReportGenerator
    
def main():
    # 1. Configuration des chemins (utilisons pathlib pour la robustesse)
    input_file = Path("data/raw/ai_student_impact_dataset.csv")
    output_file = Path("data/processed/ai_student_impact_dataset_nettoye.csv")

    if not input_file.exists():
        print(f"❌ Erreur: Le fichier {input_file} n'existe pas.")
        return

    # 2. Chargement via le Loader dédié (On gagne en modularité)
    try:
        initial_df = load_file(str(input_file))
        print(f"✅ Fichier chargé : {initial_df.shape[0]} lignes, {initial_df.shape[1]} colonnes.")
    except Exception as e:
        print(f"❌ Échec du chargement: {e}")
        return

    # 3. Nettoyage (Le Moteur)
    # On copie pour ne pas modifier le df original avant le rapport
    final_df, stats = run_all_cleaning_steps(initial_df.copy())
    
    # 4. Sauvegarde
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True) # Crée le dossier si inexistant
        final_df.to_csv(output_file, index=False, encoding='utf-8')
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return

    # 5. Rapport (Le Journaliste)
    # On génère le rapport avec l'état initial et final
    reporter = CleanReportGenerator(initial_df, stats)
    reporter.update_final_state(final_df)

    summary_text = reporter.get_summary()
    print(summary_text)
    print(f"\n✅ Fichier propre sauvegardé dans {output_file}")

if __name__ == "__main__":
    main()