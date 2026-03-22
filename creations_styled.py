import streamlit as st
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
import pandas as pd
import os
from style import section_titre
import uuid

DOSSIER_PHOTOS = "photos_creations"
TAUX_HORAIRE = 15.0

NOMS_CREATIONS = [
    "",
    "Lingette",
    "Chouchou",
    "Pochette",
    "Trousse",
    "Sac",
    "Bavoir",
    "Protège carnet",
    "Couverture bébé",
    "Bouillotte",
    "Panière",
    "Autre"
]


def afficher_page():
    if not os.path.exists(DOSSIER_PHOTOS):
        os.makedirs(DOSSIER_PHOTOS)

    if "show_add_form_creation" not in st.session_state:
        st.session_state.show_add_form_creation = False

    def get_connection():
        conn = sqlite3.connect("gestion_couture.db")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

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
            chemin_photo = os.path.join(DOSSIER_PHOTOS, nom_photo)
            if os.path.exists(chemin_photo):
                os.remove(chemin_photo)

    def charger_tissus():
        conn = get_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM tissus", conn)
        except Exception:
            df = pd.DataFrame()
        conn.close()

        if df.empty:
            return pd.DataFrame(columns=["id", "nom", "largeur", "prix"])

        colonnes_attendues = [
            "id", "nom", "type", "couleur", "largeur", "grammage",
            "quantite", "prix", "fournisseur", "seuil_alerte",
            "commentaire", "photo"
        ]
        for col in colonnes_attendues:
            if col not in df.columns:
                df[col] = None

        df["largeur"] = pd.to_numeric(df["largeur"], errors="coerce").fillna(0.0)
        df["prix"] = pd.to_numeric(df["prix"], errors="coerce").fillna(0.0)

        df["prix_m2"] = df.apply(
            lambda row: row["prix"] / (row["largeur"] / 100) if row["largeur"] > 0 else 0.0,
            axis=1
        )

        return df

    def charger_accessoires():
        conn = get_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM accessoires", conn)
        except Exception:
            df = pd.DataFrame()
        conn.close()

        if df.empty:
            return pd.DataFrame(columns=["id", "nom", "unite", "prix_unitaire"])

        colonnes_attendues = [
            "id", "nom", "type_accessoire", "couleur", "fournisseur",
            "quantite_longueur", "unite", "stock", "seuil_alerte",
            "prix", "prix_unitaire", "commentaire", "photo"
        ]
        for col in colonnes_attendues:
            if col not in df.columns:
                df[col] = None

        df["prix_unitaire"] = pd.to_numeric(df["prix_unitaire"], errors="coerce").fillna(0.0)

        return df

    def charger_creations():
        conn = get_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM creations", conn)
        except Exception:
            df = pd.DataFrame()
        conn.close()

        if df.empty:
            return pd.DataFrame(columns=[
                "id", "nom_creation", "cout_tissus", "cout_accessoires",
                "cout_fabrication", "heures", "taux_horaire",
                "prix_vente_conseille", "prix_vente_retenu",
                "marge_euros", "marge_pourcentage",
                "stock", "seuil_alerte",
                "commentaire", "photo"
            ])

        colonnes_attendues = [
            "id", "nom_creation", "cout_tissus", "cout_accessoires",
            "cout_fabrication", "heures", "taux_horaire",
            "coefficient_marge", "prix_vente_conseille",
            "prix_vente_retenu", "marge_euros", "marge_pourcentage",
            "stock", "seuil_alerte",
            "commentaire", "photo"
        ]
        for col in colonnes_attendues:
            if col not in df.columns:
                df[col] = None

        for col in [
            "cout_tissus", "cout_accessoires", "cout_fabrication", "heures",
            "taux_horaire", "prix_vente_conseille", "prix_vente_retenu",
            "marge_euros", "marge_pourcentage", "stock", "seuil_alerte"
        ]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df

    def get_details_tissus(creation_id):
        conn = get_connection()
        try:
            df = pd.read_sql_query(
                "SELECT * FROM creation_tissus WHERE creation_id = ? ORDER BY id",
                conn,
                params=(creation_id,)
            )
        except Exception:
            df = pd.DataFrame()
        conn.close()
        return df

    def get_details_accessoires(creation_id):
        conn = get_connection()
        try:
            df = pd.read_sql_query(
                "SELECT * FROM creation_accessoires WHERE creation_id = ? ORDER BY id",
                conn,
                params=(creation_id,)
            )
        except Exception:
            df = pd.DataFrame()
        conn.close()
        return df

    def calculer_prix_vente_conseille(cout_fabrication, heures):
        return (cout_fabrication + heures * TAUX_HORAIRE) / 0.716 if 0.716 != 0 else 0.0

    def calculer_marge_pourcentage(marge_euros, prix_vente_retenu):
        return (marge_euros * 100 / prix_vente_retenu) if prix_vente_retenu > 0 else 0.0

    def ajouter_creation(
        nom_creation,
        tissus_details,
        accessoires_details,
        heures,
        prix_vente_retenu,
        stock,
        seuil_alerte,
        commentaire,
        photo
    ):
        cout_tissus = sum(item["cout"] for item in tissus_details)
        cout_accessoires = sum(item["cout"] for item in accessoires_details)
        cout_fabrication = cout_tissus + cout_accessoires

        prix_vente_conseille = calculer_prix_vente_conseille(cout_fabrication, heures)
        marge_euros = prix_vente_retenu - cout_fabrication
        marge_pourcentage = calculer_marge_pourcentage(marge_euros, prix_vente_retenu)

        nom_photo = sauvegarder_photo(photo) if photo else None

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO creations (
                nom_creation, cout_tissus, cout_accessoires, cout_fabrication,
                heures, taux_horaire, coefficient_marge, prix_vente_conseille,
                prix_vente_retenu, marge_euros, marge_pourcentage,
                stock, seuil_alerte, commentaire, photo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nom_creation,
            cout_tissus,
            cout_accessoires,
            cout_fabrication,
            heures,
            TAUX_HORAIRE,
            0,
            prix_vente_conseille,
            prix_vente_retenu,
            marge_euros,
            marge_pourcentage,
            stock,
            seuil_alerte,
            commentaire,
            nom_photo
        ))

        creation_id = cursor.lastrowid

        for item in tissus_details:
            cursor.execute("""
                INSERT INTO creation_tissus (
                    creation_id, tissu_id, nom_tissu, longueur, largeur, prix_m2, nombre_coupes, cout
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                creation_id,
                item["tissu_id"],
                item["nom_tissu"],
                item["longueur"],
                item["largeur"],
                item["prix_m2"],
                item["nombre_coupes"],
                item["cout"]
            ))

        for item in accessoires_details:
            cursor.execute("""
                INSERT INTO creation_accessoires (
                    creation_id, accessoire_id, nom_accessoire, quantite, unite, prix_unitaire, cout
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                creation_id,
                item["accessoire_id"],
                item["nom_accessoire"],
                item["quantite"],
                item["unite"],
                item["prix_unitaire"],
                item["cout"]
            ))

        conn.commit()
        conn.close()

    def supprimer_creation(creation_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT photo FROM creations WHERE id = ?", (creation_id,))
        result = cursor.fetchone()

        if result and result[0]:
            supprimer_photo(result[0])

        cursor.execute("DELETE FROM creation_tissus WHERE creation_id = ?", (creation_id,))
        cursor.execute("DELETE FROM creation_accessoires WHERE creation_id = ?", (creation_id,))
        cursor.execute("DELETE FROM creations WHERE id = ?", (creation_id,))

        conn.commit()
        conn.close()

    def modifier_creation(
        creation_id,
        nom_creation,
        tissus_details,
        accessoires_details,
        heures,
        prix_vente_retenu,
        stock,
        seuil_alerte,
        commentaire,
        nouvelle_photo
    ):
        cout_tissus = sum(item["cout"] for item in tissus_details)
        cout_accessoires = sum(item["cout"] for item in accessoires_details)
        cout_fabrication = cout_tissus + cout_accessoires

        prix_vente_conseille = calculer_prix_vente_conseille(cout_fabrication, heures)
        marge_euros = prix_vente_retenu - cout_fabrication
        marge_pourcentage = calculer_marge_pourcentage(marge_euros, prix_vente_retenu)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT photo FROM creations WHERE id = ?", (creation_id,))
        result = cursor.fetchone()
        ancienne_photo = result[0] if result else None

        nom_photo = ancienne_photo

        if nouvelle_photo is not None:
            if ancienne_photo:
                supprimer_photo(ancienne_photo)
            nom_photo = sauvegarder_photo(nouvelle_photo)

        cursor.execute("""
            UPDATE creations
            SET nom_creation = ?, cout_tissus = ?, cout_accessoires = ?, cout_fabrication = ?,
                heures = ?, taux_horaire = ?, coefficient_marge = ?, prix_vente_conseille = ?,
                prix_vente_retenu = ?, marge_euros = ?, marge_pourcentage = ?,
                stock = ?, seuil_alerte = ?, commentaire = ?, photo = ?
            WHERE id = ?
        """, (
            nom_creation,
            cout_tissus,
            cout_accessoires,
            cout_fabrication,
            heures,
            TAUX_HORAIRE,
            0,
            prix_vente_conseille,
            prix_vente_retenu,
            marge_euros,
            marge_pourcentage,
            stock,
            seuil_alerte,
            commentaire,
            nom_photo,
            creation_id
        ))

        cursor.execute("DELETE FROM creation_tissus WHERE creation_id = ?", (creation_id,))
        cursor.execute("DELETE FROM creation_accessoires WHERE creation_id = ?", (creation_id,))

        for item in tissus_details:
            cursor.execute("""
                INSERT INTO creation_tissus (
                    creation_id, tissu_id, nom_tissu, longueur, largeur, prix_m2, nombre_coupes, cout
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                creation_id,
                item["tissu_id"],
                item["nom_tissu"],
                item["longueur"],
                item["largeur"],
                item["prix_m2"],
                item["nombre_coupes"],
                item["cout"]
            ))

        for item in accessoires_details:
            cursor.execute("""
                INSERT INTO creation_accessoires (
                    creation_id, accessoire_id, nom_accessoire, quantite, unite, prix_unitaire, cout
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                creation_id,
                item["accessoire_id"],
                item["nom_accessoire"],
                item["quantite"],
                item["unite"],
                item["prix_unitaire"],
                item["cout"]
            ))

        conn.commit()
        conn.close()

    def nom_creation_widget(label, key_prefix, valeur_par_defaut=""):
        options = NOMS_CREATIONS.copy()

        if valeur_par_defaut and valeur_par_defaut not in options:
            choix_defaut = "Autre"
            nom_autre_defaut = valeur_par_defaut
        else:
            choix_defaut = valeur_par_defaut if valeur_par_defaut in options else ""
            nom_autre_defaut = ""

        index_defaut = options.index(choix_defaut) if choix_defaut in options else 0

        choix_nom = st.selectbox(
            label,
            options,
            index=index_defaut,
            key=f"{key_prefix}_nom_creation_select"
        )

        if choix_nom == "Autre":
            return st.text_input(
                "Nom personnalisé de la création",
                value=nom_autre_defaut,
                key=f"{key_prefix}_nom_creation_autre"
            )

        return choix_nom

    def construire_formulaire_tissus(df_tissus, prefix, details_existants=None):
        tissus_details = []

        valeur_nb = len(details_existants) if details_existants is not None else 0
        nb_tissus = st.number_input(
            "Nombre de tissus utilisés",
            min_value=0,
            step=1,
            value=valeur_nb,
            key=f"{prefix}_nb_tissus"
        )

        options_tissus = [""] if df_tissus.empty else [""] + df_tissus["nom"].fillna("").tolist()

        for i in range(nb_tissus):
            st.markdown(f"#### Tissu {i + 1}")

            detail = details_existants[i] if details_existants is not None and i < len(details_existants) else None
            nom_defaut = detail["nom_tissu"] if detail is not None and pd.notna(detail.get("nom_tissu")) else ""
            index_defaut = options_tissus.index(nom_defaut) if nom_defaut in options_tissus else 0

            nom_tissu = st.selectbox(
                f"Nom du tissu #{i + 1}",
                options_tissus,
                index=index_defaut,
                key=f"{prefix}_nom_tissu_{i}"
            )

            tissu_id = None
            prix_m2 = 0.0

            if nom_tissu and not df_tissus.empty:
                ligne = df_tissus[df_tissus["nom"] == nom_tissu].iloc[0]
                tissu_id = int(ligne["id"])
                prix_m2 = float(ligne["prix_m2"])

            longueur = st.number_input(
                f"Longueur tissu #{i + 1} (m)",
                min_value=0.0,
                value=float(detail["longueur"]) if detail is not None and pd.notna(detail.get("longueur")) else 0.0,
                step=0.1,
                key=f"{prefix}_longueur_tissu_{i}"
            )

            largeur = st.number_input(
                f"Largeur tissu #{i + 1} (m)",
                min_value=0.0,
                value=float(detail["largeur"]) if detail is not None and pd.notna(detail.get("largeur")) else 0.0,
                step=0.1,
                key=f"{prefix}_largeur_tissu_{i}"
            )

            nombre_coupes = st.number_input(
                f"Nombre de coupes tissu #{i + 1}",
                min_value=1,
                value=int(detail["nombre_coupes"]) if detail is not None and pd.notna(detail.get("nombre_coupes")) else 1,
                step=1,
                key=f"{prefix}_nb_coupes_tissu_{i}"
            )

            cout = longueur * largeur * nombre_coupes * prix_m2 * 1.05

            st.write(f"**Prix au m² :** {prix_m2:.2f} €")
            st.write("**Marge perte tissu :** 5 %")
            st.write(f"**Coût tissu #{i + 1} :** {cout:.2f} €")

            tissus_details.append({
                "tissu_id": tissu_id,
                "nom_tissu": nom_tissu,
                "longueur": longueur,
                "largeur": largeur,
                "prix_m2": prix_m2,
                "nombre_coupes": nombre_coupes,
                "cout": cout
            })

        return tissus_details

    def construire_formulaire_accessoires(df_accessoires, prefix, details_existants=None):
        accessoires_details = []

        valeur_nb = len(details_existants) if details_existants is not None else 0
        nb_accessoires = st.number_input(
            "Nombre d'accessoires utilisés",
            min_value=0,
            step=1,
            value=valeur_nb,
            key=f"{prefix}_nb_accessoires"
        )

        options_accessoires = [""] if df_accessoires.empty else [""] + df_accessoires["nom"].fillna("").tolist()

        for i in range(nb_accessoires):
            st.markdown(f"#### Accessoire {i + 1}")

            detail = details_existants[i] if details_existants is not None and i < len(details_existants) else None
            nom_defaut = detail["nom_accessoire"] if detail is not None and pd.notna(detail.get("nom_accessoire")) else ""
            index_defaut = options_accessoires.index(nom_defaut) if nom_defaut in options_accessoires else 0

            nom_accessoire = st.selectbox(
                f"Nom accessoire #{i + 1}",
                options_accessoires,
                index=index_defaut,
                key=f"{prefix}_nom_accessoire_{i}"
            )

            accessoire_id = None
            unite = ""
            prix_unitaire = 0.0

            if nom_accessoire and not df_accessoires.empty:
                ligne = df_accessoires[df_accessoires["nom"] == nom_accessoire].iloc[0]
                accessoire_id = int(ligne["id"])
                unite = ligne["unite"] if pd.notna(ligne["unite"]) else ""
                prix_unitaire = float(ligne["prix_unitaire"])

            quantite = st.number_input(
                f"Longueur / quantité accessoire #{i + 1} ({unite if unite else 'unité'})",
                min_value=0.0,
                value=float(detail["quantite"]) if detail is not None and pd.notna(detail.get("quantite")) else 0.0,
                step=1.0,
                key=f"{prefix}_quantite_accessoire_{i}"
            )

            cout = quantite * prix_unitaire

            st.write(f"**Unité :** {unite if unite else 'unité'}")
            st.write(f"**Prix unitaire :** {prix_unitaire:.2f} € / {unite if unite else 'unité'}")
            st.write(f"**Coût accessoire #{i + 1} :** {cout:.2f} €")

            accessoires_details.append({
                "accessoire_id": accessoire_id,
                "nom_accessoire": nom_accessoire,
                "quantite": quantite,
                "unite": unite,
                "prix_unitaire": prix_unitaire,
                "cout": cout
            })

        return accessoires_details

    section_titre("Mes créations")

    df_creations = charger_creations()
    df_tissus = charger_tissus()
    df_accessoires = charger_accessoires()

    section_titre("Rechercher, filtrer et trier")

    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        recherche = st.text_input("Rechercher par nom")

    with colf2:
        tri_colonne = st.selectbox(
            "Trier par",
            ["Nom", "Coût fabrication", "Prix conseillé", "Prix retenu", "Marge €", "Marge %", "Stock"]
        )

    with colf3:
        tri_ordre = st.selectbox("Ordre", ["Croissant", "Décroissant"])

    section_titre("Ajouter une création")

    if st.button("➕ Ajouter une création"):
        st.session_state.show_add_form_creation = not st.session_state.show_add_form_creation

    if st.session_state.show_add_form_creation:
        nom_creation = nom_creation_widget("Nom création", "add")

        st.markdown("### Tissus utilisés")
        tissus_details = construire_formulaire_tissus(df_tissus, "add")

        st.markdown("### Accessoires utilisés")
        accessoires_details = construire_formulaire_accessoires(df_accessoires, "add")

        cout_tissus = sum(item["cout"] for item in tissus_details)
        cout_accessoires = sum(item["cout"] for item in accessoires_details)
        cout_fabrication = cout_tissus + cout_accessoires

        st.markdown("### Calculs")
        st.write(f"**Coût fabrication :** {cout_fabrication:.2f} €")

        heures = st.number_input(
            "Heures de fabrication",
            min_value=0.0,
            value=0.0,
            step=0.5,
            key="add_heures"
        )

        st.write(f"**Taux horaire fixe :** {TAUX_HORAIRE:.2f} € / heure")

        prix_vente_conseille = calculer_prix_vente_conseille(cout_fabrication, heures)
        st.write(f"**Prix de vente conseillé :** {prix_vente_conseille:.2f} €")

        prix_vente_retenu = st.number_input(
            "Prix de vente retenu",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="add_prix_vente_retenu"
        )

        marge_euros = prix_vente_retenu - cout_fabrication
        marge_pourcentage = calculer_marge_pourcentage(marge_euros, prix_vente_retenu)

        st.write(f"**Marge en € :** {marge_euros:.2f} €")
        st.write(f"**Marge en % :** {marge_pourcentage:.2f} %")

        stock = st.number_input(
            "Stock créations",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="add_stock_creation"
        )

        seuil_alerte = st.number_input(
            "Seuil alerte stock créations",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="add_seuil_creation"
        )

        commentaire = st.text_area("Commentaires", key="add_commentaire")
        photo = st.file_uploader("Photo", type=["jpg", "jpeg", "png"], key="add_photo_creation")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Ajouter la création", key="btn_add_creation"):
                if str(nom_creation).strip() == "":
                    st.error("Le nom de la création est obligatoire.")
                else:
                    ajouter_creation(
                        nom_creation.strip(),
                        tissus_details,
                        accessoires_details,
                        heures,
                        prix_vente_retenu,
                        stock,
                        seuil_alerte,
                        commentaire,
                        photo
                    )
                    st.session_state.show_add_form_creation = False
                    st.success("Création ajoutée avec succès !")
                    st.rerun()

        with col2:
            if st.button("❌ Annuler", key="btn_cancel_creation"):
                st.session_state.show_add_form_creation = False
                st.rerun()

    df_filtre = df_creations.copy()

    if not df_filtre.empty:
        if recherche:
            df_filtre = df_filtre[
                df_filtre["nom_creation"].fillna("").str.contains(recherche, case=False, na=False)
            ]

        mapping_tri = {
            "Nom": "nom_creation",
            "Coût fabrication": "cout_fabrication",
            "Prix conseillé": "prix_vente_conseille",
            "Prix retenu": "prix_vente_retenu",
            "Marge €": "marge_euros",
            "Marge %": "marge_pourcentage",
            "Stock": "stock"
        }

        ascending = tri_ordre == "Croissant"
        df_filtre = df_filtre.sort_values(by=mapping_tri[tri_colonne], ascending=ascending)

    section_titre("Mes créations")

    if df_filtre.empty:
        st.info("Aucune création enregistrée.")
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
                st.subheader(row["nom_creation"] if pd.notna(row["nom_creation"]) else "")
                st.write(f"**Coût fabrication :** {float(row['cout_fabrication']):.2f} €")
                st.write(f"**Prix de vente conseillé :** {float(row['prix_vente_conseille']):.2f} €")
                st.write(f"**Prix de vente retenu :** {float(row['prix_vente_retenu']):.2f} €")
                st.write(f"**Marge en € :** {float(row['marge_euros']):.2f} €")
                st.write(f"**Marge en % :** {float(row['marge_pourcentage']):.2f} %")
                st.write(f"**Stock :** {float(row['stock']):.2f}")
                st.write(f"**Seuil alerte :** {float(row['seuil_alerte']):.2f}")
                st.write(f"**Commentaire :** {row['commentaire'] if pd.notna(row['commentaire']) else ''}")

                if float(row["stock"]) < float(row["seuil_alerte"]):
                    st.error("Stock faible")

                details_tissus = get_details_tissus(row["id"])
                details_accessoires = get_details_accessoires(row["id"])

                if not details_tissus.empty:
                    st.markdown("**Tissus utilisés :**")
                    for _, t in details_tissus.iterrows():
                        st.write(
                            f"- {t['nom_tissu']} | {float(t['longueur']):.2f} m x {float(t['largeur']):.2f} m | "
                            f"{int(t['nombre_coupes'])} coupe(s) | {float(t['prix_m2']):.2f} €/m² | "
                            f"Coût : {float(t['cout']):.2f} €"
                        )

                if not details_accessoires.empty:
                    st.markdown("**Accessoires utilisés :**")
                    for _, a in details_accessoires.iterrows():
                        unite_affichee = a["unite"] if pd.notna(a["unite"]) and a["unite"] else "unité"
                        st.write(
                            f"- {a['nom_accessoire']} | {float(a['quantite']):.2f} {unite_affichee} | "
                            f"{float(a['prix_unitaire']):.2f} € / {unite_affichee} | "
                            f"Coût : {float(a['cout']):.2f} €"
                        )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("✏️ Modifier", key=f"creation_edit_btn_{row['id']}"):
                        st.session_state[f"creation_edit_{row['id']}"] = not st.session_state.get(
                            f"creation_edit_{row['id']}", False
                        )

                with col_btn2:
                    if st.button("❌ Supprimer", key=f"creation_delete_btn_{row['id']}"):
                        st.session_state[f"creation_confirm_delete_{row['id']}"] = True

            if st.session_state.get(f"creation_confirm_delete_{row['id']}", False):
                st.warning("⚠️ Voulez-vous vraiment supprimer cette création ?")

                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("✅ Oui", key=f"creation_yes_{row['id']}"):
                        supprimer_creation(row["id"])
                        st.session_state[f"creation_confirm_delete_{row['id']}"] = False
                        st.success("Création supprimée.")
                        st.rerun()

                with col_no:
                    if st.button("❌ Non", key=f"creation_no_{row['id']}"):
                        st.session_state[f"creation_confirm_delete_{row['id']}"] = False
                        st.rerun()

            if st.session_state.get(f"creation_edit_{row['id']}", False):
                st.markdown("### Modifier cette création")

                details_tissus = get_details_tissus(row["id"])
                details_accessoires = get_details_accessoires(row["id"])

                details_tissus_list = details_tissus.to_dict("records") if not details_tissus.empty else []
                details_accessoires_list = details_accessoires.to_dict("records") if not details_accessoires.empty else []

                edit_nom = nom_creation_widget(
                    "Nom création",
                    f"edit_{row['id']}",
                    row["nom_creation"] if pd.notna(row["nom_creation"]) else ""
                )

                st.markdown("### Tissus utilisés")
                edit_tissus_details = construire_formulaire_tissus(
                    df_tissus,
                    f"edit_{row['id']}",
                    details_tissus_list
                )

                st.markdown("### Accessoires utilisés")
                edit_accessoires_details = construire_formulaire_accessoires(
                    df_accessoires,
                    f"edit_{row['id']}",
                    details_accessoires_list
                )

                edit_cout_tissus = sum(item["cout"] for item in edit_tissus_details)
                edit_cout_accessoires = sum(item["cout"] for item in edit_accessoires_details)
                edit_cout_fabrication = edit_cout_tissus + edit_cout_accessoires

                st.markdown("### Calculs")
                st.write(f"**Coût fabrication :** {edit_cout_fabrication:.2f} €")

                edit_heures = st.number_input(
                    "Heures de fabrication",
                    min_value=0.0,
                    value=float(row["heures"]) if pd.notna(row["heures"]) else 0.0,
                    step=0.5,
                    key=f"edit_heures_{row['id']}"
                )

                st.write(f"**Taux horaire fixe :** {TAUX_HORAIRE:.2f} € / heure")

                edit_prix_vente_conseille = calculer_prix_vente_conseille(edit_cout_fabrication, edit_heures)
                st.write(f"**Prix de vente conseillé :** {edit_prix_vente_conseille:.2f} €")

                edit_prix_vente_retenu = st.number_input(
                    "Prix de vente retenu",
                    min_value=0.0,
                    value=float(row["prix_vente_retenu"]) if pd.notna(row["prix_vente_retenu"]) else 0.0,
                    step=1.0,
                    key=f"edit_prix_retenu_{row['id']}"
                )

                edit_marge_euros = edit_prix_vente_retenu - edit_cout_fabrication
                edit_marge_pourcentage = calculer_marge_pourcentage(edit_marge_euros, edit_prix_vente_retenu)

                st.write(f"**Marge en € :** {edit_marge_euros:.2f} €")
                st.write(f"**Marge en % :** {edit_marge_pourcentage:.2f} %")

                edit_stock = st.number_input(
                    "Stock créations",
                    min_value=0.0,
                    value=float(row["stock"]) if pd.notna(row["stock"]) else 0.0,
                    step=1.0,
                    key=f"edit_stock_creation_{row['id']}"
                )

                edit_seuil_alerte = st.number_input(
                    "Seuil alerte stock créations",
                    min_value=0.0,
                    value=float(row["seuil_alerte"]) if pd.notna(row["seuil_alerte"]) else 0.0,
                    step=1.0,
                    key=f"edit_seuil_creation_{row['id']}"
                )

                edit_commentaire = st.text_area(
                    "Commentaires",
                    value=row["commentaire"] if pd.notna(row["commentaire"]) else "",
                    key=f"edit_commentaire_{row['id']}"
                )

                edit_photo = st.file_uploader(
                    "Nouvelle photo (optionnel)",
                    type=["jpg", "jpeg", "png"],
                    key=f"edit_photo_creation_{row['id']}"
                )

                col_save, col_cancel = st.columns(2)

                with col_save:
                    if st.button("💾 Enregistrer les modifications", key=f"save_creation_{row['id']}"):
                        if str(edit_nom).strip() == "":
                            st.error("Le nom de la création est obligatoire.")
                        else:
                            modifier_creation(
                                row["id"],
                                str(edit_nom).strip(),
                                edit_tissus_details,
                                edit_accessoires_details,
                                edit_heures,
                                edit_prix_vente_retenu,
                                edit_stock,
                                edit_seuil_alerte,
                                edit_commentaire,
                                edit_photo
                            )
                            st.session_state[f"creation_edit_{row['id']}"] = False
                            st.success("Création modifiée avec succès !")
                            st.rerun()

                with col_cancel:
                    if st.button("Annuler", key=f"cancel_edit_creation_{row['id']}"):
                        st.session_state[f"creation_edit_{row['id']}"] = False
                        st.rerun()

            st.write("---")