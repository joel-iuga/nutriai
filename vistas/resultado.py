import streamlit as st
import json
from base_datos import guardar_dieta, cargar_dietas
from exportar_pdf import generar_pdf
from ia import ajustar_dieta

COLORES_DIAS = [
    {"bg": "#E6F1FB", "border": "#378ADD", "text": "#0C447C", "badge": "#B5D4F4"},
    {"bg": "#E1F5EE", "border": "#1D9E75", "text": "#085041", "badge": "#9FE1CB"},
    {"bg": "#EAF3DE", "border": "#639922", "text": "#27500A", "badge": "#C0DD97"},
    {"bg": "#FAEEDA", "border": "#BA7517", "text": "#633806", "badge": "#FAC775"},
    {"bg": "#FAECE7", "border": "#D85A30", "text": "#712B13", "badge": "#F5C4B3"},
    {"bg": "#EEEDFE", "border": "#7F77DD", "text": "#3C3489", "badge": "#CECBF6"},
    {"bg": "#FBEAF0", "border": "#D4537E", "text": "#72243E", "badge": "#F4C0D1"},
]

def card_dia(dia_data: dict, idx: int):
    c = COLORES_DIAS[idx % len(COLORES_DIAS)]
    html = f"""
    <div style="background:{c['bg']}; border-left:3px solid {c['border']};
                border-radius:0 10px 10px 0; padding:14px 16px; margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <span style="font-weight:500; font-size:15px; color:{c['text']};">{dia_data.get('dia','')}</span>
        <span style="background:{c['badge']}; color:{c['text']}; font-size:12px;
                     padding:2px 10px; border-radius:99px; font-weight:500;">
          {dia_data.get('calorias','')} kcal
        </span>
      </div>
      <div style="display:grid; gap:6px;">
        {"".join([f'''<div style="display:flex; gap:10px; font-size:13px; padding:5px 0;
                          border-bottom:0.5px solid {c['border']}22;">
          <span style="color:{c['text']}; opacity:0.7; min-width:70px; font-size:12px;">{label}</span>
          <span style="color:#1a1a1a;">{dia_data.get(key,'')}</span>
        </div>''' for label, key in [
            ('Desayuno','desayuno'),('Almuerzo','almuerzo'),
            ('Cena','cena'),('Snack','snack')
        ] if dia_data.get(key)])}
      </div>
    </div>"""
    st.html(html)

def mostrar_resultado(user_id):
    persona = st.session_state.persona_activa
    dieta = st.session_state.get("dieta_activa", {})

    if not dieta:
        st.session_state.vista = "perfil"
        st.rerun()
        return

    contenido = dieta["contenido"]
    if isinstance(contenido, str):
        try:
            contenido = json.loads(contenido)
        except Exception:
            st.error("Error al procesar la dieta.")
            return

    st.title(f"Plan de alimentación — {persona['nombre']}")
    st.caption(f"Plan de {dieta.get('dias', 7)} días")
    st.write("")

    # Resumen de macros
    macros = contenido.get("macros", {})
    calorias = contenido.get("calorias_diarias", "")
    col1, col2, col3, col4 = st.columns(4)
    for col, label, valor, unidad in [
        (col1, "Calorías/día", calorias, "kcal"),
        (col2, "Proteínas", macros.get("proteinas_g",""), "g"),
        (col3, "Carbohidratos", macros.get("carbohidratos_g",""), "g"),
        (col4, "Grasas", macros.get("grasas_g",""), "g"),
    ]:
        with col:
            st.markdown(f"""<div style="background:var(--secondary-background-color);
                border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:#666; margin-bottom:4px;">{label}</div>
                <div style="font-size:20px; font-weight:500;">{valor} <span style="font-size:12px;">{unidad}</span></div>
            </div>""", unsafe_allow_html=True)

    st.write("")

    # Cards por día
    for idx, dia in enumerate(contenido.get("dias", [])):
        card_dia(dia, idx)

    # Alimentos recomendados
    alimentos = contenido.get("alimentos_recomendados", [])
    if alimentos:
        st.write("")
        st.subheader("Alimentos recomendados")
        cols = st.columns(min(len(alimentos), 5))
        for i, alimento in enumerate(alimentos):
            with cols[i % 5]:
                st.markdown(f"""<div style="background:#E1F5EE; border-radius:8px;
                    padding:6px 10px; text-align:center; font-size:13px;
                    color:#085041; margin-bottom:6px;">{alimento}</div>""",
                    unsafe_allow_html=True)

    # Consejos
    consejos = contenido.get("consejos", [])
    if consejos:
        st.write("")
        st.subheader("Consejos personalizados")
        for i, consejo in enumerate(consejos, 1):
            st.markdown(f"**{i}.** {consejo}")

    # Advertencia
    advertencia = contenido.get("advertencia", "")
    if advertencia:
        st.write("")
        st.info(f"⚕️ {advertencia}")

    st.divider()

    # Acciones
    pdf_bytes = generar_pdf(persona["nombre"], contenido)
    st.download_button("Descargar PDF", data=pdf_bytes,
                        file_name=f"dieta_{persona['nombre'].lower()}.pdf",
                        mime="application/pdf", use_container_width=True)

    st.write("")
    with st.expander("Pedir una variación"):
        instruccion = st.text_area("¿Qué quieres cambiar?",
                                    placeholder="Ej: Más proteína, sin lácteos, más económica...")
        if st.button("Aplicar", disabled=not instruccion, type="primary"):
            with st.spinner("Aplicando cambios..."):
                try:
                    nuevo = ajustar_dieta(contenido, instruccion)
                    st.session_state.dieta_activa["contenido"] = nuevo
                    st.session_state.dieta_activa["nueva"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    if dieta.get("nueva"):
        with st.expander("Guardar esta dieta"):
            nombre_dieta = st.text_input("Nombre", placeholder="Ej: Plan enero...")
            if st.button("Guardar", disabled=not nombre_dieta, type="primary"):
                try:
                    guardar_dieta(user_id, persona["id"], nombre_dieta,
                                  json.dumps(contenido, ensure_ascii=False),
                                  dieta.get("dias", 7))
                    st.session_state.dieta_activa["nueva"] = False
                    st.success("✅ Dieta guardada")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.write("")
    if st.button("← Volver al perfil", use_container_width=True):
        st.session_state.vista = "perfil"
        st.rerun()