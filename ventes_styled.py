import os
from style import section_titre
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
from datetime import date

import pandas as pd
import streamlit as st

MODES_PAIEMENT = [
    "",
    "Espèces",
    "Carte bancaire",
    "Virement",
    "PayPal",
    "Chèque",
    "Autre",
]

DOSSIER_PHOTOS_CREATIONS = "photos_creations"


def get_connection():
    conn = sqlite3.connect("gestion_couture.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_exists(cursor, table_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()


def get_foreign_keys(cursor, table_name):
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return cursor.fetchall()


def schema_ventes_est_ancien(cursor):
    if not table_exists(cursor, "ventes"):
        return False
    colonnes = get_columns(cursor, "ventes")
    noms = [col[1] for col in colonnes]
    return "creation_id" in noms


def creer_table_ventes(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_vente TEXT NOT NULL,
            client TEXT,
            mode_paiement TEXT,
            commentaire TEXT,
            total_vente REAL DEFAULT 0,
            cout_total REAL DEFAULT 0,
            marge_totale REAL DEFAULT 0
        )
        """
    )


def creer_table_vente_lignes(cursor):
    # creation_id est volontairement nullable et sans contrainte forte
    # pour garder l'historique des ventes même si une création est supprimée plus tard.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vente_lignes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vente_id INTEGER NOT NULL,
            creation_id INTEGER,
            nom_creation_snapshot TEXT,
            photo_snapshot TEXT,
            quantite REAL DEFAULT 0,
            prix_vente_unitaire REAL DEFAULT 0,
            total_ligne REAL DEFAULT 0,
            cout_unitaire REAL DEFAULT 0,
            cout_total_ligne REAL DEFAULT 0,
            marge_unitaire REAL DEFAULT 0,
            marge_totale_ligne REAL DEFAULT 0,
            FOREIGN KEY (vente_id) REFERENCES ventes(id) ON DELETE CASCADE
        )
        """
    )


def migrer_ancienne_table_ventes(cursor):
    colonnes = [col[1] for col in get_columns(cursor, "ventes")]
    anciennes_lignes = []

    if "creation_id" in colonnes:
        cursor.execute(
            """
            SELECT
                id,
                date_vente,
                creation_id,
                nom_creation_snapshot,
                quantite,
                prix_vente_unitaire,
                total_vente,
                cout_unitaire,
                cout_total,
                marge_unitaire,
                marge_totale,
                client,
                mode_paiement,
                commentaire
            FROM ventes
            ORDER BY id
            """
        )
        anciennes_lignes = cursor.fetchall()

    cursor.execute("ALTER TABLE ventes RENAME TO ventes_ancienne_backup")
    creer_table_ventes(cursor)
    creer_table_vente_lignes(cursor)

    for ligne in anciennes_lignes:
        (
            _ancien_id,
            date_vente,
            creation_id,
            nom_creation_snapshot,
            quantite,
            prix_vente_unitaire,
            total_vente,
            cout_unitaire,
            cout_total,
            marge_unitaire,
            marge_totale,
            client,
            mode_paiement,
            commentaire,
        ) = ligne

        cursor.execute(
            """
            INSERT INTO ventes (
                date_vente, client, mode_paiement, commentaire,
                total_vente, cout_total, marge_totale
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date_vente,
                client,
                mode_paiement,
                commentaire,
                float(total_vente or 0),
                float(cout_total or 0),
                float(marge_totale or 0),
            ),
        )
        nouveau_vente_id = cursor.lastrowid

        photo_snapshot = None
        if creation_id is not None:
            cursor.execute("SELECT photo FROM creations WHERE id = ?", (int(creation_id),))
            result_photo = cursor.fetchone()
            photo_snapshot = result_photo[0] if result_photo else None

        cursor.execute(
            """
            INSERT INTO vente_lignes (
                vente_id, creation_id, nom_creation_snapshot, photo_snapshot, quantite,
                prix_vente_unitaire, total_ligne, cout_unitaire,
                cout_total_ligne, marge_unitaire, marge_totale_ligne
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nouveau_vente_id,
                int(creation_id) if creation_id is not None else None,
                nom_creation_snapshot,
                photo_snapshot,
                float(quantite or 0),
                float(prix_vente_unitaire or 0),
                float(total_vente or 0),
                float(cout_unitaire or 0),
                float(cout_total or 0),
                float(marge_unitaire or 0),
                float(marge_totale or 0),
            ),
        )


def migrer_vente_lignes_si_necessaire(cursor):
    if not table_exists(cursor, "vente_lignes"):
        creer_table_vente_lignes(cursor)
        return

    colonnes = [col[1] for col in get_columns(cursor, "vente_lignes")]
    fks = get_foreign_keys(cursor, "vente_lignes")
    fk_sur_creation = any(fk[2] == "creations" for fk in fks)
    photo_snapshot_absente = "photo_snapshot" not in colonnes

    if not fk_sur_creation and not photo_snapshot_absente:
        return

    cursor.execute(
        """
        SELECT
            id,
            vente_id,
            creation_id,
            nom_creation_snapshot,
            quantite,
            prix_vente_unitaire,
            total_ligne,
            cout_unitaire,
            cout_total_ligne,
            marge_unitaire,
            marge_totale_ligne
        FROM vente_lignes
        ORDER BY id
        """
    )
    anciennes_lignes = cursor.fetchall()

    cursor.execute("ALTER TABLE vente_lignes RENAME TO vente_lignes_backup")
    creer_table_vente_lignes(cursor)

    for ligne in anciennes_lignes:
        (
            _id,
            vente_id,
            creation_id,
            nom_creation_snapshot,
            quantite,
            prix_vente_unitaire,
            total_ligne,
            cout_unitaire,
            cout_total_ligne,
            marge_unitaire,
            marge_totale_ligne,
        ) = ligne

        photo_snapshot = None
        if creation_id is not None:
            cursor.execute("SELECT photo FROM creations WHERE id = ?", (int(creation_id),))
            result_photo = cursor.fetchone()
            photo_snapshot = result_photo[0] if result_photo else None

        cursor.execute(
            """
            INSERT INTO vente_lignes (
                vente_id, creation_id, nom_creation_snapshot, photo_snapshot, quantite,
                prix_vente_unitaire, total_ligne, cout_unitaire,
                cout_total_ligne, marge_unitaire, marge_totale_ligne
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vente_id,
                creation_id,
                nom_creation_snapshot,
                photo_snapshot,
                float(quantite or 0),
                float(prix_vente_unitaire or 0),
                float(total_ligne or 0),
                float(cout_unitaire or 0),
                float(cout_total_ligne or 0),
                float(marge_unitaire or 0),
                float(marge_totale_ligne or 0),
            ),
        )


def initialiser_tables_ventes():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if schema_ventes_est_ancien(cursor):
            migrer_ancienne_table_ventes(cursor)
        else:
            creer_table_ventes(cursor)
            migrer_vente_lignes_si_necessaire(cursor)

        colonnes_ventes = [col[1] for col in get_columns(cursor, "ventes")]
        ajouts_ventes = {
            "client": "TEXT",
            "mode_paiement": "TEXT",
            "commentaire": "TEXT",
            "total_vente": "REAL DEFAULT 0",
            "cout_total": "REAL DEFAULT 0",
            "marge_totale": "REAL DEFAULT 0",
        }
        for nom, definition in ajouts_ventes.items():
            if nom not in colonnes_ventes:
                cursor.execute(f"ALTER TABLE ventes ADD COLUMN {nom} {definition}")

        colonnes_lignes = [col[1] for col in get_columns(cursor, "vente_lignes")]
        if "photo_snapshot" not in colonnes_lignes:
            cursor.execute("ALTER TABLE vente_lignes ADD COLUMN photo_snapshot TEXT")

        conn.commit()
    finally:
        conn.close()


def charger_creations_disponibles():
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """
            SELECT id, nom_creation, cout_fabrication, prix_vente_retenu, stock, seuil_alerte, photo
            FROM creations
            ORDER BY nom_creation
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "nom_creation",
                "cout_fabrication",
                "prix_vente_retenu",
                "stock",
                "seuil_alerte",
                "photo",
            ]
        )

    for col in ["cout_fabrication", "prix_vente_retenu", "stock", "seuil_alerte"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def charger_ventes_detaillees():
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """
            SELECT
                v.id AS vente_id,
                v.date_vente,
                v.client,
                v.mode_paiement,
                v.commentaire,
                v.total_vente AS total_vente_global,
                v.cout_total AS cout_total_global,
                v.marge_totale AS marge_totale_global,
                vl.id AS ligne_id,
                vl.creation_id,
                vl.nom_creation_snapshot,
                vl.photo_snapshot,
                vl.quantite,
                vl.prix_vente_unitaire,
                vl.total_ligne,
                vl.cout_unitaire,
                vl.cout_total_ligne,
                vl.marge_unitaire,
                vl.marge_totale_ligne,
                c.nom_creation,
                c.photo AS photo_creation_actuelle
            FROM ventes v
            LEFT JOIN vente_lignes vl ON vl.vente_id = v.id
            LEFT JOIN creations c ON c.id = vl.creation_id
            ORDER BY v.date_vente DESC, v.id DESC, vl.id ASC
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "vente_id",
                "date_vente",
                "client",
                "mode_paiement",
                "commentaire",
                "total_vente_global",
                "cout_total_global",
                "marge_totale_global",
                "ligne_id",
                "creation_id",
                "nom_creation_snapshot",
                "photo_snapshot",
                "quantite",
                "prix_vente_unitaire",
                "total_ligne",
                "cout_unitaire",
                "cout_total_ligne",
                "marge_unitaire",
                "marge_totale_ligne",
                "nom_creation",
                "photo_creation_actuelle",
            ]
        )

    for col in [
        "total_vente_global",
        "cout_total_global",
        "marge_totale_global",
        "quantite",
        "prix_vente_unitaire",
        "total_ligne",
        "cout_unitaire",
        "cout_total_ligne",
        "marge_unitaire",
        "marge_totale_ligne",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def charger_vente_complete(vente_id):
    conn = get_connection()
    try:
        vente = pd.read_sql_query(
            "SELECT * FROM ventes WHERE id = ?",
            conn,
            params=(vente_id,),
        )
        lignes = pd.read_sql_query(
            "SELECT * FROM vente_lignes WHERE vente_id = ? ORDER BY id",
            conn,
            params=(vente_id,),
        )
    finally:
        conn.close()
    return vente, lignes


def _preparer_lignes(cursor, lignes):
    if not lignes:
        raise ValueError("Ajoute au moins un produit à la vente.")

    total_vente_global = 0.0
    cout_total_global = 0.0
    marge_totale_global = 0.0
    lignes_preparees = []

    for ligne in lignes:
        creation_id = int(ligne["creation_id"])
        quantite = float(ligne["quantite"])

        if quantite <= 0:
            raise ValueError("Chaque quantité doit être supérieure à 0.")

        cursor.execute(
            """
            SELECT nom_creation, cout_fabrication, prix_vente_retenu, stock, photo
            FROM creations
            WHERE id = ?
            """,
            (creation_id,),
        )
        creation = cursor.fetchone()

        if creation is None:
            raise ValueError("Une création sélectionnée est introuvable.")

        nom_creation, cout_fabrication, prix_vente_retenu, stock_actuel, photo = creation
        cout_fabrication = float(cout_fabrication or 0)
        prix_vente_retenu = float(prix_vente_retenu or 0)
        stock_actuel = float(stock_actuel or 0)

        if quantite > stock_actuel:
            raise ValueError(f"Stock insuffisant pour '{nom_creation}'.")

        prix_vente_unitaire = prix_vente_retenu
        total_ligne = quantite * prix_vente_unitaire
        cout_total_ligne = quantite * cout_fabrication
        marge_unitaire = prix_vente_unitaire - cout_fabrication
        marge_totale_ligne = total_ligne - cout_total_ligne

        total_vente_global += total_ligne
        cout_total_global += cout_total_ligne
        marge_totale_global += marge_totale_ligne

        lignes_preparees.append(
            {
                "creation_id": creation_id,
                "nom_creation_snapshot": nom_creation,
                "photo_snapshot": photo,
                "quantite": quantite,
                "prix_vente_unitaire": prix_vente_unitaire,
                "total_ligne": total_ligne,
                "cout_unitaire": cout_fabrication,
                "cout_total_ligne": cout_total_ligne,
                "marge_unitaire": marge_unitaire,
                "marge_totale_ligne": marge_totale_ligne,
            }
        )

    return lignes_preparees, total_vente_global, cout_total_global, marge_totale_global


def enregistrer_vente_multi(date_vente, client, mode_paiement, commentaire, lignes):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        lignes_preparees, total_vente_global, cout_total_global, marge_totale_global = _preparer_lignes(cursor, lignes)

        cursor.execute(
            """
            INSERT INTO ventes (
                date_vente, client, mode_paiement, commentaire,
                total_vente, cout_total, marge_totale
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(date_vente),
                (client or "").strip(),
                mode_paiement,
                (commentaire or "").strip(),
                total_vente_global,
                cout_total_global,
                marge_totale_global,
            ),
        )
        vente_id = cursor.lastrowid

        for ligne in lignes_preparees:
            cursor.execute(
                """
                INSERT INTO vente_lignes (
                    vente_id, creation_id, nom_creation_snapshot, photo_snapshot, quantite,
                    prix_vente_unitaire, total_ligne, cout_unitaire,
                    cout_total_ligne, marge_unitaire, marge_totale_ligne
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vente_id,
                    ligne["creation_id"],
                    ligne["nom_creation_snapshot"],
                    ligne["photo_snapshot"],
                    ligne["quantite"],
                    ligne["prix_vente_unitaire"],
                    ligne["total_ligne"],
                    ligne["cout_unitaire"],
                    ligne["cout_total_ligne"],
                    ligne["marge_unitaire"],
                    ligne["marge_totale_ligne"],
                ),
            )
            cursor.execute(
                "UPDATE creations SET stock = stock - ? WHERE id = ?",
                (ligne["quantite"], ligne["creation_id"]),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def supprimer_vente(vente_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT creation_id, quantite FROM vente_lignes WHERE vente_id = ?",
            (vente_id,),
        )
        lignes = cursor.fetchall()

        for creation_id, quantite in lignes:
            if creation_id is not None:
                cursor.execute(
                    "UPDATE creations SET stock = stock + ? WHERE id = ?",
                    (float(quantite or 0), int(creation_id)),
                )

        cursor.execute("DELETE FROM vente_lignes WHERE vente_id = ?", (vente_id,))
        cursor.execute("DELETE FROM ventes WHERE id = ?", (vente_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def modifier_vente(vente_id, date_vente, client, mode_paiement, commentaire, nouvelles_lignes):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT creation_id, quantite FROM vente_lignes WHERE vente_id = ?",
            (vente_id,),
        )
        anciennes_lignes = cursor.fetchall()
        for creation_id, quantite in anciennes_lignes:
            if creation_id is not None:
                cursor.execute(
                    "UPDATE creations SET stock = stock + ? WHERE id = ?",
                    (float(quantite or 0), int(creation_id)),
                )

        lignes_preparees, total_vente_global, cout_total_global, marge_totale_global = _preparer_lignes(cursor, nouvelles_lignes)

        cursor.execute(
            """
            UPDATE ventes
            SET date_vente = ?, client = ?, mode_paiement = ?, commentaire = ?,
                total_vente = ?, cout_total = ?, marge_totale = ?
            WHERE id = ?
            """,
            (
                str(date_vente),
                (client or "").strip(),
                mode_paiement,
                (commentaire or "").strip(),
                total_vente_global,
                cout_total_global,
                marge_totale_global,
                vente_id,
            ),
        )

        cursor.execute("DELETE FROM vente_lignes WHERE vente_id = ?", (vente_id,))

        for ligne in lignes_preparees:
            cursor.execute(
                """
                INSERT INTO vente_lignes (
                    vente_id, creation_id, nom_creation_snapshot, photo_snapshot, quantite,
                    prix_vente_unitaire, total_ligne, cout_unitaire,
                    cout_total_ligne, marge_unitaire, marge_totale_ligne
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vente_id,
                    ligne["creation_id"],
                    ligne["nom_creation_snapshot"],
                    ligne["photo_snapshot"],
                    ligne["quantite"],
                    ligne["prix_vente_unitaire"],
                    ligne["total_ligne"],
                    ligne["cout_unitaire"],
                    ligne["cout_total_ligne"],
                    ligne["marge_unitaire"],
                    ligne["marge_totale_ligne"],
                ),
            )
            cursor.execute(
                "UPDATE creations SET stock = stock - ? WHERE id = ?",
                (ligne["quantite"], ligne["creation_id"]),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialiser_session():
    if "vente_lignes_form" not in st.session_state:
        st.session_state.vente_lignes_form = []
    if "show_add_form_vente" not in st.session_state:
        st.session_state.show_add_form_vente = False


def ajouter_ligne_formulaire():
    st.session_state.vente_lignes_form.append({"creation_id": None, "quantite": 1.0})


def supprimer_ligne_formulaire(index):
    if 0 <= index < len(st.session_state.vente_lignes_form):
        st.session_state.vente_lignes_form.pop(index)


def vider_formulaire():
    st.session_state.vente_lignes_form = []
    st.session_state.show_add_form_vente = False


def _render_lignes_vente(df_creations, prefixe, lignes_initiales=None):
    creations_map = {
        f"{row['nom_creation']} (stock : {float(row['stock']):.0f})": row
        for _, row in df_creations.iterrows()
    }
    options = [""] + list(creations_map.keys())
    id_to_label = {int(row["id"]): label for label, row in creations_map.items()}

    if lignes_initiales is None:
        nb_lignes = len(st.session_state.vente_lignes_form)
    else:
        nb_lignes = len(lignes_initiales)

    lignes_valides = []

    for i in range(nb_lignes):
        ligne_init = lignes_initiales[i] if lignes_initiales is not None else st.session_state.vente_lignes_form[i]
        default_id = ligne_init.get("creation_id") if ligne_init else None
        index_defaut = options.index(id_to_label[default_id]) if default_id in id_to_label else 0
        quantite_defaut = float(ligne_init.get("quantite", 1.0)) if ligne_init else 1.0

        col_a, col_b, col_c, col_d, col_e = st.columns([3, 1.1, 1.2, 1.2, 0.8])

        with col_a:
            selected_label = st.selectbox(
                f"Création {i + 1}",
                options,
                index=index_defaut,
                key=f"{prefixe}_creation_{i}",
                label_visibility="collapsed",
            )

        creation_selectionnee = creations_map.get(selected_label)

        with col_b:
            quantite = st.number_input(
                f"Quantité {i + 1}",
                min_value=1.0,
                value=quantite_defaut,
                step=1.0,
                key=f"{prefixe}_quantite_{i}",
                label_visibility="collapsed",
            )

        if creation_selectionnee is not None:
            prix_unitaire = float(creation_selectionnee["prix_vente_retenu"])
            cout_unitaire = float(creation_selectionnee["cout_fabrication"])
            stock_dispo = float(creation_selectionnee["stock"])
            total_ligne = prix_unitaire * quantite
            marge_ligne = (prix_unitaire - cout_unitaire) * quantite
        else:
            prix_unitaire = 0.0
            cout_unitaire = 0.0
            stock_dispo = 0.0
            total_ligne = 0.0
            marge_ligne = 0.0

        with col_c:
            st.number_input(
                f"PU {i + 1}",
                min_value=0.0,
                value=float(prix_unitaire),
                step=0.01,
                key=f"{prefixe}_pu_{i}",
                disabled=True,
                label_visibility="collapsed",
            )

        with col_d:
            st.number_input(
                f"Total {i + 1}",
                min_value=0.0,
                value=float(total_ligne),
                step=0.01,
                key=f"{prefixe}_total_{i}",
                disabled=True,
                label_visibility="collapsed",
            )

        with col_e:
            if lignes_initiales is None:
                if st.button("🗑️", key=f"del_line_{prefixe}_{i}"):
                    supprimer_ligne_formulaire(i)
                    st.rerun()

        if creation_selectionnee is not None:
            st.caption(
                f"Stock dispo : {stock_dispo:.0f} | Coût unitaire : {cout_unitaire:.2f} € | Marge ligne : {marge_ligne:.2f} €"
            )
            lignes_valides.append(
                {
                    "creation_id": int(creation_selectionnee["id"]),
                    "quantite": float(quantite),
                    "total_ligne": total_ligne,
                    "marge_ligne": marge_ligne,
                }
            )
        else:
            st.caption("Sélectionne une création pour cette ligne.")

    return lignes_valides


def afficher_photo_top(nom_photo):
    if not nom_photo:
        return
    chemin_photo = os.path.join(DOSSIER_PHOTOS_CREATIONS, nom_photo)
    if os.path.exists(chemin_photo):
        st.image(chemin_photo, width=220)


def afficher_page():
    initialiser_tables_ventes()
    initialiser_session()

    section_titre("Mes ventes")

    df_creations = charger_creations_disponibles()
    df_ventes = charger_ventes_detaillees()

    ca_total = float(df_ventes["total_ligne"].sum()) if not df_ventes.empty else 0.0
    marge_totale = float(df_ventes["marge_totale_ligne"].sum()) if not df_ventes.empty else 0.0
    nb_ventes = int(df_ventes["vente_id"].nunique()) if not df_ventes.empty else 0
    quantite_totale = float(df_ventes["quantite"].sum()) if not df_ventes.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💶 Chiffre d’affaires", f"{ca_total:.2f} €")
    col2.metric("📈 Marge totale", f"{marge_totale:.2f} €")
    col3.metric("🧾 Nombre de ventes", nb_ventes)
    col4.metric("🪡 Quantité vendue", f"{quantite_totale:.0f}")

    st.write("---")
    section_titre("Ajouter une vente")

    if st.button("➕ Nouvelle vente"):
        st.session_state.show_add_form_vente = not st.session_state.show_add_form_vente
        if st.session_state.show_add_form_vente and not st.session_state.vente_lignes_form:
            ajouter_ligne_formulaire()

    if st.session_state.show_add_form_vente:
        if df_creations.empty:
            st.warning("Aucune création disponible. Ajoute d’abord une création en stock.")
        else:
            date_vente = st.date_input("Date de vente", value=date.today(), key="vente_date")
            client = st.text_input("Client", key="vente_client")
            mode_paiement = st.selectbox("Mode de paiement", MODES_PAIEMENT, key="vente_mode")
            commentaire = st.text_area("Commentaire", key="vente_commentaire")

            st.subheader("Produits vendus")
            lignes_valides = _render_lignes_vente(df_creations, "add")

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("➕ Ajouter un produit"):
                    ajouter_ligne_formulaire()
                    st.rerun()

            total_vente = sum(l["total_ligne"] for l in lignes_valides)
            marge_vente = sum(l["marge_ligne"] for l in lignes_valides)
            st.info(f"Total de la vente : {total_vente:.2f} € | Marge totale : {marge_vente:.2f} €")

            with col_btn2:
                if st.button("✅ Valider la vente"):
                    if not lignes_valides:
                        st.error("Ajoute au moins un produit valide.")
                    else:
                        try:
                            enregistrer_vente_multi(
                                date_vente=date_vente,
                                client=client,
                                mode_paiement=mode_paiement,
                                commentaire=commentaire,
                                lignes=lignes_valides,
                            )
                            vider_formulaire()
                            st.success("Vente enregistrée avec succès.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

            with col_btn3:
                if st.button("❌ Annuler"):
                    vider_formulaire()
                    st.rerun()

    st.write("---")
    section_titre("Historique des ventes")

    if df_ventes.empty:
        st.info("Aucune vente enregistrée.")
        return

    df_groupes = (
        df_ventes.groupby("vente_id", dropna=False)
        .agg(
            date_vente=("date_vente", "first"),
            client=("client", "first"),
            mode_paiement=("mode_paiement", "first"),
            commentaire=("commentaire", "first"),
            total_vente=("total_vente_global", "first"),
            marge_totale=("marge_totale_global", "first"),
        )
        .reset_index()
        .sort_values(by=["date_vente", "vente_id"], ascending=[False, False])
    )

    for _, vente in df_groupes.iterrows():
        vente_id = int(vente["vente_id"])
        st.write("---")
        st.subheader(f"Vente n°{vente_id} — {vente['date_vente']}")
        st.write(f"**Client :** {vente['client'] or ''}")
        st.write(f"**Paiement :** {vente['mode_paiement'] or ''}")
        st.write(f"**Total :** {float(vente['total_vente'] or 0):.2f} €")
        st.write(f"**Marge :** {float(vente['marge_totale'] or 0):.2f} €")
        st.write(f"**Commentaire :** {vente['commentaire'] or ''}")

        lignes_vente = df_ventes[df_ventes["vente_id"] == vente_id][["nom_creation_snapshot", "quantite"]].copy()
        if not lignes_vente.empty:
            st.markdown("**Produits vendus :**")
            for _, produit in lignes_vente.iterrows():
                nom_produit = produit["nom_creation_snapshot"] or "Création"
                st.write(f"- {nom_produit} (x{float(produit['quantite']):g})")


        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✏️ Modifier", key=f"vente_edit_btn_{vente_id}"):
                st.session_state[f"vente_edit_{vente_id}"] = not st.session_state.get(f"vente_edit_{vente_id}", False)

        with col_btn2:
            if st.button("❌ Supprimer", key=f"vente_delete_btn_{vente_id}"):
                st.session_state[f"vente_confirm_delete_{vente_id}"] = True

        if st.session_state.get(f"vente_confirm_delete_{vente_id}", False):
            st.warning("⚠️ Voulez-vous vraiment supprimer cette vente ? Le stock des créations sera remis.")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Oui", key=f"vente_yes_{vente_id}"):
                    try:
                        supprimer_vente(vente_id)
                        st.session_state[f"vente_confirm_delete_{vente_id}"] = False
                        st.success("Vente supprimée.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with col_no:
                if st.button("❌ Non", key=f"vente_no_{vente_id}"):
                    st.session_state[f"vente_confirm_delete_{vente_id}"] = False
                    st.rerun()

        if st.session_state.get(f"vente_edit_{vente_id}", False):
            st.markdown("### Modifier cette vente")
            vente_df, lignes_df = charger_vente_complete(vente_id)
            if vente_df.empty:
                st.error("Vente introuvable.")
            else:
                vente_row = vente_df.iloc[0]
                lignes_initiales = []
                if not lignes_df.empty:
                    for _, row in lignes_df.iterrows():
                        lignes_initiales.append(
                            {
                                "creation_id": int(row["creation_id"]) if pd.notna(row["creation_id"]) else None,
                                "quantite": float(row["quantite"]),
                            }
                        )

                with st.form(f"form_edit_vente_{vente_id}"):
                    date_edit = st.date_input(
                        "Date de vente",
                        value=pd.to_datetime(vente_row["date_vente"]).date(),
                        key=f"date_edit_vente_{vente_id}",
                    )
                    client_edit = st.text_input(
                        "Client",
                        value=vente_row["client"] if pd.notna(vente_row["client"]) else "",
                        key=f"client_edit_vente_{vente_id}",
                    )
                    mode_actuel = vente_row["mode_paiement"] if pd.notna(vente_row["mode_paiement"]) else ""
                    index_mode = MODES_PAIEMENT.index(mode_actuel) if mode_actuel in MODES_PAIEMENT else 0
                    mode_edit = st.selectbox(
                        "Mode de paiement",
                        MODES_PAIEMENT,
                        index=index_mode,
                        key=f"mode_edit_vente_{vente_id}",
                    )
                    commentaire_edit = st.text_area(
                        "Commentaire",
                        value=vente_row["commentaire"] if pd.notna(vente_row["commentaire"]) else "",
                        key=f"commentaire_edit_vente_{vente_id}",
                    )

                    st.subheader("Produits vendus")
                    lignes_valides_edit = _render_lignes_vente(df_creations, f"edit_{vente_id}", lignes_initiales=lignes_initiales)
                    total_vente_edit = sum(l["total_ligne"] for l in lignes_valides_edit)
                    marge_vente_edit = sum(l["marge_ligne"] for l in lignes_valides_edit)
                    st.info(f"Total de la vente : {total_vente_edit:.2f} € | Marge totale : {marge_vente_edit:.2f} €")

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_edit = st.form_submit_button("💾 Enregistrer les modifications")
                    with col_cancel:
                        cancel_edit = st.form_submit_button("❌ Annuler")

                if save_edit:
                    try:
                        modifier_vente(
                            vente_id=vente_id,
                            date_vente=date_edit,
                            client=client_edit,
                            mode_paiement=mode_edit,
                            commentaire=commentaire_edit,
                            nouvelles_lignes=lignes_valides_edit,
                        )
                        st.session_state[f"vente_edit_{vente_id}"] = False
                        st.success("Vente modifiée avec succès.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

                if cancel_edit:
                    st.session_state[f"vente_edit_{vente_id}"] = False
                    st.rerun()

    st.write("---")
    section_titre("Top #1 des Ventes")

    top_creations = (
        df_ventes.assign(
            Creation=df_ventes["nom_creation"].fillna(df_ventes["nom_creation_snapshot"]),
            Photo=df_ventes["photo_creation_actuelle"].fillna(df_ventes["photo_snapshot"]),
        )
        .groupby("Creation", dropna=False)
        .agg(
            quantite_vendue=("quantite", "sum"),
            photo=("Photo", "first"),
        )
        .reset_index()
        .sort_values(by="quantite_vendue", ascending=False)
    )

    if top_creations.empty:
        st.info("Aucune donnée de vente pour le moment.")
    else:
        top1 = top_creations.iloc[0]
        col_photo, col_infos = st.columns([1, 2])
        with col_photo:
            afficher_photo_top(top1["photo"])
        with col_infos:
            st.markdown(f"### {top1['Creation']}")
            st.write(f"**Quantité totale vendue :** {float(top1['quantite_vendue']):.0f}")