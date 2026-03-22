import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)

conn = sqlite3.connect("gestion_couture.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS accessoires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    type_accessoire TEXT,
    couleur TEXT,
    fournisseur TEXT,
    quantite_longueur REAL DEFAULT 0,
    unite TEXT,
    stock REAL DEFAULT 0,
    seuil_alerte REAL DEFAULT 0,
    prix REAL DEFAULT 0,
    prix_unitaire REAL DEFAULT 0,
    commentaire TEXT,
    photo TEXT
)
""")

cursor.execute("PRAGMA table_info(accessoires)")
colonnes = [col[1] for col in cursor.fetchall()]

colonnes_a_ajouter = {
    "nom": "TEXT",
    "type_accessoire": "TEXT",
    "couleur": "TEXT",
    "fournisseur": "TEXT",
    "quantite_longueur": "REAL DEFAULT 0",
    "unite": "TEXT",
    "stock": "REAL DEFAULT 0",
    "seuil_alerte": "REAL DEFAULT 0",
    "prix": "REAL DEFAULT 0",
    "prix_unitaire": "REAL DEFAULT 0",
    "commentaire": "TEXT",
    "photo": "TEXT"
}

for nom_colonne, type_colonne in colonnes_a_ajouter.items():
    if nom_colonne not in colonnes:
        cursor.execute(f"ALTER TABLE accessoires ADD COLUMN {nom_colonne} {type_colonne}")

conn.commit()
conn.close()

print("Table accessoires prête.")