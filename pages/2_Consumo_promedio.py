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
    page_title="Consumo mensual | Enaex",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()

RUTA_CONSUMO = "data/CONSUMO/consumo_rio_loa.xlsx"
CENTRO_RIO_LOA = "E024"


# =====================================================
# 2. ESTILOS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.descripcion {
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
# 3. CARGAR ARCHIVO DESDE GITHUB
# =====================================================

@st.cache_data(ttl=300)
def cargar_consumo():

    contenido = descargar_archivo_github(RUTA_CONSUMO)

    if contenido is None:
        raise Exception(
            "No se encontró el archivo de consumo mensual en GitHub."
        )

    df = pd.read_excel(
        BytesIO(contenido),
        sheet_name="Data",
        engine="openpyxl"
    )

    return df


# =====================================================
# 4. ACTUALIZACIÓN MANUAL
# =====================================================

col_actualizar, col_estado = st.columns([1, 3])

with col_actualizar:

    if st.button(
        "🔄 Actualizar datos",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()


# =====================================================
# 5. OBTENER INFORMACIÓN
# =====================================================

try:

    datos_originales = cargar_consumo()

    if datos_originales.empty:
        st.error("El archivo de consumo no contiene registros.")
        st.stop()

except Exception as error:

    st.error(
        f"No fue posible cargar el archivo de consumo: {error}"
    )

    st.stop()


# =====================================================
# 6. VALIDAR COLUMNAS
# =====================================================

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
    if columna not in datos_originales.columns
]

if faltantes:

    st.error(
        "Faltan columnas necesarias en el archivo: "
        + ", ".join(faltantes)
    )

    st.stop()


# =====================================================
# 7. LIMPIEZA DE DATOS
# =====================================================

datos = datos_originales.copy()

# Limpiar códigos de materiales

datos["Material"] = (
    datos["Material"]
    .astype(str)
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

# Limpiar centro

datos["Centro"] = (
    datos["Centro"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Filtrar Río Loa

datos = datos[
    datos["Centro"] == CENTRO_RIO_LOA
].copy()

if datos.empty:

    st.error(
        "No se encontraron registros correspondientes "
        "al centro E024 (Río Loa)."
    )

    st.stop()


# Normalizar clases de movimiento

datos["Clase de movimiento"] = (
    datos["Clase de movimiento"]
    .astype(str)
    .str.replace(r"\.0$", "", regex=True)
    .str.strip()
)

# Considerar exclusivamente movimientos 261 y 262

datos = datos[
    datos["Clase de movimiento"].isin(["261", "262"])
].copy()

# Convertir cantidades

datos["Ctd.en UM entrada"] = pd.to_numeric(
    datos["Ctd.en UM entrada"],
    errors="coerce"
).fillna(0)

# Convertir fechas

datos["Fecha contabiliz."] = pd.to_datetime(
    datos["Fecha contabiliz."],
    errors="coerce",
    dayfirst=True
)

datos = datos.dropna(
    subset=["Fecha contabiliz."]
).copy()

# Limpiar descripciones

if "Descripción material" in datos.columns:

    datos["Descripción material"] = (
        datos["Descripción material"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

else:

    datos["Descripción material"] = ""

# Limpiar unidad de medida

if "Un.medida de entrada" not in datos.columns:
    datos["Un.medida de entrada"] = "Sin unidad"

datos["Un.medida de entrada"] = (
    datos["Un.medida de entrada"]
    .fillna("Sin unidad")
    .astype(str)
    .str.strip()
)


# =====================================================
# 8. CATÁLOGO DE MATERIAS PRIMAS
# =====================================================

catalogo = (
    datos[
        ["Material", "Descripción material"]
    ]
    .drop_duplicates(subset=["Material"])
    .sort_values("Material")
    .copy()
)

catalogo["Descripción material"] = (
    catalogo["Descripción material"]
    .replace("", "Sin descripción")
)

if catalogo.empty:

    st.warning("No existen materias primas para consultar.")
    st.stop()



# =====================================================
# 9. ENCABEZADO
# =====================================================

st.title("Consumo mensual de materias primas")

st.markdown(
    '<div class="descripcion">'
    'Análisis histórico de los movimientos y consumo '
    'de materias primas de Río Loa.'
    '</div>',
    unsafe_allow_html=True
)

with st.container(border=True):

    st.caption("ANÁLISIS DE CONSUMO")

    st.markdown("## RÍO LOA")

    st.caption("Calama | Enaex Chile | Centro E024")

st.write("")
st.divider()


# =====================================================
# 10. BUSCADOR Y SELECTOR DE MATERIAS PRIMAS
# =====================================================

st.subheader("Selección de materia prima")

st.markdown(
    "Busca una materia prima por su código SAP "
    "o por su descripción."
)

busqueda = st.text_input(
    "Buscar material",
    placeholder="Escribe un código o nombre de material...",
    key="busqueda_consumo"
)

catalogo_filtrado = catalogo.copy()

if busqueda.strip():

    termino = busqueda.strip().lower()

    catalogo_filtrado = catalogo[
        catalogo["Material"].str.lower().str.contains(
            termino,
            na=False
        )
        |
        catalogo["Descripción material"].str.lower().str.contains(
            termino,
            na=False
        )
    ].copy()


if catalogo_filtrado.empty:

    st.warning("No se encontraron materias primas con esa búsqueda.")
    st.stop()


opciones_materiales = [
    (
        str(fila["Material"]),
        str(fila["Descripción material"])
    )
    for _, fila in catalogo_filtrado.iterrows()
]

seleccion = st.selectbox(
    "Seleccionar materia prima",
    options=opciones_materiales,
    format_func=lambda material: (
        f"{material[0]} -- {material[1]}"
    ),
    key="selector_consumo_rio_loa"
)

codigo_seleccionado = seleccion[0]
descripcion_seleccionada = seleccion[1]


# =====================================================
# 11. FILTRAR MOVIMIENTOS DEL MATERIAL
# =====================================================

datos_material = datos[
    datos["Material"] == codigo_seleccionado
].copy()

if datos_material.empty:

    st.info("No existen movimientos para esta materia prima.")
    st.stop()


st.write("")

st.markdown(
    f"### {descripcion_seleccionada}"
)

st.caption(
    f"Código SAP: {codigo_seleccionado}"
)


# =====================================================
# 12. UNIDAD DE MEDIDA
# =====================================================

unidades = sorted(
    datos_material["Un.medida de entrada"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

if len(unidades) > 1:

    st.warning(
        "Este material presenta más de una unidad de medida. "
        "Selecciona una para evitar sumar cantidades incompatibles."
    )

    unidad_seleccionada = st.selectbox(
        "Unidad de medida",
        options=unidades,
        key="unidad_consumo"
    )

    datos_material = datos_material[
        datos_material["Un.medida de entrada"]
        == unidad_seleccionada
    ].copy()

else:

    unidad_seleccionada = unidades[0] if unidades else "Sin unidad"


# =====================================================
# 13. CALCULAR CONSUMO MENSUAL
# =====================================================

datos_material["Mes"] = (
    datos_material["Fecha contabiliz."]
    .dt.to_period("M")
)

# Se conserva el signo original de SAP.
# 261 normalmente registra cantidades negativas.
# 262 registra anulaciones positivas.
# El negativo de la suma representa el consumo neto.

consumo_mensual = (
    datos_material
    .groupby("Mes", as_index=False)
    .agg(
        Cantidad_SAP=("Ctd.en UM entrada", "sum"),
        Movimientos=("Clase de movimiento", "count")
    )
)

consumo_mensual["Consumo"] = (
    -consumo_mensual["Cantidad_SAP"]
)

consumo_mensual["Fecha"] = (
    consumo_mensual["Mes"]
    .dt.to_timestamp()
)

consumo_mensual = consumo_mensual.sort_values("Fecha")


# =====================================================
# 14. INDICADORES DEL MATERIAL
# =====================================================

consumo_total = consumo_mensual["Consumo"].sum()

consumo_promedio = (
    consumo_mensual["Consumo"].mean()
    if not consumo_mensual.empty
    else 0
)

cantidad_movimientos = len(datos_material)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Consumo acumulado",
    f"{consumo_total:,.2f} {unidad_seleccionada}"
)

col2.metric(
    "Consumo mensual promedio",
    f"{consumo_promedio:,.2f} {unidad_seleccionada}"
)

col3.metric(
    "Movimientos SAP",
    f"{cantidad_movimientos:,}"
)

st.divider()


# =====================================================
# 15. GRÁFICO DE CONSUMO MENSUAL
# =====================================================

st.subheader("Evolución del consumo mensual")

st.markdown(
    "Consumo neto mensual calculado a partir de "
    "los movimientos SAP 261 y 262."
)

if not consumo_mensual.empty:

    fig = px.line(
        consumo_mensual,
        x="Fecha",
        y="Consumo",
        markers=True,
        custom_data=["Movimientos"],
        labels={
            "Fecha": "Mes",
            "Consumo": f"Consumo ({unidad_seleccionada})"
        }
    )

    fig.update_traces(
        line=dict(
            color="#245A91",
            width=3
        ),
        marker=dict(
            size=9,
            color="#078BCE"
        ),
        hovertemplate=(
            "<b>%{x|%B %Y}</b><br>"
            "Consumo: %{y:,.2f}<br>"
            "Movimientos: %{customdata[0]}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=430,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=25, b=30, l=20, r=20),
        xaxis=dict(
            tickformat="%b %Y",
            title="Mes",
            showgrid=False
        ),
        yaxis=dict(
            title=f"Consumo ({unidad_seleccionada})",
            gridcolor="#E2E8F0",
            zeroline=True
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info("No existen datos para construir el gráfico.")


st.divider()


# =====================================================
# 16. TABLA DE MOVIMIENTOS SAP
# =====================================================

st.subheader("Detalle de movimientos SAP")

st.markdown(
    "Movimientos de consumo y anulaciones registrados "
    "para la materia prima seleccionada."
)

columnas_tabla = [
    "Fecha contabiliz.",
    "Material",
    "Descripción material",
    "Clase de movimiento",
    "Documento material",
    "Pedido",
    "Lote",
    "Ctd.en UM entrada",
    "Un.medida de entrada",
    "Texto clase de mov."
]

columnas_disponibles = [
    columna
    for columna in columnas_tabla
    if columna in datos_material.columns
]

movimientos = (
    datos_material[columnas_disponibles]
    .sort_values(
        "Fecha contabiliz.",
        ascending=False
    )
    .copy()
)

st.dataframe(
    movimientos,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fecha contabiliz.": st.column_config.DateColumn(
            "Fecha",
            format="DD/MM/YYYY"
        ),
        "Ctd.en UM entrada": st.column_config.NumberColumn(
            "Cantidad SAP",
            format="%.3f"
        )
    }
)

st.caption(
    "Las cantidades de esta tabla mantienen el signo original "
    "registrado en SAP."
)


st.divider()


# =====================================================
# 17. PROYECCIÓN DE CONSUMO
# =====================================================

st.subheader("Proyección de consumo")

st.markdown(
    "La proyección se calcula utilizando el promedio de los "
    "últimos tres meses con registros reales de consumo."
)

if len(consumo_mensual) >= 1:

    # Últimos tres meses disponibles con registros

    ultimos_tres = (
        consumo_mensual
        .tail(3)
        .copy()
    )

    promedio_proyeccion = ultimos_tres["Consumo"].mean()

    ultimo_mes = consumo_mensual["Mes"].max()

    # Punto de unión entre consumo real y proyección

    fecha_inicio = ultimo_mes.to_timestamp()

    proyeccion = pd.DataFrame({
        "Fecha": [fecha_inicio],
        "Consumo": [
            consumo_mensual.iloc[-1]["Consumo"]
        ],
        "Tipo": ["Proyección"]
    })

    # Proyectar los siguientes tres meses

    fechas_futuras = [
        (ultimo_mes + i).to_timestamp()
        for i in range(1, 4)
    ]

    datos_futuros = pd.DataFrame({
        "Fecha": fechas_futuras,
        "Consumo": [promedio_proyeccion] * 3,
        "Tipo": ["Proyección"] * 3
    })

    proyeccion = pd.concat(
        [proyeccion, datos_futuros],
        ignore_index=True
    )

    # Datos reales

    reales = consumo_mensual[
        ["Fecha", "Consumo"]
    ].copy()

    reales["Tipo"] = "Consumo real"

    # Unir las series

    datos_grafico = pd.concat(
        [
            reales,
            proyeccion
        ],
        ignore_index=True
    )

    fig_proyeccion = px.line(
        datos_grafico,
        x="Fecha",
        y="Consumo",
        color="Tipo",
        markers=True,
        color_discrete_map={
            "Consumo real": "#245A91",
            "Proyección": "#E58A26"
        },
        labels={
            "Fecha": "Mes",
            "Consumo": f"Consumo ({unidad_seleccionada})",
            "Tipo": "Serie"
        }
    )

    fig_proyeccion.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate=(
            "<b>%{x|%B %Y}</b><br>"
            "Consumo: %{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig_proyeccion.update_layout(
        height=450,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=25, b=30, l=20, r=20),
        xaxis=dict(
            tickformat="%b %Y",
            title="Mes",
            showgrid=False
        ),
        yaxis=dict(
            title=f"Consumo ({unidad_seleccionada})",
            gridcolor="#E2E8F0"
        ),
        legend_title_text=""
    )

    st.plotly_chart(
        fig_proyeccion,
        use_container_width=True
    )

    st.info(
        f"Consumo promedio utilizado para la proyección: "
        f"{promedio_proyeccion:,.2f} {unidad_seleccionada}."
    )

    st.caption(
        "La proyección es una estimación constante basada en "
        "los últimos tres meses disponibles con registros. "
        "No representa una predicción estadística avanzada."
    )

else:

    st.info(
        "No existen suficientes registros para generar "
        "una proyección."
    )


# =====================================================
# 18. PIE DE PÁGINA
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
        ENAEX CHILE | ANÁLISIS DE CONSUMO DE MATERIAS PRIMAS
        | RÍO LOA
    </div>
    """,
    unsafe_allow_html=True
)
