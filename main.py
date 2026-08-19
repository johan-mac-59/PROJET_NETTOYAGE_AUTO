from pathlib import Path
import logging
import sys

# Import des modules du projet
from src.file_loader import load_file
from src.cleaner_engine import run_all_cleaning_steps, ask_user_outlier_correction, ask_user_missing_values_correction
from src.data_profiler import DataProfiler
from src.cleaner_logger import generate_and_print_report
from src.cleaner_reporter import generate_enhanced_report

def main():
    # 1. Configuration (Pathlib pour les chemins robustes sous Windows)
    base_dir = Path(__file__).parent
    input_file = base_dir / "data/raw/reservations_rivage_brut.csv"
    output_file = base_dir / "data/processed/dataset_nettoye.csv"
    reports_dir = base_dir / "data/reports"
    
    # On s'assure que les dossiers de sortie existent
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        print(f"❌ Impossible de trouver le fichier d'entrée : {input_file}")
        return

    # 2. Chargement
    print("⏳ Chargement du fichier...")
    initial_df = load_file(str(input_file))
    print(f"✅ Fichier chargé ({initial_df.shape[0]} lignes, {initial_df.shape[1]} colonnes)\n")

    # 3. PROFILAGE (Inséré avant le nettoyage pour avoir une trace fiable)
    profiler_results = None
    try:
        print("--- 📊 Lancement du Profilage ---")
        profiler = DataProfiler(initial_df, input_file)
        
        # choix du format du rapport pour l'utilisateur
        profiler.interactive_report_choice(reports_dir, input_file)
        
        # Exécuter l'analyse pour avoir les résultats en mémoire (dict)
        profiler_results = profiler.run_analysis()
        print(f"✅ Profilage terminé ({len(profiler_results.keys())}) critères analysés.")

    except Exception as e:
        print(f"⚠️ Erreur lors du profilage : {e} (On continue avec un profil vide)")

    # 4. PRÉPARATION DU NETTOYAGE CIBLÉ
    
    # A. Extraction des colonnes cibles pour la casse (basé sur le profiler)
    target_cols_for_case = []
    if profiler_results and 'describe_categorical' in profiler_results:
        for col, stats in profiler_results['describe_categorical'].items():
            anomalies = stats.get('format_anomalies', [])
            # On cible les colonnes qui ont des problèmes de casse OU d'espaces détectés par le profiler
            if any("Variations de casse" in str(a) or "Espaces" in str(a) for a in anomalies):
                target_cols_for_case.append(col)

    if target_cols_for_case:
        print(f"🎯 Nettoyage ciblé activé pour la casse sur : {', '.join(target_cols_for_case)}")
    else:
        print("ℹ️ Aucune colonne cible spécifique pour la détectée par le profilage. (Scan global ou ignoré selon cleaner_engine)")

    # B. Demande utilisateur pour les décisions lourdes (Outliers / Missing)
    correct_outliers = True
    fill_missing = True
    
    print("\n" + "="*60)
    print("🔧 Décisions de Nettoyage Avancé")
    print("="*60)

    if profiler_results:
        # Outliers
        if 'outliers' in profiler_results and profiler_results['outliers']:
            correct_outliers = ask_user_outlier_correction(initial_df, {}, profiler_results['outliers'])
        else:
            print("✅ Aucune valeur aberrante détectée par le profilage.")
                
        # Missing Values
        total_missing = initial_df.isnull().sum().sum()
        if total_missing > 0:
            fill_missing = ask_user_missing_values_correction(initial_df, {}, profiler_results['missing_values'])
        else:
            print("✅ Aucune valeur manquante détectée par le profilage.")
    else:
        # Fallback si pas de profil
        print("⚠️ Pas de résultats de profilage. Questions standards...")
        correct_outliers = ask_user_outlier_correction(initial_df, {}, {})
        fill_missing = ask_user_missing_values_correction(initial_df, {}, {})

    print(f"\n➡️ Configuration finale : Outliers={'ON' if correct_outliers else 'OFF'} | Missing={'ON' if fill_missing else 'OFF'}")

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