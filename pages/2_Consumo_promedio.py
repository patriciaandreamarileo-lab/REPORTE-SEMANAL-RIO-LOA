
import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import datetime, date
from openpyxl import load_workbook

from modules.github_storage import (
    descargar_archivo_github,
    RUTA_MRP
)


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

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
# 3. CARGAR ARCHIVO DE CONSUMO DESDE GITHUB
# =====================================================

@st.cache_data(ttl=300)
def cargar_consumo():

    contenido = descargar_archivo_github(
        RUTA_CONSUMO
    )

    if contenido is None:

        raise Exception(
            "No se encontró el archivo de consumo mensual "
            "de Río Loa en GitHub."
        )

    df = pd.read_excel(
        BytesIO(contenido),
        sheet_name="Data",
        engine="openpyxl"
    )

    return df


# =====================================================
# 3.1 CARGAR INFORMACIÓN DE STOCK Y CONSUMO DEL MRP
# =====================================================

@st.cache_data(ttl=300)
def cargar_datos_mrp():

    contenido = descargar_archivo_github(
        RUTA_MRP
    )

    if contenido is None:

        raise Exception(
            "No se encontró el archivo MRP de Río Loa en GitHub."
        )

    libro = load_workbook(
        BytesIO(contenido),
        data_only=True,
        read_only=True
    )

    try:

        if "MRP" not in libro.sheetnames:

            raise Exception(
                "No se encontró la hoja 'MRP' dentro del archivo XLSM."
            )

        hoja = libro["MRP"]

        # Identificar fecha de actualización en fila 6

        fechas_actualizacion = [
            valor
            for valor in next(
                hoja.iter_rows(
                    min_row=6,
                    max_row=6,
                    values_only=True
                )
            )
            if isinstance(valor, (datetime, date))
        ]

        if not fechas_actualizacion:

            raise Exception(
                "No se encontró la fecha de actualización del MRP en la fila 6."
            )

        fecha_actualizacion = max(fechas_actualizacion)

        mes_actualizacion = (
            fecha_actualizacion.year,
            fecha_actualizacion.month
        )

        # Identificar columna del mes actual en fila 8

        encabezados = next(
            hoja.iter_rows(
                min_row=8,
                max_row=8,
                values_only=True
            )
        )

        columna_mes = None

        for indice, valor in enumerate(encabezados, start=1):

            if isinstance(valor, (datetime, date)):

                if (
                    valor.year,
                    valor.month
                ) == mes_actualizacion:

                    columna_mes = indice
                    break

        if columna_mes is None:

            raise Exception(
                "No se encontró una columna mensual que coincida "
                "con la fecha de actualización del MRP."
            )

        # Leer materias primas de Río Loa

        resultados = {}

        for fila in hoja.iter_rows(
            min_row=9,
            max_col=max(27, columna_mes),
            values_only=True
        ):

            centro = str(
                fila[0] or ""
            ).strip().upper()

            if centro != CENTRO_RIO_LOA:
                continue

            material = fila[1]

            if material is None:
                continue

            if isinstance(material, float) and material.is_integer():

                codigo = str(int(material))

            else:

                codigo = str(material).strip()

            if codigo.endswith(".0"):
                codigo = codigo[:-2]

            unidad = str(
                fila[3] or ""
            ).strip()

            stock_actual = (
                fila[22]
                if len(fila) > 22
                else None
            )

            tipo_fila = str(
                fila[26]
                if len(fila) > 26 and fila[26] is not None
                else ""
            ).strip().upper()

            tipo_normalizado = (
                tipo_fila
                .replace(".", "")
                .replace(" ", "")
            )

            if codigo not in resultados:

                resultados[codigo] = {
                    "stock_actual": None,
                    "consumo_acumulado": None,
                    "unidad": unidad
                }

            # Stock actual

            if stock_actual is not None:

                try:

                    valor_stock = float(stock_actual)

                    if resultados[codigo]["stock_actual"] is None:

                        resultados[codigo]["stock_actual"] = valor_stock

                except (TypeError, ValueError):
                    pass

            # Consumo acumulado

            if tipo_normalizado == "CONSACU":

                valor_consumo = (
                    fila[columna_mes - 1]
                    if len(fila) >= columna_mes
                    else None
                )

                if valor_consumo is not None:

                    try:

                        resultados[codigo]["consumo_acumulado"] = float(
                            valor_consumo
                        )

                    except (TypeError, ValueError):
                        pass

                if unidad:
                    resultados[codigo]["unidad"] = unidad

        return (
            resultados,
            fecha_actualizacion.strftime("%d/%m/%Y")
        )

    finally:

        libro.close()


# =====================================================
# 3.2 OBTENER DATOS DEL MATERIAL SELECCIONADO
# =====================================================

def obtener_datos_mrp_material(codigo_material):

    datos_mrp, fecha_mrp = cargar_datos_mrp()

    codigo = str(codigo_material).strip()

    if codigo.endswith(".0"):
        codigo = codigo[:-2]

    informacion = datos_mrp.get(codigo)

    if informacion is None:

        return None, None, None, fecha_mrp

    return (
        informacion.get("stock_actual"),
        informacion.get("consumo_acumulado"),
        informacion.get("unidad"),
        fecha_mrp
    )


# =====================================================
# 4. ACTUALIZACIÓN MANUAL
# =====================================================

col_actualizar, col_estado = st.columns([1, 3])

with col_actualizar:

    if st.button(
        "🔄 Actualizar datos",
        use_container_width=True
    ):

        cargar_consumo.clear()
        cargar_datos_mrp.clear()

        st.rerun()


# =====================================================
# 5. OBTENER INFORMACIÓN
# =====================================================

try:

    datos_originales = cargar_consumo()

    if datos_originales.empty:

        st.error(
            "El archivo de consumo no contiene registros."
        )

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

datos["Material"] = (
    datos["Material"]
    .astype(str)
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

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

# Considerar movimientos 261 y 262

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

    st.warning(
        "No existen materias primas para consultar."
    )

    st.stop()


# =====================================================
# 9. ENCABEZADO
# =====================================================

st.title("Consumo mensual de materias primas")

st.markdown(
    "Análisis histórico de los movimientos y consumo "
    "de materias primas de Río Loa."
)

encabezado_html = (
    '<div style="background:linear-gradient(110deg,#153653 0%,#286B9B 100%);'
    'padding:35px;border-radius:16px;margin-top:20px;margin-bottom:25px;">'
    '<div style="font-size:13px;font-weight:bold;color:#FFFFFF;letter-spacing:2px;">'
    'ANÁLISIS INDIVIDUAL'
    '</div>'
    '<div style="font-size:34px;font-weight:750;color:#FFFFFF;margin-top:20px;">'
    'RÍO LOA'
    '</div>'
    '<div style="font-size:17px;color:#FFFFFF;margin-top:20px;">'
    'Calama | Enaex Chile | Centro E024'
    '</div>'
    '</div>'
)

st.markdown(
    encabezado_html,
    unsafe_allow_html=True
)

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
    key="busqueda_consumo_rio_loa"
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

    st.warning(
        "No se encontraron materias primas con esa búsqueda."
    )

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

    st.info(
        "No existen movimientos para esta materia prima."
    )

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
        key="unidad_consumo_rio_loa"
    )

    datos_material = datos_material[
        datos_material["Un.medida de entrada"]
        == unidad_seleccionada
    ].copy()

else:

    unidad_seleccionada = (
        unidades[0]
        if unidades
        else "Sin unidad"
    )


# =====================================================
# 13. CALCULAR CONSUMO MENSUAL
# =====================================================

datos_material["Mes"] = (
    datos_material["Fecha contabiliz."]
    .dt.to_period("M")
)

# Se conserva el signo original de SAP.
# El consumo neto se calcula como el negativo de la suma
# de los movimientos 261 y 262.

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

cantidad_movimientos = len(datos_material)

try:

    (
        stock_actual_mrp,
        consumo_acumulado_mrp,
        unidad_mrp,
        fecha_mrp
    ) = obtener_datos_mrp_material(codigo_seleccionado)

except Exception as error:

    stock_actual_mrp = None
    consumo_acumulado_mrp = None
    unidad_mrp = None
    fecha_mrp = None

    st.warning(
        f"No fue posible obtener el stock y el consumo acumulado "
        f"desde el MRP: {error}"
    )


unidad_mostrar = (
    unidad_mrp
    if unidad_mrp and unidad_mrp != "None"
    else unidad_seleccionada
)

col1, col2, col3 = st.columns(3)


if stock_actual_mrp is not None:

    col1.metric(
        "Stock actual",
        f"{stock_actual_mrp:,.2f} {unidad_mostrar}"
    )

else:

    col1.metric(
        "Stock actual",
        "No disponible"
    )


if consumo_acumulado_mrp is not None:

    col2.metric(
        "Consumo real a la fecha",
        f"{consumo_acumulado_mrp:,.2f} {unidad_mostrar}"
    )

else:

    col2.metric(
        "Consumo real a la fecha",
        "No disponible"
    )


col3.metric(
    "Movimientos SAP",
    f"{cantidad_movimientos:,}"
)


if fecha_mrp:

    st.caption(
        f"Stock y consumo acumulado obtenidos del MRP "
        f"actualizado al {fecha_mrp}. El consumo corresponde "
        f"al valor de la fila 'Cons. Acu.' en el mes de actualización."
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
        margin=dict(
            t=25,
            b=30,
            l=20,
            r=20
        ),
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
        use_container_width=True,
        config={"displayModeBar": False}
    )

else:

    st.info(
        "No existen datos para construir el gráfico."
    )


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
# 17. PROYECCIÓN DE CONSUMO MEDIANTE PROMEDIO MÓVIL
# =====================================================

st.subheader("Proyección de consumo")

st.markdown(
    "La proyección utiliza un promedio móvil de tres meses. "
    "Para cada nuevo mes se consideran los tres meses anteriores, "
    "incorporando los valores proyectados cuando corresponda."
)

if len(consumo_mensual) >= 1:

    # -------------------------------------------------
    # 17.1 PREPARAR HISTORIAL DE CONSUMO REAL
    # -------------------------------------------------

    historial = consumo_mensual[
        ["Mes", "Consumo"]
    ].copy()

    historial = historial.sort_values("Mes")

    historial["Mes"] = pd.PeriodIndex(
        historial["Mes"],
        freq="M"
    )

    historial = historial.drop_duplicates(
        subset=["Mes"],
        keep="last"
    )

    # Crear una serie mensual continua.
    # Los meses sin movimientos se consideran consumo cero.

    primer_mes = historial["Mes"].min()
    ultimo_mes = historial["Mes"].max()

    todos_los_meses = pd.period_range(
        start=primer_mes,
        end=ultimo_mes,
        freq="M"
    )

    consumo_real = (
        historial
        .set_index("Mes")["Consumo"]
        .reindex(todos_los_meses, fill_value=0)
        .astype(float)
    )

    # -------------------------------------------------
    # 17.2 CALCULAR PROMEDIO MÓVIL DE TRES MESES
    # -------------------------------------------------

    MESES_PROYECCION = 3

    valores_historicos = consumo_real.tolist()

    resultados_proyeccion = []

    for i in range(MESES_PROYECCION):

        ultimos_tres_meses = valores_historicos[-3:]

        promedio_movil = sum(
            ultimos_tres_meses
        ) / len(ultimos_tres_meses)

        mes_proyectado = (
            ultimo_mes + i + 1
        )

        resultados_proyeccion.append({
            "Mes": mes_proyectado,
            "Fecha": mes_proyectado.to_timestamp(),
            "Consumo": promedio_movil,
            "Tipo": "Proyección"
        })

        # Incorporar el valor proyectado al historial
        # para calcular el siguiente mes.

        valores_historicos.append(
            promedio_movil
        )

    proyeccion = pd.DataFrame(
        resultados_proyeccion
    )

    # -------------------------------------------------
    # 17.3 CONECTAR CONSUMO REAL Y PROYECCIÓN
    # -------------------------------------------------

    # El último punto real se agrega también a la serie
    # de proyección para que la línea naranja comience
    # exactamente donde termina la línea azul.

    punto_union = pd.DataFrame([{
        "Mes": ultimo_mes,
        "Fecha": ultimo_mes.to_timestamp(),
        "Consumo": float(consumo_real.iloc[-1]),
        "Tipo": "Proyección"
    }])

    proyeccion = pd.concat(
        [
            punto_union,
            proyeccion
        ],
        ignore_index=True
    )

    # -------------------------------------------------
    # 17.4 PREPARAR DATOS REALES
    # -------------------------------------------------

    reales = consumo_real.reset_index()

    reales.columns = [
        "Mes",
        "Consumo"
    ]

    reales["Fecha"] = (
        reales["Mes"].dt.to_timestamp()
    )

    reales["Tipo"] = "Consumo real"

    # -------------------------------------------------
    # 17.5 UNIR SERIES
    # -------------------------------------------------

    datos_grafico = pd.concat(
        [
            reales[
                ["Fecha", "Consumo", "Tipo"]
            ],
            proyeccion[
                ["Fecha", "Consumo", "Tipo"]
            ]
        ],
        ignore_index=True
    )

    # -------------------------------------------------
    # 17.6 GRÁFICO CON LÍNEAS CONECTADAS Y COLORES
    # -------------------------------------------------

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
        margin=dict(
            t=25,
            b=30,
            l=20,
            r=20
        ),
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

    # -------------------------------------------------
    # 17.7 TABLA DE CÁLCULO DE LA PROYECCIÓN
    # -------------------------------------------------

    st.markdown("#### Detalle del promedio móvil")

    detalle_proyeccion = []

    valores_historicos = consumo_real.tolist()

    for i in range(MESES_PROYECCION):

        ultimos_tres_meses = valores_historicos[-3:]

        promedio_movil = sum(
            ultimos_tres_meses
        ) / len(ultimos_tres_meses)

        mes_proyectado = ultimo_mes + i + 1

        detalle_proyeccion.append({
            "Mes proyectado": str(mes_proyectado),
            "Mes anterior 1": round(ultimos_tres_meses[-1], 2),
            "Mes anterior 2": round(ultimos_tres_meses[-2], 2),
            "Mes anterior 3": round(ultimos_tres_meses[-3], 2),
            "Promedio móvil": round(promedio_movil, 2)
        })

        valores_historicos.append(
            promedio_movil
        )

    tabla_proyeccion = pd.DataFrame(
        detalle_proyeccion
    )

    st.dataframe(
        tabla_proyeccion,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "La proyección se actualiza de forma recursiva: "
        "cada mes utiliza los tres meses inmediatamente anteriores. "
        "Los meses proyectados se incorporan al cálculo de los "
        "meses siguientes. Los meses sin movimientos se consideran cero."
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
        | RÍO LOA | CENTRO E024
    </div>
    """,
    unsafe_allow_html=True
)
