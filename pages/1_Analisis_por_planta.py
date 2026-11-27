import streamlit as st
import pandas as pd

from modules.navegacion import configurar_navegacion
from modules.mrp_reader import cargar_mrp


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Análisis por planta | Río Loa",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()


# =====================================================
# 2. ESTILOS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.plant-header {
    background-color: #E6EFF9;
    border-left: 7px solid #245A91;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 20px;
}

.plant-title {
    color: #245A91;
    font-size: 30px;
    font-weight: 750;
}

.plant-subtitle {
    color: #64748B;
    font-size: 15px;
}

.alert-box {
    background-color: #FEE2E2;
    border-left: 6px solid #DC2626;
    border-radius: 9px;
    padding: 15px;
    margin-bottom: 12px;
    color: #991B1B;
}

.section-description {
    color: #64748B;
    font-size: 14px;
    margin-top: -8px;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. FUNCIONES DE LIMPIEZA
# =====================================================

def convertir_numero(columna):

    return pd.to_numeric(
        columna,
        errors="coerce"
    )


def limpiar_codigo(valor):

    if pd.isna(valor):
        return ""

    valor = str(valor).strip()

    if valor.endswith(".0"):
        valor = valor[:-2]

    return valor.upper()


def formato_numero(valor):

    if pd.isna(valor):
        return "—"

    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =====================================================
# 4. CARGA DEL MRP
# =====================================================

st.title("Análisis por planta")

st.markdown(
    "Análisis de planificación, consumo y nivel de servicio "
    "de materias primas de Río Loa."
)

col_actualizar, col_fecha = st.columns([1, 4])

with col_actualizar:

    if st.button(
        "🔄 Actualizar datos",
        use_container_width=True
    ):

        cargar_mrp.clear()
        st.rerun()


try:

    datos_mrp, hojas_mrp = cargar_mrp()

    if datos_mrp is None or datos_mrp.empty:

        st.error("El archivo MRP no contiene información.")

        st.stop()

except Exception as error:

    st.error(
        f"No fue posible cargar el MRP desde GitHub: {error}"
    )

    st.info(
        "Verifica que el archivo Planificacion_MRP.xlsm "
        "esté guardado correctamente en GitHub."
    )

    st.stop()


# =====================================================
# 5. VALIDACIÓN DE COLUMNAS
# =====================================================

columnas_necesarias = [
    "Centro",
    "Material",
    "Descripción del material",
    "UM",
    "MMPP Activa",
    "Consumo X̄",
    "Stock Actual",
    "Stock Óptimo",
    "Stock Seguridad",
    "Stock Máximo",
    "Cobertura a [Días]",
    "NS",
    "NS Corregido",
    "Comentario"
]

faltantes = [
    columna
    for columna in columnas_necesarias
    if columna not in datos_mrp.columns
]

if faltantes:

    st.error(
        "Faltan columnas necesarias en el MRP: "
        + ", ".join(faltantes)
    )

    st.write("Columnas encontradas:")
    st.write(datos_mrp.columns.tolist())

    st.stop()


# =====================================================
# 6. IDENTIFICACIÓN DE RÍO LOA
# =====================================================

df = datos_mrp.copy()

df["Centro"] = df["Centro"].apply(limpiar_codigo)

df["Material"] = df["Material"].apply(limpiar_codigo)

# Identificar todas las materias primas del centro E024.
datos_rio_loa = df[
    df["Centro"] == "E024"
].copy()

if datos_rio_loa.empty:

    st.warning(
        "No se encontraron materias primas asociadas "
        "al centro E024 en el MRP."
    )

    st.stop()


# =====================================================
# 7. LIMPIEZA DE INFORMACIÓN
# =====================================================

columnas_numericas = [
    "Consumo X̄",
    "Stock Actual",
    "Stock Óptimo",
    "Stock Seguridad",
    "Stock Máximo",
    "Cobertura a [Días]"
]

for columna in columnas_numericas:

    datos_rio_loa[columna] = convertir_numero(
        datos_rio_loa[columna]
    )


# Normalizar clasificación de nivel de servicio

datos_rio_loa["NS Corregido"] = (
    datos_rio_loa["NS Corregido"]
    .fillna(datos_rio_loa["NS"])
    .astype(str)
    .str.strip()
    .str.upper()
)

# Normalizar MMPP Activa

datos_rio_loa["MMPP Activa"] = (
    datos_rio_loa["MMPP Activa"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

# Se consideran todas las materias primas E024.
# Se conserva la información de MMPP Activa para consulta.

datos_rio_loa = datos_rio_loa.reset_index(drop=True)


# =====================================================
# 8. ENCABEZADO RÍO LOA
# =====================================================

st.markdown("""
<div class="plant-header">

    <div style="
        font-size:13px;
        font-weight:bold;
        color:#245A91;
        letter-spacing:2px;
    ">
        ANÁLISIS INDIVIDUAL
    </div>

    <div class="plant-title">
        RÍO LOA
    </div>

    <div class="plant-subtitle">
        Calama | Enaex Chile | Centro E024
    </div>

</div>
""", unsafe_allow_html=True)


st.caption(
    f"Última consulta: {len(datos_rio_loa)} materias primas "
    "identificadas en el MRP para el centro E024."
)


# =====================================================
# 9. INDICADORES GENERALES
# =====================================================

st.subheader("Indicadores de la planta")

total_materiales = len(datos_rio_loa)

conteo_ns = (
    datos_rio_loa["NS Corregido"]
    .value_counts()
    .reindex(["BB", "EB", "SB"], fill_value=0)
)

total_ns = int(conteo_ns.sum())

# Indicador ponderado:
# EB = 100%, SB = 50%, BB = 0%.

if total_ns > 0:

    nivel_servicio = (
        conteo_ns["EB"] + conteo_ns["SB"] * 0.5
    ) / total_ns * 100

else:

    nivel_servicio = 0


coberturas_validas = (
    datos_rio_loa["Cobertura a [Días]"]
    .dropna()
)

if not coberturas_validas.empty:

    cobertura_promedio = coberturas_validas.mean()

else:

    cobertura_promedio = 0


col1, col2, col3 = st.columns(3)

col1.metric(
    "Materias primas",
    f"{total_materiales}"
)

col2.metric(
    "Nivel de servicio",
    f"{nivel_servicio:.1f}%"
)

col3.metric(
    "Cobertura promedio",
    f"{cobertura_promedio:.1f} días"
)


st.divider()


# =====================================================
# 10. DISTRIBUCIÓN BB, EB Y SB
# =====================================================

st.subheader("Distribución de materias primas")

st.markdown(
    '<div class="section-description">'
    'Distribución porcentual de las materias primas '
    'según su clasificación de nivel de servicio.'
    '</div>',
    unsafe_allow_html=True
)

if total_ns > 0:

    grafico_ns = pd.DataFrame({
        "Clasificación": ["BB", "EB", "SB"],
        "Cantidad": [
            int(conteo_ns["BB"]),
            int(conteo_ns["EB"]),
            int(conteo_ns["SB"])
        ]
    })

    grafico_ns = grafico_ns[
        grafico_ns["Cantidad"] > 0
    ].copy()

    grafico_ns["Porcentaje"] = (
        grafico_ns["Cantidad"] /
        grafico_ns["Cantidad"].sum()
    )

    especificacion_grafico = {

        "width": "container",
        "height": 380,

        "layer": [

            {
                "mark": {
                    "type": "arc",
                    "innerRadius": 0,
                    "outerRadius": 145,
                    "stroke": "white",
                    "strokeWidth": 3
                },

                "encoding": {

                    "theta": {
                        "field": "Cantidad",
                        "type": "quantitative",
                        "stack": True
                    },

                    "color": {
                        "field": "Clasificación",
                        "type": "nominal",

                        "scale": {
                            "domain": ["BB", "EB", "SB"],
                            "range": [
                                "#E52525",
                                "#16A34A",
                                "#009FE3"
                            ]
                        },

                        "legend": {
                            "title": "Clasificación NS",
                            "orient": "right"
                        }
                    },

                    "tooltip": [
                        {
                            "field": "Clasificación",
                            "title": "Clasificación"
                        },
                        {
                            "field": "Cantidad",
                            "title": "Cantidad"
                        },
                        {
                            "field": "Porcentaje",
                            "title": "Porcentaje",
                            "format": ".1%"
                        }
                    ]
                }
            },

            {
                "mark": {
                    "type": "text",
                    "radius": 95,
                    "fontSize": 17,
                    "fontWeight": "bold",
                    "color": "white"
                },

                "encoding": {

                    "theta": {
                        "field": "Cantidad",
                        "type": "quantitative",
                        "stack": True
                    },

                    "text": {
                        "field": "Porcentaje",
                        "type": "quantitative",
                        "format": ".1%"
                    }
                }
            }
        ]
    }

    st.vega_lite_chart(
        grafico_ns,
        especificacion_grafico,
        use_container_width=True
    )

else:

    st.warning(
        "No se encontraron clasificaciones BB, EB o SB."
    )


st.divider()


# =====================================================
# 11. CINCO MATERIAS PRIMAS CON MENOR STOCK
# =====================================================

st.subheader("Materias primas con menor stock")

st.markdown(
    '<div class="section-description">'
    'Identificación de las cinco materias primas '
    'con menor disponibilidad de stock actual.'
    '</div>',
    unsafe_allow_html=True
)

menor_stock = datos_rio_loa[
    datos_rio_loa["Stock Actual"].notna()
].copy()

menor_stock = menor_stock.sort_values(
    by="Stock Actual",
    ascending=True
).head(5)


if not menor_stock.empty:

    tabla_stock = menor_stock[[
        "Material",
        "Descripción del material",
        "UM",
        "Stock Actual",
        "Stock Seguridad",
        "Cobertura a [Días]"
    ]].copy()

    tabla_stock["Stock Actual"] = (
        tabla_stock["Stock Actual"].map(formato_numero)
    )

    tabla_stock["Stock Seguridad"] = (
        tabla_stock["Stock Seguridad"].map(formato_numero)
    )

    tabla_stock["Cobertura a [Días]"] = (
        tabla_stock["Cobertura a [Días]"].map(formato_numero)
    )

    st.dataframe(
        tabla_stock,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No hay datos disponibles de stock actual.")


st.divider()


# =====================================================
# 12. CINCO MATERIAS PRIMAS DE MENOR CONSUMO
#     CON MAYOR COBERTURA
# =====================================================

st.subheader(
    "Materias primas con menor consumo y mayor cobertura"
)

st.markdown(
    '<div class="section-description">'
    'Identificación de materias primas con menor consumo '
    'promedio y mayores días de cobertura de stock.'
    '</div>',
    unsafe_allow_html=True
)

menor_consumo = datos_rio_loa[
    datos_rio_loa["Consumo X̄"].notna()
    & datos_rio_loa["Cobertura a [Días]"].notna()
].copy()

menor_consumo = menor_consumo[
    menor_consumo["Consumo X̄"] >= 0
]

menor_consumo = menor_consumo.sort_values(
    by=[
        "Consumo X̄",
        "Cobertura a [Días]"
    ],
    ascending=[
        True,
        False
    ]
).head(5)


if not menor_consumo.empty:

    tabla_consumo = menor_consumo[[
        "Material",
        "Descripción del material",
        "UM",
        "Consumo X̄",
        "Stock Actual",
        "Cobertura a [Días]"
    ]].copy()

    tabla_consumo["Consumo X̄"] = (
        tabla_consumo["Consumo X̄"].map(formato_numero)
    )

    tabla_consumo["Stock Actual"] = (
        tabla_consumo["Stock Actual"].map(formato_numero)
    )

    tabla_consumo["Cobertura a [Días]"] = (
        tabla_consumo["Cobertura a [Días]"].map(formato_numero)
    )

    st.dataframe(
        tabla_consumo,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No se encontraron registros suficientes "
        "para realizar este análisis."
    )


st.divider()


# =====================================================
# 13. ALERTAS DE COBERTURA MENOR A 10 DÍAS
# =====================================================

st.subheader("Alertas de materias primas críticas")

st.markdown(
    '<div class="section-description">'
    'Materias primas cuya cobertura disponible '
    'es inferior a 10 días.'
    '</div>',
    unsafe_allow_html=True
)

alertas = datos_rio_loa[
    datos_rio_loa["Cobertura a [Días]"].notna()
    & (
        datos_rio_loa["Cobertura a [Días]"] < 10
    )
].copy()

alertas = alertas.sort_values(
    by="Cobertura a [Días]",
    ascending=True
)


if not alertas.empty:

    st.error(
        f"¡ATENCIÓN! Se identificaron {len(alertas)} "
        "materias primas con menos de 10 días de cobertura."
    )

    for _, fila in alertas.iterrows():

        material = fila["Material"]

        descripcion = fila["Descripción del material"]

        cobertura = fila["Cobertura a [Días]"]

        stock = fila["Stock Actual"]

        st.markdown(
            f"""
            <div class="alert-box">

                <strong>⚠️ MATERIAL {material}</strong>

                <br>

                {descripcion}

                <br><br>

                <strong>Cobertura:</strong>
                {formato_numero(cobertura)} días

                &nbsp; | &nbsp;

                <strong>Stock actual:</strong>
                {formato_numero(stock)}

            </div>
            """,
            unsafe_allow_html=True
        )

else:

    st.success(
        "No existen materias primas con cobertura "
        "inferior a 10 días."
    )


st.divider()


# =====================================================
# 14. DETALLE GENERAL DE MATERIAS PRIMAS
# =====================================================

with st.expander("Consultar todas las materias primas de Río Loa"):

    columnas_detalle = [
        "Centro",
        "Material",
        "Descripción del material",
        "UM",
        "MMPP Activa",
        "Consumo X̄",
        "Stock Actual",
        "Stock Óptimo",
        "Stock Seguridad",
        "Stock Máximo",
        "Cobertura a [Días]",
        "NS",
        "NS Corregido",
        "Comentario"
    ]

    st.dataframe(
        datos_rio_loa[columnas_detalle],
        use_container_width=True,
        hide_index=True
    )


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
        ENAEX CHILE | RÍO LOA
        <br>
        Dashboard de gestión de materias primas
    </div>
    """,
    unsafe_allow_html=True
)
