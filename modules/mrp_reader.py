import io
import pandas as pd
import streamlit as st
from openpyxl import load_workbook

from modules.github_storage import descargar_archivo_github


RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"

FILA_ENCABEZADOS = 10

COLUMNAS_MRP = [
    "Centro",
    "Material",
    "Descripción del material",
    "UM",
    "MMPP Activa",
    "Riesgo MMPP",
    "Riesgo",
    "Producto",
    "Concat",
    "Consumo X̄",
    "Stock Actual",
    "Stock Óptimo",
    "Stock Seguridad",
    "Stock Máximo",
    "Prod. saldo m",
    "Cob. [Meses]",
    "Cobertura a [Días]",
    "Sobrestock [%]",
    "NS",
    "NS Corregido",
    "Comentario"
]


# =====================================================
# LECTURA DEL MRP
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

        # Leer desde la fila 10 y columnas A:U
        filas = list(
            hoja.iter_rows(
                min_row=FILA_ENCABEZADOS,
                min_col=1,
                max_col=21,
                values_only=True
            )
        )

        if not filas:
            raise ValueError(
                "La hoja NS está vacía."
            )

        encabezados_excel = [
            str(valor).strip() if valor is not None else ""
            for valor in filas[0]
        ]

        # Validar encabezados principales
        encabezados_esperados = [
            "Centro",
            "Material",
            "Descripción del material",
            "UM"
        ]

        if encabezados_excel[:4] != encabezados_esperados:
            raise ValueError(
                "Los encabezados de la fila 10 "
                "no coinciden con la estructura esperada."
            )

        # Crear DataFrame con las 21 columnas
        df = pd.DataFrame(
            filas[1:],
            columns=COLUMNAS_MRP
        )

        # Eliminar filas completamente vacías
        df = df.dropna(how="all")

        # Conservar únicamente registros con centro y material
        df = df[
            df["Centro"].notna()
            & df["Material"].notna()
        ].copy()

        # Limpiar espacios en textos
        for columna in df.select_dtypes(
            include=["object"]
        ).columns:

            df[columna] = df[columna].apply(
                lambda valor: valor.strip()
                if isinstance(valor, str)
                else valor
            )

        # Mantener los códigos como texto
        df["Centro"] = df["Centro"].astype(str)
        df["Material"] = df["Material"].astype(str)

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
