import streamlit as st
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
import pandas as pd
import os
from style import section_titre

def afficher_page():

    if not os.path.exists("photos_tissus"):
        os.makedirs("photos_tissus")

    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False

    def get_connection():
        return sqlite3.connect("gestion_couture.db")

    def supprimer_tissu(tissu_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT photo FROM tissus WHERE id = ?", (tissu_id,))
        result = cursor.fetchone()

        if result and result[0]:
            chemin_photo = os.path.join("photos_tissus", result[0])
            if os.path.exists(chemin_photo):
                os.remove(chemin_photo)

        cursor.execute("DELETE FROM tissus WHERE id = ?", (tissu_id,))
        conn.commit()
        conn.close()

    def modifier_tissu(
        tissu_id,
        nom,
        type_tissu,
        couleur,
        largeur,
        grammage,
        quantite,
        prix,
        fournisseur,
        seuil_alerte,
        commentaire,
        nouvelle_photo
    ):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT photo FROM tissus WHERE id = ?", (tissu_id,))
        result = cursor.fetchone()
        ancienne_photo = result[0] if result else None

        nom_photo = ancienne_photo

        if nouvelle_photo is not None:
            if ancienne_photo:
                ancien_chemin = os.path.join("photos_tissus", ancienne_photo)
                if os.path.exists(ancien_chemin):
                    os.remove(ancien_chemin)

            nom_photo = nouvelle_photo.name
            chemin_photo = os.path.join("photos_tissus", nom_photo)

            with open(chemin_photo, "wb") as f:
                f.write(nouvelle_photo.getbuffer())

        cursor.execute("""
            UPDATE tissus
            SET nom = ?, type = ?, couleur = ?, largeur = ?, grammage = ?, quantite = ?,
                prix = ?, fournisseur = ?, seuil_alerte = ?, commentaire = ?, photo = ?
            WHERE id = ?
        """, (
            nom,
            type_tissu,
            couleur,
            largeur,
            grammage,
            quantite,
            prix,
            fournisseur,
            seuil_alerte,
            commentaire,
            nom_photo,
            tissu_id
        ))

        conn.commit()
        conn.close()

    section_titre("Mes tissus")

    types_tissus = [""] + [
        "Coton", "Lin", "Jersey", "Popeline", "Viscose",
        "Double gaze", "Jean", "Velours", "Satin", "Molleton", "Autre"
    ]

    couleurs = [""] + [
        "Blanc", "Noir", "Beige", "Gris", "Bleu", "Rouge",
        "Rose", "Vert", "Jaune", "Marron", "Violet",
        "Orange", "Multicolore", "Autre"
    ]

    fournisseurs = [""] + [
        "Mondial Tissus", "Self Tissus", "Les Coupons de Saint Pierre",
        "Pretty Mercerie", "Ma Petite Mercerie", "Tissus.net", "Autre"
    ]

    # ===== RÉCUPÉRATION =====
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM tissus", conn)
    conn.close()

    # ===== RECHERCHE / FILTRES / TRI =====
    section_titre("Rechercher, filtrer et trier")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        recherche = st.text_input("Rechercher par nom")

    with colf2:
        filtre_type = st.selectbox(
            "Type",
            [""] + sorted([x for x in df["type"].dropna().unique() if x != ""]) if not df.empty else [""]
        )

    with colf3:
        filtre_couleur = st.selectbox(
            "Couleur",
            [""] + sorted([x for x in df["couleur"].dropna().unique() if x != ""]) if not df.empty else [""]
        )

    with colf4:
        filtre_fournisseur = st.selectbox(
            "Fournisseur",
            [""] + sorted([x for x in df["fournisseur"].dropna().unique() if x != ""]) if not df.empty else [""]
        )

    colf5, colf6 = st.columns(2)

    with colf5:
        tri_colonne = st.selectbox("Trier par", ["Nom", "Prix", "Prix au m²", "Quantité", "Largeur"])

    with colf6:
        tri_ordre = st.selectbox("Ordre", ["Croissant", "Décroissant"])

    stock_faible_uniquement = st.checkbox("Stock faible uniquement")

    # ===== AJOUT =====
    section_titre("Ajouter des tissus")

    if st.button("➕ Ajouter un tissu"):
        st.session_state.show_add_form = not st.session_state.show_add_form

    if st.session_state.show_add_form:
        with st.form("form_tissu"):
            nom = st.text_input("Nom du tissu")
            type_tissu = st.selectbox("Type de tissu", types_tissus, index=0)
            couleur = st.selectbox("Couleur", couleurs, index=0)
            largeur = st.number_input("Largeur (cm)", min_value=0.0)
            grammage = st.number_input("Grammage (g/m²)", min_value=0.0)
            prix = st.number_input("Prix (€)", min_value=0.0)

            prix_m2 = 0
            if largeur > 0:
                prix_m2 = prix / (largeur / 100)

            st.write(f"💰 Prix au m² : {prix_m2:.2f} €")

            fournisseur = st.selectbox("Fournisseur", fournisseurs, index=0)
            quantite = st.number_input("Quantité", min_value=0.0)
            seuil_alerte = st.number_input("Seuil alerte stock", min_value=0.0)
            commentaire = st.text_area("Commentaire")
            photo = st.file_uploader("Photo du tissu", type=["jpg", "jpeg", "png"])

            col_submit1, col_submit2 = st.columns(2)

            with col_submit1:
                submitted = st.form_submit_button("✅ Ajouter le tissu")

            with col_submit2:
                cancel_add = st.form_submit_button("❌ Annuler l'ajout")

            if submitted:
                nom_photo = None

                if photo is not None:
                    nom_photo = photo.name
                    chemin_photo = os.path.join("photos_tissus", nom_photo)
                    with open(chemin_photo, "wb") as f:
                        f.write(photo.getbuffer())

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO tissus
                    (nom, type, couleur, largeur, grammage, quantite, prix, fournisseur, seuil_alerte, commentaire, photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nom,
                    type_tissu,
                    couleur,
                    largeur,
                    grammage,
                    quantite,
                    prix,
                    fournisseur,
                    seuil_alerte,
                    commentaire,
                    nom_photo
                ))

                conn.commit()
                conn.close()

                st.session_state.show_add_form = False
                st.success("Tissu ajouté avec succès !")
                st.rerun()

            if cancel_add:
                st.session_state.show_add_form = False
                st.rerun()

    # ===== APPLICATION DES FILTRES =====
    df_filtre = df.copy()

    if recherche:
        df_filtre = df_filtre[df_filtre["nom"].str.contains(recherche, case=False, na=False)]

    if filtre_type:
        df_filtre = df_filtre[df_filtre["type"] == filtre_type]

    if filtre_couleur:
        df_filtre = df_filtre[df_filtre["couleur"] == filtre_couleur]

    if filtre_fournisseur:
        df_filtre = df_filtre[df_filtre["fournisseur"] == filtre_fournisseur]

    if stock_faible_uniquement:
        df_filtre = df_filtre[df_filtre["quantite"] < df_filtre["seuil_alerte"]]

    # ===== TRI =====
    mapping = {
        "Nom": "nom",
        "Prix": "prix",
        "Quantité": "quantite",
        "Largeur": "largeur",
        "Prix au m²": "prix_m2"
    }

    ascending = True if tri_ordre == "Croissant" else False

    if not df_filtre.empty:

        # Création colonne calculée prix au m²
        df_filtre["prix_m2"] = df_filtre.apply(
            lambda row: row["prix"] / (row["largeur"] / 100) if row["largeur"] > 0 else 0,
            axis=1
        )

        colonne_tri = mapping[tri_colonne]

        df_filtre = df_filtre.sort_values(by=colonne_tri, ascending=ascending)

    # ===== AFFICHAGE =====
    section_titre("Mes tissus en stock")

    if not df_filtre.empty:
        for _, row in df_filtre.iterrows():
            col1, col2 = st.columns([1, 2])

            prix_m2 = 0
            if row["largeur"] > 0:
                prix_m2 = row["prix"] / (row["largeur"] / 100)

            with col1:
                if row["photo"]:
                    chemin_photo = os.path.join("photos_tissus", row["photo"])
                    if os.path.exists(chemin_photo):
                        st.image(chemin_photo, width=250)
                    else:
                        st.write("Photo introuvable")
                else:
                    st.write("Pas de photo")

            with col2:
                st.subheader(row["nom"])
                st.write(f"**Type :** {row['type']}")
                st.write(f"**Couleur :** {row['couleur']}")
                st.write(f"**Largeur :** {row['largeur']} cm")
                st.write(f"**Grammage :** {row['grammage']} g/m²")
                st.write(f"**Prix :** {row['prix']} €")
                st.write(f"💰 **Prix au m² :** {prix_m2:.2f} €")
                st.write(f"**Fournisseur :** {row['fournisseur']}")
                st.write(f"**Quantité :** {row['quantite']}")
                st.write(f"**Seuil alerte :** {row['seuil_alerte']}")
                st.write(f"**Commentaire :** {row['commentaire']}")

                if row["quantite"] < row["seuil_alerte"]:
                    st.error("Stock faible")

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("✏️ Modifier", key=f"edit_btn_{row['id']}"):
                        st.session_state[f"edit_{row['id']}"] = not st.session_state.get(f"edit_{row['id']}", False)

                with col_btn2:
                    if st.button("❌ Supprimer", key=f"delete_{row['id']}"):
                        st.session_state[f"confirm_delete_{row['id']}"] = True

            # ===== CONFIRMATION SUPPRESSION =====
            if st.session_state.get(f"confirm_delete_{row['id']}", False):
                st.warning("⚠️ Êtes-vous sûr de vouloir supprimer ce tissu ?")

                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("✅ Oui", key=f"yes_{row['id']}"):
                        supprimer_tissu(row["id"])
                        st.session_state[f"confirm_delete_{row['id']}"] = False
                        st.success("Tissu supprimé")
                        st.rerun()

                with col_no:
                    if st.button("❌ Non", key=f"no_{row['id']}"):
                        st.session_state[f"confirm_delete_{row['id']}"] = False
                        st.rerun()

            # ===== FORMULAIRE DE MODIFICATION =====
            if st.session_state.get(f"edit_{row['id']}", False):
                st.markdown("### Modifier ce tissu")

                type_index = types_tissus.index(row["type"]) if row["type"] in types_tissus else 0
                couleur_index = couleurs.index(row["couleur"]) if row["couleur"] in couleurs else 0
                fournisseur_index = fournisseurs.index(row["fournisseur"]) if row["fournisseur"] in fournisseurs else 0
                commentaire_valeur = row["commentaire"] if pd.notna(row["commentaire"]) else ""

                with st.form(f"form_edit_{row['id']}"):
                    edit_nom = st.text_input("Nom du tissu", value=row["nom"])
                    edit_type = st.selectbox("Type de tissu", types_tissus, index=type_index)
                    edit_couleur = st.selectbox("Couleur ou Motif", couleurs, index=couleur_index)
                    edit_largeur = st.number_input("Largeur (cm)", min_value=0.0, value=float(row["largeur"]))
                    edit_grammage = st.number_input("Grammage (g/m²)", min_value=0.0, value=float(row["grammage"]))
                    edit_prix = st.number_input("Prix (€)", min_value=0.0, value=float(row["prix"]))

                    edit_prix_m2 = 0
                    if edit_largeur > 0:
                        edit_prix_m2 = edit_prix / (edit_largeur / 100)

                    st.write(f"💰 Prix au m² : {edit_prix_m2:.2f} €")

                    edit_fournisseur = st.selectbox("Fournisseur", fournisseurs, index=fournisseur_index)
                    edit_quantite = st.number_input("Quantité (m)", min_value=0.0, value=float(row["quantite"]))
                    edit_seuil_alerte = st.number_input("Seuil alerte stock (m)", min_value=0.0, value=float(row["seuil_alerte"]))
                    edit_commentaire = st.text_area("Commentaire", value=commentaire_valeur)
                    edit_photo = st.file_uploader(
                        "Nouvelle photo du tissu (optionnel)",
                        type=["jpg", "jpeg", "png"],
                        key=f"photo_edit_{row['id']}"
                    )

                    col_save, col_cancel = st.columns(2)

                    with col_save:
                        save_edit = st.form_submit_button("💾 Enregistrer les modifications")

                    with col_cancel:
                        cancel_edit = st.form_submit_button("Annuler")

                    if save_edit:
                        modifier_tissu(
                            row["id"],
                            edit_nom,
                            edit_type,
                            edit_couleur,
                            edit_largeur,
                            edit_grammage,
                            edit_quantite,
                            edit_prix,
                            edit_fournisseur,
                            edit_seuil_alerte,
                            edit_commentaire,
                            edit_photo
                        )
                        st.session_state[f"edit_{row['id']}"] = False
                        st.success("Tissu modifié avec succès !")
                        st.rerun()

                    if cancel_edit:
                        st.session_state[f"edit_{row['id']}"] = False
                        st.rerun()

            st.write("---")
    else:
        st.write("Aucun tissu ne correspond aux filtres.")