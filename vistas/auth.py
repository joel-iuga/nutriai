import streamlit as st

def mostrar_auth(supabase):
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
        st.info("Mínimo 8 caracteres, mayúscula, minúscula y número.")
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