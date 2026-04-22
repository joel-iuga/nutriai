# app.py
import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
from supabase import create_client
from preguntas import obtener_preguntas_activas
from base_datos import (
    crear_persona, actualizar_persona, cargar_personas, eliminar_persona,
    guardar_dieta, cargar_dietas, cargar_dieta_por_id, eliminar_dieta
)
from exportar_pdf import generar_pdf

load_dotenv()

st.set_page_config(
    page_title="NutriAI",
    page_icon="🥗",
    layout="centered"
)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ── Estado global ──────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"
if "persona_activa" not in st.session_state:
    st.session_state.persona_activa = None  # dict con datos de la persona
if "vista" not in st.session_state:
    st.session_state.vista = "perfiles"  # perfiles | nueva_persona | editar_persona | cuestionario | resultado

# ── AUTENTICACIÓN ─────────────────────────────────────────────────
if st.session_state.user is None:
    st.title("🥗 NutriAI")
    st.caption("Tu plan de alimentación personalizado con inteligencia artificial")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Iniciar sesión", use_container_width=True,
                     type="primary" if st.session_state.auth_view == "login" else "secondary"):
            st.session_state.auth_view = "login"
            st.rerun()
    with col2:
        if st.button("Crear cuenta", use_container_width=True,
                     type="primary" if st.session_state.auth_view == "registro" else "secondary"):
            st.session_state.auth_view = "registro"
            st.rerun()

    st.write("")

    if st.session_state.auth_view == "login":
        with st.form("form_login"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
                try:
                    response = supabase.auth.sign_in_with_password({
                        "email": email, "password": password
                    })
                    st.session_state.user = response.user
                    st.rerun()
                except Exception:
                    st.error("Email o contraseña incorrectos")
    else:
        st.info("La contraseña debe tener mínimo 8 caracteres, mayúscula, minúscula y número.")
        with st.form("form_registro"):
            nombre_reg = st.text_input("Nombre")
            email_reg = st.text_input("Email")
            password_reg = st.text_input("Contraseña", type="password")
            password_rep = st.text_input("Repetir contraseña", type="password")
            if st.form_submit_button("Crear cuenta", use_container_width=True, type="primary"):
                if password_reg != password_rep:
                    st.error("Las contraseñas no coinciden")
                elif len(password_reg) < 8:
                    st.error("Mínimo 8 caracteres")
                else:
                    try:
                        supabase.auth.sign_up({
                            "email": email_reg,
                            "password": password_reg,
                            "options": {"data": {"nombre": nombre_reg}}
                        })
                        st.success("✅ Cuenta creada. Revisa tu email y luego inicia sesión.")
                        st.session_state.auth_view = "login"
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    st.stop()

# ── Usuario autenticado ────────────────────────────────────────────
user_id = st.session_state.user.id
nombre_real = st.session_state.user.user_metadata.get("nombre", st.session_state.user.email)

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.write(f"👤 {nombre_real}")
    st.divider()

    personas = cargar_personas(user_id)

    if personas:
        st.caption("MIS PERFILES")
        for p in personas:
            activo = st.session_state.persona_activa and \
                     st.session_state.persona_activa["id"] == p["id"]
            if st.button(
                f"{'▶ ' if activo else ''}{p['nombre']}",
                key=f"sidebar_{p['id']}",
                use_container_width=True,
                type="primary" if activo else "secondary"
            ):
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


# ── FUNCIONES IA ──────────────────────────────────────────────────
def persona_a_prompt(persona: dict) -> str:
    campos = {
        "nombre": "Nombre", "edad": "Edad", "sexo": "Sexo",
        "peso": "Peso (kg)", "altura": "Altura (cm)",
        "objetivo": "Objetivo", "actividad": "Actividad física",
        "intolerancias": "Intolerancias", "condicion_medica": "Condición médica",
        "preferencias": "Preferencias dietéticas"
    }
    lineas = ["PERFIL:"]
    for campo, etiqueta in campos.items():
        valor = persona.get(campo)
        if valor:
            if isinstance(valor, list):
                valor = ", ".join(valor)
            lineas.append(f"{etiqueta}: {valor}")
    return "\n".join(lineas)

def generar_dieta(persona: dict, dias: int = 7, historial: str = "") -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    perfil_texto = persona_a_prompt(persona)
    contexto = f"\n\nHISTORIAL PREVIO:\n{historial}" if historial else ""

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""Eres un nutricionista clínico experto. Genera un plan de alimentación COMPLETO para {dias} días.

OBLIGATORIO incluir:
1. CALORÍAS DIARIAS (cálculo Harris-Benedict con los datos del perfil)
2. MACRONUTRIENTES (proteínas, carbohidratos y grasas en gramos y porcentaje)
3. PLAN DE {dias} DÍAS — cada día con desayuno, almuerzo, cena y snacks con cantidades exactas
4. LISTA DE 10 ALIMENTOS RECOMENDADOS
5. 3 CONSEJOS PERSONALIZADOS
6. ADVERTENCIA MÉDICA

No dejes ningún día vacío. Sé específico con cantidades. Adapta todo a intolerancias y condiciones médicas.
Responde en español."""
            },
            {
                "role": "user",
                "content": f"Genera mi plan de {dias} días:\n\n{perfil_texto}{contexto}"
            }
        ],
        max_tokens=4000
    )
    return respuesta.choices[0].message.content

def evaluar_perfil_ia(persona: dict) -> dict:
    import json
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    perfil_texto = persona_a_prompt(persona)

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Evalúa si tienes suficiente información para generar un plan nutricional seguro.
Responde SOLO con JSON:
{"suficiente": true/false, "preguntas_adicionales": ["pregunta1", "pregunta2"]}
Máximo 3 preguntas si faltan datos críticos."""
            },
            {"role": "user", "content": f"Evalúa este perfil:\n{perfil_texto}"}
        ],
        max_tokens=300
    )
    texto = respuesta.choices[0].message.content.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

def ajustar_dieta(dieta_actual: str, instruccion: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Eres nutricionista. Modifica el plan según las instrucciones manteniendo el formato y las restricciones originales. Responde en español."
            },
            {
                "role": "user",
                "content": f"Plan actual:\n{dieta_actual}\n\nCambio solicitado: {instruccion}"
            }
        ],
        max_tokens=4000
    )
    return respuesta.choices[0].message.content


# ══════════════════════════════════════════════════════════════════
# VISTAS
# ══════════════════════════════════════════════════════════════════

# ── VISTA: Pantalla inicial sin perfiles ──────────────────────────
if not personas and st.session_state.vista not in ["nueva_persona"]:
    st.title("🥗 NutriAI")
    st.write(f"Bienvenido, **{nombre_real}**. Para empezar, crea tu primer perfil.")
    st.write("")
    if st.button("➕ Crear mi primer perfil", type="primary", use_container_width=True):
        st.session_state.vista = "nueva_persona"
        st.rerun()
    st.stop()


# ── VISTA: Crear nueva persona ────────────────────────────────────
elif st.session_state.vista == "nueva_persona":
    st.title("➕ Nuevo perfil")
    st.write("")

    opciones_objetivo = [
        "Perder peso", "Ganar masa muscular",
        "Mantener peso actual", "Mejorar salud general",
        "Controlar una condición médica"
    ]
    opciones_actividad = [
        "Sedentario", "Ligeramente activo",
        "Moderadamente activo", "Muy activo", "Atleta"
    ]
    opciones_preferencias = [
        "Vegetariano", "Vegano", "Sin gluten",
        "Sin lácteos", "Halal", "Kosher", "Ninguna"
    ]

    with st.form("form_nueva_persona"):
        nombre_p = st.text_input("Nombre del perfil *", placeholder="Ej: Yo, Padre, María...")
        col1, col2 = st.columns(2)
        with col1:
            edad_p = st.number_input("Edad *", min_value=5, max_value=100, value=None)
            peso_p = st.number_input("Peso (kg) *", min_value=20.0, max_value=300.0, value=None)
            sexo_p = st.radio("Sexo *", ["Masculino", "Femenino"], index=None, horizontal=True)
        with col2:
            altura_p = st.number_input("Altura (cm) *", min_value=50, max_value=250, value=None)
            objetivo_p = st.selectbox("Objetivo *", [""] + opciones_objetivo)
            actividad_p = st.selectbox("Actividad física *", [""] + opciones_actividad)
        intolerancias_p = st.text_input("Intolerancias o alergias",
                                         placeholder="Ej: lactosa, gluten... o ninguna")
        condicion_p = st.text_input("Condición médica relevante",
                                     placeholder="Ej: diabetes, hipertensión... o ninguna")
        preferencias_p = st.multiselect("Preferencias dietéticas", opciones_preferencias)

        if st.form_submit_button("Crear perfil", type="primary", use_container_width=True):
            if not all([nombre_p, edad_p, peso_p, altura_p, sexo_p, objetivo_p, actividad_p]):
                st.error("Rellena todos los campos obligatorios (*)")
            else:
                try:
                    nueva = crear_persona(user_id, {
                        "nombre": nombre_p, "edad": edad_p, "peso": peso_p,
                        "altura": altura_p, "sexo": sexo_p, "objetivo": objetivo_p,
                        "actividad": actividad_p, "intolerancias": intolerancias_p,
                        "condicion_medica": condicion_p,
                        "preferencias": preferencias_p
                    })
                    st.session_state.persona_activa = nueva
                    st.session_state.vista = "perfil"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    if st.button("← Cancelar"):
        st.session_state.vista = "perfil" if st.session_state.persona_activa else "perfiles"
        st.rerun()


# ── VISTA: Perfil + dietas ─────────────────────────────────────────
elif st.session_state.vista in ["perfil", "perfiles"] and st.session_state.persona_activa:
    persona = st.session_state.persona_activa

    # Recargar datos actualizados de la persona
    personas_actualizadas = cargar_personas(user_id)
    persona_fresca = next((p for p in personas_actualizadas if p["id"] == persona["id"]), None)
    if persona_fresca:
        st.session_state.persona_activa = persona_fresca
        persona = persona_fresca

    st.title(f"👤 {persona['nombre']}")

    # Datos básicos del perfil
    with st.expander("📋 Datos del perfil", expanded=False):
        with st.form("form_editar"):
            col1, col2 = st.columns(2)
            with col1:
                edad_e = st.number_input("Edad", value=persona.get("edad") or 0, min_value=5, max_value=100)
                peso_e = st.number_input("Peso (kg)", value=float(persona.get("peso") or 0))
                sexo_e = st.radio("Sexo", ["Masculino", "Femenino"],
                                   index=0 if persona.get("sexo") == "Masculino" else 1,
                                   horizontal=True)
            with col2:
                altura_e = st.number_input("Altura (cm)", value=persona.get("altura") or 0, min_value=50, max_value=250)
                objetivo_e = st.selectbox("Objetivo", [
                    "Perder peso", "Ganar masa muscular",
                    "Mantener peso actual", "Mejorar salud general",
                    "Controlar una condición médica"
                ], index=["Perder peso", "Ganar masa muscular",
                           "Mantener peso actual", "Mejorar salud general",
                           "Controlar una condición médica"].index(persona.get("objetivo", "Mejorar salud general"))
                           if persona.get("objetivo") else 0)
                actividad_e = st.selectbox("Actividad", [
                    "Sedentario", "Ligeramente activo",
                    "Moderadamente activo", "Muy activo", "Atleta"
                ], index=["Sedentario", "Ligeramente activo",
                           "Moderadamente activo", "Muy activo", "Atleta"].index(persona.get("actividad", "Sedentario"))
                           if persona.get("actividad") else 0)
            intolerancias_e = st.text_input("Intolerancias", value=persona.get("intolerancias") or "")
            condicion_e = st.text_input("Condición médica", value=persona.get("condicion_medica") or "")

            if st.form_submit_button("Guardar cambios", type="primary"):
                try:
                    actualizar_persona(persona["id"], user_id, {
                        "edad": edad_e, "peso": peso_e, "altura": altura_e,
                        "sexo": sexo_e, "objetivo": objetivo_e, "actividad": actividad_e,
                        "intolerancias": intolerancias_e, "condicion_medica": condicion_e
                    })
                    st.success("✅ Perfil actualizado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()

    # ── Dietas guardadas ──────────────────────────────────────────
    dietas = cargar_dietas(persona["id"], user_id)

    if dietas:
        st.subheader("📂 Dietas guardadas")
        for d in dietas:
            col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])
            with col_a:
                st.write(f"**{d['nombre']}**")
            with col_b:
                st.caption(f"{d['dias']} días")
            with col_c:
                if st.button("Ver", key=f"ver_{d['id']}"):
                    st.session_state.dieta_activa = cargar_dieta_por_id(d["id"], user_id)
                    st.session_state.vista = "resultado"
                    st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_{d['id']}"):
                    eliminar_dieta(d["id"], user_id)
                    st.rerun()
        st.write("")

    # ── Generar nueva dieta ───────────────────────────────────────
    st.subheader("🍽️ Generar nueva dieta")
    dias_dieta = st.slider("¿Para cuántos días?", min_value=1, max_value=30, value=7)

    if st.button("Generar dieta", type="primary", use_container_width=True):
        st.session_state.dias_dieta = dias_dieta
        st.session_state.vista = "cuestionario"
        st.session_state.respuestas_extra = {}
        st.session_state.evaluacion_hecha = False
        st.session_state.preguntas_adicionales = []
        st.session_state.dieta_activa = None
        st.rerun()

    st.write("")
    if st.button("🗑️ Eliminar este perfil", use_container_width=True):
        eliminar_persona(persona["id"], user_id)
        st.session_state.persona_activa = None
        st.session_state.vista = "perfiles"
        st.rerun()


# ── VISTA: Cuestionario adicional ─────────────────────────────────
elif st.session_state.vista == "cuestionario":
    persona = st.session_state.persona_activa
    st.title(f"🍽️ Nueva dieta — {persona['nombre']}")
    st.write("")

    if not st.session_state.get("evaluacion_hecha"):
        with st.spinner("🔍 Evaluando el perfil..."):
            try:
                evaluacion = evaluar_perfil_ia(persona)
                st.session_state.evaluacion_hecha = True
                st.session_state.preguntas_adicionales = evaluacion.get("preguntas_adicionales", [])
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif st.session_state.preguntas_adicionales:
        st.info("Necesito un poco más de información para personalizar tu plan:")
        with st.form("preguntas_extra"):
            respuestas_extra = {}
            for i, pregunta in enumerate(st.session_state.preguntas_adicionales):
                respuestas_extra[i] = st.text_area(pregunta, key=f"extra_{i}")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Continuar →", type="primary", use_container_width=True):
                    st.session_state.respuestas_extra = respuestas_extra
                    st.session_state.preguntas_adicionales = []
                    st.rerun()
            with col2:
                if st.form_submit_button("Saltar y generar →", use_container_width=True):
                    st.session_state.preguntas_adicionales = []
                    st.rerun()

    else:
        with st.spinner("🤖 Generando tu plan de alimentación..."):
            try:
                # Construir contexto adicional
                extras = ""
                for i, preg in enumerate(st.session_state.get("respuestas_extra", {}).values()):
                    if preg.strip():
                        extras += f"\n- {preg}"

                persona_con_extras = dict(persona)
                if extras:
                    persona_con_extras["notas_adicionales"] = extras

                # Historial de dietas anteriores
                dietas_prev = cargar_dietas(persona["id"], user_id)
                historial = "\n".join([f"- {d['nombre']} ({d['dias']} días, {d['creado_en'][:10]})"
                                       for d in dietas_prev[:3]])

                dias = st.session_state.get("dias_dieta", 7)
                dieta_texto = generar_dieta(persona_con_extras, dias=dias, historial=historial)

                st.session_state.dieta_activa = {
                    "contenido": dieta_texto,
                    "dias": dias,
                    "persona_id": persona["id"],
                    "nueva": True
                }
                st.session_state.vista = "resultado"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.button("Reintentar"):
                    st.rerun()


# ── VISTA: Resultado de la dieta ──────────────────────────────────
elif st.session_state.vista == "resultado":
    persona = st.session_state.persona_activa
    dieta = st.session_state.get("dieta_activa", {})

    if not dieta:
        st.session_state.vista = "perfil"
        st.rerun()

    st.title(f"🥗 Plan de alimentación — {persona['nombre']}")
    st.caption(f"Plan de {dieta.get('dias', 7)} días")
    st.write("")

    st.markdown(dieta["contenido"])

    st.divider()

    # Descargar PDF
    pdf_bytes = generar_pdf(persona["nombre"], dieta["contenido"])
    st.download_button(
        "📄 Descargar PDF",
        data=pdf_bytes,
        file_name=f"dieta_{persona['nombre'].lower()}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # Ajustar dieta
    with st.expander("🔄 Pedir una variación"):
        instruccion = st.text_area("¿Qué quieres cambiar?",
                                    placeholder="Ej: Hazla más económica, más proteína...")
        if st.button("Aplicar cambio", disabled=not instruccion, type="primary"):
            with st.spinner("Aplicando cambios..."):
                try:
                    nueva = ajustar_dieta(dieta["contenido"], instruccion)
                    st.session_state.dieta_activa["contenido"] = nueva
                    st.session_state.dieta_activa["nueva"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Guardar dieta
    if dieta.get("nueva"):
        with st.expander("💾 Guardar esta dieta"):
            nombre_dieta = st.text_input("Nombre para esta dieta",
                                          placeholder="Ej: Plan enero, Dieta volumen...")
            if st.button("Guardar", disabled=not nombre_dieta, type="primary"):
                try:
                    guardar_dieta(user_id, persona["id"], nombre_dieta,
                                  dieta["contenido"], dieta.get("dias", 7))
                    st.session_state.dieta_activa["nueva"] = False
                    st.success("✅ Dieta guardada")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.write("")
    if st.button("← Volver al perfil", use_container_width=True):
        st.session_state.vista = "perfil"
        st.rerun()