# base_datos.py — con aislamiento por usuario
import sqlite3
import json
from datetime import datetime

DB_PATH = "nutriai.db"

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Añadimos columna "username" para aislar datos por usuario
    c.execute("""
        CREATE TABLE IF NOT EXISTS perfiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            nombre TEXT,
            creado_en TEXT,
            respuestas TEXT,
            dieta TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_perfil(username: str, nombre: str, respuestas: dict, dieta: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO perfiles (username, nombre, creado_en, respuestas, dieta) VALUES (?,?,?,?,?)",
        (username, nombre, datetime.now().isoformat(), json.dumps(respuestas), dieta)
    )
    perfil_id = c.lastrowid
    conn.commit()
    conn.close()
    return perfil_id

def cargar_perfiles(username: str) -> list:
    """Solo devuelve los perfiles del usuario autenticado."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, nombre, creado_en FROM perfiles WHERE username=? ORDER BY creado_en DESC",
        (username,)
    )
    filas = c.fetchall()
    conn.close()
    return filas

def cargar_perfil_por_id(perfil_id: int, username: str) -> dict:
    """Carga un perfil solo si pertenece al usuario autenticado."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT nombre, respuestas, dieta FROM perfiles WHERE id=? AND username=?",
        (perfil_id, username)
    )
    fila = c.fetchone()
    conn.close()
    if fila:
        return {"nombre": fila[0], "respuestas": json.loads(fila[1]), "dieta": fila[2]}
    return None

def eliminar_perfil(perfil_id: int, username: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM perfiles WHERE id=? AND username=?", (perfil_id, username))
    conn.commit()
    conn.close()