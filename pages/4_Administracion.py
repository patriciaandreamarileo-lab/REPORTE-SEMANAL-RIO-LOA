import hmac
import streamlit as st

from modules.github_storage import (
    subir_archivo_github,
    descargar_archivo_github,
    comprobar_conexion
)


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Administración | Enaex",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"


# =====================================================
# 2. ESTADOS DE SESIÓN
# =====================================================

if "admin_autenticada" not in st.session_state:
    st.session_state.admin_autenticada = False

if "mrp_uploader_version" not in st.session_state:
    st.session_state.mrp_uploader_version = 0

if "mrp_actualizado" not in st.session_state:
    st.session_state.mrp_actualizado = False


# =====================================================
# 3. DISEÑO
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
# 4. ENCABEZADO
# =====================================================

st.markdown("""
<div class="admin-header">
    <h2>Panel de administración</h2>
    <p>ENAEX CHILE | Gestión y actualización de archivos</p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# 5. MENSAJE DE ACTUALIZACIÓN
# =====================================================

if st.session_state.mrp_actualizado:

    st.success(
        "¡El archivo MRP fue actualizado y verificado "
        "correctamente en GitHub!"
    )

    st.info(
        "La sesión de administración se ha cerrado "
        "automáticamente. Para realizar otra actualización "
        "debes ingresar nuevamente la contraseña."
    )

    st.session_state.mrp_actualizado = False


# =====================================================
# 6. CONTROL DE ACCESO
# =====================================================

if not st.session_state.admin_autenticada:

    st.subheader("Acceso de administradoras")

    st.write(
        "Ingresa la contraseña para habilitar la carga "
        "y actualización del archivo MRP."
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

        try:

            password_correcta = st.secrets["ADMIN_PASSWORD"]

            if hmac.compare_digest(
                password,
                password_correcta
            ):

                st.session_state.admin_autenticada = True
                st.rerun()

            else:

                st.error("Contraseña incorrecta.")

        except Exception as error:

            st.error(
                f"No fue posible validar el acceso: {error}"
            )

    st.stop()


# =====================================================
# 7. PANEL AUTORIZADO
# =====================================================

col1, col2 = st.columns([4, 1])

with col1:

    st.success("Acceso de administración habilitado.")

with col2:

    if st.button(
        "Cerrar sesión",
        use_container_width=True
    ):

        st.session_state.admin_autenticada = False
        st.rerun()


st.divider()


# =====================================================
# 8. CONEXIÓN CON GITHUB
# =====================================================

st.subheader("Almacenamiento de archivos")

try:

    conexion = comprobar_conexion()

    if conexion:

        st.success("Conexión con GitHub establecida.")

    else:

        st.error("No fue posible conectar con GitHub.")

        st.stop()

except Exception as error:

    st.error(f"Error de conexión: {error}")
    st.stop()


st.divider()


# =====================================================
# 9. ACTUALIZACIÓN DEL ARCHIVO MRP
# =====================================================

st.subheader("Actualización del archivo MRP")

st.write(
    "Carga aquí el archivo de planificación MRP. "
    "El sistema reemplazará la versión anterior "
    "almacenada en GitHub."
)

archivo_mrp = st.file_uploader(
    "Seleccionar archivo MRP",
    type=["xlsm"],
    accept_multiple_files=False,
    key=f"archivo_mrp_{st.session_state.mrp_uploader_version}",
    help="Selecciona el archivo Excel MRP con extensión .xlsm."
)


if archivo_mrp is not None:

    st.write(
        "**Archivo seleccionado:**",
        archivo_mrp.name
    )

    contenido_original = archivo_mrp.getvalue()

    tamano_mb = len(contenido_original) / (1024 * 1024)

    st.write(
        f"**Tamaño:** {tamano_mb:.2f} MB"
    )

    if tamano_mb >= 90:

        st.error(
            "El archivo supera el límite permitido "
            "para esta implementación."
        )

    elif not archivo_mrp.name.lower().endswith(".xlsm"):

        st.error("Debes seleccionar un archivo .xlsm.")

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

                with st.spinner(
                    "Guardando y verificando el archivo en GitHub..."
                ):

                    # Subir y reemplazar archivo
                    subir_archivo_github(
                        archivo_mrp,
                        RUTA_MRP
                    )

                    # Descargar nuevamente desde GitHub
                    archivo_verificado = descargar_archivo_github(
                        RUTA_MRP
                    )

                    # Comprobar que el archivo se guardó correctamente
                    if archivo_verificado is None:

                        raise Exception(
                            "GitHub no devolvió el archivo guardado."
                        )

                    if archivo_verificado != contenido_original:

                        raise Exception(
                            "El archivo descargado no coincide "
                            "con el archivo que se intentó subir."
                        )

                # Cerrar sesión automáticamente
                st.session_state.admin_autenticada = False

                # Generar una nueva clave para el cargador
                st.session_state.mrp_uploader_version += 1

                # Mostrar confirmación después del rerun
                st.session_state.mrp_actualizado = True

                st.rerun()

            except Exception as error:

                st.error(
                    f"No fue posible actualizar el MRP: {error}"
                )


# =====================================================
# 10. CONSULTAR ARCHIVO ALMACENADO
# =====================================================

st.divider()

st.subheader("Archivo MRP almacenado")

st.write(
    "Puedes comprobar si existe un archivo MRP "
    "guardado actualmente en GitHub."
)

if st.button(
    "Consultar archivo actual",
    use_container_width=True
):

    try:

        with st.spinner("Consultando GitHub..."):

            archivo_guardado = descargar_archivo_github(
                RUTA_MRP
            )

        if archivo_guardado is not None:

            st.success(
                "Existe un archivo MRP almacenado en GitHub."
            )

            tamano_guardado = (
                len(archivo_guardado) / (1024 * 1024)
            )

            st.metric(
                "Tamaño del archivo almacenado",
                f"{tamano_guardado:.2f} MB"
            )

        else:

            st.warning(
                "Todavía no se ha cargado ningún archivo MRP."
            )

    except Exception as error:

        st.error(
            f"No fue posible consultar el archivo: {error}"
        )


# =====================================================
# 11. VERIFICACIÓN DE DATOS DEL MRP
# =====================================================

st.divider()

st.subheader("Verificación de datos del MRP")

if st.button(
    "Leer hoja NS del MRP",
    use_container_width=True
):

    try:

        from modules.mrp_reader import obtener_resumen_mrp

        with st.spinner(
            "Leyendo archivo MRP desde GitHub..."
        ):

            resultado = obtener_resumen_mrp()

        st.success(
            "La hoja NS se leyó correctamente."
        )

        st.metric(
            "Cantidad de registros",
            resultado["cantidad_registros"]
        )

        st.write(
            "**Hojas del archivo:**",
            resultado["hojas"]
        )

        st.write("**Columnas encontradas:**")

        st.write(resultado["columnas"])

        st.write("**Vista previa de la hoja NS:**")

        st.dataframe(
            resultado["datos"].head(15),
            use_container_width=True,
            hide_index=True
        )

    except Exception as error:

        st.error(
            f"Error al leer el MRP: {error}"
        )


# =====================================================
# 12. PIE DE PÁGINA
# =====================================================

st.divider()

st.caption(
    "ENAEX CHILE | Panel exclusivo de administración"
)
