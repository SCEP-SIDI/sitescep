"""
Module de persistance ALTERNATIF utilisant Google Sheets.

A utiliser à la place de storage.py si vous voulez une persistance
garantie sur le long terme (recommandé dès que plusieurs amis
utilisent l'app régulièrement).

MISE EN PLACE (voir aussi le README.md fourni) :
1. pip install streamlit-gsheets   (déjà dans requirements.txt si vous
   décommentez la ligne correspondante)
2. Créer un compte de service Google Cloud + activer l'API Google Sheets
   et Google Drive, télécharger la clé JSON du compte de service.
3. Créer un Google Sheet, le partager (droits "Editeur") avec l'adresse
   e-mail du compte de service (ex: xxx@xxx.iam.gserviceaccount.com).
4. Renseigner les identifiants dans .streamlit/secrets.toml en local,
   et dans "Secrets" sur Streamlit Community Cloud pour la version en ligne.
5. Dans app.py, remplacer :
       from storage import load_json, save_json
   par :
       from storage_gsheets_example import load_json, save_json

Chaque "table" (occupation_hebergement, taches, depenses, menus) est
stockée dans un onglet (worksheet) distinct du même Google Sheet, sous
forme d'une unique cellule contenant le JSON complet — le plus simple
et le plus robuste pour ce cas d'usage.
"""
import json

import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)


def load_json(name: str, default):
    try:
        df = conn.read(worksheet=name, ttl=0)  # ttl=0 : toujours relire, pas de cache
        if df.empty:
            return default
        return json.loads(df.iloc[0, 0])
    except Exception:
        return default


def save_json(name: str, data) -> None:
    import pandas as pd
    df = pd.DataFrame({"data": [json.dumps(data, ensure_ascii=False)]})
    conn.update(worksheet=name, data=df)
