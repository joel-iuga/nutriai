# app.py
import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
from supabase import create_client
from preguntas import PREGUNTAS, obtener_preguntas_activas
from base_datos import guardar_perfil, cargar_perfiles, cargar_perfil_por_id, eliminar_perfil
from exportar_pdf import generar_pdf

load_dotenv()

st.set_page_config(
    page_title="NutriAI — Dieta personalizada",
    page_icon="🥗",
    layout="centered"
)

# ── Cliente Supabase ───────────────────────────────────────────────
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ── Estado de autenticación ────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"  # "login" o "registro"

# ── Pantalla de login/registro ─────────────────────────────────────
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
                        "email": email,
                        "password": password
                    })
                    st.session_state.user = response.user
                    st.rerun()
                except Exception:
                    st.error("Email o contraseña incorrectos")

    else:
        st.info("""
        **La contraseña debe tener:**
        - Mínimo 8 caracteres
        - Al menos una letra mayúscula
        - Al menos una letra minúscula
        - Al menos un número
        """)
        with st.form("form_registro"):
            nombre_reg = st.text_input("Nombre")
            email_reg = st.text_input("Email")
            password_reg = st.text_input("Contraseña", type="password")
            password_rep = st.text_input("Repetir contraseña", type="password")
            if st.form_submit_button("Crear cuenta", use_container_width=True, type="primary"):
                if password_reg != password_rep:
                    st.error("Las contraseñas no coinciden")
                elif len(password_reg) < 8:
                    st.error("La contraseña debe tener al menos 8 caracteres")
                else:
                    try:
                        response = supabase.auth.sign_up({
                            "email": email_reg,
                            "password": password_reg,
                            "options": {"data": {"nombre": nombre_reg}}
                        })
                        st.success("✅ Cuenta creada. Revisa tu email para confirmarla y luego inicia sesión.")
                        st.session_state.auth_view = "login"
                    except Exception as e:
                        st.error(f"Error al registrarse: {str(e)}")

    st.stop()

# ── Usuario autenticado ────────────────────────────────────────────
user_id = st.session_state.user.id
nombre_real = st.session_state.user.user_metadata.get("nombre", st.session_state.user.email)

with st.sidebar:
    st.write(f"👤 {nombre_real}")
    if st.button("Cerrar sesión", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.respuestas = {}
        st.session_state.pregunta_actual = 0
        st.session_state.dieta_generada = None
        st.session_state.fase = "cuestionario"
        st.rerun()

# ── Inicializar el estado de la sesión ────────────────────────────
# st.session_state es el "almacén" en memoria de Streamlit
# Persiste entre interacciones del usuario sin necesidad de base de datos

if "respuestas" not in st.session_state:
    st.session_state.respuestas = {}  # Diccionario: {id_pregunta: respuesta}

if "pregunta_actual" not in st.session_state:
    st.session_state.pregunta_actual = 0  # Índice de la pregunta que se muestra

if "dieta_generada" not in st.session_state:
    st.session_state.dieta_generada = None  # Aquí guardaremos la respuesta de la IA

if "fase" not in st.session_state:
    st.session_state.fase = "cuestionario"  # Puede ser: "cuestionario" o "resultado"


# ── Función: construir el prompt para la IA ───────────────────────
def construir_prompt(respuestas: dict) -> str:
    """
    Convierte el diccionario de respuestas del usuario en un texto
    estructurado que la IA pueda leer y entender fácilmente.
    """
    lineas = ["PERFIL DEL USUARIO:"]
    lineas.append("=" * 40)

    # Mapeo de IDs técnicos a etiquetas legibles
    etiquetas = {
        "edad": "Edad",
        "sexo": "Sexo biológico",
        "peso": "Peso",
        "altura": "Altura",
        "objetivo": "Objetivo principal",
        "actividad": "Nivel de actividad física",
        "intolerancias": "Alergias / intolerancias",
        "condicion_medica": "Condiciones médicas",
        "comidas_dia": "Comidas al día",
        "preferencias": "Preferencias dietéticas"
    }

    # Agregar unidades a los valores numéricos
    unidades = {
        "peso": "kg",
        "altura": "cm",
        "edad": "años"
    }

    for id_pregunta, etiqueta in etiquetas.items():
        if id_pregunta in respuestas:
            valor = respuestas[id_pregunta]
            unidad = unidades.get(id_pregunta, "")
            # Si es una lista (de opciones múltiples), la convertimos a texto
            if isinstance(valor, list):
                valor = ", ".join(valor)
            lineas.append(f"{etiqueta}: {valor} {unidad}".strip())

    return "\n".join(lineas)

def evaluar_perfil(respuestas: dict) -> dict:
    """
    Fase 1 del sistema de dos pasos: la IA evalúa si tiene suficiente
    información o si necesita hacer preguntas adicionales.
    Devuelve: {"suficiente": True/False, "preguntas_adicionales": [...], "razon": "..."}
    """
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    perfil_texto = construir_prompt(respuestas)

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Eres un nutricionista clínico experto. Tu tarea es evaluar si tienes 
suficiente información sobre un usuario para generar un plan de alimentación seguro y personalizado.

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, con esta estructura exacta:
{
  "suficiente": true o false,
  "razon": "explicación breve de por qué sí o no tienes suficiente info",
  "preguntas_adicionales": ["pregunta 1", "pregunta 2"]
}

- Si tienes suficiente información, pon suficiente: true y preguntas_adicionales: []
- Si falta información crítica para la seguridad o la personalización, pon suficiente: false
  y lista máximo 3 preguntas concretas y específicas que necesitas.
- Solo pide información realmente necesaria, no hagas preguntas por hacer."""
            },
            {
                "role": "user",
                "content": f"Evalúa si tengo suficiente información para este perfil:\n\n{perfil_texto}"
            }
        ],
        max_tokens=500
    )

    import json
    texto = respuesta.choices[0].message.content.strip()
    # Limpiar por si el modelo añade ```json ... ```
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

# ── Función: llamar a la API de Claude ───────────────────────────
def generar_dieta(respuestas: dict, historial_previo: str = "") -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    perfil_texto = construir_prompt(respuestas)

    contexto_historial = ""
    if historial_previo:
        contexto_historial = f"\n\nHISTORIAL — Planes anteriores de este usuario:\n{historial_previo}\nTen en cuenta esta información para mejorar y evolucionar el plan actual."

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Eres un nutricionista clínico experto con más de 15 años de experiencia.
Tu tarea es analizar el perfil nutricional del usuario y generar un plan de alimentación personalizado.

INSTRUCCIONES:
1. Si la información es suficiente, genera un plan completo para 7 días.
2. Si falta información crítica, indica exactamente qué datos necesitas y por qué.
3. Incluye siempre: calorías diarias estimadas, distribución de macronutrientes,
   plan día a día (desayuno, almuerzo, cena, snacks) y 3 consejos personalizados.
4. Adapta el plan a intolerancias, condiciones médicas y preferencias del usuario.
5. Si hay historial previo, evoluciona el plan (no repitas exactamente lo mismo).
6. Añade al final una advertencia recomendando consultar con un médico o nutricionista real.
Responde siempre en español y de forma clara y estructurada."""
            },
            {
                "role": "user",
                "content": f"Analiza mi perfil y genera mi plan de alimentación:\n\n{perfil_texto}{contexto_historial}"
            }
        ],
        max_tokens=2500
    )
    return respuesta.choices[0].message.content

def ajustar_dieta(dieta_actual: str, instruccion: str) -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Eres un nutricionista experto. El usuario ya tiene un plan de alimentación y quiere modificarlo. Aplica los cambios solicitados manteniendo el mismo formato y respetando las restricciones originales del usuario. Responde en español."
            },
            {
                "role": "user",
                "content": f"Este es mi plan actual:\n\n{dieta_actual}\n\n---\nQuiero que hagas este cambio: {instruccion}"
            }
        ],
        max_tokens=2500
    )
    return respuesta.choices[0].message.content

# ── Interfaz de usuario ───────────────────────────────────────────

# Cabecera
st.title("🥗 NutriAI")
st.caption("Tu plan de alimentación personalizado con inteligencia artificial")
st.divider()

# ── Dietas guardadas ──────────────────────────────────────────────
perfiles = cargar_perfiles(user_id)
if perfiles:
    with st.expander(f"📂 Mis dietas guardadas ({len(perfiles)})"):
        for pid, nombre, fecha in perfiles:
            col_a, col_b, col_c = st.columns([4, 2, 1])
            with col_a:
                st.write(f"**{nombre}**")
            with col_b:
                st.caption(fecha[:10])
            with col_c:
                if st.button("Ver", key=f"ver_{pid}"):
                    datos = cargar_perfil_por_id(pid, user_id)
                    st.session_state.dieta_generada = datos["dieta"]
                    st.session_state.respuestas = datos["respuestas"]
                    st.session_state.fase = "resultado"
                    st.session_state.evaluacion_hecha = True
                    st.session_state.preguntas_adicionales = []
                    st.rerun()

# ── FASE: CUESTIONARIO ────────────────────────────────────────────
if st.session_state.fase == "cuestionario":
    if "preguntas_adicionales" not in st.session_state:
        st.session_state.preguntas_adicionales = []

    if "respuestas_adicionales" not in st.session_state:
        st.session_state.respuestas_adicionales = {}

    if "evaluacion_hecha" not in st.session_state:
        st.session_state.evaluacion_hecha = False

    # Calcular progreso
    preguntas_activas = obtener_preguntas_activas(st.session_state.respuestas)
    total_preguntas = len(preguntas_activas)
    pregunta_idx = st.session_state.pregunta_actual
    progreso = pregunta_idx / total_preguntas

    # Mostrar barra de progreso
    st.progress(progreso, text=f"Pregunta {pregunta_idx + 1} de {total_preguntas}")
    st.write("")

    # Verificar si ya respondimos todas las preguntas
    if pregunta_idx >= total_preguntas:
        st.session_state.fase = "resultado"
        st.rerun()

    # Mostrar la pregunta actual
    pregunta = preguntas_activas[pregunta_idx]

    st.subheader(pregunta["texto"])
    if not pregunta["requerida"]:
        st.caption("(Opcional — puedes saltarte esta pregunta)")
    
    # Renderizar el tipo de input correcto según el tipo de pregunta
    respuesta_actual = None

    if pregunta["tipo"] == "numero":
        respuesta_actual = st.number_input(
            label="Tu respuesta",
            min_value=pregunta["min"],
            max_value=pregunta["max"],
            value=None,
            placeholder="Escribe un número...",
            label_visibility="collapsed"
        )

    elif pregunta["tipo"] == "opciones":
        respuesta_actual = st.radio(
            label="Selecciona una opción",
            options=pregunta["opciones"],
            index=None,
            label_visibility="collapsed"
        )

    elif pregunta["tipo"] == "opciones_multiple":
        respuesta_actual = st.multiselect(
            label="Puedes seleccionar varias opciones",
            options=pregunta["opciones"],
            label_visibility="collapsed"
        )
        if not respuesta_actual:
            respuesta_actual = None  # Tratar vacío como no respondido

    elif pregunta["tipo"] == "texto_libre":
        respuesta_actual = st.text_area(
            label="Tu respuesta",
            placeholder=pregunta.get("placeholder", "Escribe aquí..."),
            label_visibility="collapsed"
        )
        if respuesta_actual == "":
            respuesta_actual = None

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if pregunta_idx > 0:
            if st.button("← Atrás", use_container_width=True):
                st.session_state.pregunta_actual -= 1
                st.rerun()

    with col3:
        if pregunta["requerida"]:
            etiqueta_boton = "Siguiente →"
        else:
            etiqueta_boton = "Siguiente →" if respuesta_actual else "Saltar →"

        # Guardamos en session_state para poder leerlo al pulsar Enter
        st.session_state["_respuesta_pendiente"] = respuesta_actual

        submitted = st.button(
            etiqueta_boton,
            disabled=(pregunta["requerida"] and respuesta_actual is None),
            use_container_width=True,
            type="primary"
        )

        if submitted:
            if respuesta_actual is not None:
                st.session_state.respuestas[pregunta["id"]] = respuesta_actual
            st.session_state.pregunta_actual += 1
            st.rerun()

    # Mostrar resumen de respuestas acumuladas (para debugging / transparencia)
    if st.session_state.respuestas:
        with st.expander("Ver respuestas registradas hasta ahora"):
            for k, v in st.session_state.respuestas.items():
                st.write(f"**{k}:** {v}")


# ── FASE: RESULTADO (generación de dieta) ─────────────────────────
elif st.session_state.fase == "resultado":

    if st.session_state.dieta_generada is None:

        st.info("✅ ¡Cuestionario completado! Analizando tu perfil...")

        with st.expander("📋 Tu perfil nutricional", expanded=True):
            for pregunta in PREGUNTAS:
                if pregunta["id"] in st.session_state.respuestas:
                    valor = st.session_state.respuestas[pregunta["id"]]
                    if isinstance(valor, list):
                        valor = ", ".join(valor)
                    st.write(f"**{pregunta['texto']}**")
                    st.write(f"→ {valor}")

        st.write("")

        # ── EVALUACIÓN: ¿tenemos suficiente info? ──────────────────
        if not st.session_state.evaluacion_hecha:
            with st.spinner("🔍 Evaluando si necesito más información..."):
                try:
                    evaluacion = evaluar_perfil(st.session_state.respuestas)
                    st.session_state.evaluacion_hecha = True

                    if evaluacion["suficiente"]:
                        # Tenemos todo — generamos la dieta directamente
                        with st.spinner("🤖 Generando tu plan de alimentación..."):
                            perfiles_previos = cargar_perfiles(user_id)
                            historial = ""
                            if perfiles_previos:
                                historial = "\n".join([f"- Plan '{n}' del {f[:10]}" for _, n, f in perfiles_previos[:3]])
                            dieta = generar_dieta(st.session_state.respuestas, historial_previo=historial)
                            st.session_state.dieta_generada = dieta
                            st.rerun()
                    else:
                        # Faltan datos — guardamos las preguntas adicionales
                        st.session_state.preguntas_adicionales = evaluacion["preguntas_adicionales"]
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al conectar con la IA: {str(e)}")
                    if st.button("Reintentar"):
                        st.rerun()

        # ── PREGUNTAS ADICIONALES ──────────────────────────────────
        elif st.session_state.preguntas_adicionales:
            st.warning("⚠️ Necesito un poco más de información para personalizar mejor tu plan:")
            st.write("")

            with st.form("preguntas_extra"):
                respuestas_extra = {}
                for i, pregunta in enumerate(st.session_state.preguntas_adicionales):
                    respuestas_extra[f"extra_{i}"] = st.text_area(
                        label=pregunta,
                        placeholder="Escribe tu respuesta aquí...",
                        key=f"extra_{i}"
                    )

                if st.form_submit_button("Continuar →", type="primary", use_container_width=True):
                    # Añadir las respuestas adicionales al perfil
                    for i, pregunta in enumerate(st.session_state.preguntas_adicionales):
                        respuesta = respuestas_extra.get(f"extra_{i}", "").strip()
                        if respuesta:
                            st.session_state.respuestas[f"adicional_{i}"] = f"{pregunta}: {respuesta}"

                    st.session_state.preguntas_adicionales = []

                    with st.spinner("🤖 Generando tu plan de alimentación..."):
                        try:
                            perfiles_previos = cargar_perfiles(user_id)
                            historial = ""
                            if perfiles_previos:
                                historial = "\n".join([f"- Plan '{n}' del {f[:10]}" for _, n, f in perfiles_previos[:3]])
                            dieta = generar_dieta(st.session_state.respuestas, historial_previo=historial)
                            st.session_state.dieta_generada = dieta
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

    else:
        st.success("✅ ¡Tu plan de alimentación está listo!")
        st.write("")
        st.markdown(st.session_state.dieta_generada)
        # Botón de descarga PDF
        pdf_bytes = generar_pdf(nombre_real, st.session_state.dieta_generada)
        st.download_button(
            label="📄 Descargar dieta en PDF",
            data=pdf_bytes,
            file_name="mi_plan_nutricional.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.write("")
        with st.expander("🔄 Pedir una variación de la dieta"):
            instruccion = st.text_area(
                "¿Qué quieres cambiar?",
                placeholder="Ej: Hazla más económica, cambia las cenas, añade más proteína en el desayuno..."
            )
            if st.button("Regenerar con este ajuste", disabled=not instruccion, type="primary"):
                with st.spinner("Aplicando tus cambios..."):
                    try:
                        dieta_ajustada = ajustar_dieta(
                            st.session_state.dieta_generada,
                            instruccion
                        )
                        st.session_state.dieta_generada = dieta_ajustada
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        st.divider()

        # Guardar perfil
        st.write("")
        with st.expander("💾 Guardar este perfil"):
            nombre_perfil = st.text_input("¿Con qué nombre quieres guardar este perfil?",
                                            placeholder="Ej: Plan enero, Perfil atleta, etc.")
            if st.button("Guardar", disabled=not nombre_perfil):
                try:
                    resultado = guardar_perfil(user_id, nombre_perfil, st.session_state.respuestas,
                                st.session_state.dieta_generada)
                    if resultado:
                        st.success(f"✅ Perfil '{nombre_perfil}' guardado correctamente.")
                    else:
                        st.error("❌ No se pudo guardar. Revisa la consola.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
                    
        if st.button("🔄 Hacer un nuevo plan", use_container_width=True):
            st.session_state.respuestas = {}
            st.session_state.pregunta_actual = 0
            st.session_state.dieta_generada = None
            st.session_state.fase = "cuestionario"
            st.session_state.preguntas_adicionales = []
            st.session_state.respuestas_adicionales = {}
            st.session_state.evaluacion_hecha = False
            st.rerun()