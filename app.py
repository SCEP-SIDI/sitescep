"""
=====================================================================
 GESTION DES WEEK-ENDS DE TRAVAUX - APPLICATION WEB (Streamlit)
=====================================================================
Application collaborative accessible en ligne, à héberger gratuitement
sur Streamlit Community Cloud (voir README.md pour le déploiement).

Onglets :
    1. Plan & Hébergements        -> reprise du système de chambres
    2. Organisation & Tâches      -> structure prête à enrichir
    3. Dépenses & Budget          -> structure prête à enrichir
    4. Menus du week-end          -> structure prête à enrichir

Pour lancer en local :
    pip install -r requirements.txt
    streamlit run app.py
=====================================================================
"""
import pandas as pd
import streamlit as st

# Pour activer la persistance Google Sheets à la place du JSON local,
# remplacez la ligne ci-dessous par :
#   from storage_gsheets_example import load_json, save_json
from storage import load_json, save_json

st.set_page_config(page_title="Week-ends Chantier", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------
# 1. CONFIGURATION DES BATIMENTS (reprise exacte de la version Tkinter)
# ---------------------------------------------------------------
# NB : "coords" et "shape" sont conservés (héritage de la version avec
# plans dessinés) mais non utilisés dans cette interface web ; ils
# pourront resservir si vous ajoutez un jour une vue "plan visuel".
BUILDINGS = {
    "Maison principale": {
        "Haut": {
            "rooms": [
                {"name": "Chambre orel clem", "capacity": 2, "coords": (18, 118, 283, 238)},
                {"name": "Chambre supp", "capacity": 2, "coords": (298, 118, 543, 238)},
                {"name": "Toilettes", "capacity": None, "coords": (558, 118, 643, 233)},
                {"name": "Salle de bain", "capacity": None, "coords": (18, 253, 403, 333)},
                {"name": "Chambre flo", "capacity": 4, "coords": (18, 353, 403, 463)},
                {"name": "Escaliers", "capacity": None, "coords": (528, 288, 643, 478), "shape": "round"},
            ],
        },
        "Bas": {
            "rooms": [
                {"name": "Chambre de tom (bas)", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
    },
    "Magnanerie": {
        "Haut": {
            "rooms": [
                {"name": "Chambre 3 ", "capacity": 3, "coords": (73, 55, 330, 395)},
                {"name": "Toilettes", "capacity": None, "coords": (73, 262, 188, 395)},
                {"name": "Chambre 2 (Antoine & Céline)", "capacity": 2, "coords": (330, 55, 593, 395)},
                {"name": "Chambre 1 (Alex & Meg)", "capacity": 3, "coords": (593, 55, 813, 395)},
                {"name": "Escalier", "capacity": None, "coords": (813, 55, 955, 395)},
                {"name": "Couloir", "capacity": None, "coords": (73, 395, 955, 487)},
            ],
        },
        "Bas": {
            "rooms": [
                {"name": "Salon en bas", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
    },
    "Clède": {
        "Haut": {
            "rooms": [
                {"name": "Clède - Haut", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
        "Bas": {
            "rooms": [
                {"name": "Clède - Bas", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
    },
}

OCCUPATION_KEY = "occupation_hebergement"


def room_key(building, floor, room_name):
    return f"{building} | {floor} | {room_name}"


def find_person(occupation, nom):
    """Cherche si une personne (insensible à la casse) est déjà dans une chambre."""
    for key, occupants in occupation.items():
        for n in occupants:
            if n.lower() == nom.lower():
                return key
    return None


# ---------------------------------------------------------------
# ONGLET 1 : Plan & Hébergements
# ---------------------------------------------------------------
def render_room_card(building, floor, room, occupation):
    key = room_key(building, floor, room["name"])
    occupants = occupation.get(key, [])
    capacity = room["capacity"]

    with st.container(border=True):
        st.markdown(f"**{room['name']}**")
        ratio = (len(occupants) / capacity) if capacity else 0
        st.progress(min(ratio, 1.0), text=f"{len(occupants)} / {capacity} places")

        if occupants:
            for nom in occupants:
                c1, c2 = st.columns([4, 1])
                c1.write(f"👤 {nom}")
                if c2.button("❌", key=f"remove_{key}_{nom}", help=f"Retirer {nom}"):
                    occupation[key].remove(nom)
                    save_json(OCCUPATION_KEY, occupation)
                    st.rerun()
        else:
            st.caption("Chambre vide")

        if len(occupants) < capacity:
            with st.form(key=f"form_{key}", clear_on_submit=True):
                nom = st.text_input("Ajouter un prénom", key=f"input_{key}", label_visibility="collapsed",
                                     placeholder="Prénom à ajouter...")
                submitted = st.form_submit_button("➕ Ajouter")
                if submitted and nom.strip():
                    nom_propre = nom.strip()
                    existing = find_person(occupation, nom_propre)
                    if existing and existing != key:
                        st.error(
                            f"{nom_propre} est déjà dans « {existing.split(' | ')[-1]} ». "
                            "Retirez-le d'abord de cette chambre pour le déplacer ici."
                        )
                    else:
                        occupation.setdefault(key, []).append(nom_propre)
                        save_json(OCCUPATION_KEY, occupation)
                        st.rerun()
        else:
            st.success("✅ Chambre complète")


def render_overview(occupation):
    st.subheader("📊 Vue d'ensemble de la propriété")
    total_cap, total_occ = 0, 0
    rows = []
    for building, floors in BUILDINGS.items():
        for floor, floor_data in floors.items():
            for room in floor_data["rooms"]:
                if room["capacity"] is None:
                    continue
                key = room_key(building, floor, room["name"])
                occ = occupation.get(key, [])
                total_cap += room["capacity"]
                total_occ += len(occ)
                rows.append({
                    "Bâtiment": building,
                    "Étage": floor,
                    "Chambre": room["name"],
                    "Occupants": ", ".join(occ) if occ else "—",
                    "Places": f"{len(occ)}/{room['capacity']}",
                })
    st.metric("Total logé sur la propriété", f"{total_occ} / {total_cap}")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_hebergement_tab():
    st.header("🛏️ Plan & Hébergements")
    occupation = load_json(OCCUPATION_KEY, {})

    building = st.selectbox("Bâtiment", list(BUILDINGS.keys()), key="building_select")
    floors = BUILDINGS[building]
    floor_names = list(floors.keys())
    floor = st.radio("Étage", floor_names, horizontal=True, key=f"floor_select_{building}") \
        if len(floor_names) > 1 else floor_names[0]

    rooms = floors[floor]["rooms"]
    sleeping_rooms = [r for r in rooms if r["capacity"] is not None]
    other_rooms = [r for r in rooms if r["capacity"] is None]

    total_cap = sum(r["capacity"] for r in sleeping_rooms)
    total_occ = sum(len(occupation.get(room_key(building, floor, r["name"]), [])) for r in sleeping_rooms)
    complet = " ✅ complet" if total_cap and total_occ >= total_cap else ""
    st.caption(f"**{floor}** — {total_occ} / {total_cap} places occupées{complet}")

    cols = st.columns(2)
    for i, room in enumerate(sleeping_rooms):
        with cols[i % 2]:
            render_room_card(building, floor, room, occupation)

    if other_rooms:
        st.caption("Autres pièces (non habitables) : " + ", ".join(r["name"] for r in other_rooms))

    st.divider()
    render_overview(occupation)


# ---------------------------------------------------------------
# ONGLET 2 : Organisation & Tâches chantier (structure prête)
# ---------------------------------------------------------------
def render_taches_tab():
    st.header("🧰 Organisation & Tâches chantier")
    st.caption("Structure prête à accueillir vos tâches — ajoutez, cochez, supprimez.")

    taches = load_json("taches", [])

    with st.form("form_tache", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        titre = col1.text_input("Nouvelle tâche")
        responsable = col2.text_input("Responsable")
        if st.form_submit_button("➕ Ajouter la tâche") and titre.strip():
            taches.append({"titre": titre.strip(), "responsable": responsable.strip(), "fait": False})
            save_json("taches", taches)
            st.rerun()

    for i, tache in enumerate(taches):
        c1, c2, c3 = st.columns([0.5, 3, 0.5])
        fait = c1.checkbox("", value=tache["fait"], key=f"tache_{i}")
        if fait != tache["fait"]:
            taches[i]["fait"] = fait
            save_json("taches", taches)
            st.rerun()
        texte = tache["titre"] + (f" — *{tache['responsable']}*" if tache["responsable"] else "")
        c2.markdown(f"~~{texte}~~" if fait else texte)
        if c3.button("🗑️", key=f"del_tache_{i}"):
            taches.pop(i)
            save_json("taches", taches)
            st.rerun()

    if not taches:
        st.caption("Aucune tâche pour le moment.")


# ---------------------------------------------------------------
# ONGLET 3 : Dépenses & Budget (structure prête)
# ---------------------------------------------------------------
def render_budget_tab():
    st.header("💶 Dépenses & Budget")
    st.caption("Structure prête pour le suivi du budget — ajoutez vos lignes ci-dessous puis enregistrez.")

    depenses = load_json("depenses", [])
    df = pd.DataFrame(depenses) if depenses else pd.DataFrame(columns=["Description", "Montant (€)", "Payé par"])

    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="budget_editor")

    if st.button("💾 Enregistrer le budget"):
        save_json("depenses", edited.fillna("").to_dict(orient="records"))
        st.success("Budget enregistré.")

    if not edited.empty and "Montant (€)" in edited.columns:
        total = pd.to_numeric(edited["Montant (€)"], errors="coerce").fillna(0).sum()
        st.metric("Total des dépenses", f"{total:.2f} €")


# ---------------------------------------------------------------
# ONGLET 4 : Menus du week-end (structure prête)
# ---------------------------------------------------------------
def render_menus_tab():
    st.header("🍽️ Menus du week-end")
    st.caption("Structure prête pour organiser les repas — complétez et enregistrez.")

    menus = load_json("menus", {"Samedi midi": "", "Samedi soir": "", "Dimanche midi": ""})

    for repas in list(menus.keys()):
        menus[repas] = st.text_area(repas, value=menus[repas], key=f"menu_{repas}")

    nouveau = st.text_input("Ajouter un repas (ex : Dimanche soir)")
    col1, col2 = st.columns(2)
    if col1.button("➕ Ajouter ce repas") and nouveau.strip():
        menus[nouveau.strip()] = ""
        save_json("menus", menus)
        st.rerun()
    if col2.button("💾 Enregistrer les menus"):
        save_json("menus", menus)
        st.success("Menus enregistrés.")


# ---------------------------------------------------------------
# NAVIGATION PRINCIPALE
# ---------------------------------------------------------------
st.title("🏠 Gestion des week-ends de travaux")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛏️ Plan & Hébergements",
    "🧰 Organisation & Tâches",
    "💶 Dépenses & Budget",
    "🍽️ Menus du week-end",
])

with tab1:
    render_hebergement_tab()
with tab2:
    render_taches_tab()
with tab3:
    render_budget_tab()
with tab4:
    render_menus_tab()
