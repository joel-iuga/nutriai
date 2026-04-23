import streamlit as st
from base_datos import (
    guardar_comida_favorita, cargar_comidas_favoritas,
    eliminar_comida_favorita, actualizar_comida_favorita
)
from ia import completar_datos_comida

TIPOS = ["Desayuno", "Almuerzo", "Cena", "Snack", "Ingrediente favorito"]
ICONOS = {
    "Desayuno": "☀️",
    "Almuerzo": "🍽️",
    "Cena": "🌙",
    "Snack": "🍎",
    "Ingrediente favorito": "🥦"
}

def mostrar_comidas_favoritas(user_id):
    persona = st.session_state.persona_activa
    st.title(f"Comidas favoritas — {persona['nombre']}")
    st.write("")

    # ── Añadir nueva comida ───────────────────────────────────────
    with st.expander("➕ Añadir comida favorita", expanded=False):
        with st.form("form_nueva_comida"):
            col1, col2 = st.columns(2)
            with col1:
                nombre_c = st.text_input("Nombre de la comida *",
                                          placeholder="Ej: Tortilla de patatas, Avena con frutas...")
            with col2:
                tipo_c = st.selectbox("Tipo *", TIPOS)

            notas_c = st.text_area("Notas adicionales (opcional)",
                                    placeholder="Ej: sin sal, con aceite de oliva, versión casera...")

            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("Guardar", type="primary",
                                                   use_container_width=True)
            with col_b:
                submitted_ia = st.form_submit_button("Guardar y completar con IA",
                                                      use_container_width=True)

            if submitted or submitted_ia:
                if not nombre_c:
                    st.error("El nombre es obligatorio")
                else:
                    datos = {
                        "nombre": nombre_c,
                        "tipo": tipo_c,
                        "notas": notas_c
                    }

                    if submitted_ia:
                        with st.spinner("La IA está analizando la comida..."):
                            try:
                                datos_ia = completar_datos_comida(nombre_c, tipo_c)
                                datos.update(datos_ia)
                                st.session_state["ultima_comida_ia"] = datos_ia
                            except Exception as e:
                                st.warning(f"No se pudieron completar los datos: {str(e)}")

                    try:
                        guardar_comida_favorita(user_id, persona["id"], datos)
                        st.success(f"✅ '{nombre_c}' guardada correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Mostrar datos completados por IA si los hay
    if "ultima_comida_ia" in st.session_state:
        datos_ia = st.session_state.pop("ultima_comida_ia")
        st.info(f"""**Datos completados por IA:**
        Calorías: {datos_ia.get('calorias','')} kcal |
        Proteínas: {datos_ia.get('proteinas_g','')}g |
        Carbohidratos: {datos_ia.get('carbohidratos_g','')}g |
        Grasas: {datos_ia.get('grasas_g','')}g""")

    st.divider()

    # ── Lista de comidas favoritas ────────────────────────────────
    comidas = cargar_comidas_favoritas(persona["id"], user_id)

    if not comidas:
        st.caption("Aún no has añadido comidas favoritas.")
        st.stop()

    # Agrupar por tipo
    por_tipo = {}
    for c in comidas:
        tipo = c.get("tipo", "Otro")
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append(c)

    for tipo, lista in por_tipo.items():
        icono = ICONOS.get(tipo, "🍴")
        st.subheader(f"{icono} {tipo}")
        for comida in lista:
            with st.expander(comida["nombre"]):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Calorías", f"{comida.get('calorias') or '—'} kcal")
                with col2:
                    st.metric("Proteínas", f"{comida.get('proteinas_g') or '—'}g")
                with col3:
                    st.metric("Carbohidratos", f"{comida.get('carbohidratos_g') or '—'}g")
                with col4:
                    st.metric("Grasas", f"{comida.get('grasas_g') or '—'}g")

                if comida.get("ingredientes"):
                    st.caption(f"Ingredientes: {comida['ingredientes']}")
                if comida.get("notas"):
                    st.caption(f"Notas: {comida['notas']}")

                col_edit, col_del = st.columns([3, 1])
                with col_del:
                    if st.button("Eliminar", key=f"del_c_{comida['id']}"):
                        eliminar_comida_favorita(comida["id"], user_id)
                        st.rerun()
                with col_edit:
                    if st.button("Completar datos con IA",
                                  key=f"ia_c_{comida['id']}",
                                  disabled=bool(comida.get("calorias"))):
                        with st.spinner("Analizando..."):
                            try:
                                datos_ia = completar_datos_comida(
                                    comida["nombre"], comida["tipo"]
                                )
                                actualizar_comida_favorita(comida["id"], user_id, datos_ia)
                                st.success("✅ Datos actualizados")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

    st.write("")
    if st.button("← Volver al perfil", use_container_width=True):
        st.session_state.vista = "perfil"
        st.rerun()