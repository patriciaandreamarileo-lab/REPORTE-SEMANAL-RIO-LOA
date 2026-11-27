
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

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px;
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
# 4. ESTADO DE SELECCIÓN
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
    '<div class="plant-description">Selecciona una planta para consultar sus indicadores y analizar el comportamiento de sus materias primas.</div>',
    unsafe_allow_html=True
)


# =====================================================
# 6. TARJETAS DE SELECCIÓN
# =====================================================

if st.session_state.planta_seleccionada is None:

    columnas = st.columns(3, gap="large")

    for columna, (nombre, datos) in zip(columnas, plantas.items()):

        with columna:

            with st.container(border=True):

                # HTML construido sin saltos de línea
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
# 7. VISTA INDIVIDUAL DE CADA PLANTA
# =====================================================

else:

    nombre = st.session_state.planta_seleccionada
    datos = plantas[nombre]

    st.button(
        "← Volver a selección de plantas",
        on_click=seleccionar_planta,
        args=(None,)
    )

    st.divider()

    # Encabezado individual
    encabezado = (
        f'<div style="background-color:{datos["fondo"]};'
        f'padding:28px;border-radius:12px;'
        f'border-left:6px solid {datos["color"]};">'

        f'<div style="font-size:13px;font-weight:bold;'
        f'color:{datos["color"]};letter-spacing:2px;">'
        f'ANÁLISIS INDIVIDUAL</div>'

        f'<div style="font-size:30px;font-weight:750;'
        f'color:{datos["color"]};margin-top:8px;">'
        f'{nombre}</div>'

        f'<div style="color:#64748B;margin-top:5px;">'
        f'{datos["ubicacion"]} | Enaex Chile</div>'

        f'</div>'
    )

    st.markdown(encabezado, unsafe_allow_html=True)

    st.write("")

    # Indicadores
    st.subheader("Indicadores de la planta")

    col1, col2, col3 = st.columns(3)

    col1.metric("Materias primas", "—")
    col2.metric("Nivel de servicio", "—")
    col3.metric("Cobertura promedio", "—")

    st.divider()

    # Inventario
    st.subheader("Análisis de inventario")

    st.info(
        "En esta sección incorporaremos stock actual, "
        "stock de seguridad, stock máximo, stock óptimo "
        "y cobertura de inventario."
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

st.markdown(
    '<div style="text-align:center;color:#8492A6;'
    'font-size:12px;margin-top:45px;padding:15px;">'
    'ENAEX CHILE | Dashboard de gestión de materias primas'
    '</div>',
    unsafe_allow_html=True
)
