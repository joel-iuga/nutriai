import streamlit as st
from ia import evaluar_perfil_ia, generar_dieta
from base_datos import cargar_dietas, cargar_comidas_favoritas

def mostrar_cuestionario(user_id):
    persona = st.session_state.persona_activa
    st.title(f"Nueva dieta — {persona['nombre']}")
    st.write("")

    if not st.session_state.get("evaluacion_hecha"):
        with st.spinner("Evaluando el perfil..."):
            try:
                evaluacion = evaluar_perfil_ia(persona)
                st.session_state.evaluacion_hecha = True
                st.session_state.preguntas_adicionales = evaluacion.get("preguntas_adicionales", [])
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif st.session_state.get("preguntas_adicionales"):
        st.info("Necesito un poco más de información:")
        with st.form("preguntas_extra"):
            respuestas_extra = {}
            for i, pregunta in enumerate(st.session_state.preguntas_adicionales):
                respuestas_extra[i] = st.text_area(pregunta, key=f"extra_{i}")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Continuar", type="primary", use_container_width=True):
                    st.session_state.respuestas_extra = respuestas_extra
                    st.session_state.preguntas_adicionales = []
                    st.rerun()
            with col2:
                if st.form_submit_button("Saltar y generar", use_container_width=True):
                    st.session_state.preguntas_adicionales = []
                    st.rerun()

    else:
        comidas_fav = cargar_comidas_favoritas(persona["id"], user_id)

        if comidas_fav and st.session_state.get("frecuencia_favoritas") is None:
            st.subheader("¿Con qué frecuencia incluimos tus comidas favoritas?")
            st.write("")
            nombres = [c["nombre"] for c in comidas_fav]
            st.caption(f"Tienes {len(comidas_fav)} comidas favoritas: "
                       f"{', '.join(nombres[:5])}{'...' if len(nombres) > 5 else ''}")
            st.write("")
            frecuencia = st.select_slider(
                "Veces por semana",
                options=["1-2 veces", "3-4 veces", "Todos los días que sea posible"],
                value="3-4 veces"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Continuar con esta frecuencia", type="primary",
                             use_container_width=True):
                    st.session_state.frecuencia_favoritas = frecuencia
                    st.rerun()
            with col2:
                if st.button("No incluir favoritas", use_container_width=True):
                    st.session_state.frecuencia_favoritas = "ninguna"
                    st.rerun()

        else:
            with st.spinner("Generando tu plan de alimentación..."):
                try:
                    persona_con_extras = dict(persona)
                    extras = [v for v in st.session_state.get(
                        "respuestas_extra", {}).values() if str(v).strip()]
                    if extras:
                        persona_con_extras["notas_adicionales"] = " | ".join(extras)

                    frecuencia = st.session_state.get("frecuencia_favoritas", "ninguna")
                    if frecuencia and frecuencia != "ninguna" and comidas_fav:
                        favoritas_texto = "\n".join([
                            f"- {c['nombre']} ({c['tipo']})"
                            + (f": {c['calorias']} kcal" if c.get('calorias') else "")
                            for c in comidas_fav
                        ])
                        persona_con_extras["comidas_favoritas"] = (
                            f"Incluir {frecuencia}:\n{favoritas_texto}"
                        )

                    dietas_prev = cargar_dietas(persona["id"], user_id)
                    historial = "\n".join([
                        f"- {d['nombre']} ({d['dias']} días)"
                        for d in dietas_prev[:3]
                    ])
                    dias = st.session_state.get("dias_dieta", 7)
                    dieta_json = generar_dieta(persona_con_extras, dias=dias,
                                               historial=historial)
                    st.session_state.dieta_activa = {
                        "contenido": dieta_json,
                        "dias": dias,
                        "nueva": True
                    }
                    st.session_state.frecuencia_favoritas = None
                    st.session_state.vista = "resultado"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generando la dieta: {str(e)}")
                    if st.button("Reintentar"):
                        st.session_state.evaluacion_hecha = False
                        st.rerun()