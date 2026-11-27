import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

from io import BytesIO

from modules.navegacion import configurar_navegacion
from modules.github_storage import descargar_archivo_github


# =====================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Evolución de precios | Río Loa",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

configurar_navegacion()

RUTA_PRECIOS = "data/PRECIOS/precios_rio_loa.xlsx"
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

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. FUNCIONES AUXILIARES
# =====================================================

def limpiar_texto(serie):

    return (
        serie
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def normalizar_codigo(valor):

    if pd.isna(valor):
        return ""

    codigo = str(valor).strip()

    if codigo.endswith(".0"):
        codigo = codigo[:-2]

    return codigo.upper()


def normalizar_encabezado(valor):

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    ).encode("ascii", "ignore").decode("ascii")

    return " ".join(texto.split())


def normalizar_material(valor):

    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    ).encode("ascii", "ignore").decode("ascii")

    return " ".join(texto.split())


def convertir_numero(serie):

    return pd.to_numeric(
        serie,
        errors="coerce"
    )


def formato_numero(valor, decimales=2):

    if pd.isna(valor):
        return "—"

    return (
        f"{valor:,.{decimales}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def unir_codigos(valores):

    codigos = set()

    for valor in valores:

        if pd.isna(valor):
            continue

        partes = str(valor).split("/")

        for parte in partes:

            codigo = parte.strip()

            if codigo:
                codigos.add(codigo)

    return " / ".join(sorted(codigos))


# =====================================================
# 4. CARGAR ARCHIVO DE PRECIOS
# =====================================================

@st.cache_data(ttl=60)
def cargar_precios():

    contenido = descargar_archivo_github(
        RUTA_PRECIOS
    )

    if contenido is None:

        raise Exception(
            "No se encontró el archivo de precios en GitHub."
        )

    df = pd.read_excel(
        BytesIO(contenido),
        sheet_name="Data",
        engine="openpyxl"
    )

    df.columns = [
        str(columna).strip()
        for columna in df.columns
    ]

    return df


# =====================================================
# 5. CARGAR MAESTRO DEL MRP
# =====================================================

@st.cache_data(ttl=60)
def cargar_maestros_mrp():

    contenido = descargar_archivo_github(
        RUTA_MRP
    )

    if contenido is None:

        raise Exception(
            "No se encontró el archivo MRP en GitHub."
        )

    archivo = BytesIO(contenido)

    excel = pd.ExcelFile(
        archivo,
        engine="openpyxl"
    )

    hoja_encontrada = None
    fila_encabezado = None

    columnas_encontradas = {}

    # Buscar la hoja que contiene las cuatro columnas
    # necesarias, sin depender del nombre de la pestaña.

    columnas_necesarias = [
        "acreedor",
        "proveedor",
        "material",
        "descripcion del material"
    ]

    for nombre_hoja in excel.sheet_names:

        df_original = pd.read_excel(
            excel,
            sheet_name=nombre_hoja,
            header=None
        )

        for i in range(len(df_original)):

            encabezados = [
                normalizar_encabezado(valor)
                for valor in df_original.iloc[i].tolist()
            ]

            if all(
                columna in encabezados
                for columna in columnas_necesarias
            ):

                hoja_encontrada = nombre_hoja
                fila_encabezado = i

                columnas_encontradas = {
                    columna: encabezados.index(columna)
                    for columna in columnas_necesarias
                }

                break

        if hoja_encontrada is not None:
            break

    if hoja_encontrada is None:

        raise Exception(
            "No se encontró en el MRP una hoja que contenga "
            "Acreedor, Proveedor, Material y "
            "Descripción del material."
        )

    # Leer los datos de la hoja encontrada.

    df_original = pd.read_excel(
        excel,
        sheet_name=hoja_encontrada,
        header=None
    )

    datos_mrp = df_original.iloc[
        fila_encabezado + 1:
    ].copy()

    # Extraer las columnas exactas.

    datos_mrp = datos_mrp[
        [
            columnas_encontradas["acreedor"],
            columnas_encontradas["proveedor"],
            columnas_encontradas["material"],
            columnas_encontradas["descripcion del material"]
        ]
    ].copy()

    datos_mrp.columns = [
        "Acreedor",
        "Proveedor",
        "Material",
        "Descripción MRP"
    ]

    # Limpiar información.

    datos_mrp["Acreedor"] = (
        datos_mrp["Acreedor"]
        .apply(normalizar_codigo)
    )

    datos_mrp["Proveedor"] = (
        datos_mrp["Proveedor"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    datos_mrp["Material"] = (
        datos_mrp["Material"]
        .apply(normalizar_codigo)
    )

    datos_mrp["Descripción MRP"] = (
        datos_mrp["Descripción MRP"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    datos_mrp = datos_mrp[
        (datos_mrp["Material"] != "")
        & (datos_mrp["Descripción MRP"] != "")
    ].copy()

    # Maestro de proveedores:
    # Acreedor = código
    # Proveedor = nombre.

    maestro_proveedores = datos_mrp[
        ["Acreedor", "Proveedor"]
    ].copy()

    maestro_proveedores = maestro_proveedores[
        (maestro_proveedores["Acreedor"] != "")
        & (maestro_proveedores["Proveedor"] != "")
    ].drop_duplicates(
        subset=["Acreedor"],
        keep="first"
    )

    # Maestro de materiales.
    # Cada código queda asociado a su descripción del MRP.

    maestro_materiales = datos_mrp[
        ["Material", "Descripción MRP"]
    ].copy()

    maestro_materiales = maestro_materiales.drop_duplicates(
        subset=["Material"],
        keep="first"
    )

    return maestro_proveedores, maestro_materiales


# =====================================================
# 6. BOTÓN DE ACTUALIZACIÓN
# =====================================================

col_actualizar, col_estado = st.columns([1, 3])

with col_actualizar:

    if st.button(
        "🔄 Actualizar datos",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()


# =====================================================
# 7. CARGAR ARCHIVOS
# =====================================================

try:

    datos_originales = cargar_precios()

    maestro_proveedores, maestro_materiales = (
        cargar_maestros_mrp()
    )

except Exception as error:

    st.error(
        f"No fue posible cargar la información: {error}"
    )

    st.stop()


if datos_originales.empty:

    st.error(
        "El archivo de precios no contiene registros."
    )

    st.stop()


# =====================================================
# 8. VALIDAR COLUMNAS
# =====================================================

columnas_requeridas = [
    "Material",
    "Centro",
    "Clase de movimiento",
    "Fecha contabiliz.",
    "Pedido",
    "Moneda",
    "Impte.mon.local",
    "Ctd.en UM entrada",
    "Proveedor"
]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in datos_originales.columns
]

if faltantes:

    st.error(
        "Faltan columnas necesarias en el Excel de precios: "
        + ", ".join(faltantes)
    )

    st.stop()


# =====================================================
# 9. PREPARAR ARCHIVO DE PRECIOS
# =====================================================

datos = datos_originales.copy()

# Centro.

datos["Centro"] = (
    limpiar_texto(datos["Centro"])
    .str.upper()
)

# Filtrar Río Loa.

datos = datos[
    datos["Centro"] == CENTRO_RIO_LOA
].copy()

if datos.empty:

    st.error(
        "No se encontraron registros del centro E024."
    )

    st.stop()


# Código del material.

datos["Material"] = (
    datos["Material"]
    .apply(normalizar_codigo)
)

# Código del proveedor del Excel de precios.

datos["Codigo proveedor"] = (
    datos["Proveedor"]
    .apply(normalizar_codigo)
)

# Descripción original del Excel.

if "Descripción material" in datos.columns:

    datos["Descripción Excel"] = limpiar_texto(
        datos["Descripción material"]
    )

elif "Descripción del material" in datos.columns:

    datos["Descripción Excel"] = limpiar_texto(
        datos["Descripción del material"]
    )

else:

    datos["Descripción Excel"] = ""


# Número de OC.

datos["Pedido"] = limpiar_texto(
    datos["Pedido"]
)

# Moneda.

datos["Moneda"] = (
    limpiar_texto(datos["Moneda"])
    .str.upper()
)

# Fecha.

datos["Fecha"] = pd.to_datetime(
    datos["Fecha contabiliz."],
    errors="coerce",
    dayfirst=True
)

# Cantidad e importe.

datos["Cantidad"] = convertir_numero(
    datos["Ctd.en UM entrada"]
)

datos["Importe"] = convertir_numero(
    datos["Impte.mon.local"]
)



# =====================================================
# 10. CRUCE CON EL MAESTRO DE PROVEEDORES
# =====================================================

# Excel de precios:
# Columna Proveedor = código del proveedor.
#
# MRP:
# Columna Acreedor = código del proveedor.
# Columna Proveedor = nombre del proveedor.

# Renombrar la columna del maestro para evitar
# conflictos con la columna Proveedor del Excel de precios.

maestro_proveedores_limpio = maestro_proveedores.rename(
    columns={
        "Proveedor": "Nombre proveedor"
    }
).copy()

# Realizar el cruce utilizando los códigos.

datos = datos.merge(
    maestro_proveedores_limpio,
    left_on="Codigo proveedor",
    right_on="Acreedor",
    how="left"
)

# Identificar códigos que no encontraron coincidencia.

proveedores_sin_match = (
    datos.loc[
        datos["Nombre proveedor"].isna(),
        "Codigo proveedor"
    ]
    .drop_duplicates()
    .tolist()
)

# Si no existe coincidencia, conservar una referencia
# al código para identificar el registro.

datos["Nombre proveedor"] = (
    datos["Nombre proveedor"].fillna(
        datos["Codigo proveedor"].apply(
            lambda x: f"Proveedor no encontrado ({x})"
        )
    )
)

# Eliminar columna auxiliar del cruce.

datos = datos.drop(
    columns=["Acreedor"],
    errors="ignore"
)

# =====================================================
# 11. CRUCE CON EL MAESTRO DE MATERIALES
# =====================================================

datos = datos.merge(
    maestro_materiales,
    on="Material",
    how="left"
)

# Si un código no aparece en el MRP,
# se conserva la descripción del Excel de precios.

datos["Descripción"] = (
    datos["Descripción MRP"]
    .fillna("")
    .astype(str)
    .str.strip()
)

datos.loc[
    datos["Descripción"] == "",
    "Descripción"
] = datos.loc[
    datos["Descripción"] == "",
    "Descripción Excel"
]

datos = datos[
    datos["Descripción"].astype(str).str.strip() != ""
].copy()

# Crear una clave común para agrupar códigos equivalentes.

datos["Clave material"] = (
    datos["Descripción"]
    .apply(normalizar_material)
)


# =====================================================
# 12. FILTRAR MOVIMIENTOS SAP
# =====================================================

datos["Clase de movimiento"] = limpiar_texto(
    datos["Clase de movimiento"]
)

datos = datos[
    datos["Clase de movimiento"].isin(["101", "102"])
].copy()

datos = datos.dropna(
    subset=[
        "Material",
        "Fecha",
        "Cantidad",
        "Importe"
    ]
)

datos = datos[
    (datos["Cantidad"] != 0)
    & (datos["Importe"] != 0)
].copy()


if datos.empty:

    st.warning(
        "No existen movimientos válidos para analizar."
    )

    st.stop()


# =====================================================
# 13. CONSOLIDAR MATERIALES Y ÓRDENES DE COMPRA
# =====================================================

# Los códigos que tienen la misma descripción en el MRP
# se agrupan como una sola materia prima.
#
# Se conservan todos los códigos asociados.
#
# Se agrupan las posiciones de una misma OC para obtener
# un precio unitario ponderado por cantidad.

agrupacion = [
    "Clave material",
    "Pedido",
    "Moneda",
    "Codigo proveedor",
    "Nombre proveedor"
]

datos_precios = (
    datos
    .groupby(
        agrupacion,
        dropna=False
    )
    .agg(
        Fecha=("Fecha", "min"),
        Cantidad=("Cantidad", "sum"),
        Importe=("Importe", "sum"),
        Codigos_material=("Material", unir_codigos),
        Descripción=("Descripción", "first")
    )
    .reset_index()
)

# Precio unitario.

datos_precios["Precio unitario"] = (
    datos_precios["Importe"].abs()
    / datos_precios["Cantidad"].abs()
)

# Eliminar registros sin cantidad neta.

datos_precios = datos_precios[
    (datos_precios["Cantidad"] != 0)
    & (datos_precios["Precio unitario"] > 0)
    & (datos_precios["Fecha"].notna())
].copy()

datos_precios = datos_precios.sort_values(
    "Fecha"
).reset_index(drop=True)


if datos_precios.empty:

    st.warning(
        "No existen precios unitarios válidos para mostrar."
    )

    st.stop()


# =====================================================
# 14. ENCABEZADO
# =====================================================

st.title("Evolución de precios")

st.markdown(
    '<div class="plant-description">'
    'Análisis histórico de precios de compra de materias '
    'primas de la planta Río Loa.'
    '</div>',
    unsafe_allow_html=True
)

encabezado = (
    '<div style="'
    'background:linear-gradient(110deg,#173B65,#245A91);'
    'padding:28px;'
    'border-radius:12px;'
    'margin-bottom:25px;'
    '">'
    '<div style="'
    'color:#DCEAF8;'
    'font-size:13px;'
    'font-weight:600;'
    'letter-spacing:1.5px;'
    '">'
    'ANÁLISIS INDIVIDUAL'
    '</div>'
    '<div style="'
    'color:white;'
    'font-size:30px;'
    'font-weight:700;'
    'margin-top:5px;'
    '">'
    'RÍO LOA'
    '</div>'
    '<div style="'
    'color:#DCEAF8;'
    'font-size:15px;'
    'margin-top:5px;'
    '">'
    'Calama | Enaex Chile | Centro E024'
    '</div>'
    '</div>'
)

st.markdown(
    encabezado,
    unsafe_allow_html=True
)


# =====================================================
# 15. MATERIAS PRIMAS CON MAYORES VARIACIONES
# =====================================================

st.subheader(
    "Materias primas con mayores variaciones de precios"
)

st.markdown(
    "Se identifican las materias primas que presentan "
    "los mayores cambios entre su primer y último precio "
    "registrado, comparando siempre dentro de una misma moneda."
)

resultados_ranking = []

ranking_base = datos_precios.sort_values(
    "Fecha"
).copy()

for (clave_material, moneda), grupo in ranking_base.groupby(
    ["Clave material", "Moneda"]
):

    grupo = grupo.sort_values("Fecha")

    if len(grupo) < 2:
        continue

    primer_registro = grupo.iloc[0]
    ultimo_registro = grupo.iloc[-1]

    precio_inicial = primer_registro["Precio unitario"]
    precio_final = ultimo_registro["Precio unitario"]

    if precio_inicial <= 0:
        continue

    variacion = (
        (precio_final - precio_inicial)
        / precio_inicial
    ) * 100

    resultados_ranking.append({

        "Código(s)": unir_codigos(
            grupo["Codigos_material"]
        ),

        "Materia prima": primer_registro["Descripción"],

        "Moneda": moneda,

        "Precio inicial": precio_inicial,

        "Precio más reciente": precio_final,

        "Variación (%)": variacion,

        "Variación absoluta (%)": abs(variacion)

    })


ranking = pd.DataFrame(resultados_ranking)

if not ranking.empty:

    ranking = ranking.sort_values(
        "Variación absoluta (%)",
        ascending=False
    ).head(4).copy()

    ranking["Precio inicial"] = ranking[
        "Precio inicial"
    ].apply(
        lambda x: formato_numero(x, 2)
    )

    ranking["Precio más reciente"] = ranking[
        "Precio más reciente"
    ].apply(
        lambda x: formato_numero(x, 2)
    )

    ranking["Variación (%)"] = ranking[
        "Variación (%)"
    ].apply(
        lambda x: (
            f"+{formato_numero(x, 2)}%"
            if x > 0
            else f"{formato_numero(x, 2)}%"
        )
    )

    ranking = ranking[
        [
            "Código(s)",
            "Materia prima",
            "Moneda",
            "Precio inicial",
            "Precio más reciente",
            "Variación (%)"
        ]
    ]

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No hay suficientes registros para calcular "
        "variaciones de precios."
    )


st.divider()


# =====================================================
# 16. BUSCADOR DE MATERIAS PRIMAS
# =====================================================

st.subheader(
    "Análisis individual de materias primas"
)

st.markdown(
    "Busca una materia prima por su código o nombre "
    "para consultar la evolución de sus precios."
)

# Crear catálogo agrupado por descripción del MRP.

catalogo = (
    datos_precios
    .groupby(
        "Clave material",
        as_index=False
    )
    .agg(
        Descripción=("Descripción", "first"),
        Codigos_material=("Codigos_material", unir_codigos)
    )
)

catalogo = catalogo.sort_values(
    "Descripción"
).reset_index(drop=True)

catalogo["Etiqueta"] = (
    catalogo["Codigos_material"].astype(str)
    + " -- "
    + catalogo["Descripción"].astype(str)
)

# Barra de búsqueda.

busqueda = st.text_input(
    "Buscar materia prima",
    placeholder="Ingresa el código o nombre del material..."
)

catalogo_filtrado = catalogo.copy()

if busqueda:

    catalogo_filtrado = catalogo_filtrado[
        catalogo_filtrado["Codigos_material"].str.contains(
            busqueda,
            case=False,
            na=False,
            regex=False
        )
        |
        catalogo_filtrado["Descripción"].str.contains(
            busqueda,
            case=False,
            na=False,
            regex=False
        )
    ]

if catalogo_filtrado.empty:

    st.warning(
        "No se encontraron materias primas con esa búsqueda."
    )

    st.stop()

# Lista desplegable.

seleccion = st.selectbox(
    "Seleccionar materia prima",
    catalogo_filtrado["Etiqueta"].tolist()
)

material_seleccionado = catalogo_filtrado[
    catalogo_filtrado["Etiqueta"] == seleccion
].iloc[0]

clave_seleccionada = material_seleccionado[
    "Clave material"
]

# Obtener todos los registros de los códigos agrupados.

detalle = datos_precios[
    datos_precios["Clave material"] == clave_seleccionada
].copy()

detalle = detalle.sort_values(
    "Fecha"
).reset_index(drop=True)

st.markdown(
    f"### {material_seleccionado['Descripción']}"
)

st.caption(
    "Código(s) de material: "
    + str(material_seleccionado["Codigos_material"])
)


# =====================================================
# 17. INDICADORES DEL MATERIAL
# =====================================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Órdenes de compra",
    detalle["Pedido"].nunique()
)

col2.metric(
    "Primer registro",
    detalle["Fecha"].min().strftime("%d-%m-%Y")
)

col3.metric(
    "Último registro",
    detalle["Fecha"].max().strftime("%d-%m-%Y")
)


# =====================================================
# 18. MONEDAS DEL MATERIAL
# =====================================================

st.subheader(
    "Moneda de los precios registrados"
)

monedas = sorted(
    detalle["Moneda"]
    .dropna()
    .unique()
    .tolist()
)

columnas_monedas = st.columns(
    max(len(monedas), 1)
)

for i, moneda in enumerate(monedas):

    columnas_monedas[i].metric(
        "Moneda registrada",
        moneda
    )

st.caption(
    "Los precios se presentan en su moneda original. "
    "CLP y USD se muestran en escalas separadas."
)


# =====================================================
# 19. GRÁFICO DE EVOLUCIÓN DE PRECIOS
# =====================================================

st.subheader(
    "Evolución histórica de precios por orden de compra"
)

if detalle.empty:

    st.info(
        "No existen órdenes de compra para este material."
    )

else:

    detalle_grafico = detalle.copy()

    detalle_grafico["Fecha de OC"] = (
        detalle_grafico["Fecha"]
        .dt.strftime("%d-%m-%Y")
    )

    detalle_grafico["Detalle OC"] = (
        "OC: "
        + detalle_grafico["Pedido"].astype(str)
        + "<br>Proveedor: "
        + detalle_grafico["Nombre proveedor"].astype(str)
    )

    figura = px.line(
        detalle_grafico,
        x="Fecha",
        y="Precio unitario",
        color="Moneda",
        facet_row="Moneda",
        markers=True,
        hover_name="Detalle OC",
        hover_data={
            "Fecha": False,
            "Fecha de OC": True,
            "Pedido": True,
            "Nombre proveedor": True,
            "Precio unitario": ":,.2f",
            "Moneda": True
        },
        labels={
            "Fecha": "Fecha de la OC",
            "Precio unitario": "Precio unitario",
            "Moneda": "Moneda"
        },
        color_discrete_map={
            "CLP": "#245A91",
            "USD": "#D97706"
        }
    )

    figura.update_traces(
        mode="lines+markers",
        line=dict(width=3),
        marker=dict(size=9)
    )

    figura.update_layout(
        height=max(430, 300 * len(monedas)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Arial",
            size=12,
            color="#334155"
        ),
        hovermode="closest",
        showlegend=False,
        margin=dict(
            l=20,
            r=20,
            t=35,
            b=30
        )
    )

    figura.update_xaxes(
        title_text="Fecha de la OC",
        showgrid=True,
        gridcolor="#E2E8F0",
        tickformat="%d-%m-%Y"
    )

    figura.update_yaxes(
        title_text="Precio unitario",
        showgrid=True,
        gridcolor="#E2E8F0",
        tickformat=",.2f"
    )

    st.plotly_chart(
        figura,
        use_container_width=True
    )


# =====================================================
# 20. TABLA DE DETALLE DE ÓRDENES DE COMPRA
# =====================================================

st.subheader(
    "Detalle de órdenes de compra"
)

st.markdown(
    "A continuación se presentan los registros utilizados "
    "para construir el gráfico de evolución de precios."
)

tabla_detalle = detalle[
    [
        "Codigos_material",
        "Descripción",
        "Pedido",
        "Fecha",
        "Precio unitario",
        "Moneda",
        "Nombre proveedor"
    ]
].copy()

tabla_detalle = tabla_detalle.rename(
    columns={
        "Codigos_material": "Código(s) de material",
        "Descripción": "Nombre del material",
        "Pedido": "N.º de OC",
        "Fecha": "Fecha de OC (contabilización)",
        "Precio unitario": "Precio unitario",
        "Moneda": "Moneda",
        "Nombre proveedor": "Proveedor"
    }
)

tabla_detalle = tabla_detalle.sort_values(
    "Fecha de OC (contabilización)",
    ascending=True
)

tabla_detalle[
    "Fecha de OC (contabilización)"
] = (
    tabla_detalle[
        "Fecha de OC (contabilización)"
    ].dt.strftime("%d-%m-%Y")
)

tabla_detalle["Precio unitario"] = (
    tabla_detalle["Precio unitario"]
    .apply(
        lambda x: formato_numero(x, 2)
    )
)

st.dataframe(
    tabla_detalle,
    use_container_width=True,
    hide_index=True
)


# =====================================================
# 21. PROVEEDORES SIN COINCIDENCIA
# =====================================================

if proveedores_sin_match:

    with st.expander(
        "Revisar códigos de proveedores sin coincidencia"
    ):

        st.warning(
            "Algunos códigos de proveedor del Excel de precios "
            "no se encontraron en la columna Acreedor del MRP."
        )

        st.dataframe(
            pd.DataFrame({
                "Código de proveedor sin coincidencia":
                proveedores_sin_match
            }),
            use_container_width=True,
            hide_index=True
        )


# =====================================================
# 22. PIE DE PÁGINA
# =====================================================

st.markdown(
    '<div style="'
    'text-align:center;'
    'color:#8492A6;'
    'font-size:12px;'
    'margin-top:45px;'
    'padding:15px;'
    '">'
    'ENAEX CHILE | EVOLUCIÓN DE PRECIOS DE MATERIAS PRIMAS'
    ' | RÍO LOA'
    '</div>',
    unsafe_allow_html=True
)
