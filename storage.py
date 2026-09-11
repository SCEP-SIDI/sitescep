"""
Module de persistance des données de l'application (version JSON local).

C'est la solution la plus simple et 100 % gratuite : chaque "table"
de données (occupation des chambres, tâches, dépenses, menus) est
stockée dans un petit fichier JSON dans le dossier data/.

LIMITE IMPORTANTE sur Streamlit Community Cloud :
Le système de fichiers d'une app Streamlit Cloud est considéré comme
"éphémère" : il survit généralement tant que l'app tourne, mais peut
être réinitialisé lors d'un redéploiement (git push) ou après une
longue période de mise en veille. Pour une persistance garantie sur
la durée, remplacez ce module par storage_gsheets_example.py (voir
le README) — l'interface (load_json / save_json) est identique, donc
le reste de l'application n'a rien à changer.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _file_path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def load_json(name: str, default):
    """Charge les données stockées sous la clé `name`, ou renvoie `default` si absent/corrompu."""
    path = _file_path(name)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(name: str, data) -> None:
    """Enregistre `data` (dict ou liste) sous la clé `name`."""
    path = _file_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
