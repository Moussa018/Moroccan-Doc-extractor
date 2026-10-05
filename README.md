# Moroccan-Doc-extractor

Extraction de champs structurés (JSON) à partir d'images de documents marocains.
Pour l'instant : permis de conduire (données synthétiques).

## Pipeline

```
image ──► OCR (RapidOCR) ──► lignes {text, score, box} ──► parseur (config JSON) ──► champs
```

## Installation

```bash
pip install -r requirements.txt
playwright install chromium   # uniquement pour générer les données
```

## Utilisation

```bash
# Générer 20 permis synthétiques (images + labels)
python data/generate_license.py 20

# Extraire les champs d'une image
python src/cli.py data/synthetic/license/images/000000.png
python src/cli.py image.png --raw                    # texte OCR brut
python src/cli.py image.png --config configs/x.json  # autre type de document

# Évaluer l'OCR (exact match + CER par champ)
python eval/eval_ocr.py
```

Exemple de sortie :

```json
{
  "surname": "BERRADA",
  "given_name": "Salma",
  "dob": "24/10/1998",
  "pob": "Oujda",
  "issue_date": "08/05/2023",
  "expiry_date": "07/05/2033",
  "license_no": "SP-88616634",
  "categories": "B, C"
}
```

## Structure

| Chemin | Rôle |
|---|---|
| `data/generate_license.py` | Génère les images et les labels (valeurs et boîtes) |
| `src/ocr/rapid_engine.py` | `OCREngine.read(image)` → lignes de texte avec boîtes |
| `src/parsing/parser.py` | `parse(lines, config)` : trouve chaque libellé et lit la valeur en dessous |
| `configs/license.json` | Configuration du parseur pour les permis |
| `src/cli.py` | Ligne de commande : OCR puis parsing, sortie JSON |
| `eval/eval_ocr.py` | Évaluation face aux labels |

## Configurer le parseur

Un type de document = un fichier JSON dans `configs/` (voir `configs/license.json`) : pour chaque champ, les mots-clés de son libellé et, si besoin, une regex.

## Limites actuelles

- Données synthétiques uniquement ; pas encore testé sur de vrais documents.
- L'éval lit les champs avec les boîtes des labels et ne passe pas encore par le parseur.
- Pas d'arabe (le modèle RapidOCR par défaut lit le latin et le chinois).
