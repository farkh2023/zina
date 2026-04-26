# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal workspace containing multiple independent projects, primarily focused on cryptocurrency market analysis with machine learning. Projects are not connected to each other and each manages its own Python virtual environment.

Both Python projects run on **Python 3.13**.

## Règle absolue — Environnements Python

**Ne jamais créer ni utiliser un `.venv` dans OneDrive.** OneDrive peut passer les fichiers en mode cloud-only et rendre les exécutables inaccessibles.

- Garder dans OneDrive : code source, données, `requirements.txt` uniquement.
- Toujours créer les environnements hors OneDrive, sous `C:\Users\Youss\venvs\`.
- Toujours recréer un environnement depuis `requirements.txt` si absent.

Les anciens `.venv` présents dans les dossiers de projet OneDrive sont à ignorer.

## Active Projects

### IA_recolts_Donne — Data Collection
Downloads and stores cryptocurrency market data from external APIs. Uses **Jupyter** (`ipykernel`, `jupyter_client`, `IPython`) — scripts can be run directly or through VS Code's Jupyter integration.

- `recherche_cryptos.py` — searches/lists available cryptocurrencies
- `telecharg_donnee.py` — downloads crypto OHLCV data
- `telecharg_limitPlagedata.py` — downloads data over a specific date range
- `telecharg_liste.py` — batch download for a list of cryptos
- `Charg_fichierjson.py` / `Charg_json_Complex.py` — load and parse saved JSON data
- `Donnees_pieces_ID/` — per-coin stored data files (`BITCOIN/` subfolder present)
- Output: XLSX and JSON files (`tredingcoins.xlsx`, `tredingcoins.json`, etc.)

### IA_analyse_marche_crypto — Market Analysis & ML
Processes collected data. Contains a `modele_LSTM/` directory and a `Collecte_des_donnees_historiques/` directory, both currently **empty**. The ML layer (TensorFlow/Keras) is not yet installed.

- `cryptolist.py` — manages the list of tracked coins (`cryptos.txt`)
- `Automatisation.py` — orchestrates the full data-to-model pipeline (main entry point)
- `données histo.py` — loads and processes historical price data
- `Données de Masse.py` — bulk data processing
- `Données en Temps Réel.py` — real-time data ingestion
- `Extraction_type-donne.py` / `Extraction_boucleDonne.py` — feature extraction utilities
- `charg_json_verif.py` / `charg_verif_convervonplex.py` — JSON loading with validation
- Output: `dogecoin_historical_data.csv`, `bitcoin.json`, `tredingcoins.xlsx`

### outils_devloppeur — Developer Tools UI
A standalone HTML/CSS/JS interface with video assets. No build step required — open directly in browser.

### appliweb — Web Application
SCSS-based web app. Requires compiling SCSS to CSS using the bundled Dart Sass compiler:
```bash
.\dart-sass-1.56.1-windows-x64\sass.exe appliweb\assets\scss\main.scss appliweb\public\css\styles.css
```

## Python Environment Setup

Les environnements valides sont situés **hors OneDrive**, dans `C:\Users\Youss\venvs\` :

| Projet | Environnement |
|---|---|
| `IA_recolts_Donne` | `C:\Users\Youss\venvs\IA_recolts_Donne` |
| `IA_analyse_marche_crypto` | `C:\Users\Youss\venvs\IA_analyse_marche_crypto` |

Pour recréer un environnement depuis zéro :

```powershell
# IA_recolts_Donne
python -m venv C:\Users\Youss\venvs\IA_recolts_Donne
& "C:\Users\Youss\venvs\IA_recolts_Donne\Scripts\pip.exe" install -r "C:\Users\Youss\OneDrive\IA_JORD\IAjord_MARCHE\SAUV_onedriveyoussef2023\Bureau\IA_recolts_Donne\requirements.txt"

# IA_analyse_marche_crypto
python -m venv C:\Users\Youss\venvs\IA_analyse_marche_crypto
& "C:\Users\Youss\venvs\IA_analyse_marche_crypto\Scripts\pip.exe" install -r "C:\Users\Youss\OneDrive\IA_JORD\IAjord_MARCHE\SAUV_onedriveyoussef2023\Bureau\IA_analyse_marche_crypto\requirements.txt"
```

## Data Flow Architecture

The two main Python projects form a pipeline:

```
IA_recolts_Donne  →  downloads raw data  →  XLSX/JSON files
        ↓
IA_analyse_marche_crypto  →  loads files  →  feature extraction  →  (LSTM — not yet implemented)
```

`Automatisation.py` is the entry point for the analysis pipeline. The coin list tracked by both projects comes from `cryptos.txt` (managed by `cryptolist.py`).

## Running the Projects

### Verify environments (imports)
```powershell
# IA_recolts_Donne
& "C:\Users\Youss\venvs\IA_recolts_Donne\Scripts\python.exe" -c "import pandas, numpy, requests, openpyxl, matplotlib, IPython; print('IA_recolts_Donne OK')"

# IA_analyse_marche_crypto
& "C:\Users\Youss\venvs\IA_analyse_marche_crypto\Scripts\python.exe" -c "import pandas, numpy, requests, openpyxl; print('IA_analyse_marche_crypto OK')"
```

### Run main scripts
```powershell
$base = "C:\Users\Youss\OneDrive\IA_JORD\IAjord_MARCHE\SAUV_onedriveyoussef2023\Bureau"

# Data collection — search available coins
& "C:\Users\Youss\venvs\IA_recolts_Donne\Scripts\python.exe" "$base\IA_recolts_Donne\recherche_cryptos.py"

# Data collection — download OHLCV data
& "C:\Users\Youss\venvs\IA_recolts_Donne\Scripts\python.exe" "$base\IA_recolts_Donne\telecharg_donnee.py"

# Analysis pipeline
& "C:\Users\Youss\venvs\IA_analyse_marche_crypto\Scripts\python.exe" "$base\IA_analyse_marche_crypto\Automatisation.py"
```

## Tests

There are **no automated tests** in these projects. Verification is done by running scripts directly and checking output files.

## IA_googleCloud

This directory contains a clone of the `google-cloud-python` monorepo. It is not an original project. Each package under `IA_googleCloud/google-cloud-python/packages/` follows the standard Google Cloud Python library structure with `nox` for testing:

```bash
cd IA_googleCloud/google-cloud-python/packages/<package-name>
pip install nox
nox -s unit       # run unit tests
nox -s lint       # run flake8 linting
```
