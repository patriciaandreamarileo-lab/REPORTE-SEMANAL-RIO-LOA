import streamlit as st

from modules.navegacion import configurar_navegacion


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Análisis por planta | Enaex",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navegación corporativa
configurar_navegacion()


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
    margin-bottom: 28px;
}

.plant-card-number {
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    margin-bottom: 15px;
}

.plant-card-name {
    font-size: 23px;
    font-weight: 750;
    margin-top: 12px;
    margin-bottom: 5px;
}

.plant-card-location {
    font-size: 14px;
    color: #64748B;
    margin-top: 8px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. INFORMACIÓN DE LAS PLANTAS
# =====================================================

plantas = {

    "RIO LOA": {
        "numero": "01",
        "ubicacion": "Calama",
        "color": "#245A91",
        "fondo": "#E6EFF9",
        "icono": "🏭"
    },

    "PRILLEX": {
        "numero": "02",
        "ubicacion": "Mejillones",
        "color": "#28734A",
        "fondo": "#E5F1E9",
        "icono": "🏭"
    },

    "PUNTA TEATINOS": {
        "numero": "03",
        "ubicacion": "La Serena",
        "color": "#98643A",
        "fondo": "#F5EDE3",
        "icono": "🏭"
    }

}


# =====================================================
# 4. CONTROL DE SELECCIÓN
# =====================================================

if "planta_seleccionada" not in st.session_state:
    st.session_state.planta_seleccionada = None


def seleccionar_planta(nombre):
    st.session_state.planta_seleccionada = nombre


# =====================================================
# 5. ENCABEZADO
# =====================================================

st.title("Análisis por planta")

st.markdown(
    """
    <div class="plant-description">
        Selecciona una planta para consultar sus indicadores
        y analizar el comportamiento de sus materias primas.
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 6. SELECCIÓN DE PLANTAS
# =====================================================

if st.session_state.planta_seleccionada is None:

    columnas = st.columns(3, gap="large")

    for columna, (nombre, datos) in zip(columnas, plantas.items()):

        with columna:

            with st.container(border=True):

                # Tarjeta visual de cada planta
                html_tarjeta = f"""<div style="
                    background-color: {datos['fondo']};
                    padding: 22px;
                    border-radius: 12px;
                    margin-bottom: 15px;
                    min-height: 215px;
                ">
                    <div class="plant-card-number"
                         style="color: {datos['color']};">
                        PLANTA {datos['numero']}
                    </div>

                    <div style="font-size: 38px;">
                        {datos['icono']}
                    </div>

                    <div class="plant-card-name"
                         style="color: {datos['color']};">
                        {nombre}
                    </div>

                    <div class="plant-card-location">
                        {datos['ubicacion']}
                    </div>
                </div>"""

                st.markdown(
                    html_tarjeta,
                    unsafe_allow_html=True
                )

                # Botón de ingreso
                st.button(
                    "Ver análisis de planta →",
                    key=f"btn_{nombre}",
                    use_container_width=True,
                    on_click=seleccionar_planta,
                    args=(nombre,)
                )


# =====================================================
# 7. VISTA INDIVIDUAL DE CADA PLANTA
# =====================================================

else:

    nombre = st.session_state.planta_seleccionada
    datos = plantas[nombre]

    # Botón para regresar
    st.button(
        "← Volver a selección de plantas",
        on_click=seleccionar_planta,
        args=(None,)
    )

    st.divider()

    # Encabezado de planta
    encabezado_planta = f"""<div style="
        background-color: {datos['fondo']};
        padding: 28px;
        border-radius: 12px;
        border-left: 6px solid {datos['color']};
    ">
        <div style="
            font-size: 13px;
            font-weight: bold;
            color: {datos['color']};
            letter-spacing: 2px;
        ">
            ANÁLISIS INDIVIDUAL
        </div>

        <div style="
            font-size: 30px;
            font-weight: 750;
            color: {datos['color']};
            margin-top: 8px;
        ">
            {nombre}
        </div>

        <div style="color: #64748B; margin-top: 5px;">
            {datos['ubicacion']} | Enaex Chile
        </div>
    </div>"""

    st.markdown(
        encabezado_planta,
        unsafe_allow_html=True
    )

    st.write("")

    # Indicadores
    st.subheader("Indicadores de la planta")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Materias primas",
        "—",
        help="Cantidad de materias primas registradas."
    )

    col2.metric(
        "Nivel de servicio",
        "—",
        help="Indicador de nivel de servicio de la planta."
    )

    col3.metric(
        "Cobertura promedio",
        "—",
        help="Cobertura promedio del inventario."
    )

    st.divider()

    # Análisis de inventario
    st.subheader("Análisis de inventario")

    st.info(
        "En esta sección incorporaremos los indicadores "
        "de stock actual, stock de seguridad, stock máximo, "
        "stock óptimo y cobertura de inventario."
    )

    st.divider()

    # Materias primas críticas
    st.subheader("Materias primas críticas")

    st.info(
        "Aquí identificaremos las materias primas que "
        "requieren mayor atención por sus niveles de inventario."
    )

    st.divider()

    # Análisis individual
    st.subheader("Análisis individual de materias primas")

    st.info(
        "Aquí incorporaremos gráficos y tablas para "
        "analizar individualmente cada materia prima."
    )

    st.divider()

    # Órdenes de compra
    st.subheader("Órdenes de compra pendientes")

    st.info(
        "Aquí mostraremos el detalle de las órdenes de compra "
        "pendientes de recepción."
    )


# =====================================================
# 8. PIE DE PÁGINA
# =====================================================

st.markdown("""
<div style="
    text-align: center;
    color: #8492A6;
    font-size: 12px;
    margin-top: 45px;
    padding: 15px;
">
    ENAEX CHILE | Dashboard de gestión de materias primas
</div>
""", unsafe_allow_html=True)

