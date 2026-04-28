import streamlit as st
import os
import base64
from dotenv import load_dotenv
from supabase import create_client
from base_datos import cargar_personas
from vistas.auth import mostrar_auth
from vistas.perfil_detalle import mostrar_nueva_persona, mostrar_perfil
from vistas.cuestionario import mostrar_cuestionario
from vistas.resultado import mostrar_resultado
from vistas.comidas_favoritas import mostrar_comidas_favoritas
from vistas.ajustes import mostrar_ajustes

load_dotenv()

st.set_page_config(page_title="NutriAI", page_icon="🥗", layout="centered")

# ── CSS personalizado ──────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar fondo menta */
[data-testid="stSidebar"] {
    background-color: #A8E6D0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    background-color: #A8E6D0 !important;
}

/* Botones del sidebar — blancos y redondeados */
[data-testid="stSidebar"] .stButton > button {
    background-color: white !important;
    color: #1a1a1a !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 400 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    transition: box-shadow 0.2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    box-shadow: 0 3px 8px rgba(0,0,0,0.15) !important;
}

/* Botón primario del sidebar (perfil activo) */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: white !important;
    color: #0a7c5c !important;
    font-weight: 600 !important;
    border-left: 3px solid #0a7c5c !important;
}

/* Textos del sidebar */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #1a3a2e !important;
}

/* Divider del sidebar */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.4) !important;
}

/* Cabecera del sidebar sin fondo gris */
[data-testid="stSidebarHeader"] {
    background-color: #A8E6D0 !important;
}

/* Ocultar menú hamburguesa en móvil */
[data-testid="collapsedControl"] {
    background-color: #A8E6D0 !important;
}
</style>
""", unsafe_allow_html=True)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ── Estado global ──────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"
if "persona_activa" not in st.session_state:
    st.session_state.persona_activa = None
if "vista" not in st.session_state:
    st.session_state.vista = "perfiles"

# ── Pantalla de login ──────────────────────────────────────────────
if st.session_state.user is None:
    mostrar_auth(supabase)
    st.stop()

user_id = st.session_state.user.id
nombre_real = st.session_state.user.user_metadata.get("nombre",
              st.session_state.user.email)
personas = cargar_personas(user_id)

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    # Logo opción B — texto izquierda, logo derecha
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; padding:4px 0 8px 0;">
            <span style="font-size:20px; font-weight:700; color:#0a5c42;">NutriAI</span>
            <img src="data:image/png;base64,{logo_b64}"
                 style="width:40px; height:40px; border-radius:50%;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:20px; font-weight:700; color:#0a5c42; padding:4px 0 8px 0;">
            NutriAI 🥗
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Estado 1: Sin perfil activo ───────────────────────────────
    if st.session_state.persona_activa is None:
        col_tit, col_add = st.columns([3, 1])
        with col_tit:
            st.markdown("<p style='font-size:11px; font-weight:600; "
                        "letter-spacing:0.08em; opacity:0.6; color:#0a5c42;'>"
                        "MIS PERFILES</p>", unsafe_allow_html=True)
        with col_add:
            if st.button("＋", key="add_perfil", use_container_width=True):
                st.session_state.vista = "nueva_persona"
                st.rerun()

        for p in personas:
            if st.button(p["nombre"], key=f"sidebar_{p['id']}",
                         use_container_width=True):
                st.session_state.persona_activa = p
                st.session_state.vista = "perfil"
                st.rerun()

        # Espaciador para empujar botones al fondo
        st.markdown("<div style='flex:1; min-height:200px;'></div>",
                    unsafe_allow_html=True)
        st.divider()
        if st.button("Comidas preferidas", use_container_width=True):
            st.warning("Selecciona primero un perfil")
        if st.button("Ajustes", use_container_width=True):
            st.session_state.vista = "ajustes"
            st.rerun()
        if st.button("Cerrar sesión", use_container_width=True):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ── Estado 2: Con perfil activo ───────────────────────────────
    else:
        persona = st.session_state.persona_activa
        st.markdown(f"""
        <p style='font-size:16px; font-weight:600; color:#0a5c42;
                  padding:2px 0 6px 0;'>{persona['nombre']}</p>
        """, unsafe_allow_html=True)
        st.divider()

        if st.button("Nueva Dieta", use_container_width=True):
            st.session_state.vista = "cuestionario"
            st.session_state.evaluacion_hecha = False
            st.session_state.preguntas_adicionales = []
            st.session_state.respuestas_extra = {}
            st.session_state.frecuencia_favoritas = None
            st.session_state.dieta_activa = None
            st.rerun()

        if st.button("Dietas favoritas", use_container_width=True):
            st.session_state.vista = "perfil"
            st.rerun()

        if st.button("Historial de Dietas", use_container_width=True):
            st.session_state.vista = "perfil"
            st.rerun()

        # Espaciador
        st.markdown("<div style='flex:1; min-height:150px;'></div>",
                    unsafe_allow_html=True)

        # Salir del perfil — separado arriba y abajo
        st.divider()
        if st.button("← Salir del perfil", use_container_width=True):
            st.session_state.persona_activa = None
            st.session_state.vista = "perfiles"
            st.rerun()
        st.divider()

        # Botones inferiores fijos
        if st.button("Comidas preferidas", use_container_width=True):
            st.session_state.vista = "comidas_favoritas"
            st.rerun()
        if st.button("Mi perfil", use_container_width=True):
            st.session_state.vista = "perfil"
            st.rerun()
        if st.button("Cerrar sesión", use_container_width=True):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ── Router ─────────────────────────────────────────────────────────
if st.session_state.vista == "ajustes":
    mostrar_ajustes(supabase)

elif not personas and st.session_state.vista != "nueva_persona":
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

elif st.session_state.vista == "comidas_favoritas":
    mostrar_comidas_favoritas(user_id)