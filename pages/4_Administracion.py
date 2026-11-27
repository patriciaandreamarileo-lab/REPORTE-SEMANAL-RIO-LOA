
import streamlit as st
import hmac

from modules.github_storage import (
    subir_archivo_github,
    descargar_archivo_github,
    comprobar_conexion
)


# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Administración | Enaex",
    page_icon="🔐",
    layout="wide"
)


# =====================================================
# 2. DISEÑO
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.admin-header {
    background: linear-gradient(110deg, #123454, #24669A);
    padding: 28px;
    border-radius: 12px;
    margin-bottom: 25px;
    color: white;
}

.admin-header h2 {
    color: white;
    margin-bottom: 5px;
}

.admin-header p {
    color: #DCEAF7;
    margin-bottom: 0;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. ENCABEZADO
# =====================================================

st.markdown("""
<div class="admin-header">
    <h2>Panel de administración</h2>
    <p>ENAEX CHILE | Gestión y actualización de archivos</p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# 4. CONTROL DE ACCESO
# =====================================================

if "admin_autenticada" not in st.session_state:
    st.session_state.admin_autenticada = False


if not st.session_state.admin_autenticada:

    st.subheader("Acceso de administradoras")

    st.write(
        "Ingresa la contraseña para habilitar "
        "la carga y actualización de archivos."
    )

    with st.form("formulario_acceso"):

        password = st.text_input(
            "Contraseña de administración",
            type="password"
        )

        ingresar = st.form_submit_button(
            "Ingresar",
            use_container_width=True
        )

    if ingresar:

        password_correcta = st.secrets["ADMIN_PASSWORD"]

        if hmac.compare_digest(
            password,
            password_correcta
        ):

            st.session_state.admin_autenticada = True
            st.rerun()

        else:
            st.error("Contraseña incorrecta.")

    st.stop()


# =====================================================
# 5. PANEL AUTORIZADO
# =====================================================

col1, col2 = st.columns([4, 1])

with col1:
    st.success("Acceso de administración habilitado.")

with col2:
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.admin_autenticada = False
        st.rerun()


st.divider()


# =====================================================
# 6. ESTADO DE CONEXIÓN CON GITHUB
# =====================================================

st.subheader("Almacenamiento de archivos")

try:

    conexion = comprobar_conexion()

    if conexion:
        st.success("Conexión con GitHub establecida.")
    else:
        st.error("No fue posible conectar con GitHub.")

except Exception as error:
    st.error(f"Error de conexión: {error}")


st.divider()


# =====================================================
# 7. CARGA DEL MRP
# =====================================================

st.subheader("Actualización del archivo MRP")

st.write(
    "Carga aquí el archivo de planificación MRP. "
    "El sistema guardará la nueva versión en GitHub."
)

archivo_mrp = st.file_uploader(
    "Seleccionar archivo MRP",
    type=["xlsm"],
    accept_multiple_files=False,
    help="Selecciona el archivo Excel MRP con extensión .xlsm."
)


if archivo_mrp is not None:

    st.write("**Archivo seleccionado:**", archivo_mrp.name)

    tamano_mb = len(archivo_mrp.getvalue()) / (1024 * 1024)

    st.write(f"**Tamaño:** {tamano_mb:.2f} MB")

    if tamano_mb >= 90:

        st.error(
            "El archivo es demasiado grande para "
            "esta implementación de GitHub."
        )

    else:

        st.warning(
            "Al confirmar, el archivo MRP anterior "
            "será reemplazado por el nuevo."
        )

        confirmar = st.checkbox(
            "Confirmo que deseo reemplazar el MRP almacenado."
        )

        if st.button(
            "Actualizar archivo MRP",
            type="primary",
            use_container_width=True,
            disabled=not confirmar
        ):

            try:

                with st.spinner("Guardando archivo en GitHub..."):

                    subir_archivo_github(
                        archivo_mrp,
                        "data/MRP/Planificacion_MRP.xlsm"
                    )

                st.success(
                    "¡El archivo MRP se almacenó correctamente!"
                )

                st.info(
                    "La nueva versión ya está disponible "
                    "para ser procesada por el dashboard."
                )

            except Exception as error:

                st.error(
                    f"No fue posible actualizar el archivo: {error}"
                )


# =====================================================
# 8. CONSULTAR ARCHIVO ALMACENADO
# =====================================================

st.divider()

st.subheader("Archivo MRP almacenado")

if st.button("Consultar archivo actual"):

    try:

        archivo_guardado = descargar_archivo_github(
            "data/MRP/Planificacion_MRP.xlsm"
        )

        if archivo_guardado is not None:

            st.success("Existe un archivo MRP almacenado.")

            st.write(
                f"Tamaño almacenado: "
                f"{len(archivo_guardado) / (1024 * 1024):.2f} MB"
            )

        else:

            st.info(
                "Todavía no se ha cargado ningún archivo MRP."
            )

    except Exception as error:

        st.error(
            f"No fue posible consultar el archivo: {error}"
        )


# =====================================================
# 9. PIE DE PÁGINA
# =====================================================

st.divider()

st.caption(
    "ENAEX CHILE | Panel exclusivo de administración"
)
