from pathlib import Path
import logging
import sys

# Import des modules du projet
from src.file_loader import load_file
from src.cleaner_engine import run_all_cleaning_steps, get_user_decisions, prepare_target_columns_for_case_cleaning
from src.data_profiler import DataProfiler
from src.cleaner_logger import generate_and_print_report
from src.cleaner_reporter import generate_enhanced_report

def main():
    # ==========================================
    # 📍 1. CONFIGURATION DES CHEMINS
    # ==========================================
    base_dir = Path(__file__).parent
    
    # Définition des chemins relatifs
    RELATIVE_INPUT = "data/raw/reservations_rivage_brut.csv"
    RELATIVE_OUTPUT = "data/processed/dataset_nettoye.csv"
    RELATIVE_REPORTS = "data/reports"

    input_file = base_dir / RELATIVE_INPUT
    output_file = base_dir / RELATIVE_OUTPUT
    reports_dir = base_dir / RELATIVE_REPORTS

    # 🔎 Validation stricte des chemins existants au démarrage
    if not input_file.exists():
        raise FileNotFoundError(
            f"❌ ERREUR DE CONFIGURATION :\n"
            f"Le fichier source est introuvable à l'emplacement suivant :\n"
            f"👉 {input_file.resolve()}\n\n"
            "Veuillez vérifier le chemin relatif dans le code (variable 'RELATIVE_INPUT')."
        )

    # Création automatique du dossier de sortie s'il n'existe pas
    output_file.parent.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 2. Chargement
    print("⏳ Chargement du fichier...")
    initial_df = load_file(str(input_file))
    print(f"✅ Fichier chargé ({initial_df.shape[0]} lignes, {initial_df.shape[1]} colonnes)\n")

    # 3. PROFILAGE (Inséré avant le nettoyage pour avoir une trace fiable)
    profiler_results = {}
    profiler = DataProfiler(initial_df, input_file)
    profiler_results = profiler.run_profiling_workflow(input_file, reports_dir)

    # 4. PRÉPARATION DU NETTOYAGE CIBLÉ
    
    # A. Extraction des colonnes cibles pour la casse (basé sur le profiler)
    target_cols_for_case = prepare_target_columns_for_case_cleaning(profiler_results)
    if target_cols_for_case:
        print(f"🎯 Nettoyage ciblé activé pour la casse sur les colonnes : {', '.join(target_cols_for_case)}")
    else:
        print("ℹ️ Aucun problème de casse détecté")
    
    # B. Demande utilisateur pour les décisions lourdes (Outliers / Missing)
    correct_outliers = True
    fill_missing = True
    correct_outliers, fill_missing = get_user_decisions(initial_df, profiler_results)

    # 5. LANCEMENT DU NETTOYAGE
    try:
        # On passe LE PROFILAGE COMPLET ou la liste des cibles à cleaner_engine
        # Ici on passe profiler_results pour que cleaner_engine ait le contexte complet si besoin
        cleaned_df, stats = run_all_cleaning_steps(
            initial_df.copy(), 
            profile_info=profiler_results,
            correct_outliers=correct_outliers, 
            fill_missing=fill_missing
        )
        print("\n✅ Nettoyage terminé.")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. Sauvegarde
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        cleaned_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Données nettoyées sauvegardées dans : {output_file}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return

    # 7. Rapport Console (Comparaison Brut vs Propre)
    try:
        generate_and_print_report(initial_df, stats, cleaned_df)
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du rapport console : {e}")

    # 8. Génération du rapport Markdown final avec CleanerReporter
    try:
        logger = logging.getLogger(__name__)
        generate_enhanced_report(profiler, logger, reports_dir, input_file, stats)
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du rapport final : {e}")

if __name__ == "__main__":
    main()