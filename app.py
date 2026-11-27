import streamlit as st

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

st.set_page_config(
    page_title="Dashboard Enaex Chile",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# COLORES Y DISEÑO
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

[data-testid="stSidebar"] {
    background-color: #102B46;
}

/* Ocultar navegación automática de Streamlit */
[data-testid="stSidebarNav"] {
    display: none;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.main-title {
    font-size: 34px;
    font-weight: 750;
    color: #173B60;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 17px;
    color: #64748B;
    margin-bottom: 25px;
}

.header-box {
    background: linear-gradient(110deg, #123454, #24669A);
    padding: 30px;
    border-radius: 14px;
    margin-bottom: 30px;
}

.header-title {
    color: white;
    font-size: 29px;
    font-weight: 750;
}

.header-subtitle {
    color: #DCEAF7;
    font-size: 15px;
}

.card-title {
    color: #173B60;
    font-size: 21px;
    font-weight: 700;
    margin-bottom: 12px;
}

.card-description {
    color: #64748B;
    font-size: 14px;
    min-height: 75px;
}

.footer {
    color: #8492A6;
    font-size: 12px;
    text-align: center;
    margin-top: 60px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# MENÚ LATERAL
# ==========================================

with st.sidebar:

    st.markdown("## ENAEX CHILE")
    st.caption("Gestión de materias primas")

    st.divider()

    st.markdown("### NAVEGACIÓN")

    st.page_link(
        "app.py",
        label="Inicio",
        icon="🏠"
    )

    st.page_link(
        "pages/1_Analisis_por_planta.py",
        label="Análisis por planta",
        icon="🏭"
    )

    st.page_link(
        "pages/2_Consumo_promedio.py",
        label="Consumo promedio",
        icon="📊"
    )

    st.page_link(
        "pages/3_Evolucion_de_precios.py",
        label="Evolución de precios",
        icon="📈"
    )

    st.divider()

    st.caption("Dashboard de gestión y análisis")


# ==========================================
# ENCABEZADO PRINCIPAL
# ==========================================

st.markdown("""
<div class="header-box">
    <div class="header-title">
        DASHBOARD DE GESTIÓN DE MATERIAS PRIMAS
    </div>
    <div class="header-subtitle">
        ENAEX CHILE | Planificación, consumo y análisis de precios
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# PRESENTACIÓN
# ==========================================

st.markdown(
    '<div class="main-title">Panel de control</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Selecciona el módulo que deseas consultar para acceder '
    'a los análisis de materias primas.'
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# TARJETAS DE NAVEGACIÓN
# ==========================================

col1, col2, col3 = st.columns(3, gap="large")


# TARJETA 1: ANÁLISIS POR PLANTA

with col1:

    with st.container(border=True):

        st.markdown("## 🏭")

        st.markdown(
            '<div class="card-title">Análisis por planta</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-description">'
            'Consulta los indicadores de inventario, cobertura, '
            'nivel de servicio y situación de las materias primas '
            'de cada planta.'
            '</div>',
            unsafe_allow_html=True
        )

        st.page_link(
            "pages/1_Analisis_por_planta.py",
            label="Ingresar al análisis",
            icon="➡️",
            use_container_width=True
        )


# TARJETA 2: CONSUMO PROMEDIO

with col2:

    with st.container(border=True):

        st.markdown("## 📊")

        st.markdown(
            '<div class="card-title">Consumo promedio</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-description">'
            'Analiza el comportamiento histórico del consumo, '
            'sus variaciones mensuales y las tendencias de '
            'las materias primas.'
            '</div>',
            unsafe_allow_html=True
        )

        st.page_link(
            "pages/2_Consumo_promedio.py",
            label="Ingresar al consumo",
            icon="➡️",
            use_container_width=True
        )


# TARJETA 3: EVOLUCIÓN DE PRECIOS

with col3:

    with st.container(border=True):

        st.markdown("## 📈")

        st.markdown(
            '<div class="card-title">Evolución de precios</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-description">'
            'Visualiza la evolución de los precios de compra, '
            'las variaciones de las órdenes de compra y '
            'el comportamiento de los proveedores.'
            '</div>',
            unsafe_allow_html=True
        )

        st.page_link(
            "pages/3_Evolucion_de_precios.py",
            label="Ingresar a precios",
            icon="➡️",
            use_container_width=True
        )


# ==========================================
# PIE DE PÁGINA
# ==========================================

st.markdown("""
<div class="footer">
    ENAEX CHILE | Dashboard de gestión de materias primas
</div>
""", unsafe_allow_html=True)

