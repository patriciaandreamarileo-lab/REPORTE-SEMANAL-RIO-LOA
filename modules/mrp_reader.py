
import io
import re
import unicodedata

import pandas as pd
import streamlit as st

from openpyxl import load_workbook

from modules.github_storage import descargar_archivo_github


# =====================================================
# 1. CONFIGURACIÓN GENERAL
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

    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass

    return str(valor).strip()


def normalizar_codigo(valor):

    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass

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

    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if texto in ["", "-", "—", "None"]:
        return None

    texto = texto.replace(" ", "")

    # Formato chileno: 146.933,00
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
# 7. IDENTIFICAR ENCABEZADOS DE LA HOJA MRP
# =====================================================

def encontrar_columnas_hoja_mrp(hoja):

    # Buscar encabezados en las primeras 20 filas.

    for numero_fila, fila in enumerate(
        hoja.iter_rows(
            min_row=1,
            max_row=20,
            values_only=True
        ),
        start=1
    ):

        encabezados = {}

        for indice, valor in enumerate(fila):

            nombre = normalizar_encabezado(valor)

            if nombre:
                encabezados[nombre] = indice

        columnas_necesarias = [
            "centro",
            "material",
            "descripcion del material",
            "stock actual",
            "mrp"
        ]

        if all(
            nombre in encabezados
            for nombre in columnas_necesarias
        ):

            return (
                numero_fila,
                encabezados,
                fila
            )

    raise ValueError(
        "No se encontraron los encabezados necesarios "
        "en la hoja MRP."
    )


# =====================================================
# 8. IDENTIFICAR LA COLUMNA DEL MES
# =====================================================

def identificar_columnas_meses(
    valores_encabezado,
    columna_mrp
):

    meses = []

    patron_mes = (
        r"^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)"
        r"[- /]\d{2,4}$"
    )

    for indice, valor in enumerate(valores_encabezado):

        if indice <= columna_mrp:
            continue

        if valor is None:
            continue

        # Encabezado como fecha real de Excel.

        if (
            hasattr(valor, "year")
            and hasattr(valor, "month")
        ):

            meses.append({
                "indice": indice,
                "valor": valor,
                "orden": (
                    valor.year * 100 + valor.month
                )
            })

        # Encabezado como texto: nov-26, dic-26, etc.

        elif isinstance(valor, str):

            texto = valor.strip().lower()

            if re.match(patron_mes, texto):

                meses.append({
                    "indice": indice,
                    "valor": valor,
                    "orden": texto
                })

    if not meses:
        raise ValueError(
            "No se encontraron columnas mensuales "
            "a la derecha de la columna MRP."
        )

    return meses


# =====================================================
# 9. CARGAR INDICADORES DE LA HOJA MRP
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
                "No se encontró la hoja MRP."
            )

        hoja = libro["MRP"]

        # -------------------------------------------------
        # A. IDENTIFICAR ENCABEZADOS
        # -------------------------------------------------

        (
            fila_encabezados,
            encabezados,
            valores_encabezado
        ) = encontrar_columnas_hoja_mrp(hoja)

        col_centro = encabezados["centro"]
        col_material = encabezados["material"]
        col_descripcion = encabezados[
            "descripcion del material"
        ]
        col_stock = encabezados["stock actual"]
        col_tipo = encabezados["mrp"]

        # -------------------------------------------------
        # B. IDENTIFICAR EL ÚLTIMO MES
        # -------------------------------------------------

        meses = identificar_columnas_meses(
            valores_encabezado,
            col_tipo
        )

        # Tomar el último mes según el orden de las columnas.

        mes_actual = meses[-1]

        columna_mes_actual = mes_actual["indice"]

        nombre_mes_actual = mes_actual["valor"]

        # Limitar la lectura hasta la columna necesaria.

        max_columna_lectura = max(
            col_centro,
            col_material,
            col_descripcion,
            col_stock,
            col_tipo,
            columna_mes_actual
        ) + 1

        # -------------------------------------------------
        # C. RECORRER LA HOJA UNA SOLA VEZ
        # -------------------------------------------------

        registros = []

        material_actual = None

        for fila in hoja.iter_rows(
            min_row=fila_encabezados + 1,
            max_col=max_columna_lectura,
            values_only=True
        ):

            centro = normalizar_codigo(
                fila[col_centro]
                if len(fila) > col_centro
                else None
            ).upper()

            material = normalizar_codigo(
                fila[col_material]
                if len(fila) > col_material
                else None
            )

            descripcion = limpiar_texto(
                fila[col_descripcion]
                if len(fila) > col_descripcion
                else None
            )

            tipo = normalizar_encabezado(
                fila[col_tipo]
                if len(fila) > col_tipo
                else None
            )

            # ---------------------------------------------
            # D. DETECTAR UNA NUEVA MATERIA PRIMA
            # ---------------------------------------------

            if centro == CENTRO_RIO_LOA and material:

                material_actual = None

                if tipo in [
                    "cons proy",
                    "consumo proy",
                    ""
                ]:

                    stock = convertir_numero(
                        fila[col_stock]
                        if len(fila) > col_stock
                        else None
                    )

                    material_actual = {

                        "Centro": centro,

                        "Material": material,

                        "Descripción": descripcion,

                        "Stock Actual": stock,

                        "Consumo real acumulado": None,

                        "Mes MRP": nombre_mes_actual

                    }

                    registros.append(material_actual)

                continue

            # ---------------------------------------------
            # E. BUSCAR CONS. ACU EN EL BLOQUE ACTUAL
            # ---------------------------------------------

            if material_actual is not None:

                if tipo in [
                    "cons acu",
                    "consumo acu"
                ]:

                    valor_consumo = (
                        fila[columna_mes_actual]
                        if len(fila) > columna_mes_actual
                        else None
                    )

                    material_actual[
                        "Consumo real acumulado"
                    ] = convertir_numero(
                        valor_consumo
                    )

                    material_actual = None

        # -------------------------------------------------
        # F. CONSTRUIR RESULTADO
        # -------------------------------------------------

        indicadores = pd.DataFrame(registros)

        if indicadores.empty:
            return indicadores

        indicadores = indicadores.drop_duplicates(
            subset=["Centro", "Material"],
            keep="last"
        )

        indicadores = indicadores.reset_index(
            drop=True
        )

        return indicadores

    finally:
        libro.close()


# =====================================================
# 10. OBTENER INDICADORES DE UN MATERIAL
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

        "consumo_acumulado": fila[
            "Consumo real acumulado"
        ],

        "mes_mrp": fila["Mes MRP"],

        "descripcion": fila["Descripción"]

    }


# =====================================================
# 11. ACTUALIZAR CACHÉ DEL MRP
# =====================================================

def actualizar_mrp():

    cargar_mrp.clear()

    obtener_datos_rio_loa.clear()

    obtener_materias_primas_activas.clear()

    cargar_indicadores_mrp.clear()
