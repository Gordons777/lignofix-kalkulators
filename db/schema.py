"""
JZ pārvaldības sistēma — datubāzes shēma
Inicializē visas tabulas ar init_db()
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "jz.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS darbinieki (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vards           TEXT    NOT NULL,
            loma            TEXT    NOT NULL DEFAULT 'darbinieks',
            aktivs          INTEGER NOT NULL DEFAULT 1,
            piekluves_kods  TEXT    UNIQUE,
            izveidots       TEXT    DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS grafiks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            darbinieks_id   INTEGER NOT NULL,
            nodala          TEXT    NOT NULL,
            maina           TEXT    NOT NULL,
            datums          TEXT    NOT NULL,
            FOREIGN KEY (darbinieks_id) REFERENCES darbinieki(id),
            UNIQUE(darbinieks_id, datums, nodala, maina)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS prombutne (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            darbinieks_id   INTEGER NOT NULL,
            datums          TEXT    NOT NULL,
            iemesls         TEXT    DEFAULT 'slims',
            FOREIGN KEY (darbinieks_id) REFERENCES darbinieki(id),
            UNIQUE(darbinieks_id, datums)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS klienti (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums           TEXT    NOT NULL UNIQUE,
            regnr               TEXT,
            adrese              TEXT,
            epasts              TEXT,
            telefons            TEXT,
            kontaktpersona      TEXT,
            piezimes            TEXT,
            aktivs              INTEGER NOT NULL DEFAULT 1,
            izveidots_datums    TEXT    DEFAULT (datetime('now')),
            atjauninots_datums  TEXT    DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS piegadatajs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums           TEXT    NOT NULL UNIQUE,
            regnr               TEXT,
            adrese              TEXT,
            epasts              TEXT,
            telefons            TEXT,
            kontaktpersona      TEXT,
            piezimes            TEXT,
            aktivs              INTEGER NOT NULL DEFAULT 1,
            izveidots_datums    TEXT    DEFAULT (datetime('now')),
            atjauninots_datums  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
