# 📊 Rapport d'Inspection des Données (2026-08-03)

---

## 🧱 Structure

- **nb_lignes**: 73810
- **nb_colonnes**: 13
- **duplicates_count**: 1447

## 🏷️ Colonnes et Types

| id_reservation | str |
| date_reservation | str |
| date_arrivee | str |
| date_depart | str |
| hotel | str |
| ville | str |
| region | str |
| canal | str |
| nb_nuits | float64 |
| nb_personnes | float64 |
| montant_total | str |
| statut | str |
| --- | --- |
| note_satisfaction | str |

## ⚠️ Valeurs Manquantes

- **region**: 5.06% (3736 lignes)
- **nb_nuits**: 0.48% (356 lignes)
- **nb_personnes**: 3.90% (2877 lignes)
- **montant_total**: 2.47% (1820 lignes)
- **note_satisfaction**: 16.16% (11925 lignes)

## 📈 Statistiques Numériques

|       |   nb_nuits |   nb_personnes |
|:------|-----------:|---------------:|
| count |   73454    |       70933    |
| mean  |       5.07 |           2.37 |
| std   |       2.77 |           5.35 |
| min   |     -12    |           0    |
| 25%   |       3    |           1    |
| 50%   |       5    |           2    |
| 75%   |       7    |           3    |
| max   |      12    |          99    |

## 👀 Aperçu

| id_reservation   | date_reservation   | date_arrivee   | date_depart   | hotel              | ville     | region                     | canal       |   nb_nuits |   nb_personnes |   montant_total | statut    |   note_satisfaction |
|:-----------------|:-------------------|:---------------|:--------------|:-------------------|:----------|:---------------------------|:------------|-----------:|---------------:|----------------:|:----------|--------------------:|
| R43873           | 13/09/2024         | 17/12/2024     | 2024-12-24    | Rivage Bord de Mer | Nice      | Provence-Alpes-Côte d'Azur | Telephone   |          7 |              1 |         1274.52 | ANNULEE   |                 nan |
| R41625           | 24/12/2024         | 19/04/2025     | 24/04/2025    | Rivage Bord de Mer | Nice      | Provence-Alpes-Côte d'Azur | expedia     |          5 |            nan |         -712.36 | realisee  |                   5 |
| R45532           | 29/08/2023         | 16/11/2023     | 20/11/2023    | Rivage Vieux-Port  | Marseille | nan                        | Booking.com |          4 |              2 |          591.4  | ANNULEE   |                   5 |
| R55572           | 18/07/2023         | 21/08/2023     | 2023-08-25    | Rivage Presqu'île  | Lyon      | Auvergne-Rhone-Alpes       | site web    |          4 |              2 |          731.52 | realisee  |                   5 |
| R59416           | 07/09/2024         | 04/01/2025     | 12/01/2025    | Rivage Presqu'île  | Lyon      | Auvergne-Rhône-Alpes       | telephone   |          8 |              2 |         1308.89 | confirmee |                   5 |