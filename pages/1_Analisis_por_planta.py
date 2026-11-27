import streamlit as st

from modules.navegacion import configurar_navegacion


# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Análisis por planta | Enaex",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()


# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>

.plant-description {
    color: #64748B;
    font-size: 16px;
    margin-bottom: 25px;
}

.plant-number {
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    margin-bottom: 10px;
}

.plant-name {
    font-size: 23px;
    font-weight: 750;
    margin-bottom: 5px;
}

.plant-location {
    font-size: 14px;
    color: #64748B;
    margin-bottom: 18px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# ENCABEZADO
# ==========================================

st.title("Análisis por planta")

st.markdown("""
<div class="plant-description">
Selecciona una planta para consultar sus indicadores
y analizar el comportamiento de sus materias primas.
</div>
""", unsafe_allow_html=True)


# ==========================================
# INFORMACIÓN DE LAS PLANTAS
# ==========================================

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


# ==========================================
# ESTADO DE SELECCIÓN
# ==========================================

if "planta_seleccionada" not in st.session_state:
    st.session_state.planta_seleccionada = None


def seleccionar_planta(nombre):
    st.session_state.planta_seleccionada = nombre


# ==========================================
# TARJETAS DE SELECCIÓN
# ==========================================

if st.session_state.planta_seleccionada is None:

    columnas = st.columns(3, gap="large")

    for columna, (nombre, datos) in zip(columnas, plantas.items()):

        with columna:

            with st.container(border=True):

                st.markdown(
                    f"""
                    <div style="
                        background-color: {datos['fondo']};
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 15px;
                    ">

                        <div class="plant-number"
                             style="color: {datos['color']};">
                            PLANTA {datos['numero']}
                        </div>

                        <div style="font-size: 35px;">
                            {datos['icono']}
                        </div>

                        <div class="plant-name"
                             style="color: {datos['color']};">
                            {nombre}
                        </div>

                        <div class="plant-location">
                            {datos['ubicacion']}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.button(
                    "Ver análisis de planta →",
                    key=f"btn_{nombre}",
                    use_container_width=True,
                    on_click=seleccionar_planta,
                    args=(nombre,)
                )


# ==========================================
# VISTA INDIVIDUAL DE PLANTA
# ==========================================

else:

    nombre = st.session_state.planta_seleccionada
    datos = plantas[nombre]

    st.button(
        "← Volver a selección de plantas",
        on_click=seleccionar_planta,
        args=(None,)
    )

    st.divider()

    st.markdown(
        f"""
        <div style="
            background-color: {datos['fondo']};
            padding: 25px;
            border-radius: 12px;
            border-left: 6px solid {datos['color']};
        ">

            <div style="
                font-size: 13px;
                color: {datos['color']};
            ">
                ANÁLISIS INDIVIDUAL
            </div>

            <div style="
                font-size: 30px;
                font-weight: 750;
                color: {datos['color']};
            ">
                {nombre}
            </div>

            <div style="color: #64748B;">
                {datos['ubicacion']} | Enaex Chile
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Indicadores de la planta")

    st.info(
        "Los indicadores de inventario, cobertura y nivel de "
        "servicio se incorporarán en la siguiente etapa."
    )

    st.subheader("Análisis de materias primas")

    st.info(
        "Aquí incorporaremos el análisis individual de cada "
        "materia prima, utilizando los archivos Excel de esta planta."
    )
