--!SQLITE3

PRAGMA foreign_keys = ON;


CREATE TABLE IF NOT EXISTS producto (
    cdb INTEGER PRIMARY KEY, 
    nombre TEXT NOT NULL, 
    precio REAL NOT NULL, 
    cantidad INTEGER DEFAULT 0, 
    umbral INTEGER DEFAULT 0, 
    margen REAL DEFAULT 0.20, 
    perecedero BOOLEAN DEFAULT 0 
);

CREATE TABLE IF NOT EXISTS venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS venta_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cdb INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_venta REAL,
    venta INTEGER,
    FOREIGN KEY (venta) REFERENCES venta(id),
    FOREIGN KEY (cdb) REFERENCES producto(cdb)
);

CREATE TABLE IF NOT EXISTS compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compra_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cdb INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_compra REAL,
    compra INTEGER,
    FOREIGN KEY (compra) REFERENCES compra(id),
    FOREIGN KEY (cdb) REFERENCES producto(cdb)
);

CREATE TABLE IF NOT EXISTS vencimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cdb INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    FOREIGN KEY (cdb) REFERENCES producto(cdb)
);

CREATE TABLE IF NOT EXISTS dinero (
    id INTEGER PRIMARY KEY CHECK (id = 1), 
    total REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS configuracion (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    fg TEXT,
    bg TEXT,
    font_name TEXT,
    font_size INTEGER
);

INSERT INTO dinero (id, total) VALUES(1, 0);

CREATE TABLE IF NOT EXISTS configuracion (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    fg TEXT,
    bg TEXT,
    passwd TEXT, 
    font_name TEXT,
    font_size INTEGER
);

ALTER TABLE configuracion ADD COLUMN passwd TEXT;

INSERT INTO configuracion (id, fg, bg, font_name, font_size, passwd) 
    VALUES (1, '#000000', '#FFFFFF', 'Arial', '12', '12341234')
