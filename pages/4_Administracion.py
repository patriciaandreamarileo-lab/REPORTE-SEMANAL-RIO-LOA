import streamlit as st
import pandas as pd

from io import BytesIO
from modules.navegacion import configurar_navegacion
from modules.github_storage import subir_archivo_github, descargar_archivo_github


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Administración | Enaex",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"
RUTA_CONSUMO = "data/CONSUMO/consumo_rio_loa.xlsx"


# =====================================================
# 2. ESTILOS
# =====================================================

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FB;
}

.bloque-admin {
    background-color: white;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. ENCABEZADO
# =====================================================

st.title("Administración")

st.markdown(
    "Gestión y actualización de los archivos utilizados "
    "en el dashboard de materias primas."
)

st.divider()


# =====================================================
# 4. AUTENTICACIÓN
# =====================================================

st.subheader("Acceso de administrador")

if "admin_autorizado" not in st.session_state:
    st.session_state.admin_autorizado = False

if not st.session_state.admin_autorizado:

    clave = st.text_input(
        "Contraseña de administración",
        type="password",
        key="clave_administracion"
    )

    if st.button("Ingresar", use_container_width=True):

        try:
            clave_correcta = st.secrets["CLAVE_SUBIDA"]
        except Exception:
            st.error(
                "No se encontró CLAVE_SUBIDA en los secretos "
                "de Streamlit."
            )
            st.stop()

        if clave == clave_correcta:
            st.session_state.admin_autorizado = True
            st.rerun()
        else:
            st.error("La contraseña ingresada es incorrecta.")

    st.stop()


# =====================================================
# 5. CERRAR SESIÓN
# =====================================================

col_titulo, col_cerrar = st.columns([4, 1])

with col_titulo:
    st.success("Acceso autorizado.")

with col_cerrar:
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.admin_autorizado = False
        st.rerun()

st.divider()


# =====================================================
# 6. FUNCIÓN PARA VALIDAR EL MRP
# =====================================================

def validar_mrp(archivo):

    contenido = archivo.getvalue()

    excel = pd.ExcelFile(
        BytesIO(contenido),
        engine="openpyxl"
    )

    if "NS" not in excel.sheet_names:
        raise ValueError(
            "El archivo MRP no contiene la hoja NS."
        )

    datos = pd.read_excel(
        BytesIO(contenido),
        sheet_name="NS",
        header=None,
        engine="openpyxl"
    )

    encabezados_encontrados = False

    for _, fila in datos.iterrows():

        valores = (
            fila.fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .tolist()
        )

        if (
            "CENTRO" in valores
            and "MATERIAL" in valores
            and "DESCRIPCIÓN DEL MATERIAL" in valores
        ):
            encabezados_encontrados = True
            break

    if not encabezados_encontrados:
        raise ValueError(
            "No se encontraron los encabezados esperados "
            "en la hoja NS."
        )

    return True


# =====================================================
# 7. FUNCIÓN PARA VALIDAR CONSUMO
# =====================================================

def validar_consumo(archivo):

    contenido = archivo.getvalue()

    excel = pd.ExcelFile(
        BytesIO(contenido),
        engine="openpyxl"
    )

    if "Data" not in excel.sheet_names:
        raise ValueError(
            "El archivo de consumo no contiene la hoja Data."
        )

    datos = pd.read_excel(
        BytesIO(contenido),
        sheet_name="Data",
        nrows=5,
        engine="openpyxl"
    )

    columnas_requeridas = [
        "Material",
        "Centro",
        "Clase de movimiento",
        "Ctd.en UM entrada",
        "Fecha contabiliz."
    ]

    faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in datos.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias: "
            + ", ".join(faltantes)
        )

    return True


# =====================================================
# 8. CARGA DEL MRP
# =====================================================

st.subheader("Actualización del MRP")

st.markdown(
    "Carga aquí la nueva versión del archivo MRP. "
    "El archivo reemplazará la versión almacenada en GitHub."
)

archivo_mrp = st.file_uploader(
    "Seleccionar archivo MRP",
    type=["xlsm"],
    key="subir_mrp"
)

if archivo_mrp is not None:

    st.caption(f"Archivo seleccionado: {archivo_mrp.name}")

    if st.button(
        "Actualizar MRP",
        use_container_width=True,
        key="boton_mrp"
    ):

        try:

            validar_mrp(archivo_mrp)

            resultado = subir_archivo_github(
                archivo_mrp,
                RUTA_MRP
            )

            st.success(
                "MRP actualizado correctamente en GitHub."
            )

            st.cache_data.clear()

        except Exception as error:

            st.error(
                f"No fue posible actualizar el MRP: {error}"
            )


st.divider()


# =====================================================
# 9. CARGA DEL CONSUMO MENSUAL
# =====================================================

st.subheader("Actualización del consumo mensual")

st.markdown(
    "Carga el Excel exportado desde SAP con los movimientos "
    "de consumo de materias primas de Río Loa."
)

archivo_consumo = st.file_uploader(
    "Seleccionar archivo de consumo mensual",
    type=["xlsx"],
    key="subir_consumo"
)

if archivo_consumo is not None:

    st.caption(f"Archivo seleccionado: {archivo_consumo.name}")

    if st.button(
        "Actualizar consumo mensual",
        use_container_width=True,
        key="boton_consumo"
    ):

        try:

            validar_consumo(archivo_consumo)

            resultado = subir_archivo_github(
                archivo_consumo,
                RUTA_CONSUMO
            )

            st.success(
                "Archivo de consumo mensual actualizado correctamente."
            )

            st.cache_data.clear()

        except Exception as error:

            st.error(
                f"No fue posible actualizar el consumo: {error}"
            )


st.divider()


# =====================================================
# 10. ESTADO DE LOS ARCHIVOS
# =====================================================

st.subheader("Archivos almacenados en GitHub")

col1, col2 = st.columns(2)

with col1:

    try:

        mrp_guardado = descargar_archivo_github(RUTA_MRP)

        if mrp_guardado:
            st.success("MRP: archivo disponible")
        else:
            st.warning("MRP: archivo no encontrado")

    except Exception:
        st.warning("MRP: no fue posible verificar el archivo")


with col2:

    try:

        consumo_guardado = descargar_archivo_github(RUTA_CONSUMO)

        if consumo_guardado:
            st.success("Consumo mensual: archivo disponible")
        else:
            st.warning("Consumo mensual: archivo no encontrado")

    except Exception:
        st.warning(
            "Consumo mensual: no fue posible verificar el archivo"
        )


# =====================================================
# 11. PIE DE PÁGINA
# =====================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#8492A6;
        font-size:12px;
        margin-top:45px;
        padding:15px;
    ">
        ENAEX CHILE | ADMINISTRACIÓN DEL DASHBOARD
    </div>
    """,
    unsafe_allow_html=True
)
