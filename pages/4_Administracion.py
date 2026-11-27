import streamlit as st
import pandas as pd

from io import BytesIO
from modules.navegacion import configurar_navegacion
from modules.github_storage import (
    subir_archivo_github,
    descargar_archivo_github
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

configurar_navegacion()


# Rutas internas de GitHub

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"

RUTA_CONSUMO = "data/CONSUMO/consumo_rio_loa.xlsx"

RUTA_PRECIOS = "data/PRECIOS/precios_rio_loa.xlsx"


# =====================================================
# 2. ESTILOS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
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

    if st.button(
        "Ingresar",
        use_container_width=True
    ):

        try:

            clave_correcta = st.secrets["CLAVE_SUBIDA"]

        except Exception:

            st.error(
                "No se encontró CLAVE_SUBIDA en los secretos "
                "de Streamlit. Revisa su nombre y ubicación."
            )

            st.stop()

        if clave == clave_correcta:

            st.session_state.admin_autorizado = True
            st.rerun()

        else:

            st.error(
                "La contraseña ingresada es incorrecta."
            )

    st.stop()


# =====================================================
# 5. CERRAR SESIÓN
# =====================================================

col_titulo, col_cerrar = st.columns([4, 1])

with col_titulo:

    st.success("Acceso autorizado.")

with col_cerrar:

    if st.button(
        "Cerrar sesión",
        use_container_width=True
    ):

        st.session_state.admin_autorizado = False
        st.rerun()


st.divider()


# =====================================================
# 6. FUNCIÓN PARA LEER EXCEL
# =====================================================

def leer_excel(archivo, hoja="Data", nrows=None):

    contenido = archivo.getvalue()

    return pd.read_excel(
        BytesIO(contenido),
        sheet_name=hoja,
        header=0,
        nrows=nrows,
        engine="openpyxl"
    )


# =====================================================
# 7. VALIDACIÓN DEL MRP
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
# 8. VALIDACIÓN DEL CONSUMO MENSUAL
# =====================================================

def validar_consumo(archivo):

    excel = pd.ExcelFile(
        BytesIO(archivo.getvalue()),
        engine="openpyxl"
    )

    if "Data" not in excel.sheet_names:

        raise ValueError(
            "El archivo de consumo no contiene la hoja Data."
        )

    datos = leer_excel(
        archivo,
        hoja="Data",
        nrows=5
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
# 9. VALIDACIÓN DE PRECIOS
# =====================================================

def validar_precios(archivo):

    excel = pd.ExcelFile(
        BytesIO(archivo.getvalue()),
        engine="openpyxl"
    )

    if "Data" not in excel.sheet_names:

        raise ValueError(
            "El archivo de precios no contiene la hoja Data."
        )

    datos = leer_excel(
        archivo,
        hoja="Data",
        nrows=5
    )

    columnas_requeridas = [
        "Material",
        "Centro",
        "Clase de movimiento",
        "Fecha contabiliz.",
        "Pedido",
        "Moneda",
        "Impte.mon.local",
        "Ctd.en UM entrada",
        "Un.medida de entrada"
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
# 10. FUNCIÓN GENERAL PARA SUBIR ARCHIVOS
# =====================================================

def procesar_carga(archivo, ruta, funcion_validacion, nombre):

    try:

        if archivo is None:

            st.warning(
                "Primero debes seleccionar un archivo."
            )

            return

        funcion_validacion(archivo)

        subir_archivo_github(
            archivo,
            ruta
        )

        st.success(
            f"{nombre} actualizado correctamente en GitHub."
        )

        st.cache_data.clear()

    except Exception as error:

        st.error(
            f"No fue posible actualizar {nombre}: {error}"
        )


# =====================================================
# 11. ACTUALIZACIÓN DEL MRP
# =====================================================

st.subheader("Actualización del MRP")

st.markdown(
    "Carga la nueva versión del archivo MRP. "
    "Este archivo reemplazará la versión anterior "
    "almacenada en GitHub."
)

archivo_mrp = st.file_uploader(
    "Seleccionar archivo MRP",
    type=["xlsm"],
    key="subir_mrp"
)

if archivo_mrp is not None:

    st.caption(
        f"Archivo seleccionado: {archivo_mrp.name}"
    )

    if st.button(
        "Actualizar MRP",
        use_container_width=True,
        key="boton_mrp"
    ):

        procesar_carga(
            archivo_mrp,
            RUTA_MRP,
            validar_mrp,
            "El MRP"
        )


st.divider()


# =====================================================
# 12. ACTUALIZACIÓN DEL CONSUMO MENSUAL
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

    st.caption(
        f"Archivo seleccionado: {archivo_consumo.name}"
    )

    if st.button(
        "Actualizar consumo mensual",
        use_container_width=True,
        key="boton_consumo"
    ):

        procesar_carga(
            archivo_consumo,
            RUTA_CONSUMO,
            validar_consumo,
            "El consumo mensual"
        )


st.divider()


# =====================================================
# 13. ACTUALIZACIÓN DE PRECIOS DE RÍO LOA
# =====================================================

st.subheader("Actualización de precios de Río Loa")

st.markdown(
    "Carga el Excel exportado desde SAP con los movimientos "
    "de entrada de mercancías y precios de las materias primas "
    "de Río Loa."
)

archivo_precios = st.file_uploader(
    "Seleccionar archivo de precios",
    type=["xlsx"],
    key="subir_precios"
)

if archivo_precios is not None:

    st.caption(
        f"Archivo seleccionado: {archivo_precios.name}"
    )

    if st.button(
        "Actualizar precios de Río Loa",
        use_container_width=True,
        key="boton_precios"
    ):

        procesar_carga(
            archivo_precios,
            RUTA_PRECIOS,
            validar_precios,
            "Los precios de Río Loa"
        )


st.divider()


# =====================================================
# 14. ESTADO DE LOS ARCHIVOS EN GITHUB
# =====================================================

st.subheader("Archivos almacenados en GitHub")

col1, col2, col3 = st.columns(3)


# Estado del MRP

with col1:

    try:

        mrp_guardado = descargar_archivo_github(
            RUTA_MRP
        )

        if mrp_guardado:

            st.success(
                "MRP: archivo disponible"
            )

        else:

            st.warning(
                "MRP: archivo no encontrado"
            )

    except Exception:

        st.warning(
            "MRP: no fue posible verificar el archivo"
        )


# Estado del consumo

with col2:

    try:

        consumo_guardado = descargar_archivo_github(
            RUTA_CONSUMO
        )

        if consumo_guardado:

            st.success(
                "Consumo: archivo disponible"
            )

        else:

            st.warning(
                "Consumo: archivo no encontrado"
            )

    except Exception:

        st.warning(
            "Consumo: no fue posible verificar el archivo"
        )


# Estado de precios

with col3:

    try:

        precios_guardados = descargar_archivo_github(
            RUTA_PRECIOS
        )

        if precios_guardados:

            st.success(
                "Precios: archivo disponible"
            )

        else:

            st.warning(
                "Precios: archivo no encontrado"
            )

    except Exception:

        st.warning(
            "Precios: no fue posible verificar el archivo"
        )


st.divider()


# =====================================================
# 15. PIE DE PÁGINA
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
