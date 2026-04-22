# base_datos.py
import os
from supabase import create_client
import json

def get_client():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

def guardar_perfil(user_id: str, nombre: str, respuestas: dict, dieta: str) -> bool:
    try:
        client = get_client()
        result = client.table("perfiles").insert({
            "user_id": user_id,
            "nombre": nombre,
            "respuestas": respuestas,
            "dieta": dieta
        }).execute()
        print(f"Resultado guardar: {result}")
        return True
    except Exception as e:
        print(f"Error guardando perfil: {e}")
        raise e  # Re-lanzar para que app.py lo capture
        
def cargar_perfiles(user_id: str) -> list:
    try:
        client = get_client()
        result = client.table("perfiles")\
            .select("id, nombre, creado_en")\
            .eq("user_id", user_id)\
            .order("creado_en", desc=True)\
            .execute()
        return [(r["id"], r["nombre"], r["creado_en"]) for r in result.data]
    except Exception as e:
        print(f"Error cargando perfiles: {e}")
        return []

def cargar_perfil_por_id(perfil_id: str, user_id: str) -> dict:
    try:
        client = get_client()
        result = client.table("perfiles")\
            .select("nombre, respuestas, dieta")\
            .eq("id", perfil_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        return result.data
    except Exception as e:
        print(f"Error cargando perfil: {e}")
        return None

def eliminar_perfil(perfil_id: str, user_id: str) -> bool:
    try:
        client = get_client()
        client.table("perfiles")\
            .delete()\
            .eq("id", perfil_id)\
            .eq("user_id", user_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Error eliminando perfil: {e}")
        return False