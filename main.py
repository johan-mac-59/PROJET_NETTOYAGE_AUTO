from pathlib import Path
import logging

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
    initial_df = load_file(str(input_file))
    print(f"✅ Fichier chargé ({initial_df.shape[0]} lignes, {initial_df.shape[1]} colonnes)")

    # 3. PROFILAGE (Inséré avant le nettoyage pour avoir une trace fiable)
    try:
        profiler = DataProfiler(initial_df, input_file)
        
        # Générer un rapport interactif
        profiler.interactive_report_choice(reports_dir, input_file)
        
        # Exécuter l'analyse pour avoir les résultats
        profiler.run_analysis()
            
    except Exception as e:
        print(f"⚠️ Erreur lors du profilage (continuation du pipeline) : {e}")

    # 4. Nettoyage - Demande utilisateur pour outliers et valeurs manquantes
    try:
        # --- Nouvelle logique : Demander à l'utilisateur si on corrige les outliers ---
        print("\n" + "="*60)
        print("🔧 Options de Nettoyage Avancé")
        print("="*60)
        
        # Gestion des valeurs manquantes
        fill_missing = True  # Par défaut, on remplit
        correct_outliers = True  # Par défaut, on corrige
        
        if hasattr(profiler, 'profile_results') and profiler.profile_results:
            # Vérifier si des outliers ont été détectés dans les résultats du profiler
            if 'outliers' in profiler.profile_results and profiler.profile_results['outliers']:
                correct_outliers = ask_user_outlier_correction(initial_df, {}, profiler.profile_results)
            else:
                print("✅ Aucune valeur aberrante détectée. Correction ignorée.")
                
            # Vérifier si des valeurs manquantes ont été détectées
            total_missing = initial_df.isnull().sum().sum()
            if total_missing > 0:
                fill_missing = ask_user_missing_values_correction(initial_df, {}, profiler.profile_results)
            else:
                print("✅ Aucune valeur manquante détectée. Remplissage ignoré.")
        else:
            # Si pas de profilage, on demande quand même
            correct_outliers = ask_user_outlier_correction(initial_df, {}, {})
            fill_missing = ask_user_missing_values_correction(initial_df, {}, {})
        
        print(f"{'✅' if correct_outliers else '❌'} Correction des outliers : {'OUI' if correct_outliers else 'NON'}")
        print(f"{'✅' if fill_missing else '❌'} Remplissage des valeurs manquantes : {'OUI' if fill_missing else 'NON'}")
        
        cleaned_df, stats = run_all_cleaning_steps(initial_df.copy(), correct_outliers=correct_outliers, fill_missing=fill_missing)
        print("✅ Nettoyage terminé.")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")
        return

    # 5. Sauvegarde
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        cleaned_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Données nettoyées sauvegardées dans : {output_file}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return

    # 6. Rapport Console (Comparaison Brut vs Propre)
    try:
        generate_and_print_report(initial_df, stats, cleaned_df)
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du rapport console : {e}")

    # 7. Génération du rapport Markdown final avec CleanerReporter
    try:
        # Création d'un logger simulé pour le reporter (ou utilisation du logger existant)
        logger = logging.getLogger(__name__)
        
        # Génération du rapport final avec les statistiques
        generate_enhanced_report(profiler, logger, reports_dir, input_file, stats)
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du rapport final : {e}")

if __name__ == "__main__":
    main()