"""
=====================================================================
 GESTION DES WEEK-ENDS DE TRAVAUX - APPLICATION WEB (Streamlit)
=====================================================================
Application collaborative accessible en ligne, à héberger gratuitement
sur Streamlit Community Cloud (voir README.md pour le déploiement).

Onglets :
    1. Plan & Hébergements   -> gestion des chambres + sous-onglet plan visuel
    2. Organisation & Tâches -> cocher une tâche l'archive automatiquement
    3. Archives              -> historique par semaine (couplé aux tâches)
    4. Dépenses & Budget     -> structure prête à enrichir
    5. Menus du week-end     -> structure prête à enrichir
    6. Liste de courses      -> nourriture / outils & fournitures

Pour lancer en local :
    pip install -r requirements.txt
    streamlit run app.py
=====================================================================
"""
import re
from html import escape

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
# "coords" et "shape" reprennent la position des chambres telle que
# dessinée dans la version Tkinter ; ils servent ici à générer le
# sous-onglet "Plan visuel".
BUILDINGS = {
    "Maison principale": {
        "Haut": {
            "size": (800, 550),
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
            "size": (800, 300),
            "rooms": [
                {"name": "Chambre de Tom (bas)", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
    },
    "Magnanerie": {
        "Haut": {
            "size": (960, 500),
            "rooms": [
                {"name": "Chambre 3", "capacity": 3, "coords": (73, 55, 330, 395)},
                {"name": "Toilettes", "capacity": None, "coords": (73, 262, 188, 395)},
                {"name": "Chambre 2 (Antoine & Céline)", "capacity": 2, "coords": (330, 55, 593, 395)},
                {"name": "Chambre 1 (Alex & Meg)", "capacity": 3, "coords": (593, 55, 813, 395)},
                {"name": "Escalier", "capacity": None, "coords": (813, 55, 955, 395)},
                {"name": "Couloir", "capacity": None, "coords": (73, 395, 955, 487)},
            ],
        },
        "Bas": {
            "size": (800, 300),
            "rooms": [
                {"name": "Salon en bas", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
    },
    "Clède": {
        "Haut": {
            "size": (800, 300),
            "rooms": [
                {"name": "Clède - Haut", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
        "Bas": {
            "size": (800, 300),
            "rooms": [
                {"name": "Clède - Bas", "capacity": 2, "coords": (280, 60, 520, 240)},
            ],
        },
    },
}

OCCUPATION_KEY = "occupation_hebergement"

COLOR_EMPTY = "#f5f5f5"
COLOR_PARTIAL = "#fff3b0"
COLOR_FULL = "#b7e4a1"
COLOR_NON_SLEEPING = "#e0e0e0"


def room_key(building, floor, room_name):
    return f"{building} | {floor} | {room_name}"


def find_person(occupation, nom):
    """Cherche si une personne (insensible à la casse) est déjà dans une chambre."""
    for key, occupants in occupation.items():
        for n in occupants:
            if n.lower() == nom.lower():
                return key
    return None


def natural_key(s):
    """Clé de tri 'naturelle' pour que 'Semaine 2' passe avant 'Semaine 10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


# ---------------------------------------------------------------
# ONGLET 1 : Plan & Hébergements
# ---------------------------------------------------------------
def render_reset_button_hebergement():
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Réinitialiser l'onglet", key="btn_reset_hebergement"):
            st.session_state["confirm_reset_hebergement"] = True

    if st.session_state.get("confirm_reset_hebergement"):
        st.warning("⚠️ Cette action va vider **toutes** les chambres de **tous** les bâtiments. Confirmez-vous ?")
        c1, c2 = st.columns(2)
        if c1.button("Oui, tout réinitialiser", type="primary", key="confirm_reset_yes"):
            save_json(OCCUPATION_KEY, {})
            st.session_state["confirm_reset_hebergement"] = False
            st.success("Onglet Plan & Hébergements réinitialisé.")
            st.rerun()
        if c2.button("Annuler", key="confirm_reset_no"):
            st.session_state["confirm_reset_hebergement"] = False
            st.rerun()


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


def generate_svg_plan(building, floor, occupation):
    """
    Génère un plan SVG de l'étage, avec les noms des occupants affichés en direct.

    Le SVG est rendu directement dans la page (via st.markdown, pas dans une
    iframe séparée), ce qui permet :
      - un redimensionnement fluide et centré (pas de barre de défilement) ;
      - une compatibilité mode sombre / mode clair, en utilisant la variable
        CSS var(--text-color) que Streamlit met à jour automatiquement selon
        le thème actif (les couleurs de fond des chambres restent volontai-
        rement fixes : elles restent lisibles dans les deux thèmes).
    """
    floor_data = BUILDINGS[building][floor]
    width, height = floor_data["size"]
    rooms = floor_data["rooms"]

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;display:block;font-family:sans-serif;">'
    ]

    for room in rooms:
        x1, y1, x2, y2 = room["coords"]
        w, h = x2 - x1, y2 - y1
        capacity = room["capacity"]

        if capacity is None:
            fill = COLOR_NON_SLEEPING
            occ = []
        else:
            occ = occupation.get(room_key(building, floor, room["name"]), [])
            if len(occ) == 0:
                fill = COLOR_EMPTY
            elif len(occ) >= capacity:
                fill = COLOR_FULL
            else:
                fill = COLOR_PARTIAL

        rx = 20 if room.get("shape") == "round" else 2
        parts.append(
            f'<rect x="{x1}" y="{y1}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="var(--text-color)" stroke-opacity="0.6" stroke-width="2" />'
        )

        cx = x1 + w / 2
        cy = y1 + 22
        parts.append(
            f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="13" font-weight="bold" '
            f'fill="#111">{escape(room["name"])}</text>'
        )

        if capacity is not None:
            parts.append(
                f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" font-size="11" '
                f'fill="#333">({len(occ)}/{capacity})</text>'
            )
            for idx, nom in enumerate(occ):
                parts.append(
                    f'<text x="{cx}" y="{cy + 38 + idx * 16}" text-anchor="middle" font-size="11" '
                    f'fill="#111">{escape(nom)}</text>'
                )

    parts.append("</svg>")
    return "\n".join(parts)


def render_hebergement_tab():
    st.header("🛏️ Plan & Hébergements")
    render_reset_button_hebergement()

    occupation = load_json(OCCUPATION_KEY, {})

    building = st.selectbox("Bâtiment", list(BUILDINGS.keys()), key="building_select")
    floors = BUILDINGS[building]
    floor_names = list(floors.keys())
    floor = st.radio("Étage", floor_names, horizontal=True, key=f"floor_select_{building}") \
        if len(floor_names) > 1 else floor_names[0]

    sub_tab_gestion, sub_tab_plan = st.tabs(["📋 Gestion des chambres", "🗺️ Plan visuel"])

    with sub_tab_gestion:
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

    with sub_tab_plan:
        st.caption("Plan indicatif pour se repérer — les noms et couleurs se mettent à jour automatiquement.")
        st.markdown(
            f"<span style='background:{COLOR_EMPTY};padding:2px 8px;border:1px solid #999;color:#111;'>Vide</span>&nbsp;&nbsp;"
            f"<span style='background:{COLOR_PARTIAL};padding:2px 8px;border:1px solid #999;color:#111;'>Partiel</span>&nbsp;&nbsp;"
            f"<span style='background:{COLOR_FULL};padding:2px 8px;border:1px solid #999;color:#111;'>Complet</span>&nbsp;&nbsp;"
            f"<span style='background:{COLOR_NON_SLEEPING};padding:2px 8px;border:1px solid #999;color:#111;'>Non habitable</span>",
            unsafe_allow_html=True,
        )
        svg = generate_svg_plan(building, floor, occupation)
        # Rendu direct dans la page (pas d'iframe) : centré, largeur adaptative,
        # pas de barre de défilement, et compatible avec le mode sombre.
        st.markdown(
            f'<div style="display:flex;justify-content:center;margin-top:10px;">'
            f'<div style="max-width:900px;width:100%;">{svg}</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------
# ONGLET 2 : Organisation & Tâches chantier (couplé aux Archives)
# ---------------------------------------------------------------
def render_taches_tab():
    st.header("🧰 Organisation & Tâches chantier")
    st.caption("Cochez une tâche terminée : elle est automatiquement déplacée dans l'onglet Archives, "
               "dans la semaine indiquée ci-dessous.")

    config = load_json("config", {})
    semaine_defaut = config.get("semaine_actuelle", "Semaine 1")
    semaine_actuelle = st.text_input("📅 Semaine actuelle (utilisée pour l'archivage automatique)",
                                      value=semaine_defaut)
    if semaine_actuelle != semaine_defaut:
        config["semaine_actuelle"] = semaine_actuelle
        save_json("config", config)

    taches = load_json("taches", [])

    with st.form("form_tache", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        titre = col1.text_input("Nouvelle tâche")
        responsable = col2.text_input("Responsable")
        if st.form_submit_button("➕ Ajouter la tâche") and titre.strip():
            taches.append({"titre": titre.strip(), "responsable": responsable.strip(), "fait": False})
            save_json("taches", taches)
            st.rerun()

    if not taches:
        st.caption("Aucune tâche en cours.")

    for i, tache in enumerate(taches):
        c1, c2, c3 = st.columns([0.5, 3, 0.5])
        fait = c1.checkbox("", value=tache["fait"], key=f"tache_{i}")
        if fait:
            # Archivage automatique dans la semaine en cours, puis retrait de la liste active
            archives = load_json("archives", {})
            archives.setdefault(semaine_actuelle, []).append({
                "titre": tache["titre"],
                "responsable": tache["responsable"],
            })
            save_json("archives", archives)
            taches.pop(i)
            save_json("taches", taches)
            st.rerun()
        texte = tache["titre"] + (f" — *{tache['responsable']}*" if tache["responsable"] else "")
        c2.markdown(texte)
        if c3.button("🗑️", key=f"del_tache_{i}"):
            taches.pop(i)
            save_json("taches", taches)
            st.rerun()


# ---------------------------------------------------------------
# ONGLET 3 : Archives (couplé aux Tâches)
# ---------------------------------------------------------------
def render_archives_tab():
    st.header("🗄️ Archives")
    st.caption("Historique de ce qui a été fait, semaine par semaine. Rempli automatiquement depuis "
               "l'onglet Tâches, ou complétez manuellement ci-dessous.")

    archives = load_json("archives", {})

    with st.expander("➕ Ajouter une entrée manuellement"):
        col1, col2 = st.columns([1, 3])
        semaine_manuel = col1.text_input("Semaine", key="archive_semaine_manuel", placeholder="ex: Semaine 5")
        description_manuel = col2.text_input("Ce qui a été fait", key="archive_desc_manuel",
                                              placeholder="ex: Refait le toit")
        if st.button("Ajouter à l'archive") and semaine_manuel.strip() and description_manuel.strip():
            archives.setdefault(semaine_manuel.strip(), []).append(
                {"titre": description_manuel.strip(), "responsable": ""}
            )
            save_json("archives", archives)
            st.rerun()

    if not archives:
        st.caption("Aucune archive pour le moment.")
        return

    for semaine in sorted(archives.keys(), key=natural_key, reverse=True):
        entries = archives[semaine]
        with st.expander(f"📅 {semaine} ({len(entries)} élément(s))", expanded=False):
            for i, entry in enumerate(entries):
                c1, c2 = st.columns([5, 1])
                texte = entry["titre"] + (f" — *{entry['responsable']}*" if entry.get("responsable") else "")
                c1.markdown(f"✅ {texte}")
                if c2.button("🗑️", key=f"del_archive_{semaine}_{i}"):
                    archives[semaine].pop(i)
                    if not archives[semaine]:
                        del archives[semaine]
                    save_json("archives", archives)
                    st.rerun()


# ---------------------------------------------------------------
# ONGLET 4 : Dépenses & Budget (structure prête)
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
# ONGLET 5 : Menus du week-end (structure prête)
# ---------------------------------------------------------------
def render_menus_tab():
    st.header("🍽️ Menus du week-end")
    st.caption("Complétez chaque repas, et utilisez ⬆️/⬇️ pour les remettre dans le bon ordre "
               "(un repas ajouté apparaît en bas de liste par défaut).")

    menus = load_json("menus", None)
    if menus is None:
        # Première utilisation : liste ordonnée par défaut
        menus = [
            {"nom": "Samedi midi", "texte": ""},
            {"nom": "Samedi soir", "texte": ""},
            {"nom": "Dimanche midi", "texte": ""},
        ]
        save_json("menus", menus)
    elif isinstance(menus, dict):
        # Migration depuis l'ancien format (dict non-ordonnable) vers une liste
        menus = [{"nom": nom, "texte": texte} for nom, texte in menus.items()]
        save_json("menus", menus)

    for i, repas in enumerate(menus):
        c1, c2, c3, c4 = st.columns([0.4, 0.4, 4, 0.4])
        if c1.button("⬆️", key=f"up_menu_{i}", disabled=(i == 0), help="Monter"):
            menus[i - 1], menus[i] = menus[i], menus[i - 1]
            save_json("menus", menus)
            st.rerun()
        if c2.button("⬇️", key=f"down_menu_{i}", disabled=(i == len(menus) - 1), help="Descendre"):
            menus[i + 1], menus[i] = menus[i], menus[i + 1]
            save_json("menus", menus)
            st.rerun()
        with c3:
            nouveau_texte = st.text_area(repas["nom"], value=repas["texte"], key=f"menu_text_{i}")
            if nouveau_texte != repas["texte"]:
                menus[i]["texte"] = nouveau_texte
                save_json("menus", menus)
        if c4.button("🗑️", key=f"del_menu_{i}", help="Supprimer ce repas"):
            menus.pop(i)
            save_json("menus", menus)
            st.rerun()

    st.divider()
    with st.form("form_add_menu", clear_on_submit=True):
        nouveau_nom = st.text_input("Ajouter un repas (ex : Vendredi soir)")
        if st.form_submit_button("➕ Ajouter en fin de liste") and nouveau_nom.strip():
            menus.append({"nom": nouveau_nom.strip(), "texte": ""})
            save_json("menus", menus)
            st.rerun()


# ---------------------------------------------------------------
# ONGLET 6 : Liste de courses (Nourriture / Outils & fournitures)
# ---------------------------------------------------------------
def render_liste_courses(cle, titre):
    st.subheader(titre)
    items = load_json(f"courses_{cle}", [])

    with st.form(f"form_course_{cle}", clear_on_submit=True):
        nouvel_item = st.text_input("Ajouter un article", key=f"input_course_{cle}",
                                     label_visibility="collapsed", placeholder="Article à ajouter...")
        if st.form_submit_button("➕ Ajouter") and nouvel_item.strip():
            items.append({"nom": nouvel_item.strip(), "achete": False})
            save_json(f"courses_{cle}", items)
            st.rerun()

    for i, item in enumerate(items):
        c1, c2 = st.columns([4, 1])
        achete = c1.checkbox(item["nom"], value=item["achete"], key=f"course_{cle}_{i}")
        if achete != item["achete"]:
            items[i]["achete"] = achete
            save_json(f"courses_{cle}", items)
            st.rerun()
        if c2.button("🗑️", key=f"del_course_{cle}_{i}"):
            items.pop(i)
            save_json(f"courses_{cle}", items)
            st.rerun()

    if not items:
        st.caption("Liste vide.")
    else:
        restants = sum(1 for it in items if not it["achete"])
        st.caption(f"{restants} article(s) restant(s) sur {len(items)}.")


def render_courses_tab():
    st.header("🛒 Liste de courses")
    st.caption("Séparez nourriture et outils/fournitures. Cochez au fur et à mesure des achats.")

    col1, col2 = st.columns(2)
    with col1:
        render_liste_courses("nourriture", "🍞 Nourriture")
    with col2:
        render_liste_courses("fournitures", "🔧 Outils & fournitures")


# ---------------------------------------------------------------
# NAVIGATION PRINCIPALE
# ---------------------------------------------------------------
st.title("🏠 Gestion des week-ends de travaux")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛏️ Plan & Hébergements",
    "🧰 Organisation & Tâches",
    "🗄️ Archives",
    "💶 Dépenses & Budget",
    "🍽️ Menus du week-end",
    "🛒 Liste de courses",
])

with tab1:
    render_hebergement_tab()
with tab2:
    render_taches_tab()
with tab3:
    render_archives_tab()
with tab4:
    render_budget_tab()
with tab5:
    render_menus_tab()
with tab6:
    render_courses_tab()
