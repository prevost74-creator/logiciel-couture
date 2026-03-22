import streamlit as st
import base64
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def image_to_base64(path):
    path = Path(path)
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def appliquer_style_global():
    st.markdown("""
    <style>
    /* -----------------------------
       Base générale
    ----------------------------- */
    .stApp {
        background-color: #F7F2E8;
        color: #4F3A3A;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", sans-serif;
    }

    /* -----------------------------
       Sidebar
    ----------------------------- */
    section[data-testid="stSidebar"] {
        background-color: #8E4D4D;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] * {
        color: #F8F1E7 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.12);
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        background: rgba(255,255,255,0.04);
        color: #F8F1E7 !important;
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 16px;
        text-align: left;
        padding: 0.85rem 1rem;
        font-weight: 500;
        font-size: 17px;
        margin-bottom: 0.45rem;
        box-shadow: none;
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.10);
        border-color: #D4B062;
        color: #FFF8E8 !important;
        transform: translateX(2px);
    }

    section[data-testid="stSidebar"] .stButton > button:focus:not(:active) {
        border-color: #D4B062 !important;
        box-shadow: 0 0 0 1px #D4B062 !important;
    }

    /* -----------------------------
       Titres
    ----------------------------- */
    h1, h2, h3 {
        color: #C9A55B !important;
        font-family: "Georgia", serif;
        font-weight: 500;
    }

    .plumette-title {
        text-align: center;
        font-size: 54px;
        color: #C9A55B;
        font-family: "Georgia", serif;
        margin-top: 10px;
        margin-bottom: 8px;
        line-height: 1.1;
    }

    .plumette-subtitle {
        text-align: center;
        color: #8E4D4D;
        font-size: 18px;
        margin-bottom: 24px;
    }

    .section-title {
        color: #8E4D4D;
        font-size: 28px;
        font-family: "Georgia", serif;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .mini-separator {
        height: 2px;
        background: linear-gradient(to right, transparent, #C9A55B, transparent);
        border-radius: 999px;
        margin: 12px 0 24px 0;
    }

    /* -----------------------------
       Cartes générales
    ----------------------------- */
    .plumette-card {
        background: rgba(255,255,255,0.72);
        border: 1px solid #E2D3B0;
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 4px 18px rgba(90, 60, 60, 0.08);
        margin-bottom: 18px;
    }

    /* -----------------------------
       Cartes Home
    ----------------------------- */
    .plumette-home-card {
        background: rgba(255,255,255,0.55);
        border: 1px solid #E2D3B0;
        border-radius: 22px;
        padding: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 18px rgba(90, 60, 60, 0.08);
    }

    .plumette-home-card-title {
        text-align: center;
        margin-top: 12px;
        margin-bottom: 6px;
    }

    .plumette-home-link {
        color: #8E4D4D !important;
        text-decoration: none !important;
        font-family: "Georgia", serif;
        font-size: 28px;
        font-weight: 500;
        display: inline-block;
        transition: all 0.2s ease;
    }

    .plumette-home-link:visited {
        color: #8E4D4D !important;
        text-decoration: none !important;
    }

    .plumette-home-link:hover {
        color: #C9A55B !important;
        text-decoration: none !important;
        transform: scale(1.02);
    }

    .plumette-home-link:active,
    .plumette-home-link:focus {
        color: #8E4D4D !important;
        text-decoration: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* -----------------------------
       Boutons généraux
    ----------------------------- */
    .stButton > button {
        background-color: #8E4D4D;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.50rem 1rem;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #744040;
        color: white;
    }

    .stButton > button:focus:not(:active) {
        border: none;
        box-shadow: 0 0 0 2px rgba(201,165,91,0.35);
    }

    /* -----------------------------
       Inputs / formulaires
    ----------------------------- */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stDateInput input {
        background-color: #FFFDF8 !important;
        border-radius: 10px !important;
        border: 1px solid #D9C7A3 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #FFFDF8 !important;
        border-radius: 10px !important;
        border: 1px solid #D9C7A3 !important;
    }

    /* -----------------------------
       Expanders
    ----------------------------- */
    .streamlit-expanderHeader {
        color: #8E4D4D !important;
        font-weight: 600;
    }

    /* -----------------------------
       Metrics
    ----------------------------- */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.55);
        border: 1px solid #D9C7A3;
        border-radius: 18px;
        padding: 14px;
    }

    div[data-testid="stMetricLabel"] {
        color: #8E4D4D !important;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #4F3A3A !important;
    }

    /* -----------------------------
       DataFrame / tableaux Streamlit
    ----------------------------- */
    div[data-testid="stDataFrame"] {
        border: 1px solid #D9C7A3;
        border-radius: 14px;
        overflow: hidden;
        background: white;
    }

    /* -----------------------------
       Alertes
    ----------------------------- */
    div[data-baseweb="notification"] {
        border-radius: 14px;
    }

    /* -----------------------------
       Images
    ----------------------------- */
    img {
        border-radius: 18px;
    }

    /* -----------------------------
       Tableau HTML style Excel chic
    ----------------------------- */
    .table-plumette {
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
        overflow: hidden;
        border-radius: 14px;
        margin-top: 10px;
    }

    .table-plumette th {
        background-color: #E8C7BD;
        color: #6D4A4A;
        padding: 12px;
        border: 1px solid #D4B062;
        text-align: center;
        font-weight: 700;
    }

    .table-plumette td {
        background-color: #1F1F1F;
        color: #F7F2E8;
        padding: 10px;
        border: 1px solid #D4B062;
        text-align: center;
    }

    .table-plumette td.col-highlight {
        background-color: #D4B062;
        color: #3A2B1A;
        font-weight: bold;
    }

    .plumette-info-box {
        background: rgba(255,255,255,0.70);
        border: 1px solid #E2D3B0;
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 14px;
    }

    .plumette-info-title {
        color: #8E4D4D;
        font-size: 20px;
        font-family: "Georgia", serif;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)


def afficher_entete(logo_path=None, titre="Les Créations de Plumette", sous_titre="Gestion couture"):
    if logo_path is None:
        logo_path = BASE_DIR / "LOGO 2.png"

    logo_b64 = image_to_base64(logo_path)


    st.markdown(f'<div class="plumette-title">{titre}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="plumette-subtitle">{sous_titre}</div>', unsafe_allow_html=True)
    st.markdown('<div class="mini-separator"></div>', unsafe_allow_html=True)


def ouvrir_carte():
    st.markdown('<div class="plumette-card">', unsafe_allow_html=True)


def fermer_carte():
    st.markdown('</div>', unsafe_allow_html=True)


def titre_section(texte):
    st.markdown(f'<div class="section-title">{texte}</div>', unsafe_allow_html=True)


def afficher_tableau_html(df, colonnes, colonnes_highlight=None):
    """
    df : dataframe pandas
    colonnes : liste de tuples [("colonne_df", "Titre affiché"), ...]
    colonnes_highlight : liste optionnelle des noms de colonnes df à surligner
    """
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    colonnes_highlight = colonnes_highlight or []

    html = '<table class="table-plumette">'
    html += "<tr>"
    for _, titre in colonnes:
        html += f"<th>{titre}</th>"
    html += "</tr>"

    for _, row in df.iterrows():
        html += "<tr>"
        for nom_colonne, _ in colonnes:
            value = row.get(nom_colonne, "")
            classe = "col-highlight" if nom_colonne in colonnes_highlight else ""
            html += f'<td class="{classe}">{value}</td>'
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
def section_titre(texte):
    titre_section(texte)