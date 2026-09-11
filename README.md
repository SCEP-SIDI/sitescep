# Gestion des week-ends de travaux — Application web

Application Streamlit collaborative pour gérer les hébergements, les
tâches, le budget et les menus de vos week-ends de travaux.

## Fichiers du projet

```
streamlit_app/
├── app.py                        # Application principale (4 onglets)
├── storage.py                    # Persistance JSON locale (par défaut)
├── storage_gsheets_example.py    # Persistance Google Sheets (optionnelle)
├── requirements.txt              # Dépendances Python
└── data/                         # Fichiers JSON créés automatiquement
```

## 1. Tester en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Une page s'ouvre dans votre navigateur à l'adresse `http://localhost:8501`.

## 2. Créer le dépôt GitHub

1. Créez un compte sur [github.com](https://github.com) si vous n'en avez pas.
2. Cliquez sur **New repository** (bouton vert "New").
3. Donnez-lui un nom, par exemple `weekend-chantier`. Laissez-le en **Public**
   (nécessaire pour le plan gratuit de Streamlit Cloud, sauf si vous
   avez un compte GitHub payant permettant les dépôts privés connectés).
4. Ne cochez rien d'autre (pas de README auto), cliquez sur **Create repository**.

Ensuite, depuis le dossier `streamlit_app` sur votre ordinateur :

```bash
git init
git add .
git commit -m "Première version de l'application"
git branch -M main
git remote add origin https://github.com/VOTRE_UTILISATEUR/weekend-chantier.git
git push -u origin main
```

(Remplacez `VOTRE_UTILISATEUR` par votre nom d'utilisateur GitHub.)

> 💡 Pensez à ajouter un fichier `.gitignore` avec `data/` si vous ne
> voulez pas versionner les données de test, ou laissez-le tel quel si
> vous préférez garder un historique des fichiers JSON.

## 3. Déployer sur Streamlit Community Cloud (gratuit)

1. Allez sur [share.streamlit.io](https://share.streamlit.io).
2. Connectez-vous avec votre compte GitHub (bouton "Continue with GitHub").
3. Cliquez sur **"New app"**.
4. Sélectionnez :
   - **Repository** : `VOTRE_UTILISATEUR/weekend-chantier`
   - **Branch** : `main`
   - **Main file path** : `app.py`
5. Cliquez sur **"Deploy"**.

Après une à deux minutes, votre application est en ligne avec une URL du type :
```
https://weekend-chantier-xxxxx.streamlit.app
```

Partagez ce lien avec vos amis : ils pourront l'ouvrir depuis n'importe
quel navigateur (ordinateur ou téléphone), sans rien installer.

## 4. Mettre à jour l'application

À chaque fois que vous modifiez le code localement :

```bash
git add .
git commit -m "Description du changement"
git push
```

Streamlit Cloud redéploie automatiquement l'application en quelques
secondes après chaque `git push`.

## 5. (Optionnel) Activer la persistance Google Sheets

Le stockage JSON local fonctionne bien pour commencer, mais les
données peuvent être réinitialisées si l'application redémarre après
une longue période d'inactivité. Pour une persistance garantie :

1. Allez sur [console.cloud.google.com](https://console.cloud.google.com),
   créez un projet, puis activez les API **Google Sheets API** et
   **Google Drive API**.
2. Dans "IAM et administration" → "Comptes de service", créez un
   compte de service, puis générez une clé JSON.
3. Créez un Google Sheet, et partagez-le (droits "Editeur") avec
   l'adresse e-mail du compte de service (visible dans la clé JSON,
   du type `xxx@xxx.iam.gserviceaccount.com`).
4. En local, créez le fichier `.streamlit/secrets.toml` avec le
   contenu de la clé JSON, au format attendu par `streamlit-gsheets`
   (voir la [documentation officielle](https://docs.streamlit.io/develop/tutorials/databases/private-gsheet)).
5. Sur Streamlit Community Cloud, ouvrez les paramètres de votre
   application → **"Secrets"**, et collez-y le même contenu.
6. Dans `requirements.txt`, décommentez la ligne `streamlit-gsheets`.
7. Dans `app.py`, remplacez :
   ```python
   from storage import load_json, save_json
   ```
   par :
   ```python
   from storage_gsheets_example import load_json, save_json
   ```
8. `git add . && git commit -m "Activation Google Sheets" && git push`

Vos données seront désormais stockées de façon permanente dans le
Google Sheet, consultable/éditable aussi manuellement si besoin.

## Notes

- L'application est collaborative "en temps quasi réel" : chaque
  action (ajout/suppression) est immédiatement enregistrée et visible
  par les autres au prochain rafraîchissement de leur page.
- Les onglets "Tâches", "Budget" et "Menus" sont volontairement
  simples pour l'instant — la structure (formulaires, tableaux,
  sauvegarde) est prête à être enrichie selon vos besoins.
