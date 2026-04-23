import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client
from base_datos import cargar_personas
from vistas.auth import mostrar_auth
from vistas.perfil_detalle import mostrar_nueva_persona, mostrar_perfil
from vistas.cuestionario import mostrar_cuestionario
from vistas.resultado import mostrar_resultado

load_dotenv()

st.set_page_config(page_title="NutriAI", page_icon="🥗", layout="centered")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

if "user" not in st.session_state:
    st.session_state.user = None
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"
if "persona_activa" not in st.session_state:
    st.session_state.persona_activa = None
if "vista" not in st.session_state:
    st.session_state.vista = "perfiles"

if st.session_state.user is None:
    mostrar_auth(supabase)
    st.stop()

user_id = st.session_state.user.id
nombre_real = st.session_state.user.user_metadata.get("nombre", st.session_state.user.email)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.write(f"👤 {nombre_real}")
    st.divider()
    personas = cargar_personas(user_id)
    if personas:
        st.caption("MIS PERFILES")
        for p in personas:
            activo = (st.session_state.persona_activa and
                      st.session_state.persona_activa["id"] == p["id"])
            if st.button(f"{'▶ ' if activo else ''}{p['nombre']}",
                         key=f"sidebar_{p['id']}", use_container_width=True,
                         type="primary" if activo else "secondary"):
                st.session_state.persona_activa = p
                st.session_state.vista = "perfil"
                st.rerun()
    st.write("")
    if st.button("➕ Nuevo perfil", use_container_width=True):
        st.session_state.vista = "nueva_persona"
        st.rerun()
    st.divider()
    if st.button("Cerrar sesión", use_container_width=True):
        supabase.auth.sign_out()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Router ─────────────────────────────────────────────────────────
if not personas and st.session_state.vista != "nueva_persona":
    st.title("🥗 NutriAI")
    st.write(f"Bienvenido, **{nombre_real}**. Crea tu primer perfil para empezar.")
    st.write("")
    if st.button("➕ Crear mi primer perfil", type="primary", use_container_width=True):
        st.session_state.vista = "nueva_persona"
        st.rerun()

elif st.session_state.vista == "nueva_persona":
    mostrar_nueva_persona(user_id)

elif st.session_state.vista in ["perfil", "perfiles"] and st.session_state.persona_activa:
    mostrar_perfil(user_id)

elif st.session_state.vista == "cuestionario":
    mostrar_cuestionario(user_id)

elif st.session_state.vista == "resultado":
    mostrar_resultado(user_id)