from pathlib import Path
from datetime import datetime
import logging

# Import des modules du projet
from src.file_loader import load_file
from src.cleaner_engine import run_all_cleaning_steps
from src.data_profiler import DataProfiler
from src.cleaner_logger import generate_and_print_report
from src.cleaner_reporter import CleanerReporter, generate_enhanced_report

def main():
    # 1. Configuration (Pathlib pour les chemins robustes sous Windows)
    base_dir = Path(__file__).parent
    input_file = base_dir / "data/raw/reservations_rivage_brut.csv"
    output_file = base_dir / "data/processed/dataset_nettoye.cs2v"
    reports_dir = base_dir / "data/reports"
    
    # On s'assure que les dossiers de sortie existent
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        print(f"❌ Impossible de trouver le fichier d'entrée : {input_file}")
        return

    # 2. Chargement
    try:
        initial_df = load_file(str(input_file))
        print(f"✅ Fichier chargé ({initial_df.shape[0]} lignes, {initial_df.shape[1]} colonnes)")
    except FileNotFoundError:
        print(f"❌ Impossible de charger {input_file}")
        return
    except ValueError as e:
        print(f"❌ Erreur de format : {e}")
        return

    # 3. PROFILAGE (Inséré avant le nettoyage pour avoir une trace fiable)
    try:
        profiler = DataProfiler(initial_df, input_file)
        
        # Interaction utilisateur pour choisir le format du rapport
        print("\n--- 📊 Choix du Format de Rapport ---")
        print("Souhaitez-vous un rapport en format Markdown (.md) ou HTML avec graphiques ?")
        print("1. Markdown (.md)")
        print("2. HTML avec graphiques")
        
        choice = input("Votre choix (1 ou 2) : ").strip()
        
        # Nom du rapport avec timestamp pour éviter l'écrasement
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        if choice == "1":
            report_filename = reports_dir / f"profiling_{input_file.stem}_{timestamp}.md"
            profiler.generate_report(str(report_filename))
            print(f"📊 Rapport Markdown généré : {report_filename}")
        elif choice == "2":
            report_filename = reports_dir / f"profiling_{input_file.stem}_{timestamp}.html"
            profiler.generate_html_report(str(report_filename))
            print(f"📊 Rapport HTML avec graphiques généré : {report_filename}")
        else:
            print("❌ Choix non valide. Génération par défaut en Markdown.")
            report_filename = reports_dir / f"profiling_{input_file.stem}_{timestamp}.md"
            profiler.generate_report(str(report_filename))
            print(f"📊 Rapport Markdown généré : {report_filename}")
            
    except Exception as e:
        print(f"⚠️ Erreur lors du profilage (continuation du pipeline) : {e}")

    # 4. Nettoyage
    try:
        cleaned_df, stats = run_all_cleaning_steps(initial_df.copy())
        print("✅ Nettoyage terminé.")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")
        return

    # 5. Sauvegarde
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        cleaned_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Données propres sauvegardées dans : {output_file}")
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