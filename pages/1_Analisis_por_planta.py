
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from modules.navegacion import configurar_navegacion
from modules.mrp_reader import obtener_datos_rio_loa


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
    padding: 28px;
    border-radius: 12px;
    border-left: 6px solid #245A91;
    margin-bottom: 25px;
}

.plant-label {
    font-size: 13px;
    font-weight: bold;
    color: #245A91;
    letter-spacing: 2px;
}

.plant-name {
    font-size: 30px;
    font-weight: 750;
    color: #245A91;
    margin-top: 8px;
}

.plant-location {
    color: #64748B;
    margin-top: 5px;
}

.alert-title {
    color: #B91C1C;
    font-weight: bold;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 16px;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. FUNCIONES AUXILIARES
# =====================================================

def convertir_numerico(df, columna):

    if columna in df.columns:

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        )

    return df


def formato_tabla(df):

    df = df.copy()

    columnas_numericas = [
        "Stock Actual",
        "Consumo X̄",
        "Cobertura a [Días]",
        "Stock Seguridad",
        "Stock Óptimo",
        "Stock Máximo"
    ]

    for columna in columnas_numericas:

        if columna in df.columns:

            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            ).round(2)

    return df


def columnas_disponibles(df, columnas):

    return [
        columna
        for columna in columnas
        if columna in df.columns
    ]


# =====================================================
# 4. CARGA DE INFORMACIÓN DEL MRP
# =====================================================

st.title("Análisis por planta")

st.markdown(
    "Análisis de planificación, inventario y nivel "
    "de servicio de materias primas de Río Loa."
)

try:

    datos_mrp = obtener_datos_rio_loa()

except Exception as error:

    st.error(
        f"Error al cargar el archivo MRP: {error}"
    )

    st.stop()


if datos_mrp.empty:

    st.error(
        "No se encontraron materias primas "
        "correspondientes al centro E024."
    )

    st.stop()


# =====================================================
# 5. PREPARACIÓN DE LOS DATOS
# =====================================================

datos = datos_mrp.copy()

# Normalizar centro
datos["Centro"] = (
    datos["Centro"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

# Mantener exclusivamente E024
datos = datos[
    datos["Centro"] == "E024"
].copy()


# Convertir columnas numéricas

columnas_numericas = [
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

    datos = convertir_numerico(
        datos,
        columna
    )


# Limpiar clasificación NS

if "NS Corregido" in datos.columns:

    ns_corregido = (
        datos["NS Corregido"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .replace("", pd.NA)
    )

    ns_original = (
        datos["NS"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    datos["Clasificacion_NS"] = (
        ns_corregido.fillna(ns_original)
    )

else:

    datos["Clasificacion_NS"] = (
        datos["NS"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )


# Identificar materias primas activas

if "MMPP Activa" in datos.columns:

    datos["MMPP Activa"] = (
        datos["MMPP Activa"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    datos_activas = datos[
        datos["MMPP Activa"].isin(
            ["SI", "SÍ", "1", "TRUE", "X"]
        )
    ].copy()

else:

    datos_activas = datos.copy()


# Eliminar filas sin código de material

datos = datos[
    datos["Material"].notna()
    & (datos["Material"].astype(str).str.strip() != "")
].copy()

datos_activas = datos_activas[
    datos_activas["Material"].notna()
    & (datos_activas["Material"].astype(str).str.strip() != "")
].copy()


# =====================================================
# 6. ENCABEZADO INDIVIDUAL
# =====================================================

st.markdown(
    '<div class="plant-header">'
    '<div class="plant-label">ANÁLISIS INDIVIDUAL</div>'
    '<div class="plant-name">RÍO LOA</div>'
    '<div class="plant-location">'
    'Calama | Enaex Chile | Centro E024'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)


# =====================================================
# 7. INDICADORES GENERALES
# =====================================================

st.subheader("Indicadores de la planta")

col1, col2, col3 = st.columns(3)

cantidad_materiales = datos["Material"].nunique()

cantidad_activas = datos_activas["Material"].nunique()

if "Cobertura a [Días]" in datos.columns:

    cobertura_promedio = (
        datos["Cobertura a [Días]"]
        .mean()
    )

else:

    cobertura_promedio = None


col1.metric(
    "Materias primas",
    f"{cantidad_materiales:,}".replace(",", ".")
)

col2.metric(
    "Materias primas activas",
    f"{cantidad_activas:,}".replace(",", ".")
)

col3.metric(
    "Cobertura promedio",
    (
        f"{cobertura_promedio:.1f} días"
        if pd.notna(cobertura_promedio)
        else "Sin información"
    )
)


st.divider()


# =====================================================
# 8. DISTRIBUCIÓN DE MATERIAS PRIMAS
# =====================================================

st.subheader("Distribución de materias primas")

st.markdown(
    "Distribución de las materias primas según "
    "su clasificación de nivel de servicio."
)

clasificaciones = (
    datos_activas["Clasificacion_NS"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

conteo_ns = (
    clasificaciones[
        clasificaciones.isin(["BB", "EB", "SB"])
    ]
    .value_counts()
    .reindex(["BB", "EB", "SB"], fill_value=0)
)

total_ns = conteo_ns.sum()

if total_ns > 0:

    colores = [
        "#E52525",  # BB: rojo
        "#16A34A",  # EB: verde
        "#00A6E8"   # SB: azul vibrante
    ]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.pie(
        conteo_ns.values,
        labels=conteo_ns.index,
        colors=colores,
        autopct=lambda p: (
            f"{p:.1f}%" if p > 0 else ""
        ),
        startangle=90,
        counterclock=False,
        pctdistance=0.65,
        labeldistance=1.12,
        wedgeprops={
            "edgecolor": "white",
            "linewidth": 2
        },
        textprops={
            "fontsize": 12,
            "fontweight": "bold"
        }
    )

    ax.set_aspect("equal")

    plt.tight_layout()

    st.pyplot(
        fig,
        use_container_width=True
    )

    plt.close(fig)

    # Resumen de clasificación

    c1, c2, c3 = st.columns(3)

    for columna, clasificacion, color in zip(
        [c1, c2, c3],
        ["BB", "EB", "SB"],
        ["#E52525", "#16A34A", "#00A6E8"]
    ):

        cantidad = int(conteo_ns[clasificacion])

        porcentaje = (
            cantidad / total_ns * 100
        )

        columna.markdown(
            f"""
            <div style="
                background:white;
                padding:15px;
                border-radius:10px;
                border-left:5px solid {color};
                text-align:center;
            ">
                <div style="font-size:14px;color:#64748B;">
                    Clasificación {clasificacion}
                </div>
                <div style="
                    font-size:25px;
                    font-weight:bold;
                    color:{color};
                ">
                    {porcentaje:.1f}%
                </div>
                <div style="font-size:12px;color:#64748B;">
                    {cantidad} materias primas
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

else:

    st.warning(
        "No se encontraron clasificaciones BB, EB o SB."
    )


st.divider()


# =====================================================
# 9. CINCO MATERIAS PRIMAS CON MENOR STOCK
# =====================================================

st.subheader("5 materias primas con menor stock")

st.markdown(
    "Se identifican las materias primas que presentan "
    "los niveles más bajos de stock actual."
)

if "Stock Actual" in datos.columns:

    menor_stock = (
        datos
        .dropna(subset=["Stock Actual"])
        .sort_values(
            by="Stock Actual",
            ascending=True
        )
        .drop_duplicates(subset=["Material"])
        .head(5)
    )

    columnas_tabla = columnas_disponibles(
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

    if not menor_stock.empty:

        st.dataframe(
            formato_tabla(
                menor_stock[columnas_tabla]
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No hay información disponible de stock actual."
        )

else:

    st.warning(
        "El MRP no contiene la columna Stock Actual."
    )


st.divider()


# =====================================================
# 10. CINCO MATERIAS PRIMAS CON MENOR CONSUMO
#     Y MAYOR COBERTURA
# =====================================================

st.subheader(
    "5 materias primas con menor consumo y mayor cobertura"
)

st.markdown(
    "Se identifican materias primas con bajo consumo "
    "promedio y se priorizan aquellas que presentan "
    "mayor cobertura de stock."
)

if (
    "Consumo X̄" in datos.columns
    and "Cobertura a [Días]" in datos.columns
):

    menor_consumo = (
        datos
        .dropna(
            subset=[
                "Consumo X̄",
                "Cobertura a [Días]"
            ]
        )
        .sort_values(
            by=[
                "Consumo X̄",
                "Cobertura a [Días]"
            ],
            ascending=[
                True,
                False
            ]
        )
        .drop_duplicates(subset=["Material"])
        .head(5)
    )

    columnas_tabla = columnas_disponibles(
        menor_consumo,
        [
            "Material",
            "Descripción del material",
            "UM",
            "Consumo X̄",
            "Stock Actual",
            "Cobertura a [Días]"
        ]
    )

    if not menor_consumo.empty:

        st.dataframe(
            formato_tabla(
                menor_consumo[columnas_tabla]
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No hay información suficiente "
            "para realizar este análisis."
        )

else:

    st.warning(
        "No se encontraron las columnas de consumo "
        "y cobertura necesarias."
    )


st.divider()


# =====================================================
# 11. ALERTAS DE COBERTURA INFERIOR A 10 DÍAS
# =====================================================

st.subheader("Alertas de materias primas críticas")

st.markdown(
    '<div class="alert-title">'
    'Materias primas con menos de 10 días de cobertura'
    '</div>',
    unsafe_allow_html=True
)

if "Cobertura a [Días]" in datos.columns:

    alertas = datos[
        datos["Cobertura a [Días]"].notna()
        & (datos["Cobertura a [Días]"] < 10)
    ].copy()

    alertas = (
        alertas
        .sort_values(
            by="Cobertura a [Días]",
            ascending=True
        )
        .drop_duplicates(subset=["Material"])
    )

    if not alertas.empty:

        st.error(
            f"¡ALERTA! Se identificaron "
            f"{len(alertas)} materias primas "
            "con menos de 10 días de cobertura."
        )

        columnas_alerta = columnas_disponibles(
            alertas,
            [
                "Material",
                "Descripción del material",
                "UM",
                "Stock Actual",
                "Consumo X̄",
                "Stock Seguridad",
                "Cobertura a [Días]",
                "Comentario"
            ]
        )

        st.dataframe(
            formato_tabla(
                alertas[columnas_alerta]
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No existen materias primas con cobertura "
            "inferior a 10 días."
        )

else:

    st.warning(
        "No se encontró la columna Cobertura a [Días]."
    )


st.divider()


# =====================================================
# 12. BUSCADOR DE MATERIAS PRIMAS
# =====================================================

st.subheader("Consulta individual de materias primas")

st.markdown(
    "Busca una materia prima por su código o descripción "
    "para consultar sus indicadores."
)

busqueda = st.text_input(
    "Buscar materia prima",
    placeholder="Ingresa el código o nombre del material..."
)

if busqueda.strip():

    resultado = datos[
        datos["Material"]
        .astype(str)
        .str.contains(
            busqueda.strip(),
            case=False,
            na=False
        )
        |
        datos["Descripción del material"]
        .astype(str)
        .str.contains(
            busqueda.strip(),
            case=False,
            na=False
        )
    ].copy()

    if not resultado.empty:

        st.dataframe(
            formato_tabla(resultado),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "No se encontraron materias primas "
            "con ese código o descripción."
        )


# =====================================================
# 13. INFORMACIÓN DEL REPORTE
# =====================================================

st.divider()

with st.expander("Información de los datos"):

    st.write(
        "Fuente: Archivo de planificación MRP, "
        "hoja NS."
    )

    st.write(
        "Centro analizado: E024 – Río Loa."
    )

    st.write(
        f"Total de registros identificados: {len(datos)}."
    )

    st.write(
        f"Materias primas activas: {cantidad_activas}."
    )

    st.write(
        "La clasificación BB, EB y SB utiliza "
        "NS Corregido cuando está disponible; "
        "en caso contrario utiliza NS."
    )


# =====================================================
# 14. PIE DE PÁGINA
# =====================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#8492A6;
        font-size:12px;
        margin-top:40px;
        padding:15px;
    ">
        ENAEX CHILE | REPORTE DE GESTIÓN DE MATERIAS PRIMAS
        <br>
        RÍO LOA – CALAMA
    </div>
    """,
    unsafe_allow_html=True
)
