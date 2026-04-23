import streamlit as st
from base_datos import (
    crear_persona, actualizar_persona, eliminar_persona,
    guardar_dieta, cargar_dietas, cargar_dieta_por_id, eliminar_dieta, cargar_personas
)

OBJETIVOS = ["Perder peso", "Ganar masa muscular", "Mantener peso actual",
             "Mejorar salud general", "Controlar una condición médica"]
ACTIVIDADES = ["Sedentario", "Ligeramente activo", "Moderadamente activo",
               "Muy activo", "Atleta"]
PREFERENCIAS = ["Vegetariano", "Vegano", "Sin gluten", "Sin lácteos",
                "Halal", "Kosher", "Ninguna"]

def mostrar_nueva_persona(user_id):
    st.title("Nuevo perfil")
    st.write("")

    with st.form("form_nueva_persona"):
        nombre_p = st.text_input("Nombre del perfil *", placeholder="Ej: Yo, Padre, María...")
        col1, col2 = st.columns(2)
        with col1:
            edad_p = st.number_input("Edad *", min_value=5, max_value=100, value=None)
            peso_p = st.number_input("Peso (kg) *", min_value=20.0, max_value=300.0, value=None)
            sexo_p = st.radio("Sexo *", ["Masculino", "Femenino"], index=None, horizontal=True)
        with col2:
            altura_p = st.number_input("Altura (cm) *", min_value=50, max_value=250, value=None)
            objetivo_p = st.selectbox("Objetivo *", [""] + OBJETIVOS)
            actividad_p = st.selectbox("Actividad física *", [""] + ACTIVIDADES)
        intolerancias_p = st.text_input("Intolerancias o alergias",
                                         placeholder="Ej: lactosa, gluten... o ninguna")
        condicion_p = st.text_input("Condición médica",
                                     placeholder="Ej: diabetes... o ninguna")
        preferencias_p = st.multiselect("Preferencias dietéticas", PREFERENCIAS)

        if st.form_submit_button("Crear perfil", type="primary", use_container_width=True):
            if not all([nombre_p, edad_p, peso_p, altura_p, sexo_p, objetivo_p, actividad_p]):
                st.error("Rellena todos los campos obligatorios (*)")
            else:
                try:
                    nueva = crear_persona(user_id, {
                        "nombre": nombre_p, "edad": edad_p, "peso": peso_p,
                        "altura": altura_p, "sexo": sexo_p, "objetivo": objetivo_p,
                        "actividad": actividad_p, "intolerancias": intolerancias_p,
                        "condicion_medica": condicion_p, "preferencias": preferencias_p
                    })
                    st.session_state.persona_activa = nueva
                    st.session_state.vista = "perfil"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    if st.button("← Cancelar"):
        st.session_state.vista = "perfil" if st.session_state.persona_activa else "perfiles"
        st.rerun()

def mostrar_perfil(user_id):
    personas_actualizadas = cargar_personas(user_id)
    persona = next((p for p in personas_actualizadas
                    if p["id"] == st.session_state.persona_activa["id"]), None)
    if not persona:
        st.session_state.vista = "perfiles"
        st.rerun()
        return
    st.session_state.persona_activa = persona

    st.title(f"👤 {persona['nombre']}")

    with st.expander("Editar datos del perfil"):
        with st.form("form_editar"):
            col1, col2 = st.columns(2)
            with col1:
                edad_e = st.number_input("Edad", value=int(persona.get("edad") or 0),
                                          min_value=5, max_value=100)
                peso_e = st.number_input("Peso (kg)", value=float(persona.get("peso") or 0))
                sexo_e = st.radio("Sexo", ["Masculino", "Femenino"],
                                   index=0 if persona.get("sexo") == "Masculino" else 1,
                                   horizontal=True)
            with col2:
                altura_e = st.number_input("Altura (cm)",
                                            value=int(persona.get("altura") or 0),
                                            min_value=50, max_value=250)
                idx_obj = OBJETIVOS.index(persona["objetivo"]) if persona.get("objetivo") in OBJETIVOS else 0
                objetivo_e = st.selectbox("Objetivo", OBJETIVOS, index=idx_obj)
                idx_act = ACTIVIDADES.index(persona["actividad"]) if persona.get("actividad") in ACTIVIDADES else 0
                actividad_e = st.selectbox("Actividad", ACTIVIDADES, index=idx_act)
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

    dietas = cargar_dietas(persona["id"], user_id)
    if dietas:
        st.subheader("Dietas guardadas")
        for d in dietas:
            col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])
            with col_a:
                st.write(f"**{d['nombre']}**")
            with col_b:
                st.caption(f"{d['dias']} días")
            with col_c:
                if st.button("Ver", key=f"ver_{d['id']}"):
                    import json
                    datos = cargar_dieta_por_id(d["id"], user_id)
                    contenido = datos["contenido"]
                    if isinstance(contenido, str):
                        contenido = json.loads(contenido)
                    st.session_state.dieta_activa = {
                        "contenido": contenido,
                        "dias": datos["dias"],
                        "nueva": False
                    }
                    st.session_state.vista = "resultado"
                    st.rerun()
            with col_d:
                if st.button("🗑", key=f"del_{d['id']}"):
                    eliminar_dieta(d["id"], user_id)
                    st.rerun()
        st.write("")

    st.subheader("Generar nueva dieta")
    dias_dieta = st.slider("¿Para cuántos días?", min_value=1, max_value=30, value=7)

    if st.button("Generar dieta", type="primary", use_container_width=True):
        st.session_state.dias_dieta = dias_dieta
        st.session_state.vista = "cuestionario"
        st.session_state.evaluacion_hecha = False
        st.session_state.preguntas_adicionales = []
        st.session_state.respuestas_extra = {}
        st.session_state.dieta_activa = None
        st.rerun()

    st.write("")
    if st.button("Eliminar este perfil", use_container_width=True):
        eliminar_persona(persona["id"], user_id)
        st.session_state.persona_activa = None
        st.session_state.vista = "perfiles"
        st.rerun()