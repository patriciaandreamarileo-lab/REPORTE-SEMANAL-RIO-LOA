
import streamlit as st
import hmac

from modules.github_storage import (
    subir_archivo_github,
    descargar_archivo_github,
    comprobar_conexion,
    obtener_info_archivo
)


# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Administración | Enaex",
    page_icon="🔐",
    layout="wide"
)

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"


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

    if st.button(
        "Cerrar sesión",
        use_container_width=True
    ):

        st.session_state.admin_autenticada = False
        st.rerun()


st.divider()


# =====================================================
# 6. CONEXIÓN CON GITHUB
# =====================================================

st.subheader("Almacenamiento de archivos")

try:

    if comprobar_conexion():

        st.success("Conexión con GitHub establecida.")

    else:

        st.error("No fue posible conectar con GitHub.")

except Exception as error:

    st.error(f"Error de conexión: {error}")


st.divider()


# =====================================================
# 7. ACTUALIZACIÓN DEL MRP
# =====================================================

st.subheader("Actualización del archivo MRP")

st.write(
    "Carga aquí el archivo de planificación MRP. "
    "La nueva versión reemplazará el archivo almacenado "
    "en GitHub y estará disponible para el dashboard."
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
            "El archivo es demasiado grande "
            "para esta implementación."
        )

    else:

        st.warning(
            "Al confirmar, el MRP anterior será "
            "reemplazado por el nuevo."
        )

        confirmar = st.checkbox(
            "Confirmo que deseo reemplazar el MRP almacenado.",
            key="confirmar_reemplazo_mrp"
        )

        if st.button(
            "Actualizar archivo MRP",
            type="primary",
            use_container_width=True,
            disabled=not confirmar
        ):

            try:

                with st.spinner(
                    "Subiendo y verificando el archivo en GitHub..."
                ):

                    resultado = subir_archivo_github(
                        archivo_mrp,
                        RUTA_MRP
                    )

                    # Limpiar caché del lector MRP

                    from modules.mrp_reader import cargar_mrp

                    cargar_mrp.clear()

                st.session_state["mrp_actualizado"] = True
                st.session_state["mrp_resultado"] = resultado

                st.success(
                    "¡El MRP fue actualizado y verificado correctamente!"
                )

                st.write("**Ruta:**", resultado["ruta"])

                st.write(
                    "**SHA del archivo:**",
                    resultado["sha_archivo"]
                )

                st.write(
                    "**SHA del commit:**",
                    resultado["sha_commit"]
                )

                st.write(
                    "**Tamaño almacenado:**",
                    f'{resultado["tamano"] / (1024 * 1024):.2f} MB'
                )

                st.info(
                    "La nueva versión ya está disponible "
                    "en GitHub. La caché del lector MRP "
                    "también fue limpiada."
                )

            except Exception as error:

                st.error(
                    f"No fue posible actualizar el MRP: {error}"
                )


st.divider()


# =====================================================
# 8. CONSULTAR ARCHIVO ALMACENADO
# =====================================================

st.subheader("Archivo MRP almacenado")

if st.button(
    "Consultar archivo actual",
    use_container_width=True
):

    try:

        informacion = obtener_info_archivo(RUTA_MRP)

        if informacion is not None:

            st.success(
                "Se encontró el archivo MRP en GitHub."
            )

            st.write(
                "**Nombre:**",
                informacion.get("name")
            )

            st.write(
                "**Ruta:**",
                informacion.get("path")
            )

            st.write(
                "**Tamaño:**",
                f'{informacion.get("size", 0) / (1024 * 1024):.2f} MB'
            )

            st.write(
                "**SHA actual:**",
                informacion.get("sha")
            )

            st.write(
                "**Última actualización:**",
                informacion.get("git_url")
            )

            st.write(
                "**Último commit:**",
                informacion.get("html_url")
            )

        else:

            st.warning(
                "No existe ningún archivo MRP en la ruta indicada."
            )

    except Exception as error:

        st.error(
            f"No fue posible consultar GitHub: {error}"
        )


st.divider()


# =====================================================
# 9. VERIFICACIÓN DE DATOS DEL MRP
# =====================================================

st.subheader("Verificación de datos del MRP")

if st.button(
    "Leer hoja NS del MRP",
    use_container_width=True
):

    try:

        from modules.mrp_reader import (
            cargar_mrp,
            obtener_resumen_mrp
        )

        with st.spinner(
            "Descargando y leyendo la última versión del MRP..."
        ):

            cargar_mrp.clear()

            resultado = obtener_resumen_mrp()

        st.success(
            "La hoja NS se leyó correctamente."
        )

        st.write(
            "**Cantidad de registros:**",
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
            use_container_width=True
        )

    except Exception as error:

        st.error(
            f"Error al leer el MRP: {error}"
        )


# =====================================================
# 10. PIE DE PÁGINA
# =====================================================

st.divider()

st.caption(
    "ENAEX CHILE | Panel exclusivo de administración"
)
