# lib_db.py
import sqlite3
import json
import os

DB_INIT_SQL = """
CREATE TABLE IF NOT EXISTS producto (
    cdb INTEGER PRIMARY KEY,
    nombre TEXT,
    precio REAL DEFAULT 0,
    cantidad INTEGER DEFAULT 0,
    umbral INTEGER DEFAULT 0,
    perecedero INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS dinero (
    id INTEGER PRIMARY KEY,
    total REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT
);
CREATE TABLE IF NOT EXISTS venta_detalle (
    venta INTEGER,
    cdb INTEGER,
    cantidad INTEGER,
    precio_venta REAL
);
CREATE TABLE IF NOT EXISTS reposicion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT
);
CREATE TABLE IF NOT EXISTS reposicion_detalle (
    reposicion INTEGER,
    cdb INTEGER,
    cantidad INTEGER,
    precio_compra REAL
);
CREATE TABLE IF NOT EXISTS vencimientos (
    cdb INTEGER,
    cantidad INTEGER,
    fecha_vencimiento TEXT
);
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    rol TEXT CHECK(rol IN ('admin', 'cajero')) NOT NULL
);
"""

def get_connection(path):
    return sqlite3.connect(path)

def init_db(path):
    conn = get_connection(path)
    cur = conn.cursor()
    cur.executescript(DB_INIT_SQL)
    cur.execute("INSERT OR IGNORE INTO dinero (id, total) VALUES (1, 0)")
    cur.execute("INSERT OR IGNORE INTO usuario (id, username, password, rol) VALUES (1, 'admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

def validate_login(path, user, pw):
    conn = get_connection(path)
    cur = conn.cursor()
    cur.execute("SELECT rol FROM usuario WHERE username=? AND password=?", (user, pw))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None

def register_user(path, user, pw, rol):
    conn = get_connection(path)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuario (username, password, rol) VALUES (?, ?, ?)", (user, pw, rol))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Configuración global -------------------
def load_config():
    if not os.path.exists("config.json"):
        save_config({"moneda": "$", "modo": "Dark", "fuente": 14, "iva": 21})
    with open("config.json", "r", encoding="utf8") as f:
        return json.load(f)

def save_config(data):
    with open("config.json", "w", encoding="utf8") as f:
        json.dump(data, f, indent=4)
