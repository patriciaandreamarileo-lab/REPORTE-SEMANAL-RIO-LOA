import streamlit as st


def configurar_navegacion():

    st.markdown("""
    <style>

    [data-testid="stSidebarNav"] {
        display: none;
    }

    [data-testid="stSidebar"] {
        background-color: #102B46;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .stApp {
        background-color: #F4F7FB;
    }

    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:

        st.markdown("# ENAEX CHILE")
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

        st.page_link(
            "pages/4_Administracion.py",
            label="Administración",
            icon="🔐"
        )

        st.divider()

        st.caption("Dashboard de gestión y análisis")
