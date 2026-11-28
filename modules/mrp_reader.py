import io
import re
import unicodedata
import pandas as pd
import streamlit as st

from openpyxl import load_workbook
from modules.github_storage import descargar_archivo_github


# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"

FILA_ENCABEZADOS = 10

CENTRO_RIO_LOA = "E024"

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
# 2. FUNCIONES DE LIMPIEZA
# =====================================================

def limpiar_texto(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def normalizar_codigo(valor):

    if pd.isna(valor):
        return ""

    codigo = str(valor).strip()

    if codigo.endswith(".0"):
        codigo = codigo[:-2]

    return codigo


def normalizar_encabezado(valor):

    texto = limpiar_texto(valor).lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    ).encode("ascii", "ignore").decode("ascii")

    return " ".join(texto.split())


def convertir_numero(valor):

    if valor is None or pd.isna(valor):
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if not texto or texto in ["-", "—"]:
        return None

    texto = texto.replace(" ", "")

    # Formato numérico chileno: 146.933,00
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")

    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except (ValueError, TypeError):
        return None


# =====================================================
# 3. LECTURA DEL MRP DESDE GITHUB
#    HOJA NS
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
            limpiar_texto(valor)
            for valor in filas[0]
        ]

        if encabezados_excel[:4] != [
            "Centro",
            "Material",
            "Descripción del material",
            "UM"
        ]:

            raise ValueError(
                "Los encabezados de la hoja NS "
                "no coinciden con la estructura esperada. "
                f"Se encontraron: {encabezados_excel[:4]}"
            )

        df = pd.DataFrame(
            filas[1:],
            columns=COLUMNAS_MRP
        )

        df = df.dropna(how="all").copy()

        for columna in df.select_dtypes(
            include=["object"]
        ).columns:

            df[columna] = df[columna].apply(
                limpiar_texto
            )

        df["Centro"] = (
            df["Centro"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df["Material"] = (
            df["Material"]
            .apply(normalizar_codigo)
        )

        df = df[
            (df["Centro"] != "")
            & (df["Centro"] != "NONE")
            & (df["Material"] != "")
            & (df["Material"] != "NONE")
        ].copy()

        return df.reset_index(drop=True), libro.sheetnames

    finally:
        libro.close()


# =====================================================
# 4. OBTENER MATERIAS PRIMAS DE RÍO LOA
# =====================================================

@st.cache_data(ttl=60)
def obtener_datos_rio_loa():

    df, _ = cargar_mrp()

    datos_rio_loa = df[
        df["Centro"].astype(str).str.strip().str.upper()
        == CENTRO_RIO_LOA
    ].copy()

    return datos_rio_loa.reset_index(drop=True)


# =====================================================
# 5. OBTENER MATERIAS PRIMAS ACTIVAS
# =====================================================

@st.cache_data(ttl=60)
def obtener_materias_primas_activas():

    df = obtener_datos_rio_loa()

    if df.empty:
        return df

    activas = (
        df["MMPP Activa"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    datos_activos = df[
        activas.isin(["SI", "SÍ", "1", "TRUE", "X"])
    ].copy()

    return datos_activos.reset_index(drop=True)


# =====================================================
# 6. RESUMEN DEL MRP
# =====================================================

def obtener_resumen_mrp():

    df, hojas = cargar_mrp()

    datos_rio_loa = obtener_datos_rio_loa()

    return {
        "datos": df,
        "datos_rio_loa": datos_rio_loa,
        "hojas": hojas,
        "columnas": df.columns.tolist(),
        "cantidad_registros": len(df),
        "cantidad_rio_loa": len(datos_rio_loa)
    }


# =====================================================
# 7. BUSCAR ESTRUCTURA DE LA HOJA MRP
# =====================================================

def encontrar_columnas_hoja_mrp(hoja):

    # Buscar los encabezados en las primeras filas.
    # No se depende de una fila fija.

    for numero_fila in range(1, min(20, hoja.max_row) + 1):

        encabezados = {}

        for columna in range(1, hoja.max_column + 1):

            valor = hoja.cell(
                numero_fila,
                columna
            ).value

            nombre = normalizar_encabezado(valor)

            if nombre:
                encabezados[nombre] = columna

        if (
            "centro" in encabezados
            and "material" in encabezados
            and "descripcion del material" in encabezados
            and "stock actual" in encabezados
            and "mrp" in encabezados
        ):

            return numero_fila, encabezados

    raise ValueError(
        "No se encontraron los encabezados Centro, Material, "
        "Descripción del material, Stock Actual y MRP "
        "en la hoja MRP."
    )


# =====================================================
# 8. CARGAR INDICADORES DE LA HOJA MRP
# =====================================================

@st.cache_data(ttl=60)
def cargar_indicadores_mrp():

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

        if "MRP" not in libro.sheetnames:
            raise ValueError(
                "No se encontró la hoja MRP en el archivo."
            )

        hoja = libro["MRP"]

        fila_encabezados, encabezados = (
            encontrar_columnas_hoja_mrp(hoja)
        )

        col_centro = encabezados["centro"]
        col_material = encabezados["material"]
        col_descripcion = encabezados["descripcion del material"]
        col_stock = encabezados["stock actual"]
        col_tipo_mrp = encabezados["mrp"]

        # -------------------------------------------------
        # Identificar la columna del último mes disponible
        # -------------------------------------------------

        columnas_meses = []

        for columna in range(
            col_tipo_mrp + 1,
            hoja.max_column + 1
        ):

            valor = hoja.cell(
                fila_encabezados,
                columna
            ).value

            if valor is None:
                continue

            # Encabezados que son fechas reales de Excel.

            if hasattr(valor, "year") and hasattr(valor, "month"):

                columnas_meses.append(
                    (columna, valor)
                )

            # Encabezados escritos como nov-26, dic-26, etc.

            elif isinstance(valor, str):

                texto = valor.strip().lower()

                if re.match(
                    r"^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[- /]\d{2,4}$",
                    texto
                ):

                    columnas_meses.append(
                        (columna, texto)
                    )

        if not columnas_meses:

            raise ValueError(
                "No se encontraron encabezados mensuales "
                "a la derecha de la columna MRP."
            )

        # La última columna mensual es la más reciente
        # dentro del archivo.

        columna_mes_actual, mes_actual = columnas_meses[-1]

        registros = []

        # -------------------------------------------------
        # Recorrer filas y reconocer los bloques de materiales
        # -------------------------------------------------

        fila_inicio = fila_encabezados + 1

        for fila in range(
            fila_inicio,
            hoja.max_row + 1
        ):

            centro = normalizar_codigo(
                hoja.cell(fila, col_centro).value
            ).upper()

            material = normalizar_codigo(
                hoja.cell(fila, col_material).value
            )

            if centro != CENTRO_RIO_LOA or not material:
                continue

            descripcion = limpiar_texto(
                hoja.cell(fila, col_descripcion).value
            )

            stock = convertir_numero(
                hoja.cell(fila, col_stock).value
            )

            tipo = normalizar_encabezado(
                hoja.cell(fila, col_tipo_mrp).value
            )

            # La fila principal corresponde a Cons. Proy.
            # Si el valor está vacío, igualmente se conserva
            # el registro para no perder el material.

            if tipo not in ["cons proy", "consumo proy", ""]:

                continue

            consumo_acumulado = None

            # Buscar Cons. Acu dentro del bloque del material.
            # Las filas secundarias normalmente no repiten
            # el centro ni el código del material.

            for fila_secundaria in range(
                fila + 1,
                hoja.max_row + 1
            ):

                siguiente_centro = normalizar_codigo(
                    hoja.cell(
                        fila_secundaria,
                        col_centro
                    ).value
                ).upper()

                siguiente_material = normalizar_codigo(
                    hoja.cell(
                        fila_secundaria,
                        col_material
                    ).value
                )

                # Si comienza otro material, termina el bloque actual.

                if siguiente_centro or siguiente_material:
                    break

                etiqueta = normalizar_encabezado(
                    hoja.cell(
                        fila_secundaria,
                        col_tipo_mrp
                    ).value
                )

                if etiqueta in ["cons acu", "consumo acu"]:

                    consumo_acumulado = convertir_numero(
                        hoja.cell(
                            fila_secundaria,
                            columna_mes_actual
                        ).value
                    )

                    break

            registros.append({

                "Centro": centro,

                "Material": material,

                "Descripción": descripcion,

                "Stock Actual": stock,

                "Consumo real acumulado": consumo_acumulado,

                "Mes MRP": mes_actual

            })

        indicadores = pd.DataFrame(registros)

        if indicadores.empty:
            return indicadores

        # En caso de registros repetidos, conservar
        # el último registro leído para cada material.

        indicadores = indicadores.drop_duplicates(
            subset=["Centro", "Material"],
            keep="last"
        )

        return indicadores.reset_index(drop=True)

    finally:
        libro.close()


# =====================================================
# 9. OBTENER INDICADORES DE UN MATERIAL
# =====================================================

def obtener_indicadores_material(material):

    df = cargar_indicadores_mrp()

    material = normalizar_codigo(material)

    if df.empty:
        return None

    resultado = df[
        (df["Centro"] == CENTRO_RIO_LOA)
        & (df["Material"] == material)
    ]

    if resultado.empty:

        return None

    fila = resultado.iloc[0]

    return {
        "stock_actual": fila["Stock Actual"],
        "consumo_acumulado": fila["Consumo real acumulado"],
        "mes_mrp": fila["Mes MRP"],
        "descripcion": fila["Descripción"]
    }


# =====================================================
# 10. LIMPIAR CACHÉ DEL MRP
# =====================================================

def actualizar_mrp():

    cargar_mrp.clear()
    obtener_datos_rio_loa.clear()
    obtener_materias_primas_activas.clear()
    cargar_indicadores_mrp.clear()
