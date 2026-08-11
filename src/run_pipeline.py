import sys
from pathlib import Path
from datetime import datetime

# Cela permet à 'from src...' et 'import cleaner_logger' de fonctionner même si on lance ce script depuis l'intérieur de src/
current_dir = Path(__file__).resolve().parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import des modules du projet
from src.file_loader import load_file
from src.cleaner_engine import run_all_cleaning_steps
from src.data_profiler import DataProfiler 
from src.cleaner_logger import generate_and_print_report

def main():
    # 1. Configuration (Pathlib pour les chemins robustes sous Windows)
    # On remonte deux niveaux: un pour sortir de 'src/', un pour sortir du fichier actuel
    base_dir = Path(__file__).parent.parent 
    
    input_file = base_dir / "data/raw/reservations_rivage_brut.csv"
    output_file = base_dir / "data/processed/dataset_nettoye.csv"
    reports_dir = base_dir / "data/reports"
    
    # On s'assure que les dossiers de sortie existent (sécurité)
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
        profiler = DataProfiler(initial_df)
        # Nom du rapport avec timestamp pour éviter l'écrasement
        report_filename = reports_dir / f"profiling_{input_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        profiler.generate_report(str(report_filename))
        print(f"📊 Rapport de profilage généré : {report_filename}")
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

if __name__ == "__main__":
    main()