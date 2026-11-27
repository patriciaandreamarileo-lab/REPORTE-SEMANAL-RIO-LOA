import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from modules.navegacion import configurar_navegacion
from modules.github_storage import descargar_archivo_github


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Evolución de precios | Río Loa",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()

RUTA_PRECIOS = "data/PRECIOS/precios_rio_loa.xlsx"
CENTRO_RIO_LOA = "E024"


# =====================================================
# 2. ESTILOS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.plant-description {
    color: #64748B;
    font-size: 16px;
    margin-bottom: 20px;
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
# 3. FUNCIONES AUXILIARES
# =====================================================

def limpiar_texto(serie):

    return (
        serie
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def convertir_numero(serie):

    return pd.to_numeric(
        serie,
        errors="coerce"
    )


def formato_numero(valor, decimales=2):

    if pd.isna(valor):
        return "—"

    return (
        f"{valor:,.{decimales}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# =====================================================
# 4. CARGAR ARCHIVO DE PRECIOS DESDE GITHUB
# =====================================================

@st.cache_data(ttl=60)
def cargar_precios():

    contenido = descargar_archivo_github(
        RUTA_PRECIOS
    )

    if contenido is None:

        raise Exception(
            "No se encontró el archivo de precios "
            "en GitHub."
        )

    df = pd.read_excel(
        BytesIO(contenido),
        sheet_name="Data",
        engine="openpyxl"
    )

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df


# =====================================================
# 5. ACTUALIZACIÓN DE DATOS
# =====================================================

col_actualizar, col_estado = st.columns([1, 3])

with col_actualizar:

    if st.button(
        "🔄 Actualizar datos",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()


try:

    datos_originales = cargar_precios()

    if datos_originales.empty:

        st.error(
            "El archivo de precios no contiene registros."
        )

        st.stop()

except Exception as error:

    st.error(
        f"No fue posible cargar los precios desde GitHub: {error}"
    )

    st.stop()


# =====================================================
# 6. VALIDAR COLUMNAS
# =====================================================

columnas_requeridas = [
    "Material",
    "Centro",
    "Clase de movimiento",
    "Fecha contabiliz.",
    "Pedido",
    "Moneda",
    "Impte.mon.local",
    "Ctd.en UM entrada",
    "Proveedor"
]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in datos_originales.columns
]

if faltantes:

    st.error(
        "Faltan columnas necesarias en el archivo: "
        + ", ".join(faltantes)
    )

    st.stop()


# =====================================================
# 7. PREPARAR INFORMACIÓN
# =====================================================

datos = datos_originales.copy()

# Normalizar centro

datos["Centro"] = (
    limpiar_texto(datos["Centro"])
    .str.upper()
)

# Filtrar exclusivamente Río Loa

datos = datos[
    datos["Centro"] == CENTRO_RIO_LOA
].copy()

if datos.empty:

    st.error(
        "No se encontraron registros del centro E024 "
        "en el archivo de precios."
    )

    st.stop()


# Normalizar código de material

datos["Material"] = limpiar_texto(
    datos["Material"]
)


# Descripción del material

if "Descripción material" in datos.columns:

    datos["Descripción"] = limpiar_texto(
        datos["Descripción material"]
    )

elif "Descripción del material" in datos.columns:

    datos["Descripción"] = limpiar_texto(
        datos["Descripción del material"]
    )

else:

    datos["Descripción"] = datos["Material"]


# Número de OC

datos["Pedido"] = limpiar_texto(
    datos["Pedido"]
)


# Moneda

datos["Moneda"] = (
    limpiar_texto(datos["Moneda"])
    .str.upper()
)


# Proveedor

if "Nombre 1" in datos.columns:

    datos["Nombre proveedor"] = limpiar_texto(
        datos["Nombre 1"]
    )

    datos["Nombre proveedor"] = (
        datos["Nombre proveedor"]
        .replace("", pd.NA)
        .fillna(limpiar_texto(datos["Proveedor"]))
    )

else:

    datos["Nombre proveedor"] = limpiar_texto(
        datos["Proveedor"]
    )


# Fecha

datos["Fecha contabiliz."] = pd.to_datetime(
    datos["Fecha contabiliz."],
    errors="coerce",
    dayfirst=True
)


# Valores numéricos

datos["Cantidad"] = convertir_numero(
    datos["Ctd.en UM entrada"]
)

datos["Importe"] = convertir_numero(
    datos["Impte.mon.local"]
)


# Tipos de movimiento

datos["Clase de movimiento"] = limpiar_texto(
    datos["Clase de movimiento"]
)


datos = datos[
    datos["Clase de movimiento"].isin(["101", "102"])
].copy()


# Eliminar registros sin información esencial

datos = datos.dropna(
    subset=[
        "Material",
        "Fecha contabiliz.",
        "Cantidad",
        "Importe"
    ]
)


datos = datos[
    (datos["Cantidad"] != 0)
    & (datos["Importe"] != 0)
]


# =====================================================
# 8. CONSOLIDAR ÓRDENES DE COMPRA
# =====================================================

# Se agrupan los movimientos 101 y 102 por OC,
# material y moneda. De esta manera se consideran
# las anulaciones o reversiones cuando sus cantidades
# e importes vienen con signo contrario en SAP.

agrupacion = [
    "Material",
    "Descripción",
    "Pedido",
    "Moneda",
    "Nombre proveedor"
]

datos_precios = (
    datos
    .groupby(
        agrupacion,
        dropna=False
    )
    .agg(
        Fecha=("Fecha contabiliz.", "min"),
        Cantidad=("Cantidad", "sum"),
        Importe=("Importe", "sum")
    )
    .reset_index()
)


# Precio unitario ponderado por cantidad

datos_precios["Precio unitario"] = (
    datos_precios["Importe"].abs()
    / datos_precios["Cantidad"].abs()
)


# Eliminar órdenes sin cantidad neta o sin precio válido

datos_precios = datos_precios[
    (datos_precios["Cantidad"] != 0)
    & (datos_precios["Precio unitario"] > 0)
    & (datos_precios["Fecha"].notna())
].copy()


# Orden cronológico

datos_precios = datos_precios.sort_values(
    "Fecha"
).reset_index(drop=True)


if datos_precios.empty:

    st.warning(
        "No existen registros válidos para analizar precios."
    )

    st.stop()


# =====================================================
# 9. ENCABEZADO
# =====================================================

st.title("Evolución de precios")

st.markdown(
    '<div class="plant-description">'
    'Análisis histórico de precios de compra de materias '
    'primas de la planta Río Loa.'
    '</div>',
    unsafe_allow_html=True
)


encabezado = (
    '<div style="'
    'background:linear-gradient(110deg,#173B65,#245A91);'
    'padding:28px;'
    'border-radius:12px;'
    'margin-bottom:25px;'
    '">'
    '<div style="'
    'color:#DCEAF8;'
    'font-size:13px;'
    'font-weight:600;'
    'letter-spacing:1.5px;'
    '">'
    'ANÁLISIS INDIVIDUAL'
    '</div>'
    '<div style="'
    'color:white;'
    'font-size:30px;'
    'font-weight:700;'
    'margin-top:5px;'
    '">'
    'RÍO LOA'
    '</div>'
    '<div style="'
    'color:#DCEAF8;'
    'font-size:15px;'
    'margin-top:5px;'
    '">'
    'Calama | Enaex Chile | Centro E024'
    '</div>'
    '</div>'
)

st.markdown(
    encabezado,
    unsafe_allow_html=True
)


# =====================================================
# 10. RANKING DE MATERIAS PRIMAS CON MAYORES CAMBIOS
# =====================================================

st.subheader(
    "Materias primas con mayores variaciones de precios"
)

st.markdown(
    "Se identifican las materias primas que presentan "
    "las mayores variaciones entre su primer y último "
    "precio registrado, comparando siempre dentro "
    "de una misma moneda."
)


ranking_base = datos_precios.sort_values(
    "Fecha"
).copy()


resultados_ranking = []

for (codigo, moneda), grupo in ranking_base.groupby(
    ["Material", "Moneda"]
):

    grupo = grupo.sort_values("Fecha")

    if len(grupo) < 2:
        continue

    primer_registro = grupo.iloc[0]
    ultimo_registro = grupo.iloc[-1]

    precio_inicial = primer_registro["Precio unitario"]
    precio_final = ultimo_registro["Precio unitario"]

    if precio_inicial <= 0:
        continue

    variacion = (
        (precio_final - precio_inicial)
        / precio_inicial
    ) * 100

    resultados_ranking.append({

        "Código": codigo,

        "Materia prima": grupo.iloc[0]["Descripción"],

        "Moneda": moneda,

        "Precio inicial": precio_inicial,

        "Precio más reciente": precio_final,

        "Variación (%)": variacion,

        "Variación absoluta (%)": abs(variacion)

    })


ranking = pd.DataFrame(resultados_ranking)


if not ranking.empty:

    ranking = ranking.sort_values(
        "Variación absoluta (%)",
        ascending=False
    ).head(4).reset_index(drop=True)

    ranking["Precio inicial"] = ranking[
        "Precio inicial"
    ].apply(
        lambda x: formato_numero(x, 2)
    )

    ranking["Precio más reciente"] = ranking[
        "Precio más reciente"
    ].apply(
        lambda x: formato_numero(x, 2)
    )

    ranking["Variación (%)"] = ranking[
        "Variación (%)"
    ].apply(
        lambda x: (
            f"+{formato_numero(x, 2)}%"
            if x > 0
            else f"{formato_numero(x, 2)}%"
        )
    )

    ranking = ranking[
        [
            "Código",
            "Materia prima",
            "Moneda",
            "Precio inicial",
            "Precio más reciente",
            "Variación (%)"
        ]
    ]

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No hay suficientes registros para calcular "
        "variaciones de precios."
    )


st.divider()


# =====================================================
# 11. BUSCADOR DE MATERIAS PRIMAS
# =====================================================

st.subheader(
    "Análisis individual de materias primas"
)

st.markdown(
    "Busca una materia prima por su código o nombre "
    "para consultar la evolución de sus precios."
)


# Crear catálogo de materiales

catalogo = (
    datos_precios[
        ["Material", "Descripción"]
    ]
    .drop_duplicates()
    .sort_values("Material")
    .reset_index(drop=True)
)


catalogo["Etiqueta"] = (
    catalogo["Material"].astype(str)
    + " -- "
    + catalogo["Descripción"].astype(str)
)


# Buscador

busqueda = st.text_input(
    "Buscar materia prima",
    placeholder="Ingresa el código o nombre del material..."
)


catalogo_filtrado = catalogo.copy()


if busqueda:

    catalogo_filtrado = catalogo_filtrado[
        catalogo_filtrado["Material"].str.contains(
            busqueda,
            case=False,
            na=False,
            regex=False
        )
        |
        catalogo_filtrado["Descripción"].str.contains(
            busqueda,
            case=False,
            na=False,
            regex=False
        )
    ]


if catalogo_filtrado.empty:

    st.warning(
        "No se encontraron materias primas con ese código "
        "o descripción."
    )

    st.stop()


seleccion = st.selectbox(
    "Seleccionar materia prima",
    catalogo_filtrado["Etiqueta"].tolist()
)


material_seleccionado = catalogo_filtrado[
    catalogo_filtrado["Etiqueta"] == seleccion
].iloc[0]


codigo_seleccionado = material_seleccionado["Material"]


# Filtrar material seleccionado

detalle = datos_precios[
    datos_precios["Material"] == codigo_seleccionado
].copy()


detalle = detalle.sort_values(
    "Fecha"
).reset_index(drop=True)


st.markdown(
    f"### {material_seleccionado['Descripción']}"
)

st.caption(
    f"Código de material: {codigo_seleccionado}"
)


# =====================================================
# 12. INDICADORES DEL MATERIAL
# =====================================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Órdenes de compra",
    detalle["Pedido"].nunique()
)

col2.metric(
    "Primer registro",
    detalle["Fecha"].min().strftime("%d-%m-%Y")
)

col3.metric(
    "Último registro",
    detalle["Fecha"].max().strftime("%d-%m-%Y")
)


# =====================================================
# 13. MONEDAS DISPONIBLES
# =====================================================

st.subheader(
    "Moneda de los precios registrados"
)


monedas = sorted(
    detalle["Moneda"]
    .dropna()
    .unique()
    .tolist()
)


columnas_monedas = st.columns(
    max(len(monedas), 1)
)


for i, moneda in enumerate(monedas):

    columnas_monedas[i].metric(
        "Moneda",
        moneda
    )


st.caption(
    "Los precios se muestran en su moneda original. "
    "USD y CLP se representan en escalas separadas "
    "para evitar comparaciones incorrectas."
)


# =====================================================
# 14. GRÁFICO DE EVOLUCIÓN DE PRECIOS
# =====================================================

st.subheader(
    "Evolución histórica de precios por orden de compra"
)


if detalle.empty:

    st.info(
        "No existen órdenes de compra para este material."
    )

else:

    detalle_grafico = detalle.copy()

    detalle_grafico["Fecha de OC"] = (
        detalle_grafico["Fecha"]
        .dt.strftime("%d-%m-%Y")
    )

    detalle_grafico["Detalle OC"] = (
        "OC: "
        + detalle_grafico["Pedido"].astype(str)
        + "<br>Proveedor: "
        + detalle_grafico["Nombre proveedor"].astype(str)
    )

    # Cada moneda se presenta en un panel independiente.
    # Así no se mezclan escalas de USD y CLP.

    figura = px.line(
        detalle_grafico,
        x="Fecha",
        y="Precio unitario",
        color="Moneda",
        facet_row="Moneda",
        markers=True,
        hover_name="Detalle OC",
        hover_data={
            "Fecha": False,
            "Fecha de OC": True,
            "Pedido": True,
            "Nombre proveedor": True,
            "Precio unitario": ":,.2f",
            "Moneda": True
        },
        labels={
            "Fecha": "Fecha de la OC",
            "Precio unitario": "Precio unitario",
            "Moneda": "Moneda"
        },
        color_discrete_map={
            "CLP": "#245A91",
            "USD": "#D97706"
        }
    )

    figura.update_traces(
        mode="lines+markers",
        line=dict(width=3),
        marker=dict(size=9)
    )

    figura.update_layout(
        height=max(430, 300 * len(monedas)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Arial",
            size=12,
            color="#334155"
        ),
        hovermode="closest",
        showlegend=False,
        margin=dict(
            l=20,
            r=20,
            t=35,
            b=30
        )
    )

    figura.update_xaxes(
        title_text="Fecha de la OC",
        showgrid=True,
        gridcolor="#E2E8F0",
        tickformat="%d-%m-%Y"
    )

    figura.update_yaxes(
        title_text="Precio unitario",
        showgrid=True,
        gridcolor="#E2E8F0",
        tickformat=",.2f"
    )

    st.plotly_chart(
        figura,
        use_container_width=True
    )


# =====================================================
# 15. TABLA DE DETALLE DE ÓRDENES DE COMPRA
# =====================================================

st.subheader(
    "Detalle de órdenes de compra"
)

st.markdown(
    "A continuación se presentan los registros utilizados "
    "para construir el gráfico de evolución de precios."
)


tabla_detalle = detalle[
    [
        "Material",
        "Descripción",
        "Pedido",
        "Fecha",
        "Precio unitario",
        "Moneda",
        "Nombre proveedor"
    ]
].copy()


tabla_detalle = tabla_detalle.rename(
    columns={
        "Material": "Código de material",
        "Descripción": "Nombre del material",
        "Pedido": "N.º de OC",
        "Fecha": "Fecha de OC (contabilización)",
        "Precio unitario": "Precio unitario",
        "Moneda": "Moneda",
        "Nombre proveedor": "Proveedor"
    }
)


tabla_detalle["Fecha de OC (contabilización)"] = (
    tabla_detalle["Fecha de OC (contabilización)"]
    .dt.strftime("%d-%m-%Y")
)


tabla_detalle["Precio unitario"] = (
    tabla_detalle["Precio unitario"]
    .apply(
        lambda x: formato_numero(x, 2)
    )
)


tabla_detalle = tabla_detalle.sort_values(
    "Fecha de OC (contabilización)",
    ascending=True
)


st.dataframe(
    tabla_detalle,
    use_container_width=True,
    hide_index=True
)


# =====================================================
# 16. PIE DE PÁGINA
# =====================================================

st.markdown(
    '<div style="'
    'text-align:center;'
    'color:#8492A6;'
    'font-size:12px;'
    'margin-top:45px;'
    'padding:15px;'
    '">'
    'ENAEX CHILE | EVOLUCIÓN DE PRECIOS DE MATERIAS PRIMAS'
    ' | RÍO LOA'
    '</div>',
    unsafe_allow_html=True
)
