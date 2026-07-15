import sys
import os
from src.cleaner_engine import run_all_cleaning_steps
from src.report_generator import generate_and_print_report
from src.file_loader import load_file


def main():
    # Configuration des chemins
    input_file = "data/raw/ai_student_impact_dataset.csv"
    output_file = "data/processed/ai_student_impact_dataset_nettoye.csv"

    # 1. Chargement (Délègue la logique complexe de détection à file_loader)
    try:
        initial_df = load_file(input_file)
    except FileNotFoundError:
        print(f"❌ Impossible de charger {input_file}")
        return
    except ValueError as e:
        print(f"❌ Erreur de format : {e}")
        return

    # 2. Nettoyage (Le cœur du programme)
    # On utilise .copy() pour éviter les avertissements pandas (SettingWithCopyWarning)
    cleaned_df, stats = run_all_cleaning_steps(initial_df.copy())

    # 3. Sauvegarde (I/O simple)
    try:
        cleaned_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n✅ Données propres sauvegardées dans : {output_file}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return

    # 4. Rapport (Visualisation)
    generate_and_print_report(initial_df, stats, cleaned_df)


if __name__ == "__main__":
    main()

