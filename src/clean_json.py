import json

def clean_json(input_file, output_file):
    # Lire le fichier JSON
    with open(input_file, 'r') as file:
        data = json.load(file)
    
    # Nettoyer les données manquantes
    cleaned_data = {k: v for k, v in data.items() if pd.notna(v)}
    
    # Sauvegarder le fichier nettoyé
    with open(output_file, 'w') as file:
        json.dump(cleaned_data, file, indent=4)

if __name__ == "__main__":
    input_file = "input.json"
    output_file = "cleaned_output.json"
    clean_json(input_file, output_file)