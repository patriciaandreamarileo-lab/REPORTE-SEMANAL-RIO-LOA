
# =====================================================
# 12. DISTRIBUCIÓN Y ANÁLISIS DE MATERIAS PRIMAS
# =====================================================

st.subheader("Distribución de materias primas")

# -----------------------------------------------------
# 12.1 GRÁFICO CIRCULAR EB, BB Y SB
# -----------------------------------------------------

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
        .reindex(["BB", "EB", "SB"], fill_value=0)
    )

    total_clasificados = int(conteo.sum())

    if total_clasificados > 0:

        datos_grafico = pd.DataFrame({
            "Clasificación": ["BB", "EB", "SB"],
            "Cantidad": [
                int(conteo["BB"]),
                int(conteo["EB"]),
                int(conteo["SB"])
            ]
        })

        datos_grafico["Porcentaje"] = (
            datos_grafico["Cantidad"]
            .apply(lambda x: f"{x / total_clasificados:.1%}")
        )

        especificacion = {

            "layer": [

                {
                    "mark": {
                        "type": "arc",
                        "outerRadius": 145,
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
                                    "#E52525",
                                    "#16A34A",
                                    "#007BFF"
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
                                "title": "Clasificación"
                            },
                            {
                                "field": "Cantidad",
                                "title": "Materias primas"
                            },
                            {
                                "field": "Porcentaje",
                                "title": "Porcentaje"
                            }
                        ]
                    }
                },

                {
                    "mark": {
                        "type": "text",
                        "radius": 95,
                        "fontSize": 17,
                        "fontWeight": "bold",
                        "fill": "white"
                    },

                    "encoding": {

                        "theta": {
                            "field": "Cantidad",
                            "type": "quantitative",
                            "stack": True
                        },

                        "text": {
                            "field": "Porcentaje",
                            "type": "nominal"
                        }
                    }
                }
            ],

            "view": {
                "stroke": None
            },

            "width": 500,
            "height": 370
        }

        col_izq, col_grafico, col_der = st.columns([1, 4, 1])

        with col_grafico:

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

        st.info("No existen clasificaciones EB, BB o SB.")

else:

    st.warning("No se encontró la columna NS Corregido.")


st.divider()


# =====================================================
# 13. CINCO MATERIAS PRIMAS CON MENOR STOCK
# =====================================================

st.subheader("Cinco materias primas con menor stock")

st.markdown(
    "Identificación de los materiales que presentan "
    "las menores cantidades disponibles en la planta."
)

if (
    not datos_activos.empty
    and "Stock Actual" in datos_activos.columns
):

    menor_stock = (
        datos_activos
        .dropna(subset=["Stock Actual"])
        .sort_values(
            by="Stock Actual",
            ascending=True
        )
        .head(5)
        .copy()
    )

    columnas_stock = [
        "Material",
        "Descripción del material",
        "UM",
        "Stock Actual",
        "Stock Seguridad",
        "NS Corregido"
    ]

    disponibles = [
        c for c in columnas_stock
        if c in menor_stock.columns
    ]

    if not menor_stock.empty:

        st.dataframe(
            menor_stock[disponibles],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No existen datos de stock disponibles.")

else:

    st.info("No se encontró información de stock actual.")


st.divider()


# =====================================================
# 14. CINCO MATERIAS PRIMAS CON MENOR CONSUMO
#     Y MAYOR COBERTURA
# =====================================================

st.subheader(
    "Materias primas con menor consumo y mayor cobertura"
)

st.markdown(
    "Identificación de materiales con menor consumo promedio "
    "y mayor cantidad de días de cobertura disponible."
)

if (
    not datos_activos.empty
    and "Consumo X̄" in datos_activos.columns
    and "Cobertura a [Días]" in datos_activos.columns
):

    menor_consumo = datos_activos.dropna(
        subset=["Consumo X̄", "Cobertura a [Días]"]
    ).copy()

    # Considerar consumos positivos
    menor_consumo = menor_consumo[
        menor_consumo["Consumo X̄"] > 0
    ]

    # Ordenar primero por menor consumo
    # y luego por mayor cobertura

    menor_consumo = menor_consumo.sort_values(
        by=[
            "Consumo X̄",
            "Cobertura a [Días]"
        ],
        ascending=[
            True,
            False
        ]
    ).head(5)

    columnas_consumo = [
        "Material",
        "Descripción del material",
        "UM",
        "Consumo X̄",
        "Stock Actual",
        "Cobertura a [Días]"
    ]

    disponibles = [
        c for c in columnas_consumo
        if c in menor_consumo.columns
    ]

    if not menor_consumo.empty:

        st.dataframe(
            menor_consumo[disponibles],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No existen materiales con consumo positivo "
            "y cobertura disponible."
        )

else:

    st.info(
        "No se encontraron las columnas necesarias "
        "para realizar este análisis."
    )


st.divider()


# =====================================================
# 15. ALERTA DE MATERIAS PRIMAS CON MENOS DE 10 DÍAS
# =====================================================

st.subheader("Alertas de cobertura")

st.markdown(
    "Materias primas cuya cobertura disponible "
    "es inferior a 10 días."
)

if (
    not datos_activos.empty
    and "Cobertura a [Días]" in datos_activos.columns
):

    alertas_cobertura = datos_activos[
        datos_activos["Cobertura a [Días]"].notna()
        &
        (datos_activos["Cobertura a [Días]"] < 10)
    ].copy()

    alertas_cobertura = alertas_cobertura.sort_values(
        by="Cobertura a [Días]",
        ascending=True
    )

    if not alertas_cobertura.empty:

        st.error(
            f"¡ATENCIÓN! Se identificaron "
            f"{len(alertas_cobertura)} materias primas "
            f"con menos de 10 días de cobertura."
        )

        columnas_alerta = [
            "Material",
            "Descripción del material",
            "UM",
            "Consumo X̄",
            "Stock Actual",
            "Cobertura a [Días]",
            "NS Corregido",
            "Comentario"
        ]

        disponibles = [
            c for c in columnas_alerta
            if c in alertas_cobertura.columns
        ]

        st.dataframe(
            alertas_cobertura[disponibles],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No existen materias primas con cobertura "
            "inferior a 10 días."
        )

else:

    st.info(
        "No hay información disponible para generar "
        "las alertas de cobertura."
    )

st.divider()
