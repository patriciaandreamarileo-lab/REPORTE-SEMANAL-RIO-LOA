import streamlit as st
import pandas as pd

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


# =====================================================
# 2. INFORMACIÓN DE LAS PLANTAS
# =====================================================

plantas = {
    "RIO LOA": {
        "numero": "01",
        "ubicacion": "Calama",
        "centro": "E024",
        "color": "#245A91",
        "fondo": "#E6EFF9",
        "icono": "🏭"
    },
    "PRILLEX": {
        "numero": "02",
        "ubicacion": "Mejillones",
        "centro": "E002",
        "color": "#28734A",
        "fondo": "#E5F1E9",
        "icono": "🏭"
    },
    "PUNTA TEATINOS": {
        "numero": "03",
        "ubicacion": "La Serena",
        "centro": "E026",
        "color": "#98643A",
        "fondo": "#F5EDE3",
        "icono": "🏭"
    }
}


# =====================================================
# 3. ESTILOS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.plant-description {
    color: #64748B;
    font-size: 16px;
    margin-bottom: 28px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px;
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
# 4. CARGAR INFORMACIÓN DEL MRP
# =====================================================

@st.cache_data(ttl=60)
def obtener_datos_mrp():

    df, hojas = cargar_mrp()

    return df


try:

    datos_mrp = obtener_datos_mrp()

    if datos_mrp.empty:
        st.error("El MRP no contiene registros.")
        st.stop()

except Exception as e:

    st.error(
        f"No fue posible cargar el MRP desde GitHub: {e}"
    )

    st.stop()


# =====================================================
# 5. LIMPIEZA Y PREPARACIÓN DE DATOS
# =====================================================

datos_mrp = datos_mrp.copy()

datos_mrp.columns = [
    str(c).strip()
    for c in datos_mrp.columns
]

datos_mrp["Centro"] = (
    datos_mrp["Centro"]
    .astype(str)
    .str.strip()
)

datos_mrp["Material"] = (
    datos_mrp["Material"]
    .astype(str)
    .str.strip()
)

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
# 6. FUNCIONES
# =====================================================

def obtener_activos(df):

    return df[
        df["MMPP Activa"]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(["SI", "SÍ"])
    ].copy()


def calcular_nivel_servicio(df):

    if df.empty:
        return None

    riesgo = pd.to_numeric(
        df["Riesgo MMPP"],
        errors="coerce"
    ).fillna(0)

    clasificacion = (
        df["NS"]
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

    resultado = (
        (riesgo_eb + (0.5 * riesgo_sb))
        / total
    ) * 100

    return resultado


def formato_numero(valor, decimales=0):

    if pd.isna(valor):
        return "—"

    return (
        f"{valor:,.{decimales}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# =====================================================
# 7. ESTADO DE SELECCIÓN
# =====================================================

if "planta_seleccionada" not in st.session_state:
    st.session_state.planta_seleccionada = None


def seleccionar_planta(nombre):

    st.session_state.planta_seleccionada = nombre


# =====================================================
# 8. ENCABEZADO
# =====================================================

st.title("Análisis por planta")

st.markdown(
    '<div class="plant-description">'
    'Selecciona una planta para consultar sus indicadores '
    'y analizar el comportamiento de sus materias primas.'
    '</div>',
    unsafe_allow_html=True
)


# =====================================================
# 9. TARJETAS DE SELECCIÓN
# =====================================================

if st.session_state.planta_seleccionada is None:

    columnas = st.columns(3, gap="large")

    for columna, (nombre, datos) in zip(
        columnas,
        plantas.items()
    ):

        with columna:

            with st.container(border=True):

                html_tarjeta = (

                    f'<div style="background-color:{datos["fondo"]};'
                    f'padding:22px;border-radius:12px;'
                    f'margin-bottom:15px;min-height:215px;">'

                    f'<div style="font-size:13px;font-weight:bold;'
                    f'letter-spacing:2px;color:{datos["color"]};">'
                    f'PLANTA {datos["numero"]}</div>'

                    f'<div style="font-size:38px;margin-top:15px;">'
                    f'{datos["icono"]}</div>'

                    f'<div style="font-size:23px;font-weight:750;'
                    f'color:{datos["color"]};margin-top:10px;">'
                    f'{nombre}</div>'

                    f'<div style="font-size:14px;color:#64748B;'
                    f'margin-top:8px;">'
                    f'{datos["ubicacion"]}</div>'

                    f'</div>'
                )

                st.markdown(
                    html_tarjeta,
                    unsafe_allow_html=True
                )

                st.button(
                    "Ver análisis de planta →",
                    key=f"btn_{nombre}",
                    use_container_width=True,
                    on_click=seleccionar_planta,
                    args=(nombre,)
                )


# =====================================================
# 10. VISTA INDIVIDUAL DE CADA PLANTA
# =====================================================

else:

    nombre = st.session_state.planta_seleccionada

    datos_planta = plantas[nombre]

    centro = datos_planta["centro"]

    st.button(
        "← Volver a selección de plantas",
        on_click=seleccionar_planta,
        args=(None,)
    )

    st.divider()


    # -------------------------------------------------
    # 10.1 FILTRAR INFORMACIÓN DEL MRP
    # -------------------------------------------------

    datos = datos_mrp[
        datos_mrp["Centro"] == centro
    ].copy()

    if datos.empty:

        st.warning(
            f"No se encontraron registros para {nombre} "
            f"(Centro {centro}) en la hoja NS del MRP."
        )

        st.stop()

    datos_activos = obtener_activos(datos)


    # -------------------------------------------------
    # 10.2 ENCABEZADO INDIVIDUAL
    # -------------------------------------------------

    encabezado = (

        f'<div style="background-color:{datos_planta["fondo"]};'
        f'padding:28px;border-radius:12px;'
        f'border-left:6px solid {datos_planta["color"]};">'

        f'<div style="font-size:13px;font-weight:bold;'
        f'color:{datos_planta["color"]};letter-spacing:2px;">'
        f'ANÁLISIS INDIVIDUAL</div>'

        f'<div style="font-size:30px;font-weight:750;'
        f'color:{datos_planta["color"]};margin-top:8px;">'
        f'{nombre}</div>'

        f'<div style="color:#64748B;margin-top:5px;">'
        f'{datos_planta["ubicacion"]} | Enaex Chile</div>'

        f'</div>'
    )

    st.markdown(
        encabezado,
        unsafe_allow_html=True
    )

    st.write("")


    # =================================================
    # 11. INDICADORES DE LA PLANTA
    # =================================================

    st.subheader("Indicadores de la planta")

    cantidad_materiales = len(datos_activos)

    nivel_servicio = calcular_nivel_servicio(
        datos_activos
    )

    if (
        not datos_activos.empty
        and "Cobertura a [Días]" in datos_activos.columns
    ):

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
        (
            f"{nivel_servicio:.1f}%"
            if nivel_servicio is not None
            else "—"
        )
    )

    col3.metric(
        "Cobertura promedio",
        (
            f"{cobertura_promedio:.1f} días"
            if cobertura_promedio is not None
            else "—"
        )
    )

    st.caption(
        "Información obtenida directamente de la hoja NS "
        "del último MRP almacenado en GitHub."
    )

    st.divider()


    # =================================================
    # 12. ALERTAS Y OBSERVACIONES
    # =================================================

    st.subheader("Alertas y observaciones")

    st.markdown(
        "Distribución de las materias primas según su "
        "clasificación NS corregida y seguimiento de "
        "los comentarios registrados en el MRP."
    )

    if "NS Corregido" in datos_activos.columns:

        clasificaciones = (
            datos_activos["NS Corregido"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # Conteo de clasificaciones

        conteo = (
            clasificaciones[
                clasificaciones.isin(["BB", "EB", "SB"])
            ]
            .value_counts()
            .reindex(["BB", "EB", "SB"], fill_value=0)
        )

        total_clasificados = int(conteo.sum())

        # Indicadores de clasificación

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Clasificación EB",
            int(conteo["EB"])
        )

        col2.metric(
            "Clasificación BB",
            int(conteo["BB"])
        )

        col3.metric(
            "Clasificación SB",
            int(conteo["SB"])
        )

        st.write("")

        # -------------------------------------------------
        # GRÁFICO DE TORTA
        # -------------------------------------------------

        st.markdown("### Distribución de materias primas")

        if total_clasificados > 0:

            datos_grafico = pd.DataFrame({
                "Clasificación": ["BB", "EB", "SB"],
                "Cantidad": [
                    int(conteo["BB"]),
                    int(conteo["EB"]),
                    int(conteo["SB"])
                ]
            })

            especificacion = {

                "mark": {
                    "type": "arc",
                    "innerRadius": 0,
                    "outerRadius": 115,
                    "stroke": "white",
                    "strokeWidth": 2
                },

                "encoding": {

                    "theta": {
                        "field": "Cantidad",
                        "type": "quantitative"
                    },

                    "color": {
                        "field": "Clasificación",
                        "type": "nominal",
                        "scale": {
                            "domain": ["BB", "EB", "SB"],
                            "range": [
                                "#DC2626",
                                "#16A34A",
                                "#0891B2"
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
                            "type": "nominal",
                            "title": "Clasificación"
                        },
                        {
                            "field": "Cantidad",
                            "type": "quantitative",
                            "title": "Materias primas"
                        }
                    ]
                },

                "view": {
                    "stroke": None
                },

                "width": "container",
                "height": 300
            }

            st.vega_lite_chart(
                datos_grafico,
                especificacion,
                use_container_width=True
            )

            st.caption(
                f"Total de materias primas clasificadas: "
                f"{total_clasificados}"
            )

        else:

            st.info(
                "No existen materias primas clasificadas "
                "como EB, BB o SB para esta planta."
            )


        # -------------------------------------------------
        # LISTADO DE ALERTAS
        # -------------------------------------------------

        st.markdown("### Materias primas que requieren seguimiento")

        alertas = datos_activos[
            clasificaciones.isin(["BB", "SB"])
        ].copy()

        if not alertas.empty:

            columnas_alertas = [
                "Material",
                "Descripción del material",
                "NS",
                "NS Corregido",
                "Comentario"
            ]

            columnas_disponibles = [
                c for c in columnas_alertas
                if c in alertas.columns
            ]

            alertas = alertas[columnas_disponibles]

            def colorear_alerta(valor):

                if str(valor).upper() == "BB":

                    return (
                        "background-color: #FEE2E2;"
                        "color: #991B1B;"
                        "font-weight: bold;"
                    )

                if str(valor).upper() == "SB":

                    return (
                        "background-color: #CFFAFE;"
                        "color: #155E75;"
                        "font-weight: bold;"
                    )

                if str(valor).upper() == "EB":

                    return (
                        "background-color: #DCFCE7;"
                        "color: #166534;"
                        "font-weight: bold;"
                    )

                return ""

            st.dataframe(
                alertas.style.map(
                    colorear_alerta,
                    subset=["NS Corregido"]
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "No se registran materiales clasificados "
                "como BB o SB."
            )

    else:

        st.warning(
            "No se encontró la columna NS Corregido en el MRP."
        )

    st.divider()


    # =================================================
    # 13. MATERIAS PRIMAS CRÍTICAS
    # =================================================

    st.subheader("Materias primas críticas")

    st.markdown(
        "Identificación de materias primas con menores "
        "niveles de stock actual."
    )

    if (
        not datos_activos.empty
        and "Stock Actual" in datos_activos.columns
    ):

        criticas = datos_activos.dropna(
            subset=["Stock Actual"]
        ).copy()

        criticas = criticas.sort_values(
            by="Stock Actual",
            ascending=True
        ).head(5)

        if not criticas.empty:

            columnas_criticas = [
                "Material",
                "Descripción del material",
                "UM",
                "Stock Actual",
                "Stock Seguridad",
                "Stock Óptimo",
                "NS"
            ]

            columnas_disponibles = [
                c for c in columnas_criticas
                if c in criticas.columns
            ]

            st.dataframe(
                criticas[columnas_disponibles],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No hay registros de stock disponibles."
            )

    else:

        st.info(
            "No hay información de stock para esta planta."
        )

    st.divider()


    # =================================================
    # 14. ANÁLISIS INDIVIDUAL DE MATERIAS PRIMAS
    # =================================================

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
            placeholder="Ingresa código o descripción...",
            key=f"busqueda_{nombre}"
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
                catalogo["Etiqueta"].tolist(),
                key=f"seleccion_{nombre}"
            )

            material_seleccionado = catalogo[
                catalogo["Etiqueta"] == seleccion
            ].iloc[0]

            st.write("")

            st.markdown(
                f"### {material_seleccionado['Descripción del material']}"
            )

            st.caption(
                f"Código: {material_seleccionado['Material']}"
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Consumo promedio",
                formato_numero(
                    material_seleccionado["Consumo X̄"]
                )
            )

            c2.metric(
                "Stock actual",
                formato_numero(
                    material_seleccionado["Stock Actual"]
                )
            )

            cobertura_material = material_seleccionado.get(
                "Cobertura a [Días]"
            )

            c3.metric(
                "Cobertura",
                (
                    f"{cobertura_material:.1f} días"
                    if pd.notna(cobertura_material)
                    else "—"
                )
            )

            st.write("")

            c4, c5, c6 = st.columns(3)

            c4.metric(
                "Riesgo MMPP",
                formato_numero(
                    material_seleccionado["Riesgo MMPP"]
                )
            )

            c5.metric(
                "Clasificación NS",
                str(material_seleccionado["NS"])
            )

            c6.metric(
                "NS Corregido",
                str(material_seleccionado["NS Corregido"])
            )

            if (
                "Comentario" in material_seleccionado.index
                and pd.notna(material_seleccionado["Comentario"])
                and str(material_seleccionado["Comentario"]).strip()
            ):

                st.write("**Comentario del MRP**")

                st.info(
                    str(material_seleccionado["Comentario"])
                )

        else:

            st.warning(
                "No se encontraron materias primas "
                "con ese código o descripción."
            )

    else:

        st.info(
            "No existen materias primas activas para consultar."
        )


# =====================================================
# 15. PIE DE PÁGINA
# =====================================================

st.markdown(
    '<div style="text-align:center;color:#8492A6;'
    'font-size:12px;margin-top:45px;padding:15px;">'
    'ENAEX CHILE | Dashboard de gestión de materias primas'
    '</div>',
    unsafe_allow_html=True
)
