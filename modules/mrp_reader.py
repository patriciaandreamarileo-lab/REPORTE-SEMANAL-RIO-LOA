import io
import re
import unicodedata
import pandas as pd
import streamlit as st

from openpyxl import load_workbook
from modules.github_storage import descargar_archivo_github


RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"


# =====================================================
# NORMALIZAR TEXTOS
# =====================================================

def normalizar_texto(valor):

    if valor is None:
        return ""

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


# =====================================================
# EVITAR NOMBRES DE COLUMNAS REPETIDOS
# =====================================================

def nombres_unicos(encabezados):

    resultado = []
    contador = {}

    for i, nombre in enumerate(encabezados):

        nombre = str(nombre).strip()

        if not nombre or nombre.lower() == "none":
            nombre = f"Columna_{i + 1}"

        if nombre in contador:

            contador[nombre] += 1
            nombre = f"{nombre}_{contador[nombre]}"

        else:
            contador[nombre] = 1

        resultado.append(nombre)

    return resultado


# =====================================================
# IDENTIFICAR LA FILA REAL DE ENCABEZADOS
# =====================================================

def buscar_fila_encabezados(filas):

    encabezados_requeridos = {
        "centro",
        "material",
        "descripcion del material"
    }

    for indice, fila in enumerate(filas):

        valores = {
            normalizar_texto(valor)
            for valor in fila
            if valor is not None
        }

        if encabezados_requeridos.issubset(valores):
            return indice

    raise ValueError(
        "No se encontró la fila de encabezados reales "
        "de la hoja NS."
    )


# =====================================================
# LEER HOJA NS
# =====================================================

@st.cache_data(ttl=60)
def cargar_mrp():

    contenido = descargar_archivo_github(RUTA_MRP)

    if contenido is None:

        raise FileNotFoundError(
            "No se encontró el archivo MRP en GitHub."
        )

    archivo = io.BytesIO(contenido)

    libro = load_workbook(
        archivo,
        read_only=True,
        data_only=True
    )

    try:

        if "NS" not in libro.sheetnames:

            raise ValueError(
                "No se encontró la hoja NS."
            )

        hoja = libro["NS"]

        filas = list(
            hoja.iter_rows(values_only=True)
        )

        if not filas:

            raise ValueError(
                "La hoja NS está vacía."
            )

        # Buscar la fila que contiene los encabezados reales
        indice_encabezados = buscar_fila_encabezados(
            filas
        )

        fila_encabezados = filas[indice_encabezados]

        encabezados = [
            str(valor).strip()
            if valor is not None
            else f"Columna_{i + 1}"

            for i, valor in enumerate(fila_encabezados)
        ]

        encabezados = nombres_unicos(encabezados)

        # Obtener únicamente los registros posteriores
        registros = filas[indice_encabezados + 1:]

        df = pd.DataFrame(
            registros,
            columns=encabezados
        )

        # Eliminar filas completamente vacías
        df = df.dropna(how="all")

        # Eliminar filas que sean encabezados repetidos
        if "Centro" in df.columns:

            df = df[
                df["Centro"].apply(
                    normalizar_texto
                ) != "centro"
            ]

        # Eliminar columnas completamente vacías
        df = df.dropna(axis=1, how="all")

        # Limpiar espacios en columnas de texto
        for columna in df.select_dtypes(
            include=["object"]
        ).columns:

            df[columna] = df[columna].apply(
                lambda x: x.strip()
                if isinstance(x, str)
                else x
            )

        df = df.reset_index(drop=True)

        return df, libro.sheetnames

    finally:

        libro.close()


# =====================================================
# RESUMEN DEL MRP
# =====================================================

def obtener_resumen_mrp():

    df, hojas = cargar_mrp()

    return {
        "datos": df,
        "hojas": hojas,
        "columnas": df.columns.tolist(),
        "cantidad_registros": len(df)
    }
