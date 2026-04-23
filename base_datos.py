# base_datos.py
import os
from supabase import create_client

def get_client():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

# ── PERSONAS ──────────────────────────────────────────────────────

def crear_persona(user_id: str, datos: dict) -> dict:
    try:
        client = get_client()
        result = client.table("personas").insert({
            "user_id": user_id,
            "nombre": datos.get("nombre"),
            "edad": datos.get("edad"),
            "peso": datos.get("peso"),
            "altura": datos.get("altura"),
            "sexo": datos.get("sexo"),
            "objetivo": datos.get("objetivo"),
            "actividad": datos.get("actividad"),
            "intolerancias": datos.get("intolerancias"),
            "condicion_medica": datos.get("condicion_medica"),
            "preferencias": datos.get("preferencias", [])
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise e

def actualizar_persona(persona_id: str, user_id: str, datos: dict) -> bool:
    try:
        client = get_client()
        client.table("personas").update(datos)\
            .eq("id", persona_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        raise e

def cargar_personas(user_id: str) -> list:
    try:
        client = get_client()
        result = client.table("personas")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("creado_en")\
            .execute()
        return result.data
    except Exception as e:
        return []

def eliminar_persona(persona_id: str, user_id: str) -> bool:
    try:
        client = get_client()
        client.table("personas")\
            .delete()\
            .eq("id", persona_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        raise e

# ── DIETAS ────────────────────────────────────────────────────────

def guardar_dieta(user_id: str, persona_id: str, nombre: str,
                  contenido: str, dias: int = 7) -> bool:
    try:
        client = get_client()
        client.table("dietas").insert({
            "user_id": user_id,
            "persona_id": persona_id,
            "nombre": nombre,
            "contenido": contenido,
            "dias": dias
        }).execute()
        return True
    except Exception as e:
        raise e

def cargar_dietas(persona_id: str, user_id: str) -> list:
    try:
        client = get_client()
        result = client.table("dietas")\
            .select("id, nombre, dias, creado_en")\
            .eq("persona_id", persona_id)\
            .eq("user_id", user_id)\
            .order("creado_en", desc=True)\
            .execute()
        return result.data
    except Exception as e:
        return []

def cargar_dieta_por_id(dieta_id: str, user_id: str) -> dict:
    try:
        client = get_client()
        result = client.table("dietas")\
            .select("*")\
            .eq("id", dieta_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        return result.data
    except Exception as e:
        return None

def eliminar_dieta(dieta_id: str, user_id: str) -> bool:
    try:
        client = get_client()
        client.table("dietas")\
            .delete()\
            .eq("id", dieta_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        raise e

def guardar_comida_favorita(user_id: str, persona_id: str, datos: dict) -> dict:
    try:
        client = get_client()
        result = client.table("comidas_favoritas").insert({
            "user_id": user_id,
            "persona_id": persona_id,
            "nombre": datos.get("nombre"),
            "tipo": datos.get("tipo"),
            "calorias": datos.get("calorias"),
            "proteinas_g": datos.get("proteinas_g"),
            "carbohidratos_g": datos.get("carbohidratos_g"),
            "grasas_g": datos.get("grasas_g"),
            "ingredientes": datos.get("ingredientes"),
            "notas": datos.get("notas")
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise e

def cargar_comidas_favoritas(persona_id: str, user_id: str) -> list:
    try:
        client = get_client()
        result = client.table("comidas_favoritas")\
            .select("*")\
            .eq("persona_id", persona_id)\
            .eq("user_id", user_id)\
            .order("tipo")\
            .execute()
        return result.data
    except Exception:
        return []

def eliminar_comida_favorita(comida_id: str, user_id: str) -> bool:
    try:
        client = get_client()
        client.table("comidas_favoritas")\
            .delete()\
            .eq("id", comida_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        raise e

def actualizar_comida_favorita(comida_id: str, user_id: str, datos: dict) -> bool:
    try:
        client = get_client()
        client.table("comidas_favoritas")\
            .update(datos)\
            .eq("id", comida_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        raise e