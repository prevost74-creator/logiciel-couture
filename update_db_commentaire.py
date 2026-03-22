import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)

conn = sqlite3.connect("gestion_couture.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE tissus ADD COLUMN commentaire TEXT")
except:
    pass

conn.commit()
conn.close()

print("Colonne commentaire ajoutée !")