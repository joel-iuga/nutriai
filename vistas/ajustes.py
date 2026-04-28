import streamlit as st

def mostrar_ajustes(supabase):
    st.title("Ajustes")
    st.write("")

    st.subheader("Cambiar contraseña")
    with st.form("form_password"):
        nueva_password = st.text_input("Nueva contraseña", type="password")
        repetir_password = st.text_input("Repetir contraseña", type="password")
        if st.form_submit_button("Actualizar contraseña", type="primary",
                                  use_container_width=True):
            if nueva_password != repetir_password:
                st.error("Las contraseñas no coinciden")
            elif len(nueva_password) < 8:
                st.error("Mínimo 8 caracteres")
            else:
                try:
                    supabase.auth.update_user({"password": nueva_password})
                    st.success("✅ Contraseña actualizada correctamente")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()

    st.subheader("Cambiar email")
    with st.form("form_email"):
        nuevo_email = st.text_input("Nuevo email",
                                     placeholder="nuevo@email.com")
        if st.form_submit_button("Actualizar email", type="primary",
                                  use_container_width=True):
            if not nuevo_email or "@" not in nuevo_email:
                st.error("Introduce un email válido")
            else:
                try:
                    supabase.auth.update_user({"email": nuevo_email})
                    st.success("✅ Email actualizado. Revisa tu bandeja para confirmar.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.write("")
    if st.button("← Volver", use_container_width=True):
        st.session_state.vista = "perfiles"
        st.rerun()