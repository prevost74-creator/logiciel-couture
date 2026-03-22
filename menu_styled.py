from pathlib import Path
from urllib.parse import quote, unquote
import streamlit as st

import tissus_styled as tissus
import accessoires_styled as accessoires
import creations_styled as creations
import dashboard_styled as dashboard
import ventes_styled as ventes

from init_db import initialiser_bdd
from style import appliquer_style_global, afficher_entete


BASE_DIR = Path(__file__).resolve().parent

LOGO_PATH = BASE_DIR / "LOGO 2.png"
IMG_STOCK = BASE_DIR / "photo home stock.png"
IMG_TISSU = BASE_DIR / "photo home tissu.png"
IMG_ACCESSOIRE = BASE_DIR / "photo home accessoire.png"
IMG_CREATION = BASE_DIR / "photo home création.jpg"
IMG_VENTE = BASE_DIR / "photo home vente.png"

PAGES = {
    "Home": "Accueil",
    "Mon suivi des stocks": "Mon suivi des stocks",
    "Mes Tissus": "Mes tissus",
    "Mes Accessoires": "Mes accessoires",
    "Mes Créations": "Mes créations",
    "Mes ventes": "Mes ventes",
}


st.set_page_config(
    page_title="Les Créations de Plumette",
    page_icon="🧵",
    layout="wide"
)

initialiser_bdd()
appliquer_style_global()


def changer_page(page: str):
    st.session_state["page_active"] = page
    st.query_params["page"] = page


def lire_page_depuis_url():
    page_url = st.query_params.get("page", "Home")

    if isinstance(page_url, list):
        page_url = page_url[0] if page_url else "Home"

    page_url = unquote(str(page_url))

    if page_url in PAGES:
        st.session_state["page_active"] = page_url
    else:
        st.session_state["page_active"] = "Home"


def afficher_image_si_existe(path: Path, message: str):
    if path.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(path), use_container_width=True)
    else:
        st.warning(message)


def carte_home(image_path: Path, titre: str, page_cible: str):
    page_url = quote(page_cible)

    st.markdown('<div class="plumette-home-card">', unsafe_allow_html=True)
    afficher_image_si_existe(image_path, f"Image introuvable : {image_path.name}")

    st.markdown(
        f"""
        <div class="plumette-home-card-title">
            <a href="?page={page_url}" target="_self" class="plumette-home-link">{titre}</a>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)


if "page_active" not in st.session_state:
    st.session_state["page_active"] = "Home"

lire_page_depuis_url()


# Sidebar
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)

st.sidebar.markdown("## Navigation")

for page_key, label in PAGES.items():
    if st.sidebar.button(label, use_container_width=True):
        changer_page(page_key)
        st.rerun()


page = st.session_state["page_active"]


if page == "Home":
    afficher_entete(None, "Accueil", "")

    col1, col2 = st.columns(2)

    with col1:
        carte_home(IMG_STOCK, "Mon suivi des stocks", "Mon suivi des stocks")
        carte_home(IMG_TISSU, "Mes tissus", "Mes Tissus")
        carte_home(IMG_CREATION, "Mes créations", "Mes Créations")

    with col2:
        carte_home(IMG_ACCESSOIRE, "Mes accessoires", "Mes Accessoires")
        carte_home(IMG_VENTE, "Mes ventes", "Mes ventes")

elif page == "Mon suivi des stocks":
    afficher_entete(None, "Mon suivi des stocks","")
    afficher_image_si_existe(IMG_STOCK, "Image stock introuvable")
    dashboard.afficher_page()

elif page == "Mes Tissus":
    afficher_entete(None, "Mes tissus","")
    afficher_image_si_existe(IMG_TISSU, "Image tissu introuvable")
    tissus.afficher_page()

elif page == "Mes Accessoires":
    afficher_entete(None, "Mes accessoires","")
    afficher_image_si_existe(IMG_ACCESSOIRE, "Image accessoire introuvable")
    accessoires.afficher_page()

elif page == "Mes Créations":
    afficher_entete(None, "Mes créations","")
    afficher_image_si_existe(IMG_CREATION, "Image création introuvable")
    creations.afficher_page()

elif page == "Mes ventes":
    afficher_entete(None, "Mes ventes","")
    afficher_image_si_existe(IMG_VENTE, "Image vente introuvable")
    ventes.afficher_page()