
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
    page_title="Análisis Río Loa | Enaex",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"
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

.alerta-roja {
    background-color: #FEE2E2;
    border-left: 6px solid #DC2626;
    color: #991B1B;
    padding: 18px;
    border-radius: 9px;
    margin: 12px 0;
}

.alerta-verde {
    background-color: #DCFCE7;
    border-left: 6px solid #16A34A;
    color: #166534;
    padding: 18px;
    border-radius: 9px;
    margin: 12px 0;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. CARGAR MRP DESDE GITHUB
# =====================================================

@st.cache_data(ttl=60)
def cargar_datos_mrp():

    contenido = descargar_archivo_github(RUTA_MRP)

    if contenido is None:
        raise Exception(
            "No se encontró el archivo MRP almacenado en GitHub."
        )

    archivo = BytesIO(contenido)

    df = pd.read_excel(
        archivo,
        sheet_name="NS",
        header=3,
        engine="openpyxl"
    )

    return df


try:

    datos_mrp = cargar_datos_mrp()

    if datos_mrp.empty:
        st.error("La hoja NS no contiene información.")
        st.stop()

except Exception as e:

    st.error(f"Error al cargar el MRP: {e}")
    st.stop()


# =====================================================
# 4. PREPARACIÓN DE DATOS
# =====================================================

datos_mrp.columns = [
    str(columna).strip()
    for columna in datos_mrp.columns
]

columnas_requeridas = [
    "Centro",
    "Material",
    "Descripción del material",
    "MMPP Activa",
    "NS"
]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in datos_mrp.columns
]

if faltantes:

    st.error(
        "Faltan columnas necesarias en la hoja NS: "
        + ", ".join(faltantes)
    )

    st.stop()


# Limpiar registros vacíos

datos_mrp = datos_mrp.dropna(
    subset=["Centro", "Material"]
).copy()


# Normalizar centro

datos_mrp["Centro"] = (
    datos_mrp["Centro"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# Normalizar material

datos_mrp["Material"] = (
    datos_mrp["Material"]
    .astype(str)
    .str.strip()
)


# Convertir columnas numéricas

columnas_numericas = [
    "Riesgo MMPP",
    "Consumo X̄",
    "Stock Actual",
    "Stock Óptimo",
    "Stock Seguridad",
    "Stock Máximo",
    "Cob. [Meses]",
    "Cobertura a [Días]",
    "Sobrestock [%]"
]

for columna in columnas_numericas:

    if columna in datos_mrp.columns:

        datos_mrp[columna] = pd.to_numeric(
            datos_mrp[columna],
            errors="coerce"
        )


# Normalizar clasificaciones

for columna in ["NS", "NS Corregido"]:

    if columna in datos_mrp.columns:

        datos_mrp[columna] = (
            datos_mrp[columna]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )


# =====================================================
# 5. FILTRAR EXCLUSIVAMENTE RÍO LOA
# =====================================================

datos = datos_mrp[
    datos_mrp["Centro"] == CENTRO_RIO_LOA
].copy()


if datos.empty:

    st.error(
        "No se encontraron registros del centro E024 "
        "en la hoja NS del MRP."
    )

    st.stop()


# Materias primas activas

datos_activos = datos[
    datos["MMPP Activa"]
    .astype(str)
    .str.strip()
    .str.upper()
    .isin(["SI", "SÍ"])
].copy()


if datos_activos.empty:

    st.warning(
        "No se encontraron materias primas activas para Río Loa."
    )


# =====================================================
# 6. FUNCIONES AUXILIARES
# =====================================================

def formato_numero(valor, decimales=0):

    if pd.isna(valor):
        return "—"

    return (
        f"{valor:,.{decimales}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def calcular_nivel_servicio(df):

    if (
        "Riesgo MMPP" not in df.columns
        or "NS" not in df.columns
    ):
        return None

    riesgo = pd.to_numeric(
        df["Riesgo MMPP"],
        errors="coerce"
    ).fillna(0)

    clasificacion = (
        df["NS"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    riesgo_eb = riesgo[clasificacion == "EB"].sum()
    riesgo_sb = riesgo[clasificacion == "SB"].sum()
    riesgo_bb = riesgo[clasificacion == "BB"].sum()

    total = riesgo_eb + riesgo_sb + riesgo_bb

    if total <= 0:
        return None

    return (
        (riesgo_eb + 0.5 * riesgo_sb)
        / total
    ) * 100


def mostrar_tabla(df, columnas, decimales=None):

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    if not disponibles:

        st.info("No hay información disponible.")

        return

    vista = df[disponibles].copy()

    formatos = {}

    for columna, decimales_col in (decimales or {}).items():

        if columna in vista.columns:

            formatos[columna] = (
                lambda x, d=decimales_col:
                formato_numero(x, d)
            )

    st.dataframe(
        vista.style.format(
            formatos,
            na_rep="—"
        ),
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# 7. ENCABEZADO
# =====================================================

st.title("Análisis por planta")

st.markdown(
    '<div class="plant-description">'
    'Análisis de planificación, inventario y nivel de servicio '
    'de materias primas de Río Loa.'
    '</div>',
    unsafe_allow_html=True
)


encabezado = """
<div style="
    background-color:#E6EFF9;
    padding:28px;
    border-radius:12px;
    border-left:6px solid #245A91;
">

    <div style="
        font-size:13px;
        font-weight:bold;
        color:#245A91;
        letter-spacing:2px;
    ">
        ANÁLISIS INDIVIDUAL
    </div>

    <div style="
        font-size:30px;
        font-weight:750;
        color:#245A91;
        margin-top:8px;
    ">
        RÍO LOA
    </div>

    <div style="color:#64748B;margin-top:5px;">
        Calama | Enaex Chile
    </div>

</div>
"""

st.markdown(
    encabezado,
    unsafe_allow_html=True
)

st.write("")


# =====================================================
# 8. INDICADORES GENERALES
# =====================================================

st.subheader("Indicadores de la planta")


cantidad_materiales = len(datos_activos)

nivel_servicio = calcular_nivel_servicio(
    datos_activos
)


if "Cobertura a [Días]" in datos_activos.columns:

    coberturas = datos_activos[
        "Cobertura a [Días]"
    ].dropna()

    cobertura_promedio = (
        coberturas.mean()
        if not coberturas.empty
        else None
    )

else:

    cobertura_promedio = None


col1, col2, col3 = st.columns(3)

col1.metric(
    "Materias primas activas",
    formato_numero(cantidad_materiales)
)

col2.metric(
    "Nivel de servicio",
    f"{nivel_servicio:.1f}%"
    if nivel_servicio is not None
    else "—"
)

col3.metric(
    "Cobertura promedio",
    f"{cobertura_promedio:.1f} días"
    if cobertura_promedio is not None
    else "—"
)

st.caption(
    "Información obtenida de la hoja NS del último MRP "
    "almacenado en GitHub."
)

st.divider()


# =====================================================
# 9. DISTRIBUCIÓN BB, EB Y SB
# =====================================================

st.subheader("Distribución de materias primas")

st.markdown(
    "Participación de las materias primas según su clasificación "
    "NS corregida."
)


if "NS Corregido" in datos_activos.columns:

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
        .reindex(
            ["BB", "EB", "SB"],
            fill_value=0
        )
    )

    if conteo.sum() > 0:

        grafico = pd.DataFrame({

            "Clasificación": ["BB", "EB", "SB"],

            "Cantidad": [
                int(conteo["BB"]),
                int(conteo["EB"]),
                int(conteo["SB"])
            ]

        })

        grafico["Porcentaje"] = (
            grafico["Cantidad"]
            / grafico["Cantidad"].sum()
            * 100
        )

        colores = {
            "BB": "#E32636",
            "EB": "#16A34A",
            "SB": "#078BCE"
        }

        fig = px.pie(
            grafico,
            names="Clasificación",
            values="Cantidad",
            color="Clasificación",
            color_discrete_map=colores,
            hole=0,
            custom_data=["Porcentaje"]
        )

        fig.update_traces(

            textposition="inside",

            texttemplate="%{customdata[0]:.1f}%",

            textfont=dict(
                size=18,
                color="white"
            ),

            hovertemplate=(
                "<b>%{label}</b><br>"
                "Materias primas: %{value}<br>"
                "Participación: %{customdata[0]:.1f}%"
                "<extra></extra>"
            )

        )

        fig.update_layout(

            height=430,

            showlegend=True,

            legend_title_text="Clasificación NS",

            margin=dict(
                t=20,
                b=20,
                l=20,
                r=20
            ),

            paper_bgcolor="#FFFFFF",

            plot_bgcolor="#FFFFFF"

        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("BB", int(conteo["BB"]))
        c2.metric("EB", int(conteo["EB"]))
        c3.metric("SB", int(conteo["SB"]))

    else:

        st.info(
            "No existen materias primas clasificadas como BB, EB o SB."
        )

else:

    st.warning(
        "No se encontró la columna NS Corregido."
    )


st.divider()


# =====================================================
# 10. CINCO MATERIAS PRIMAS CON MENOR STOCK
# =====================================================

st.subheader("5 materias primas con menor stock")

st.markdown(
    "Materias primas activas ordenadas desde el menor "
    "stock actual."
)


if "Stock Actual" in datos_activos.columns:

    menor_stock = datos_activos.copy()

    menor_stock = menor_stock.dropna(
        subset=["Stock Actual"]
    )

    menor_stock = menor_stock.sort_values(
        "Stock Actual",
        ascending=True
    ).head(5)

    if not menor_stock.empty:

        mostrar_tabla(
            menor_stock,

            [
                "Material",
                "Descripción del material",
                "UM",
                "Stock Actual",
                "Stock Seguridad",
                "Stock Óptimo",
                "NS Corregido"
            ],

            {
                "Stock Actual": 2,
                "Stock Seguridad": 2,
                "Stock Óptimo": 2
            }
        )

    else:

        st.info("No hay información de stock disponible.")

else:

    st.warning("No se encontró Stock Actual.")


st.divider()


# =====================================================
# 11. CINCO MATERIAS PRIMAS CON MENOR CONSUMO
#     Y MAYOR COBERTURA
# =====================================================

st.subheader(
    "5 materias primas con menor consumo y mayor cobertura"
)

st.markdown(
    "Se identifican las materias primas de menor consumo "
    "promedio y, dentro de ese grupo, aquellas con mayor "
    "cobertura de inventario."
)


if (
    "Consumo X̄" in datos_activos.columns
    and "Cobertura a [Días]" in datos_activos.columns
):

    bajo_consumo = datos_activos.copy()

    bajo_consumo = bajo_consumo.dropna(
        subset=[
            "Consumo X̄",
            "Cobertura a [Días]"
        ]
    )

    if not bajo_consumo.empty:

        # Identificar el grupo de menor consumo.
        limite_consumo = bajo_consumo[
            "Consumo X̄"
        ].quantile(0.50)

        bajo_consumo = bajo_consumo[
            bajo_consumo["Consumo X̄"] <= limite_consumo
        ].copy()

        # Dentro de ese grupo, priorizar mayor cobertura.
        bajo_consumo = bajo_consumo.sort_values(
            [
                "Cobertura a [Días]",
                "Consumo X̄"
            ],
            ascending=[False, True]
        ).head(5)

        if not bajo_consumo.empty:

            mostrar_tabla(
                bajo_consumo,

                [
                    "Material",
                    "Descripción del material",
                    "UM",
                    "Consumo X̄",
                    "Stock Actual",
                    "Cobertura a [Días]",
                    "Cob. [Meses]"
                ],

                {
                    "Consumo X̄": 2,
                    "Stock Actual": 2,
                    "Cobertura a [Días]": 1,
                    "Cob. [Meses]": 2
                }
            )

        else:

            st.info(
                "No hay materias primas disponibles para este análisis."
            )

    else:

        st.info(
            "No hay datos suficientes de consumo y cobertura."
        )

else:

    st.warning(
        "Faltan las columnas de consumo o cobertura en el MRP."
    )


st.divider()


# =====================================================
# 12. ALERTAS DE COBERTURA INFERIOR A 10 DÍAS
# =====================================================

st.subheader(
    "Alerta de materias primas con cobertura crítica"
)


if "Cobertura a [Días]" in datos_activos.columns:

    cobertura_critica = datos_activos[
        datos_activos["Cobertura a [Días]"].notna()
        &
        (
            datos_activos["Cobertura a [Días]"] < 10
        )
    ].copy()

    cobertura_critica = cobertura_critica.sort_values(
        "Cobertura a [Días]",
        ascending=True
    )

    if not cobertura_critica.empty:

        st.markdown(

            f'<div class="alerta-roja">'
            f'<strong>ATENCIÓN: COBERTURA CRÍTICA</strong><br><br>'
            f'Se identificaron {len(cobertura_critica)} materias primas '
            f'con menos de 10 días de cobertura. '
            f'Requieren revisión prioritaria para prevenir '
            f'posibles quiebres de stock.'
            f'</div>',

            unsafe_allow_html=True
        )

        mostrar_tabla(
            cobertura_critica,

            [
                "Material",
                "Descripción del material",
                "UM",
                "Stock Actual",
                "Consumo X̄",
                "Cobertura a [Días]",
                "NS",
                "NS Corregido"
            ],

            {
                "Stock Actual": 2,
                "Consumo X̄": 2,
                "Cobertura a [Días]": 1
            }
        )

    else:

        st.markdown(

            '<div class="alerta-verde">'
            '<strong>SIN ALERTAS CRÍTICAS</strong><br><br>'
            'No se identificaron materias primas activas '
            'con menos de 10 días de cobertura.'
            '</div>',

            unsafe_allow_html=True
        )

else:

    st.warning(
        "No se encontró la columna Cobertura a [Días]."
    )


st.divider()


# =====================================================
# 13. ANÁLISIS INDIVIDUAL DE MATERIAS PRIMAS
# =====================================================

st.subheader(
    "Análisis individual de materias primas"
)

st.markdown(
    "Busca una materia prima por código o descripción "
    "para consultar sus indicadores."
)


if not datos_activos.empty:

    catalogo = datos_activos.copy()

    catalogo["Etiqueta"] = (
        catalogo["Material"].astype(str)
        + " — "
        + catalogo["Descripción del material"].fillna("").astype(str)
    )

    busqueda = st.text_input(
        "Buscar materia prima",
        placeholder="Ingresa código o descripción..."
    )

    if busqueda:

        catalogo = catalogo[
            catalogo["Material"].str.contains(
                busqueda,
                case=False,
                na=False,
                regex=False
            )
            |
            catalogo["Descripción del material"].astype(str).str.contains(
                busqueda,
                case=False,
                na=False,
                regex=False
            )
        ]

    if not catalogo.empty:

        seleccion = st.selectbox(
            "Seleccionar materia prima",
            catalogo["Etiqueta"].tolist()
        )

        material = catalogo[
            catalogo["Etiqueta"] == seleccion
        ].iloc[0]

        st.write("")

        st.markdown(
            f"### {material['Descripción del material']}"
        )

        st.caption(
            f"Código: {material['Material']}"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Consumo promedio",
            formato_numero(
                material.get("Consumo X̄"),
                2
            )
        )

        c2.metric(
            "Stock actual",
            formato_numero(
                material.get("Stock Actual"),
                2
            )
        )

        cobertura = material.get("Cobertura a [Días]")

        c3.metric(
            "Cobertura",
            f"{cobertura:.1f} días"
            if pd.notna(cobertura)
            else "—"
        )

        c4, c5, c6 = st.columns(3)

        c4.metric(
            "Riesgo MMPP",
            formato_numero(
                material.get("Riesgo MMPP")
            )
        )

        c5.metric(
            "Clasificación NS",
            str(material.get("NS", "—"))
        )

        c6.metric(
            "NS Corregido",
            str(material.get("NS Corregido", "—"))
        )

        comentario = material.get("Comentario")

        if pd.notna(comentario) and str(comentario).strip():

            st.write("**Comentario del MRP**")

            st.info(str(comentario))

    else:

        st.warning(
            "No se encontraron materias primas con ese código "
            "o descripción."
        )

else:

    st.info(
        "No hay materias primas activas para consultar."
    )


# =====================================================
# 14. PIE DE PÁGINA
# =====================================================

st.markdown(
    '<div style="text-align:center;color:#8492A6;'
    'font-size:12px;margin-top:45px;padding:15px;">'
    'ENAEX CHILE | REPORTE DE GESTIÓN DE MATERIAS PRIMAS'
    ' | RÍO LOA'
    '</div>',
    unsafe_allow_html=True
)
