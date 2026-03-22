import streamlit as st
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
import pandas as pd
from style import section_titre


def afficher_page():
    section_titre("Mon suivi des stocks")

    def get_connection():
        return sqlite3.connect("gestion_couture.db")

    conn = get_connection()

    try:
        df_tissus = pd.read_sql_query("SELECT * FROM tissus", conn)
    except Exception:
        df_tissus = pd.DataFrame()

    try:
        df_accessoires = pd.read_sql_query("SELECT * FROM accessoires", conn)
    except Exception:
        df_accessoires = pd.DataFrame()

    try:
        df_creations = pd.read_sql_query("SELECT * FROM creations", conn)
    except Exception:
        df_creations = pd.DataFrame()

    conn.close()

    # =========================
    # SÉCURISATION COLONNES
    # =========================
    colonnes_tissus = [
        "id", "nom", "type", "couleur", "largeur", "grammage",
        "quantite", "prix", "fournisseur", "seuil_alerte",
        "commentaire", "photo"
    ]

    colonnes_accessoires = [
        "id", "nom", "type_accessoire", "couleur", "fournisseur",
        "quantite_longueur", "unite", "stock", "seuil_alerte",
        "prix", "prix_unitaire", "commentaire", "photo"
    ]

    colonnes_creations = [
        "id", "nom_creation", "cout_fabrication", "prix_vente_conseille",
        "prix_vente_retenu", "marge_euros", "marge_pourcentage",
        "stock", "seuil_alerte", "commentaire", "photo"
    ]

    for col in colonnes_tissus:
        if col not in df_tissus.columns:
            df_tissus[col] = None

    for col in colonnes_accessoires:
        if col not in df_accessoires.columns:
            df_accessoires[col] = None

    for col in colonnes_creations:
        if col not in df_creations.columns:
            df_creations[col] = None

    # =========================
    # CONVERSIONS NUMÉRIQUES
    # =========================
    if not df_tissus.empty:
        df_tissus["quantite"] = pd.to_numeric(df_tissus["quantite"], errors="coerce").fillna(0)
        df_tissus["prix"] = pd.to_numeric(df_tissus["prix"], errors="coerce").fillna(0)
        df_tissus["seuil_alerte"] = pd.to_numeric(df_tissus["seuil_alerte"], errors="coerce").fillna(0)
        df_tissus["valeur_stock"] = df_tissus["quantite"] * df_tissus["prix"]

    if not df_accessoires.empty:
        df_accessoires["stock"] = pd.to_numeric(df_accessoires["stock"], errors="coerce").fillna(0)
        df_accessoires["prix_unitaire"] = pd.to_numeric(df_accessoires["prix_unitaire"], errors="coerce").fillna(0)
        df_accessoires["seuil_alerte"] = pd.to_numeric(df_accessoires["seuil_alerte"], errors="coerce").fillna(0)
        df_accessoires["valeur_stock"] = df_accessoires["stock"] * df_accessoires["prix_unitaire"]

    if not df_creations.empty:
        df_creations["stock"] = pd.to_numeric(df_creations["stock"], errors="coerce").fillna(0)
        df_creations["seuil_alerte"] = pd.to_numeric(df_creations["seuil_alerte"], errors="coerce").fillna(0)
        df_creations["prix_vente_retenu"] = pd.to_numeric(df_creations["prix_vente_retenu"], errors="coerce").fillna(0)
        df_creations["cout_fabrication"] = pd.to_numeric(df_creations["cout_fabrication"], errors="coerce").fillna(0)
        df_creations["valeur_stock_vente"] = df_creations["stock"] * df_creations["prix_vente_retenu"]
        df_creations["valeur_stock_cout"] = df_creations["stock"] * df_creations["cout_fabrication"]

    # =========================
    # INDICATEURS
    # =========================
    nb_tissus = len(df_tissus)
    nb_accessoires = len(df_accessoires)
    nb_creations = len(df_creations)

    tissus_stock_faible = df_tissus[
        df_tissus["quantite"] < df_tissus["seuil_alerte"]
    ] if not df_tissus.empty else pd.DataFrame()

    accessoires_stock_faible = df_accessoires[
        df_accessoires["stock"] < df_accessoires["seuil_alerte"]
    ] if not df_accessoires.empty else pd.DataFrame()

    creations_stock_faible = df_creations[
        df_creations["stock"] < df_creations["seuil_alerte"]
    ] if not df_creations.empty else pd.DataFrame()

    valeur_tissus = df_tissus["valeur_stock"].sum() if not df_tissus.empty else 0
    valeur_accessoires = df_accessoires["valeur_stock"].sum() if not df_accessoires.empty else 0
    valeur_creations = df_creations["valeur_stock_vente"].sum() if not df_creations.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🧵 Tissus", nb_tissus)

    with col2:
        st.metric("🧷 Accessoires", nb_accessoires)

    with col3:
        st.metric("🪡 Créations", nb_creations)

    with col4:
        total_alertes = len(tissus_stock_faible) + len(accessoires_stock_faible) + len(creations_stock_faible)
        st.metric("⚠️ Stocks faibles", total_alertes)

    st.write("---")

    col5, col6, col7 = st.columns(3)

    with col5:
        st.metric("💰 Valeur stock tissus", f"{valeur_tissus:.2f} €")

    with col6:
        st.metric("💰 Valeur stock accessoires", f"{valeur_accessoires:.2f} €")

    with col7:
        st.metric("💰 Valeur stock créations", f"{valeur_creations:.2f} €")

    st.write("---")

    # =========================
    # TISSUS
    # =========================
    section_titre("Tissus à surveiller")

    if tissus_stock_faible.empty:
        st.success("Aucun tissu en stock faible.")
    else:
        affichage_tissus = tissus_stock_faible[
            ["nom", "type", "couleur", "quantite", "seuil_alerte", "fournisseur"]
        ].copy()
        affichage_tissus.columns = [
            "Nom", "Type", "Couleur", "Quantité", "Seuil alerte", "Fournisseur"
        ]
        st.dataframe(affichage_tissus, use_container_width=True)

    st.write("---")

    # =========================
    # ACCESSOIRES
    # =========================
    section_titre("Accessoires à surveiller")

    if accessoires_stock_faible.empty:
        st.success("Aucun accessoire en stock faible.")
    else:
        affichage_accessoires = accessoires_stock_faible[
            ["nom", "type_accessoire", "couleur", "stock", "seuil_alerte", "unite", "fournisseur"]
        ].copy()
        affichage_accessoires.columns = [
            "Nom", "Type", "Couleur", "Stock", "Seuil alerte", "Unité", "Fournisseur"
        ]
        st.dataframe(affichage_accessoires, use_container_width=True)

    st.write("---")

    # =========================
    # CREATIONS
    # =========================
    section_titre("Créations à surveiller")

    if creations_stock_faible.empty:
        st.success("Aucune création en stock faible.")
    else:
        affichage_creations = creations_stock_faible[
            ["nom_creation", "stock", "seuil_alerte", "cout_fabrication", "prix_vente_retenu"]
        ].copy()
        affichage_creations.columns = [
            "Nom création", "Stock", "Seuil alerte", "Coût fabrication", "Prix vente retenu"
        ]
        st.dataframe(affichage_creations, use_container_width=True)

    st.write("---")

    # =========================
    # RÉPARTITIONS
    # =========================
    col8, col9, col10 = st.columns(3)

    with col8:
        st.markdown("### Répartition tissus")
        if not df_tissus.empty:
            repartition_tissus = df_tissus["type"].fillna("Non renseigné").value_counts()
            st.bar_chart(repartition_tissus)
        else:
            st.info("Aucun tissu")

    with col9:
        st.markdown("### Répartition accessoires")
        if not df_accessoires.empty:
            repartition_accessoires = df_accessoires["type_accessoire"].fillna("Non renseigné").value_counts()
            st.bar_chart(repartition_accessoires)
        else:
            st.info("Aucun accessoire")

    with col10:
        st.markdown("### Répartition créations")
        if not df_creations.empty:
            repartition_creations = df_creations["nom_creation"].fillna("Non renseigné").value_counts()
            st.bar_chart(repartition_creations)
        else:
            st.info("Aucune création")