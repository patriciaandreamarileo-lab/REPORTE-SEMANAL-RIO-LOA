
import io
import pandas as pd
import streamlit as st
from openpyxl import load_workbook

from modules.github_storage import descargar_archivo_github


RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"


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

    if "NS" not in libro.sheetnames:
        raise ValueError(
            "No se encontró la hoja NS en el archivo MRP."
        )

    hoja = libro["NS"]

    filas = list(hoja.iter_rows(values_only=True))

    if not filas:
        raise ValueError("La hoja NS está vacía.")

    # Buscar la fila que contiene los encabezados.
    # Se identifica por la presencia de Material.
    fila_encabezados = None

    for i, fila in enumerate(filas):

        valores = [
            str(valor).strip().lower()
            if valor is not None else ""
            for valor in fila
        ]

        if "material" in valores:
            fila_encabezados = i
            break

    if fila_encabezados is None:
        raise ValueError(
            "No se encontró la fila de encabezados "
            "con la columna Material."
        )

    encabezados = [
        str(valor).strip() if valor is not None
        else f"Columna_{i}"
        for i, valor in enumerate(filas[fila_encabezados])
    ]

    datos = filas[fila_encabezados + 1:]

    df = pd.DataFrame(
        datos,
        columns=encabezados
    )

    # Eliminar filas completamente vacías.
    df = df.dropna(how="all")

    # Eliminar columnas sin encabezado o completamente vacías.
    df = df.loc[:, [
        columna for columna in df.columns
        if not str(columna).startswith("Columna_")
        or df[columna].notna().any()
    ]]

    return df, libro.sheetnames


def obtener_resumen_mrp():

    df, hojas = cargar_mrp()

    return {
        "datos": df,
        "hojas": hojas,
        "columnas": df.columns.tolist(),
        "cantidad_registros": len(df)
    }
