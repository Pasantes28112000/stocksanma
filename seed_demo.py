# seed_demo.py
import sqlite3, os
from datetime import date, timedelta

db = os.path.join("data", "data.db")
conn = sqlite3.connect(db)
cur = conn.cursor()
products = [
    (1001, "Café Molido 250g", 1200.0, 10, 2, 0),
    (1002, "Leche 1L", 220.0, 8, 5, 1),
    (1003, "Arroz 1kg", 320.0, 3, 5, 0),
    (1004, "Pan Familiar", 150.0, 20, 5, 1),
    (1005, "Azúcar 1kg", 200.0, 2, 3, 0),
    (1006, "Aceite 1L", 720.0, 6, 4, 0)
]
for p in products:
    try:
        cur.execute("INSERT INTO producto (cdb, nombre, precio, cantidad, umbral, perecedero) VALUES (?, ?, ?, ?, ?, ?)", p)
    except Exception:
        pass

# some vencimientos
today = date.today()
cur.execute("INSERT OR IGNORE INTO vencimientos (cdb, cantidad, fecha_vencimiento) VALUES (?, ?, ?)", (1002, 3, (today + timedelta(days=5)).isoformat()))
cur.execute("INSERT OR IGNORE INTO vencimientos (cdb, cantidad, fecha_vencimiento) VALUES (?, ?, ?)", (1004, 5, (today + timedelta(days=2)).isoformat()))
conn.commit()
conn.close()
print("Seed demo cargado.")
