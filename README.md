PROJET consistant à créer des outils intéractifs de nettoyage automatique de fichier .CVS, .JSON




"" Arborescense :
```
mon-projet-nettoyage/
├── .venv/                  # Ton environnement virtuel géré par uv
├── data/
│   ├── raw/                # Fichiers CSV/JSON d'origine (non modifiés, "lecture seule")
│   └── processed/          # Fichiers propres générés par tes scripts/agents
├── docs_references/        # Si tu y déposes des PDF ou des schémas de données locaux
├── src/
│   ├── __init__.py
│   ├── cleaner.py          # Le script Python principal de nettoyage
│   └── validator.py        # Le script qui contrôle la conformité des données
├── tests/                  # Pour vérifier que le nettoyage n'a pas cassé les types de données

```