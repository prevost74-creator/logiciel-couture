import streamlit as st
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
import pandas as pd
import os
from style import section_titre
import uuid

def afficher_page():

    DOSSIER_PHOTOS = "photos_accessoires"

    if not os.path.exists(DOSSIER_PHOTOS):
        os.makedirs(DOSSIER_PHOTOS)

    if "show_add_form_accessoire" not in st.session_state:
        st.session_state.show_add_form_accessoire = False

    def get_connection():
        return sqlite3.connect("gestion_couture.db")

    def get_unite_par_type(type_accessoire):
        mapping = {
            "Bouton": "pièce",
            "Fermeture éclair": "pièce",
            "Pression": "pièce",
            "Perle": "pièce",
            "Ruban": "mètre",
            "Dentelle": "mètre",
            "Élastique": "mètre",
            "Biais": "mètre",
            "Passepoil": "mètre",
            "Fil": "bobine",
            "Autre": "unité"
        }
        return mapping.get(type_accessoire, "unité")

    def get_libelle_quantite(type_accessoire):
        unite = get_unite_par_type(type_accessoire)
        if unite == "mètre":
            return "Longueur"
        elif unite == "pièce":
            return "Quantité"
        elif unite == "bobine":
            return "Nombre"
        return "Quantité / Longueur"

    def sauvegarder_photo(photo):
        if photo is None:
            return None

        extension = os.path.splitext(photo.name)[1]
        nom_photo = f"{uuid.uuid4()}{extension}"
        chemin_photo = os.path.join(DOSSIER_PHOTOS, nom_photo)

        with open(chemin_photo, "wb") as f:
            f.write(photo.getbuffer())

        return nom_photo

    def supprimer_photo(nom_photo):
        if nom_photo:
            chemin = os.path.join(DOSSIER_PHOTOS, nom_photo)
            if os.path.exists(chemin):
                os.remove(chemin)

    def ajouter_accessoire(
        nom,
        type_accessoire,
        couleur,
        fournisseur,
        quantite_longueur,
        unite,
        stock,
        seuil_alerte,
        prix,
        commentaire,
        photo
    ):
        conn = get_connection()
        cursor = conn.cursor()

        prix_unitaire = prix / quantite_longueur if quantite_longueur > 0 else 0
        nom_photo = sauvegarder_photo(photo) if photo else None

        cursor.execute("""
            INSERT INTO accessoires
            (nom, type_accessoire, couleur, fournisseur, quantite_longueur, unite, stock, seuil_alerte, prix, prix_unitaire, commentaire, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nom,
            type_accessoire,
            couleur,
            fournisseur,
            quantite_longueur,
            unite,
            stock,
            seuil_alerte,
            prix,
            prix_unitaire,
            commentaire,
            nom_photo
        ))

        conn.commit()
        conn.close()

    def supprimer_accessoire(accessoire_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT photo FROM accessoires WHERE id = ?", (accessoire_id,))
        result = cursor.fetchone()

        if result and result[0]:
            supprimer_photo(result[0])

        cursor.execute("DELETE FROM accessoires WHERE id = ?", (accessoire_id,))
        conn.commit()
        conn.close()

    def modifier_accessoire(
        accessoire_id,
        nom,
        type_accessoire,
        couleur,
        fournisseur,
        quantite_longueur,
        unite,
        stock,
        seuil_alerte,
        prix,
        commentaire,
        nouvelle_photo
    ):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT photo FROM accessoires WHERE id = ?", (accessoire_id,))
        result = cursor.fetchone()
        ancienne_photo = result[0] if result else None

        nom_photo = ancienne_photo

        if nouvelle_photo is not None:
            if ancienne_photo:
                supprimer_photo(ancienne_photo)
            nom_photo = sauvegarder_photo(nouvelle_photo)

        prix_unitaire = prix / quantite_longueur if quantite_longueur > 0 else 0

        cursor.execute("""
            UPDATE accessoires
            SET nom = ?, type_accessoire = ?, couleur = ?, fournisseur = ?, quantite_longueur = ?, unite = ?,
                stock = ?, seuil_alerte = ?, prix = ?, prix_unitaire = ?, commentaire = ?, photo = ?
            WHERE id = ?
        """, (
            nom,
            type_accessoire,
            couleur,
            fournisseur,
            quantite_longueur,
            unite,
            stock,
            seuil_alerte,
            prix,
            prix_unitaire,
            commentaire,
            nom_photo,
            accessoire_id
        ))

        conn.commit()
        conn.close()

    types_accessoires = [
        "",
        "Bouton",
        "Fermeture éclair",
        "Ruban",
        "Dentelle",
        "Élastique",
        "Biais",
        "Passepoil",
        "Fil",
        "Pression",
        "Perle",
        "Autre"
    ]

    couleurs = [""] + [
        "Blanc", "Noir", "Beige", "Gris", "Bleu", "Rouge",
        "Rose", "Vert", "Jaune", "Marron", "Violet",
        "Orange", "Multicolore", "Autre"
    ]

    fournisseurs = [""] + [
        "Mondial Tissus",
        "Self Tissus",
        "Les Coupons de Saint Pierre",
        "Pretty Mercerie",
        "Ma Petite Mercerie",
        "Tissus.net",
        "Autre"
    ]

    section_titre("Mes accessoires")

    # =========================
    # RÉCUPÉRATION
    # =========================
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM accessoires", conn)
    conn.close()

    colonnes_attendues = [
        "id", "nom", "type_accessoire", "couleur", "fournisseur",
        "quantite_longueur", "unite", "stock", "seuil_alerte",
        "prix", "prix_unitaire", "commentaire", "photo"
    ]

    for col in colonnes_attendues:
        if col not in df.columns:
            df[col] = None

    # =========================
    # RECHERCHE / FILTRES / TRI
    # =========================
    section_titre("Rechercher, filtrer et trier")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        recherche = st.text_input("Rechercher par nom")

    with colf2:
        filtre_type = st.selectbox(
            "Type",
            [""] + sorted([x for x in df["type_accessoire"].dropna().unique() if x != ""]) if not df.empty else [""]
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
        tri_colonne = st.selectbox("Trier par", ["Nom", "Type", "Couleur", "Prix", "Prix unitaire", "Stock"])

    with colf6:
        tri_ordre = st.selectbox("Ordre", ["Croissant", "Décroissant"])

    stock_faible_uniquement = st.checkbox("Stock faible uniquement")

    # =========================
    # AJOUT
    # =========================
    section_titre("Ajouter un accessoire")

    if st.button("➕ Ajouter un accessoire"):
        st.session_state.show_add_form_accessoire = not st.session_state.show_add_form_accessoire

    if st.session_state.show_add_form_accessoire:
        st.markdown("### Nouvel accessoire")

        add_nom = st.text_input("Nom de l'accessoire", key="add_nom")
        add_type = st.selectbox("Type d'accessoire", types_accessoires, key="add_type")
        add_couleur = st.selectbox("Couleur", couleurs, key="add_couleur")

        add_unite = get_unite_par_type(add_type)
        add_libelle_quantite = get_libelle_quantite(add_type)

        add_fournisseur = st.selectbox("Fournisseur", fournisseurs, key="add_fournisseur")

        add_quantite_longueur = st.number_input(
            f"{add_libelle_quantite} achetée ({add_unite})",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="add_quantite_longueur"
        )

        add_stock = st.number_input(
            f"Stock restant ({add_unite})",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="add_stock"
        )

        add_seuil_alerte = st.number_input(
            f"Seuil alerte stock ({add_unite})",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="add_seuil_alerte"
        )

        add_prix = st.number_input(
            "Prix (€)",
            min_value=0.0,
            value=0.0,
            step=0.5,
            key="add_prix"
        )

        add_prix_unitaire = add_prix / add_quantite_longueur if add_quantite_longueur > 0 else 0
        st.write(f"💰 **Prix unitaire :** {add_prix_unitaire:.2f} € / {add_unite}")

        add_commentaire = st.text_area("Commentaire", key="add_commentaire")
        add_photo = st.file_uploader("Photo", type=["jpg", "jpeg", "png"], key="add_photo")

        col_add1, col_add2 = st.columns(2)

        with col_add1:
            if st.button("✅ Ajouter l'accessoire"):
                if add_nom.strip() == "":
                    st.error("Le nom est obligatoire.")
                else:
                    ajouter_accessoire(
                        add_nom,
                        add_type,
                        add_couleur,
                        add_fournisseur,
                        add_quantite_longueur,
                        add_unite,
                        add_stock,
                        add_seuil_alerte,
                        add_prix,
                        add_commentaire,
                        add_photo
                    )
                    st.session_state.show_add_form_accessoire = False
                    st.success("Accessoire ajouté avec succès !")
                    st.rerun()

        with col_add2:
            if st.button("❌ Annuler l'ajout"):
                st.session_state.show_add_form_accessoire = False
                st.rerun()

    # =========================
    # APPLICATION FILTRES
    # =========================
    df_filtre = df.copy()

    if recherche:
        df_filtre = df_filtre[df_filtre["nom"].fillna("").str.contains(recherche, case=False, na=False)]

    if filtre_type:
        df_filtre = df_filtre[df_filtre["type_accessoire"] == filtre_type]

    if filtre_couleur:
        df_filtre = df_filtre[df_filtre["couleur"] == filtre_couleur]

    if filtre_fournisseur:
        df_filtre = df_filtre[df_filtre["fournisseur"] == filtre_fournisseur]

    if stock_faible_uniquement:
        df_filtre = df_filtre[
            pd.to_numeric(df_filtre["stock"], errors="coerce").fillna(0) <
            pd.to_numeric(df_filtre["seuil_alerte"], errors="coerce").fillna(0)
        ]

    mapping_tri = {
        "Nom": "nom",
        "Type": "type_accessoire",
        "Couleur": "couleur",
        "Prix": "prix",
        "Prix unitaire": "prix_unitaire",
        "Stock": "stock"
    }

    ascending = True if tri_ordre == "Croissant" else False

    if not df_filtre.empty:
        df_filtre = df_filtre.sort_values(by=mapping_tri[tri_colonne], ascending=ascending)

    # =========================
    # AFFICHAGE
    # =========================
    section_titre("Mes accessoires en stock")

    if df_filtre.empty:
        st.info("Aucun accessoire ne correspond aux filtres.")
    else:
        for _, row in df_filtre.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                if pd.notna(row["photo"]) and row["photo"]:
                    chemin_photo = os.path.join(DOSSIER_PHOTOS, row["photo"])
                    if os.path.exists(chemin_photo):
                        st.image(chemin_photo, width=250)
                    else:
                        st.write("Photo introuvable")
                else:
                    st.write("Pas de photo")

            with col2:
                type_row = row["type_accessoire"] if pd.notna(row["type_accessoire"]) else ""
                unite_row = row["unite"] if pd.notna(row["unite"]) else ""

                st.subheader(row["nom"] if pd.notna(row["nom"]) else "")
                st.write(f"**Type :** {type_row}")
                st.write(f"**Couleur :** {row['couleur'] if pd.notna(row['couleur']) else ''}")
                st.write(f"**Fournisseur :** {row['fournisseur'] if pd.notna(row['fournisseur']) else ''}")
                st.write(f"**{get_libelle_quantite(type_row)} achetée :** {row['quantite_longueur'] if pd.notna(row['quantite_longueur']) else 0} {unite_row}")
                st.write(f"**Stock restant :** {row['stock'] if pd.notna(row['stock']) else 0} {unite_row}")
                st.write(f"**Seuil alerte :** {row['seuil_alerte'] if pd.notna(row['seuil_alerte']) else 0} {unite_row}")
                st.write(f"**Prix :** {row['prix'] if pd.notna(row['prix']) else 0} €")
                st.write(f"💰 **Prix unitaire :** {row['prix_unitaire'] if pd.notna(row['prix_unitaire']) else 0:.2f} € / {unite_row}")
                st.write(f"**Commentaire :** {row['commentaire'] if pd.notna(row['commentaire']) else ''}")

                if pd.notna(row["stock"]) and pd.notna(row["seuil_alerte"]):
                    if float(row["stock"]) < float(row["seuil_alerte"]):
                        st.error("Stock faible")

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("✏️ Modifier", key=f"edit_{row['id']}"):
                        st.session_state[f"open_edit_{row['id']}"] = not st.session_state.get(f"open_edit_{row['id']}", False)

                with col_btn2:
                    if st.button("❌ Supprimer", key=f"delete_{row['id']}"):
                        st.session_state[f"confirm_delete_{row['id']}"] = True

            # =========================
            # CONFIRMATION SUPPRESSION
            # =========================
            if st.session_state.get(f"confirm_delete_{row['id']}", False):
                st.warning("⚠️ Voulez-vous vraiment supprimer cet accessoire ?")

                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("✅ Oui", key=f"yes_{row['id']}"):
                        supprimer_accessoire(row["id"])
                        st.session_state[f"confirm_delete_{row['id']}"] = False
                        st.success("Accessoire supprimé.")
                        st.rerun()

                with col_no:
                    if st.button("❌ Non", key=f"no_{row['id']}"):
                        st.session_state[f"confirm_delete_{row['id']}"] = False
                        st.rerun()

            # =========================
            # MODIFICATION
            # =========================
            if st.session_state.get(f"open_edit_{row['id']}", False):
                st.markdown("### Modifier cet accessoire")

                type_index = types_accessoires.index(row["type_accessoire"]) if row["type_accessoire"] in types_accessoires else 0
                couleur_index = couleurs.index(row["couleur"]) if row["couleur"] in couleurs else 0
                fournisseur_index = fournisseurs.index(row["fournisseur"]) if row["fournisseur"] in fournisseurs else 0
                commentaire_valeur = row["commentaire"] if pd.notna(row["commentaire"]) else ""

                edit_nom = st.text_input(
                    "Nom de l'accessoire",
                    value=row["nom"] if pd.notna(row["nom"]) else "",
                    key=f"edit_nom_{row['id']}"
                )

                edit_type = st.selectbox(
                    "Type d'accessoire",
                    types_accessoires,
                    index=type_index,
                    key=f"edit_type_{row['id']}"
                )

                edit_couleur = st.selectbox(
                    "Couleur",
                    couleurs,
                    index=couleur_index,
                    key=f"edit_couleur_{row['id']}"
                )

                edit_unite = get_unite_par_type(edit_type)
                edit_libelle_quantite = get_libelle_quantite(edit_type)

                edit_fournisseur = st.selectbox(
                    "Fournisseur",
                    fournisseurs,
                    index=fournisseur_index,
                    key=f"edit_fournisseur_{row['id']}"
                )

                edit_quantite_longueur = st.number_input(
                    f"{edit_libelle_quantite} achetée ({edit_unite})",
                    min_value=0.0,
                    value=float(row["quantite_longueur"]) if pd.notna(row["quantite_longueur"]) else 0.0,
                    step=1.0,
                    key=f"edit_quantite_longueur_{row['id']}"
                )

                edit_stock = st.number_input(
                    f"Stock restant ({edit_unite})",
                    min_value=0.0,
                    value=float(row["stock"]) if pd.notna(row["stock"]) else 0.0,
                    step=1.0,
                    key=f"edit_stock_{row['id']}"
                )

                edit_seuil_alerte = st.number_input(
                    f"Seuil alerte stock ({edit_unite})",
                    min_value=0.0,
                    value=float(row["seuil_alerte"]) if pd.notna(row["seuil_alerte"]) else 0.0,
                    step=1.0,
                    key=f"edit_seuil_alerte_{row['id']}"
                )

                edit_prix = st.number_input(
                    "Prix (€)",
                    min_value=0.0,
                    value=float(row["prix"]) if pd.notna(row["prix"]) else 0.0,
                    step=0.5,
                    key=f"edit_prix_{row['id']}"
                )

                edit_prix_unitaire = edit_prix / edit_quantite_longueur if edit_quantite_longueur > 0 else 0
                st.write(f"💰 **Prix unitaire :** {edit_prix_unitaire:.2f} € / {edit_unite}")

                edit_commentaire = st.text_area(
                    "Commentaire",
                    value=commentaire_valeur,
                    key=f"edit_commentaire_{row['id']}"
                )

                edit_photo = st.file_uploader(
                    "Nouvelle photo (optionnel)",
                    type=["jpg", "jpeg", "png"],
                    key=f"edit_photo_{row['id']}"
                )

                col_save, col_cancel = st.columns(2)

                with col_save:
                    if st.button("💾 Enregistrer les modifications", key=f"save_{row['id']}"):
                        if edit_nom.strip() == "":
                            st.error("Le nom est obligatoire.")
                        else:
                            modifier_accessoire(
                                row["id"],
                                edit_nom,
                                edit_type,
                                edit_couleur,
                                edit_fournisseur,
                                edit_quantite_longueur,
                                edit_unite,
                                edit_stock,
                                edit_seuil_alerte,
                                edit_prix,
                                edit_commentaire,
                                edit_photo
                            )
                            st.session_state[f"open_edit_{row['id']}"] = False
                            st.success("Accessoire modifié avec succès !")
                            st.rerun()

                with col_cancel:
                    if st.button("Annuler", key=f"cancel_edit_{row['id']}"):
                        st.session_state[f"open_edit_{row['id']}"] = False
                        st.rerun()

            st.write("---")