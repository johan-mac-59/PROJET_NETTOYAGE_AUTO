import pandas as pd

def clean_csv(input_file, output_file):
    # Lire le fichier CSV
    df = pd.read_csv(input_file)
    
    # Nettoyer les données manquantes
    df_cleaned = df.dropna()
    
    # Sauvegarder le fichier nettoyé
    df_cleaned.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_file = "input.csv"
    output_file = "cleaned_output.csv"
    clean_csv(input_file, output_file)