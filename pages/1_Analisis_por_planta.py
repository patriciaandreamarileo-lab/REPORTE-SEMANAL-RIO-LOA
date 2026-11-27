
import pandas as pd
import streamlit as st
import plotly.express as px

from modules.navegacion import configurar_navegacion
from modules.mrp_reader import cargar_mrp


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Análisis por planta | Enaex",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()

CENTRO_RIO_LOA = "E024"


# =====================================================
# 2. DISEÑO
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.plant-header {
    background: linear-gradient(110deg, #123454, #24669A);
    padding: 28px;
    border-radius: 14px;
    margin-bottom: 20px;
    color: white;
}

.plant-header h2 {
    color: white;
    margin: 0;
    font-size: 30px;
}

.plant-header p {
    color: #DCEAF7;
    margin-top: 8px;
    margin-bottom: 0;
}

.section-title {
    color: #173F63;
    font-weight: 700;
}

div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #E2E8F0;
    padding: 18px;
    border-radius: 12px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. FUNCIONES AUXILIARES
# =====================================================

def normalizar_texto(serie):

    return (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )


def convertir_numerico(df, columnas):

    df = df.copy()

    for columna in columnas:

        if columna in df.columns:

            df[columna] = pd.to_numeric(
                df[columna]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace("%", "", regex=False)
                .str.replace(r"[^\d.\-]", "", regex=True),
                errors="coerce"
            )

    return df


def mostrar_tabla(df, columnas):

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    if df.empty:
        st.info("No hay registros disponibles para mostrar.")
        return

    st.dataframe(
        df[disponibles],
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# 4. CARGA DEL MRP DESDE GITHUB
# =====================================================

st.title("Análisis por planta")

st.markdown(
    "Análisis de planificación, consumo y nivel de servicio "
    "de materias primas de Río Loa."
)

col_actualizar, col_estado = st.columns([1, 3])

with col_actualizar:

    if st.button(
        "🔄 Actualizar datos",
        use_container_width=True
    ):

        cargar_mrp.clear()
        st.cache_data.clear()
        st.rerun()


try:

    with st.spinner("Consultando información del MRP..."):

        datos_mrp, hojas_mrp = cargar_mrp()

except Exception as error:

    st.error(
        f"No fue posible cargar el MRP desde GitHub: {error}"
    )

    st.stop()


# =====================================================
# 5. VALIDACIÓN DE COLUMNAS
# =====================================================

COLUMNAS_NECESARIAS = [
    "Centro",
    "Material",
    "Descripción del material",
    "MMPP Activa",
    "NS",
    "NS Corregido",
    "Consumo X̄",
    "Stock Actual",
    "Stock Óptimo",
    "Stock Seguridad",
    "Stock Máximo",
    "Cob. [Meses]",
    "Cobertura a [Días]"
]

faltantes = [
    columna
    for columna in COLUMNAS_NECESARIAS
    if columna not in datos_mrp.columns
]

if faltantes:

    st.error(
        "Faltan columnas necesarias en el MRP: "
        + ", ".join(faltantes)
    )

    st.stop()


# =====================================================
# 6. FILTRAR RÍO LOA (E024)
# =====================================================

datos_mrp = datos_mrp.copy()

datos_mrp["Centro"] = (
    datos_mrp["Centro"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

datos_rio_loa = datos_mrp[
    datos_mrp["Centro"] == CENTRO_RIO_LOA
].copy()


if datos_rio_loa.empty:

    st.warning(
        "No se encontraron materias primas del centro E024 "
        "en el archivo MRP."
    )

    st.stop()


# =====================================================
# 7. FILTRAR MATERIAS PRIMAS ACTIVAS
# =====================================================

datos_rio_loa["MMPP Activa"] = (
    normalizar_texto(datos_rio_loa["MMPP Activa"])
)

datos_activos = datos_rio_loa[
    datos_rio_loa["MMPP Activa"].isin(
        ["SI", "SÍ", "YES", "1"]
    )
].copy()


if datos_activos.empty:

    st.warning(
        "Se encontraron registros E024, pero no se "
        "identificaron materias primas activas. "
        "Revisa la columna MMPP Activa."
    )

    st.write(
        "Valores encontrados:",
        datos_rio_loa["MMPP Activa"].value_counts()
    )

    st.stop()


# =====================================================
# 8. CONVERSIÓN DE COLUMNAS NUMÉRICAS
# =====================================================

COLUMNAS_NUMERICAS = [
    "Consumo X̄",
    "Stock Actual",
    "Stock Óptimo",
    "Stock Seguridad",
    "Stock Máximo",
    "Cob. [Meses]",
    "Cobertura a [Días]",
    "Sobrestock [%]"
]

datos_activos = convertir_numerico(
    datos_activos,
    COLUMNAS_NUMERICAS
)

# Limpiar clasificación del nivel de servicio

datos_activos["NS Corregido"] = (
    normalizar_texto(datos_activos["NS Corregido"])
)

datos_activos["NS"] = (
    normalizar_texto(datos_activos["NS"])
)


# =====================================================
# 9. ENCABEZADO DE RÍO LOA
# =====================================================

st.markdown("""
<div class="plant-header">

    <div style="
        font-size:13px;
        font-weight:bold;
        letter-spacing:2px;
        color:#DCEAF7;
    ">
        ANÁLISIS INDIVIDUAL
    </div>

    <h2>RÍO LOA</h2>

    <p>Calama | Enaex Chile | Centro E024</p>

</div>
""", unsafe_allow_html=True)


st.caption(
    f"Materias primas activas encontradas: "
    f"{len(datos_activos)}"
)


# =====================================================
# 10. DISTRIBUCIÓN DEL NIVEL DE SERVICIO
# =====================================================

st.divider()

col_grafico, col_resumen = st.columns(
    [1, 1],
    gap="medium"
)


# -----------------------------------------------------
# 10.1 CLASIFICACIÓN
# -----------------------------------------------------

clasificaciones = (
    datos_activos["NS Corregido"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

conteo = (
    clasificaciones[
        clasificaciones.isin(["BB", "EB", "SB"])
    ]
    .value_counts()
    .reindex(["EB", "SB", "BB"], fill_value=0)
)

total_clasificados = int(conteo.sum())


# -----------------------------------------------------
# 10.2 NIVEL DE SERVICIO
# -----------------------------------------------------

if total_clasificados > 0:

    nivel_servicio = (
        (
            conteo["EB"]
            + conteo["SB"] * 0.5
        )
        / total_clasificados
    ) * 100

else:

    nivel_servicio = 0


# -----------------------------------------------------
# 10.3 COBERTURA
# -----------------------------------------------------

cobertura_dias = pd.to_numeric(
    datos_activos["Cobertura a [Días]"],
    errors="coerce"
)

alertas = int(
    (
        cobertura_dias.notna()
        & (cobertura_dias < 10)
    ).sum()
)


# -----------------------------------------------------
# 10.4 GRÁFICO DE DONA
# -----------------------------------------------------

with col_grafico:

    st.subheader("Distribución del nivel de servicio")

    grafico_df = pd.DataFrame({
        "Clasificación": ["EB", "SB", "BB"],
        "Cantidad": [
            int(conteo["EB"]),
            int(conteo["SB"]),
            int(conteo["BB"])
        ]
    })

    grafico_df = grafico_df[
        grafico_df["Cantidad"] > 0
    ]

    if not grafico_df.empty:

        fig = px.pie(
            grafico_df,
            names="Clasificación",
            values="Cantidad",
            hole=0.48,
            color="Clasificación",
            color_discrete_map={
                "EB": "#16A34A",
                "SB": "#3B82F6",
                "BB": "#EF4444"
            }
        )

        fig.update_traces(
            textposition="inside",
            texttemplate=(
                "%{label}<br>%{percent:.1%}"
            ),
            textfont_size=12,
            marker=dict(
                line=dict(
                    color="white",
                    width=2
                )
            )
        )

        fig.update_layout(
            height=340,
            margin=dict(
                l=10,
                r=10,
                t=15,
                b=10
            ),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1
            ),
            showlegend=True
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

    else:

        st.info(
            "No hay clasificaciones BB, EB o SB "
            "para construir el gráfico."
        )


# -----------------------------------------------------
# 10.5 RESUMEN DE INVENTARIO
# -----------------------------------------------------

with col_resumen:

    st.subheader("Resumen de inventario")

    with st.container(border=True):

        st.metric(
            "Materias primas",
            f"{len(datos_activos):,}".replace(",", ".")
        )

    with st.container(border=True):

        st.metric(
            "Nivel de servicio",
            f"{nivel_servicio:.1f}%".replace(".", ",")
        )

    with st.container(border=True):

        st.metric(
            "Materias con cobertura menor a 10 días",
            alertas
        )


# =====================================================
# 11. CINCO MATERIAS PRIMAS CON MENOR STOCK
# =====================================================

st.divider()

st.subheader("Materias primas con menor stock")

st.caption(
    "Se muestran las cinco materias primas activas "
    "con menor cantidad disponible en stock actual."
)

menor_stock = datos_activos.dropna(
    subset=["Stock Actual"]
).copy()

menor_stock = menor_stock.sort_values(
    by="Stock Actual",
    ascending=True
).head(5)

mostrar_tabla(
    menor_stock,
    [
        "Material",
        "Descripción del material",
        "UM",
        "Stock Actual",
        "Stock Seguridad",
        "Stock Óptimo",
        "Cobertura a [Días]"
    ]
)


# =====================================================
# 12. CINCO MATERIAS PRIMAS CON MENOR CONSUMO
#     Y MAYOR COBERTURA
# =====================================================

st.divider()

st.subheader(
    "Materias primas con menor consumo y mayor cobertura"
)

st.caption(
    "Se priorizan las materias primas con menor consumo "
    "promedio y, en caso de empate, mayor cobertura."
)

menor_consumo = datos_activos.dropna(
    subset=[
        "Consumo X̄",
        "Cobertura a [Días]"
    ]
).copy()

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

mostrar_tabla(
    menor_consumo,
    [
        "Material",
        "Descripción del material",
        "UM",
        "Consumo X̄",
        "Stock Actual",
        "Cobertura a [Días]",
        "Cob. [Meses]"
    ]
)


# =====================================================
# 13. ALERTAS DE MATERIAS PRIMAS
#     CON MENOS DE 10 DÍAS DE COBERTURA
# =====================================================

st.divider()

st.subheader("Alertas de cobertura de inventario")

materias_criticas = datos_activos[
    datos_activos["Cobertura a [Días]"].notna()
    & (
        datos_activos["Cobertura a [Días]"] < 10
    )
].copy()

materias_criticas = materias_criticas.sort_values(
    by="Cobertura a [Días]",
    ascending=True
)

if not materias_criticas.empty:

    st.error(
        f"⚠️ ¡ATENCIÓN! Se identificaron "
        f"{len(materias_criticas)} materias primas "
        "con menos de 10 días de cobertura."
    )

    for _, fila in materias_criticas.iterrows():

        with st.container(border=True):

            st.markdown(
                f"### 🔴 Material {fila['Material']}"
            )

            st.write(
                fila["Descripción del material"]
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Cobertura",
                f"{fila['Cobertura a [Días]']:.2f} días"
            )

            col2.metric(
                "Stock actual",
                (
                    f"{fila['Stock Actual']:,.2f}"
                    if pd.notna(fila["Stock Actual"])
                    else "Sin información"
                )
            )

            col3.metric(
                "Consumo promedio",
                (
                    f"{fila['Consumo X̄']:,.2f}"
                    if pd.notna(fila["Consumo X̄"])
                    else "Sin información"
                )
            )

            if (
                "Comentario" in fila.index
                and pd.notna(fila["Comentario"])
                and str(fila["Comentario"]).strip()
            ):

                st.caption(
                    f"Comentario: {fila['Comentario']}"
                )

else:

    st.success(
        "No se identificaron materias primas "
        "con menos de 10 días de cobertura."
    )


# =====================================================
# 14. BUSCADOR INDIVIDUAL DE MATERIAS PRIMAS
# =====================================================

st.divider()

st.subheader("Consulta individual de materias primas")

materiales_disponibles = sorted(
    datos_activos["Material"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

if materiales_disponibles:

    material_seleccionado = st.selectbox(
        "Selecciona una materia prima",
        options=materiales_disponibles,
        index=None,
        placeholder="Buscar por código de material..."
    )

    if material_seleccionado:

        detalle = datos_activos[
            datos_activos["Material"].astype(str)
            == material_seleccionado
        ]

        if not detalle.empty:

            fila = detalle.iloc[0]

            st.markdown(
                f"### {fila['Descripción del material']}"
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Stock actual",
                (
                    f"{fila['Stock Actual']:,.2f}"
                    if pd.notna(fila["Stock Actual"])
                    else "Sin información"
                )
            )

            col2.metric(
                "Consumo promedio",
                (
                    f"{fila['Consumo X̄']:,.2f}"
                    if pd.notna(fila["Consumo X̄"])
                    else "Sin información"
                )
            )

            col3.metric(
                "Cobertura en días",
                (
                    f"{fila['Cobertura a [Días]']:.2f}"
                    if pd.notna(fila["Cobertura a [Días]"])
                    else "Sin información"
                )
            )

            mostrar_tabla(
                detalle,
                datos_activos.columns.tolist()
            )


# =====================================================
# 15. PIE DE PÁGINA
# =====================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#8492A6;
        font-size:12px;
        padding:15px;
    ">
        ENAEX CHILE | RÍO LOA | CENTRO E024
        <br>
        Dashboard de gestión de materias primas
    </div>
    """,
    unsafe_allow_html=True
)
