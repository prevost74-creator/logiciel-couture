import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)


def ajouter_colonne_si_absente(cursor, nom_table, nom_colonne, definition):
    cursor.execute(f"PRAGMA table_info({nom_table})")
    colonnes = [col[1] for col in cursor.fetchall()]
    if nom_colonne not in colonnes:
        cursor.execute(f"ALTER TABLE {nom_table} ADD COLUMN {nom_colonne} {definition}")


def initialiser_bdd():
    conn = sqlite3.connect("gestion_couture.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tissus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        type TEXT,
        couleur TEXT,
        largeur REAL,
        grammage REAL,
        quantite REAL,
        prix REAL,
        fournisseur TEXT,
        seuil_alerte REAL,
        commentaire TEXT,
        photo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accessoires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        type_accessoire TEXT,
        couleur TEXT,
        fournisseur TEXT,
        quantite_longueur REAL,
        unite TEXT,
        stock REAL,
        seuil_alerte REAL,
        prix REAL,
        prix_unitaire REAL,
        commentaire TEXT,
        photo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS creations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_creation TEXT NOT NULL,
        cout_tissus REAL DEFAULT 0,
        cout_accessoires REAL DEFAULT 0,
        cout_fabrication REAL DEFAULT 0,
        heures REAL DEFAULT 0,
        taux_horaire REAL DEFAULT 0,
        coefficient_marge REAL DEFAULT 0,
        prix_vente_conseille REAL DEFAULT 0,
        prix_vente_retenu REAL DEFAULT 0,
        marge_euros REAL DEFAULT 0,
        marge_pourcentage REAL DEFAULT 0,
        stock REAL DEFAULT 0,
        seuil_alerte REAL DEFAULT 0,
        commentaire TEXT,
        photo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS creation_tissus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creation_id INTEGER NOT NULL,
        tissu_id INTEGER,
        nom_tissu TEXT,
        longueur REAL DEFAULT 0,
        largeur REAL DEFAULT 0,
        prix_m2 REAL DEFAULT 0,
        nombre_coupes REAL DEFAULT 1,
        cout REAL DEFAULT 0,
        FOREIGN KEY (creation_id) REFERENCES creations(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS creation_accessoires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creation_id INTEGER NOT NULL,
        accessoire_id INTEGER,
        nom_accessoire TEXT,
        quantite REAL DEFAULT 0,
        unite TEXT,
        prix_unitaire REAL DEFAULT 0,
        cout REAL DEFAULT 0,
        FOREIGN KEY (creation_id) REFERENCES creations(id) ON DELETE CASCADE
    )
    """)

    # Vente = entête
    cursor.execute("""
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
    """)

    # Une vente peut contenir plusieurs créations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vente_lignes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vente_id INTEGER NOT NULL,
        creation_id INTEGER NOT NULL,
        nom_creation_snapshot TEXT,
        quantite REAL DEFAULT 0,
        prix_vente_unitaire REAL DEFAULT 0,
        total_ligne REAL DEFAULT 0,
        cout_unitaire REAL DEFAULT 0,
        cout_total_ligne REAL DEFAULT 0,
        marge_unitaire REAL DEFAULT 0,
        marge_totale_ligne REAL DEFAULT 0,
        FOREIGN KEY (vente_id) REFERENCES ventes(id) ON DELETE CASCADE,
        FOREIGN KEY (creation_id) REFERENCES creations(id)
    )
    """)

    ajouter_colonne_si_absente(cursor, "creations", "stock", "REAL DEFAULT 0")
    ajouter_colonne_si_absente(cursor, "creations", "seuil_alerte", "REAL DEFAULT 0")

    # Compatibilité si l'ancienne table ventes existe déjà
    for nom_colonne, definition in {
        "client": "TEXT",
        "mode_paiement": "TEXT",
        "commentaire": "TEXT",
        "total_vente": "REAL DEFAULT 0",
        "cout_total": "REAL DEFAULT 0",
        "marge_totale": "REAL DEFAULT 0",
    }.items():
        ajouter_colonne_si_absente(cursor, "ventes", nom_colonne, definition)

    conn.commit()
    conn.close()
