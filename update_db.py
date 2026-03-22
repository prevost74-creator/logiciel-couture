import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)

conn = sqlite3.connect("gestion_couture.db")
cursor = conn.cursor()

# Ajouter nouvelles colonnes
try:
    cursor.execute("ALTER TABLE tissus ADD COLUMN largeur REAL")
except:
    pass

try:
    cursor.execute("ALTER TABLE tissus ADD COLUMN fournisseur TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE tissus ADD COLUMN emplacement TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE tissus ADD COLUMN seuil_alerte REAL")
except:
    pass

conn.commit()
conn.close()

print("Base mise à jour !")