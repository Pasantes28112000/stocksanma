# lib_db.py
import sqlite3
import datetime
from typing import Optional, Tuple, List

DB_INIT_SQL = """
CREATE TABLE IF NOT EXISTS producto (
    cdb INTEGER PRIMARY KEY,
    nombre TEXT,
    precio REAL DEFAULT 0,
    cantidad INTEGER DEFAULT 0,
    umbral INTEGER DEFAULT 0,
    margen REAL DEFAULT 0.2,
    perecedero INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS dinero (
    id INTEGER PRIMARY KEY,
    total REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS compra ( id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT );
CREATE TABLE IF NOT EXISTS compra_detalle ( compra INTEGER, cdb INTEGER, cantidad INTEGER, precio_compra REAL );
CREATE TABLE IF NOT EXISTS venta ( id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT );
CREATE TABLE IF NOT EXISTS venta_detalle ( venta INTEGER, cdb INTEGER, cantidad INTEGER, precio_venta REAL );
CREATE TABLE IF NOT EXISTS vencimientos ( cdb INTEGER, cantidad INTEGER, fecha_vencimiento TEXT );
CREATE TABLE IF NOT EXISTS configuracion ( id INTEGER PRIMARY KEY, passwd TEXT );
"""

def get_connection(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    return conn

def init_db(path: str):
    conn = get_connection(path)
    cur = conn.cursor()
    cur.executescript(DB_INIT_SQL)
    # ensure dinero row exists
    cur.execute("INSERT OR IGNORE INTO dinero (id, total) VALUES (1, 0)")
    cur.execute("INSERT OR IGNORE INTO configuracion (id, passwd) VALUES (1, '')")
    conn.commit()
    conn.close()

# Small convenience helpers used across modules
def fetch_all_products(path: str) -> List[Tuple]:
    conn = get_connection(path)
    cur = conn.cursor()
    cur.execute("SELECT cdb, nombre, precio, cantidad, margen, umbral, perecedero FROM producto")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_product(path: str, cdb: int) -> Optional[Tuple]:
    conn = get_connection(path)
    cur = conn.cursor()
    cur.execute("SELECT cdb, nombre, precio, cantidad, margen, umbral, perecedero FROM producto WHERE cdb=?", (cdb,))
    row = cur.fetchone()
    conn.close()
    return row
